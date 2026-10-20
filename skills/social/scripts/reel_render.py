#!/usr/bin/env python3
"""
reel_render.py — turn a reel manifest into actual 1080x1920 MP4 files.

Formats (per _Shared/Facebook-Shared/Reels/reels-mechanics.md):

  S  Static winning-image reel. The banked screenshot IS the visual — we hold it
     on a blurred fill with a slow push. NO text is drawn over it; the card's own
     headline is the message, and redrawing it would double the words.
  N  News-clash / quote / number reel. Numbered lines reveal one at a time so the
     viewer has to stay for the payoff.
  B  Short open-loop hook. One withholding line held over calm motion; the value
     lives in the caption.

Composition is done in Pillow (reliable wrapping, kerning and shadows) and ffmpeg
only handles motion, audio and encoding. That avoids drawtext's escaping traps
with apostrophes, colons and em dashes — all of which are common in these specs.

Ported for Yeez from the Clark Bros Media network's reel renderer. yeez_build.py drives it:
footage comes from the buyer's own folders (yeez-work/footage/broll/<mood>/, music in
yeez-work/footage/music/). RENDER ONLY: writes MP4s to disk, never posts.

Usage:
    python3 reel_render.py --manifest manifest-2026-08-15.json --out ./out
    python3 reel_render.py --manifest m.json --out ./out --only TRW --duration 32
"""

import argparse
import csv
import json
import math
import os
import random
import shutil
import subprocess
import sys
import tempfile
from datetime import datetime

from PIL import Image, ImageDraw, ImageFilter, ImageFont

# ---------------------------------------------------------------- canvas

W, H = 1080, 1920
FPS = 30

# x264 speed/size tradeoff for the FINAL encode. Default "medium" — unchanged
# from every night rendered before 2026-09-02, so Alex's Mac behaves exactly as
# before. The Cowork sandbox caps a shell call at ~175s and kills backgrounded
# processes, and a "medium" reel costs 145-175s there, so the walk harness sets
# REEL_X264_PRESET=faster to finish inside one call. Same CRF, so quality is
# visually equivalent; files run a few MB larger. Encoder knob only — it does
# not touch footage selection, music, timing, or a single word of the spec.
X264_PRESET = os.environ.get("REEL_X264_PRESET", "faster")

# Facebook's Reels chrome eats the top and bottom of the frame. Everything that
# must be readable lives inside this box.
SAFE_TOP = 430
SAFE_BOTTOM = 1400
SAFE_X = 90
SAFE_W = W - (SAFE_X * 2)
SAFE_H = SAFE_BOTTOM - SAFE_TOP

# ---- Caption-card style, measured off the reference reel -------------------
# "Claimed social security too early - Ask Retirement.mp4" (1080x1920):
#   white box  x 41-1038 (998w)  y 786-1015 (230h)   black text
#   red box    x 178-900 (723w)  y 1044-1132 (89h)   white text, shrink-to-fit
#   ~72px line pitch, ~20px corner radius, 29px gap between the boxes
CARD_MAX_W = 998          # 1080 - 2*41
CARD_X_MARGIN = (W - CARD_MAX_W) // 2
CARD_TOP = 786            # top of the white box
CARD_PAD_X = 30
CARD_PAD_Y = 10
CARD_RADIUS = 20
CARD_GAP = 29             # white box bottom -> red box top
CARD_LINE_RATIO = 1.29    # 72px pitch at a 56px face

WHITE_BOX = (255, 255, 255, 255)
WHITE_BOX_TEXT = (0, 0, 0, 255)
RED_BOX = (252, 6, 5, 255)
RED_BOX_TEXT = (255, 255, 255, 255)

# The fitter searches down from MAX; dropping under MIN means the line is too
# long for the format and gets flagged in QA rather than shrunk to something
# nobody can read on a phone.
FONT_MAX = 58
FONT_MIN = 34

# Drop the real caption font (.ttf/.otf) into assets/fonts/ and it wins over
# everything else. The reference reel's lettering has a DOUBLE-STOREY 'a', so
# it is definitely not Poppins — Poppins' 'a' is a single-storey geometric
# circle. Poppins stays last only as a can't-render-nothing fallback.
FONT_CANDIDATES = [
    "/usr/share/fonts/truetype/google-fonts/Montserrat-Bold.ttf",
    "/usr/share/fonts/truetype/google-fonts/Poppins-Bold.ttf",
    "/usr/share/fonts/truetype/lato/Lato-Bold.ttf",
    "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
]


def find_font():
    """Yeez bundles Montserrat Bold (SIL OFL) next to this file; system fonts are the fallback."""
    local = os.path.join(os.path.dirname(os.path.abspath(__file__)), "fonts", "Montserrat-Bold.ttf")
    if os.path.exists(local):
        return local
    for path in FONT_CANDIDATES:
        if os.path.exists(path):
            return path
    raise SystemExit("ERROR: no usable bold font found on this system.")

DEFAULT_DURATION = 30.0   # reels-mechanics: "make every reel 30-40 seconds"
MIN_CARD_SECONDS = 3.0    # no card flashes past faster than this
HOOK_MIN_SECONDS = 3.0    # "hook in the first 3 seconds"


FONT_PATH = find_font()


# ---------------------------------------------------------------- text layout

def wrap_to_width(text, font, max_width, draw):
    """Greedy wrap; falls back to hard-splitting a single oversized word."""
    words, lines, cur = text.split(), [], ""
    for word in words:
        trial = f"{cur} {word}".strip()
        if draw.textlength(trial, font=font) <= max_width or not cur:
            cur = trial
        else:
            lines.append(cur)
            cur = word
    if cur:
        lines.append(cur)

    out = []
    for line in lines:
        if draw.textlength(line, font=font) <= max_width:
            out.append(line)
            continue
        buf = ""
        for ch in line:
            if draw.textlength(buf + ch, font=font) <= max_width or not buf:
                buf += ch
            else:
                out.append(buf)
                buf = ch
        if buf:
            out.append(buf)
    return out


def fit_text(text, box_w, box_h, draw, max_size=FONT_MAX, min_size=FONT_MIN):
    """
    Largest font size at which the wrapped text fits the box.
    Returns (font, lines, size, overflowed).
    """
    best = None
    for size in range(max_size, min_size - 1, -2):
        font = ImageFont.truetype(FONT_PATH, size)
        lines = wrap_to_width(text, font, box_w, draw)
        line_h = int(size * 1.26)
        if line_h * len(lines) <= box_h:
            return font, lines, size, False
        best = (font, lines, size)
    # Nothing fit; use the floor size and flag it.
    font = ImageFont.truetype(FONT_PATH, min_size)
    lines = wrap_to_width(text, font, box_w, draw)
    return font, lines, min_size, True


# Keep each card short so the footage stays visible behind it. Roughly two
# lines at the reference face size.
MAX_CARD_CHARS = 72

_SENTENCE_RE = None


def split_sentences(text):
    import re as _re
    parts = _re.split(r"(?<=[.!?])\s+", text.strip())
    return [p.strip() for p in parts if p.strip()]


def split_clause(text, limit):
    """Break an over-long sentence at the most natural internal seam."""
    for sep in ("—", " - ", ";", ":", ","):
        if sep in text:
            head, _, tail = text.partition(sep)
            head, tail = head.strip(), tail.strip()
            keep = sep if sep in ("—",) else ""
            if head and tail:
                return [f"{head}{keep}".strip(), tail]
    # No seam: split on the nearest word boundary to the midpoint.
    words = text.split()
    if len(words) < 4:
        return [text]
    mid = len(words) // 2
    return [" ".join(words[:mid]), " ".join(words[mid:])]


def chunk_text(text, limit=MAX_CARD_CHARS):
    """
    Turn one on-screen field into a sequence of short cards.

    Sentence first, then clause, so the reveal breaks where the writer's own
    punctuation says it should. A single huge block would cover the footage,
    which is the whole point of shooting b-roll.
    """
    out = []
    for sentence in split_sentences(text):
        if len(sentence) <= limit:
            out.append(sentence)
            continue
        queue = [sentence]
        while queue:
            piece = queue.pop(0)
            if len(piece) <= limit:
                out.append(piece)
                continue
            halves = split_clause(piece, limit)
            if len(halves) == 1:
                out.append(piece)
            else:
                queue = halves + queue
    return out or [text]


# All of a reel's text now sits in one card, so the box has to accommodate a
# longer block. Hold the face size and let it wrap; only shrink once it will
# not fit at all, because small text is the one thing that fails on a phone.
MAX_CARD_LINES = 7


def _fit_card(text, draw, max_text_w):
    """Largest face size at which `text` wraps to at most MAX_CARD_LINES."""
    for size in range(FONT_MAX, FONT_MIN - 1, -2):
        font = ImageFont.truetype(FONT_PATH, size)
        lines = wrap_to_width(text, font, max_text_w, draw)
        if len(lines) <= MAX_CARD_LINES:
            return font, lines, size, False
    font = ImageFont.truetype(FONT_PATH, FONT_MIN)
    return font, wrap_to_width(text, font, max_text_w, draw), FONT_MIN, True


# ---------------------------------------------------------------- row stack
#
# The real house style, measured off 13 reference reels (2026-08-16).
# "Reel 31 - Cost of Living.mov" is the cleanest specimen:
#
#   row 1  y  228- 292  h=64  w=794  WHITE  title / setup
#   row 2  y  373- 447  h=74  w=544  BLACK  data line
#   row 3  y  523- 597  h=74  w=578  BLACK
#   row 4  y  673- 747  h=74  w=476  BLACK
#   row 5  y  823- 897  h=74  w=726  BLACK
#   row 6  y  978-1042  h=64  w=612  WHITE  summary
#   row 7  y 1128-1192  h=64  w=956  RED    kicker
#
# Every row is its own shrink-to-fit box, centred on x=540, at a 150px pitch,
# and EVERY row is on screen from t=0 for the whole runtime. No animation.
ROW_PITCH = 150          # reference row-to-row pitch for single-line rows
ROW_GAP = 78             # measured edge-to-edge gap between boxes
ROW_PAD_X = 24
ROW_PAD_Y = 15
ROW_RADIUS = 10
ROW_FONT = 42
ROW_FONT_MIN = 26
ROW_MAX_W = 1000
STACK_CENTER_Y = 710      # measured centre of the Reel 31 block
STACK_MIN_TOP = 200

ROW_STYLES = {
    "white": ((255, 255, 255, 255), (0, 0, 0, 255)),
    "black": ((0, 0, 0, 235), (255, 255, 255, 255)),
    "red":   ((252, 6, 5, 255), (255, 255, 255, 255)),
}


def assign_row_styles(n, seed=None):
    """
    Colour pattern for an n-row stack, VARIED per reel.

    Alex, 2026-08-16: there is no fixed pattern in the reference set, so do not
    impose one. Reel 31 runs title / data / summary / kicker; Reel 49 alternates
    white and black; others are mostly-white. We pick among those observed
    shapes, seeded per reel so a given reel is stable across re-renders while
    the network as a whole varies.

    Varying also helps §5: a single rigid visual formula across 60-100 pages is
    exactly the look-alike-network signature that gets pages throttled.
    """
    if n <= 0:
        return []
    if n == 1:
        return ["white"]
    if n == 2:
        return ["white", "red"]

    rnd = random.Random(seed)

    def ladder():        # Reel 31: title, data block, summary, kicker
        s = ["white"] + ["black"] * (n - 2) + ["red"]
        if n >= 4:
            s[-2] = "white"
        return s

    def alternating():   # Reel 49
        s = ["white" if i % 2 == 0 else "black" for i in range(n)]
        s[-1] = "red"
        return s

    def mostly_white():
        s = ["white"] * n
        s[-1] = "red"
        if n >= 5:
            s[n // 2] = "black"
        return s

    def mostly_black():
        s = ["black"] * n
        s[0] = "white"
        s[-1] = "red"
        return s

    def no_kicker():     # some reels end on a white summary, no red at all
        s = ["white"] + ["black"] * (n - 1)
        s[-1] = "white"
        return s

    return rnd.choice([ladder, alternating, mostly_white,
                       mostly_black, no_kicker])()


def draw_row_stack(img, rows, center_y=STACK_CENTER_Y):
    """
    Draw the stacked ladder. `rows` is a list of (text, style) pairs.
    Returns (font_size, overflowed).
    """
    draw = ImageDraw.Draw(img)
    max_text_w = ROW_MAX_W - ROW_PAD_X * 2

    # One face size for the whole stack, stepped down until every row fits on
    # at most two lines. A stack with mixed sizes reads as sloppy.
    size, overflowed = ROW_FONT, False
    while size > ROW_FONT_MIN:
        font = ImageFont.truetype(FONT_PATH, size)
        if all(len(wrap_to_width(t, font, max_text_w, draw)) <= 2
               for t, _s in rows):
            break
        size -= 2
    else:
        overflowed = True
    font = ImageFont.truetype(FONT_PATH, size)
    line_h = int(size * 1.25)

    # Lay out first so the whole block can be centred vertically.
    laid = []
    for text, style in rows:
        lines = wrap_to_width(text, font, max_text_w, draw)
        ink_top, ink_bottom = _ink_extents(lines, font, line_h)
        box_h = int((ink_bottom - ink_top) + ROW_PAD_Y * 2)
        text_w = max((draw.textlength(l, font=font) for l in lines), default=0)
        box_w = int(min(ROW_MAX_W, text_w + ROW_PAD_X * 2))
        laid.append((lines, style, box_w, box_h, ink_top))

    # Constant GAP between boxes, not a constant pitch. Reference rows sit
    # ~78px apart edge-to-edge; a fixed pitch would open a hole under any row
    # that wrapped to two lines.
    total_h = sum(b[3] for b in laid) + ROW_GAP * (len(laid) - 1)
    y = max(STACK_MIN_TOP, int(center_y - total_h / 2))

    for lines, style, box_w, box_h, ink_top in laid:
        bg, fg = ROW_STYLES[style]
        box_x = (W - box_w) // 2
        draw.rounded_rectangle([box_x, y, box_x + box_w, y + box_h],
                               radius=ROW_RADIUS, fill=bg)
        ty = y + ROW_PAD_Y - ink_top
        for line in lines:
            tw = draw.textlength(line, font=font)
            draw.text(((W - tw) / 2, ty), line, font=font, fill=fg)
            ty += line_h
        y += box_h + ROW_GAP

    return size, overflowed


def _ink_extents(lines, font, line_h):
    """
    (top, bottom) of the real drawn pixels for a block of lines laid out at
    `line_h` pitch, relative to the first line's draw origin.
    """
    tops, bottoms = [], []
    for i, line in enumerate(lines):
        bbox = font.getbbox(line)
        if bbox is None:
            continue
        tops.append(bbox[1] + i * line_h)
        bottoms.append(bbox[3] + i * line_h)
    if not tops:
        return 0, line_h * max(1, len(lines))
    return min(tops), max(bottoms)


def draw_caption_card(img, main_text, punch_text=None, top=CARD_TOP):
    """
    The reference treatment: a white rounded box of black text, optionally with
    a shrink-to-fit red box beneath it. Both are horizontally centred and both
    hug their content. Returns (size, overflowed).
    """
    draw = ImageDraw.Draw(img)
    max_text_w = CARD_MAX_W - (CARD_PAD_X * 2)

    font, lines, size, overflowed = _fit_card(main_text, draw, max_text_w)
    line_h = int(size * CARD_LINE_RATIO)

    # Measure the ACTUAL ink, not font metrics. Ascent/descent reserve room for
    # accents and descenders the glyphs may never use, which is what left more
    # air above the text than below it.
    ink_top, ink_bottom = _ink_extents(lines, font, line_h)
    ink_h = ink_bottom - ink_top

    text_w = max((draw.textlength(l, font=font) for l in lines), default=0)
    box_w = int(min(CARD_MAX_W, text_w + CARD_PAD_X * 2))
    box_h = int(ink_h + CARD_PAD_Y * 2)
    box_x = (W - box_w) // 2

    draw.rounded_rectangle([box_x, top, box_x + box_w, top + box_h],
                           radius=CARD_RADIUS, fill=WHITE_BOX)

    # Offset so the ink sits exactly CARD_PAD_Y from the top edge, which makes
    # the space above and below equal.
    y = top + CARD_PAD_Y - ink_top
    for line in lines:
        tw = draw.textlength(line, font=font)
        draw.text(((W - tw) / 2, y), line, font=font, fill=WHITE_BOX_TEXT)
        y += line_h

    if punch_text:
        pfont, plines, psize, pover = _fit_card(punch_text, draw, max_text_w)
        overflowed = overflowed or pover
        pline_h = int(psize * CARD_LINE_RATIO)
        pink_top, pink_bottom = _ink_extents(plines, pfont, pline_h)
        pink_h = pink_bottom - pink_top
        ptext_w = max((draw.textlength(l, font=pfont) for l in plines), default=0)
        pbox_w = int(min(CARD_MAX_W, ptext_w + 40 * 2))
        pbox_h = int(pink_h + 16 * 2)
        pbox_x = (W - pbox_w) // 2
        ptop = top + box_h + CARD_GAP

        draw.rounded_rectangle([pbox_x, ptop, pbox_x + pbox_w, ptop + pbox_h],
                               radius=CARD_RADIUS, fill=RED_BOX)
        py = ptop + 16 - pink_top
        for line in plines:
            tw = draw.textlength(line, font=pfont)
            draw.text(((W - tw) / 2, py), line, font=pfont, fill=RED_BOX_TEXT)
            py += pline_h

    return size, overflowed


def draw_text_block(img, text, center_y=None):
    """Compatibility wrapper used by the no-b-roll fallback path."""
    return draw_caption_card(img, text)


# ---------------------------------------------------------------- backgrounds

def gradient_background(seed=0):
    """Calm dark gradient used when no still or b-roll is available."""
    rnd = random.Random(seed)
    palettes = [
        ((14, 20, 34), (38, 52, 82)),
        ((26, 16, 20), (74, 38, 44)),
        ((12, 26, 26), (30, 66, 62)),
        ((20, 18, 30), (58, 46, 84)),
    ]
    top, bottom = rnd.choice(palettes)
    base = Image.new("RGB", (2, H))
    px = base.load()
    for y in range(H):
        t = y / (H - 1)
        px[0, y] = px[1, y] = tuple(
            int(top[i] + (bottom[i] - top[i]) * t) for i in range(3))
    img = base.resize((W, H), Image.BILINEAR).convert("RGBA")

    # Soft vignette keeps the eye centered.
    vig = Image.new("L", (W, H), 0)
    ImageDraw.Draw(vig).ellipse([-W * 0.35, -H * 0.12, W * 1.35, H * 1.12], fill=110)
    vig = vig.filter(ImageFilter.GaussianBlur(220))
    img.alpha_composite(Image.merge("RGBA", (
        Image.new("L", (W, H), 0),) * 3 + (Image.eval(vig, lambda v: 150 - v),)))
    return img


def blurred_fill(src):
    """Cover-scale + blur a still to fill the vertical frame behind itself."""
    ratio = max(W / src.width, H / src.height)
    big = src.resize((max(1, int(src.width * ratio)), max(1, int(src.height * ratio))),
                     Image.LANCZOS)
    left = (big.width - W) // 2
    top = (big.height - H) // 2
    bg = big.crop((left, top, left + W, top + H)).filter(
        ImageFilter.GaussianBlur(46)).convert("RGBA")
    # These cards are often mostly white, which blurs to a washed-out grey.
    # Push it well down so the card itself is clearly the subject.
    return Image.blend(bg, Image.new("RGBA", (W, H), (0, 0, 0, 255)), 0.46)


# The card is inset from the frame edge by more than the slow push will ever
# travel, so the zoom never crops the headline. Keep these in step with
# ZOOM_MAX["S"] below.
STILL_MAX_W = 940
STILL_MAX_H = 1380
STILL_CENTER_Y = 900   # nudged above centre; FB's chrome eats more at the bottom


def compose_still(src_path):
    """Format S frame: the card held large and centred on its own blurred fill."""
    src = Image.open(src_path).convert("RGBA")
    frame = blurred_fill(src)

    ratio = min(STILL_MAX_W / src.width, STILL_MAX_H / src.height)
    card = src.resize((max(1, int(src.width * ratio)),
                       max(1, int(src.height * ratio))), Image.LANCZOS)

    x = (W - card.width) // 2
    y = int(STILL_CENTER_Y - card.height / 2)
    y = max(60, min(y, H - card.height - 60))

    shadow = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    ImageDraw.Draw(shadow).rounded_rectangle(
        [x - 10, y - 6, x + card.width + 10, y + card.height + 16],
        radius=26, fill=(0, 0, 0, 190))
    frame.alpha_composite(shadow.filter(ImageFilter.GaussianBlur(26)))
    frame.alpha_composite(card, (x, y))
    return frame


# ---- 2026-10-12 REEL REBUILD (Alex): R1 "read it on screen" ------------------------------
# The competitor reels that win (United American Patriots 79K, Conservative Tradition 95K, Good
# Financial Cents 67K) put the WHOLE message on screen from the first frame: 6-10 short centred
# lines, big type, white words on dark boxes (or white words with a shadow), over calm footage.
FULL_FONT_MAX = 64
FULL_FONT_MIN = 40
FULL_TOP = 300            # keep clear of the Reels header
FULL_BOTTOM = 1500        # and of the caption/buttons at the bottom
FULL_CENTER_Y = 900
FULL_ROW_GAP = 16
FULL_PAD_X = 22
FULL_PAD_Y = 10


def balanced_lines(text, font, max_w, draw):
    """Wrap into the fewest lines, then even them out so no line ends with one orphan word."""
    words = text.split()
    lines = wrap_to_width(text, font, max_w, draw)
    n = len(lines)
    if n <= 1:
        return lines
    best = None
    def rec(start, k, acc):
        nonlocal best
        if k == 1:
            ln = " ".join(words[start:])
            w = draw.textlength(ln, font=font)
            if w <= max_w:
                cand = acc + [ln]
                score = max(draw.textlength(x, font=font) for x in cand) - min(draw.textlength(x, font=font) for x in cand)
                if best is None or score < best[0]:
                    best = (score, cand)
            return
        for end in range(start + 1, len(words) - k + 2):
            ln = " ".join(words[start:end])
            if draw.textlength(ln, font=font) > max_w:
                break
            rec(end, k - 1, acc + [ln])
    if len(words) <= 18:
        rec(0, n, [])
    return best[1] if best else lines


def draw_full_stack(img, rows):
    """Every line in its own dark box, one face size for the stack, centred. Returns (size, overflowed)."""
    draw = ImageDraw.Draw(img)
    max_text_w = ROW_MAX_W - FULL_PAD_X * 2
    avail = FULL_BOTTOM - FULL_TOP
    size, chosen, overflowed = FULL_FONT_MAX, None, False
    while size >= FULL_FONT_MIN:
        font = ImageFont.truetype(FONT_PATH, size)
        line_h = int(size * 1.22)
        laid = []
        for text, style in rows:
            for ln in balanced_lines(text, font, max_text_w, draw):
                laid.append((ln, style))
        total = len(laid) * (line_h + FULL_PAD_Y * 2) + FULL_ROW_GAP * (len(laid) - 1)
        one_line = len(laid) == len(rows)
        # prefer the biggest size at which every written line stays on ONE line; wrap (balanced) at 54px and below
        if total <= avail and (one_line or size <= 54):
            chosen = (font, line_h, laid, total)
            break
        size -= 2
    if chosen is None:
        overflowed = True
        font = ImageFont.truetype(FONT_PATH, FULL_FONT_MIN)
        line_h = int(FULL_FONT_MIN * 1.22)
        laid = [(ln, st) for t, st in rows for ln in wrap_to_width(t, font, max_text_w, draw)]
        total = len(laid) * (line_h + FULL_PAD_Y * 2) + FULL_ROW_GAP * (len(laid) - 1)
        chosen = (font, line_h, laid, total)
        size = FULL_FONT_MIN
    font, line_h, laid, total = chosen
    y = max(FULL_TOP, int(FULL_CENTER_Y - total / 2))
    for ln, style in laid:
        bg, fg = ROW_STYLES.get(style or "black", ROW_STYLES["black"])
        tw = draw.textlength(ln, font=font)
        bw, bh = int(tw + FULL_PAD_X * 2), line_h + FULL_PAD_Y * 2
        bx = (W - bw) // 2
        draw.rounded_rectangle([bx, y, bx + bw, y + bh], radius=12, fill=bg)
        bb = font.getbbox("Hg")
        draw.text(((W - tw) / 2, y + (bh - (bb[3] - bb[1])) / 2 - bb[1]), ln, font=font, fill=fg)
        y += bh + FULL_ROW_GAP
    return size, overflowed


def text_overlay_full(rows):
    layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    size, overflowed = draw_full_stack(layer, rows)
    return layer, size, overflowed


def text_overlay(rows):
    """
    The row stack on a fully transparent 1080x1920 layer, for compositing over
    b-roll. `rows` is a list of (text, style). Returns (layer, size, overflowed).
    """
    layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    size, overflowed = draw_row_stack(layer, rows)
    return layer, size, overflowed


# ---------------------------------------------------------------- b-roll

VIDEO_EXTS = (".mov", ".mp4", ".m4v", ".mkv", ".webm", ".avi")


def list_broll(assets_dir):
    """Every usable clip in assets/broll/, including one level of subfolders
    so the Drive layout (Porsche/, McLaren/, Beach Ocean/ ...) can be mirrored."""
    root = os.path.join(assets_dir, "broll")
    if not os.path.isdir(root):
        return []
    clips = []
    for dirpath, _dirnames, filenames in os.walk(root):
        for fn in filenames:
            if fn.lower().endswith(VIDEO_EXTS) and not fn.startswith("."):
                clips.append(os.path.join(dirpath, fn))
    return sorted(clips)


def clip_label(path):
    """'Porsche/IMG_2298.MOV' — the inventory-style name for the QA report."""
    parent = os.path.basename(os.path.dirname(path))
    return f"{parent}/{os.path.basename(path)}"


def ensure_proxy(clip, assets_dir, duration=DEFAULT_DURATION):
    """
    Source footage is 4K (2160x3840 and 3840x2160). Decoding that per reel is
    the slowest part of a batch, so transcode once to a 1080x1920 proxy and
    reuse it. The crop happens here, so the proxy is already 9:16.

    Returns the proxy path, or the original clip if the transcode fails.
    """
    proxy_dir = os.path.join(assets_dir, "_proxies")
    os.makedirs(proxy_dir, exist_ok=True)
    # v2 = natural-length proxies (v1 looped each clip to fill the runtime,
    # which prevented joining clips together). Bump this to invalidate.
    key = f"{os.path.basename(os.path.dirname(clip))}__{os.path.basename(clip)}"
    proxy = os.path.join(proxy_dir, os.path.splitext(key)[0] + ".v2.mp4")

    # A proxy left behind by an interrupted run can be truncated, which ffmpeg
    # only discovers later as "moov atom not found". Verify it decodes.
    if os.path.exists(proxy) and _decodes(proxy):
        return proxy

    # Write to a temp name and rename only on success, so an interrupted run
    # never leaves a half-file that looks valid by size alone.
    # NOTE the extension order: ffmpeg picks the muxer from the FINAL suffix, so
    # a bare ".part" makes it fail with "Unable to find a suitable output
    # format". That failure was swallowed by the except below and every reel
    # silently fell back to raw 4K clips, which then broke the concat.
    tmp = proxy + ".part.mp4"
    try:
        # Keep the clip's NATURAL length — no looping, no trimming. Short clips
        # get joined to siblings from the same folder instead of looping, so a
        # 9-second Porsche shot never repeats four times inside one reel.
        run([
            "ffmpeg", "-y", "-loglevel", "error",
            "-i", clip,
            "-vf", f"scale={W}:{H}:force_original_aspect_ratio=increase,"
                   f"crop={W}:{H},setsar=1,fps={FPS}",
            "-an", "-c:v", "libx264", "-preset", "veryfast", "-crf", "20",
            "-pix_fmt", "yuv420p", "-movflags", "+faststart",
            "-f", "mp4", tmp,
        ])
        if not _decodes(tmp):
            raise RuntimeError("proxy did not decode after transcode")
        os.replace(tmp, proxy)
        return proxy
    except Exception as exc:
        if os.path.exists(tmp):
            try:
                os.remove(tmp)
            except OSError:
                pass
        # Do NOT quietly hand back the raw clip. Originals are 4K and of mixed
        # orientation; concatenating them produces frozen segments. Failing
        # loudly here is what surfaces the problem instead of shipping it.
        raise RuntimeError(f"proxy build failed for {clip_label(clip)}: {exc}")


def _decodes(path):
    """True if ffprobe can read a video stream and a duration out of `path`."""
    if not os.path.exists(path) or os.path.getsize(path) < 10000:
        return False
    proc = subprocess.run(
        ["ffprobe", "-v", "error", "-select_streams", "v:0",
         "-show_entries", "stream=codec_name", "-show_entries", "format=duration",
         "-of", "csv=p=0", path],
        capture_output=True, text=True)
    return proc.returncode == 0 and proc.stdout.strip() != ""


def clip_duration(path):
    proc = subprocess.run(
        ["ffprobe", "-v", "error", "-show_entries", "format=duration",
         "-of", "csv=p=0", path], capture_output=True, text=True)
    try:
        return float(proc.stdout.strip())
    except ValueError:
        return 0.0


def category_of(path):
    return os.path.basename(os.path.dirname(path))


class BrollPicker:
    """
    Chooses footage for each reel, optimising for VARIETY across nights.

    Three things keep the background from going stale (Alex, 2026-08-16):

    1. A persistent usage ledger (broll-usage.csv). Selection is
       least-recently-used first, so rotation carries ACROSS nights instead of
       resetting every run. Without this the same few clips resurface nightly.
    2. Varied assembly. Sometimes one long clip from a fresh start offset,
       sometimes two, three or four joined — so the cut rhythm differs reel to
       reel rather than always being the same three-clip pattern.
    3. Optional horizontal mirroring, so a clip that does come round again does
       not read as the identical shot.

    Clips are always drawn from ONE footage folder per reel, so subjects never
    mix inside a single reel.
    """

    LEDGER = "broll-usage.csv"

    def __init__(self, clips, seed=0, target_seconds=DEFAULT_DURATION,
                 assets_dir=None, working_date=None):
        self.rnd = random.Random(seed)
        self.target = target_seconds
        self.working_date = working_date or datetime.now().strftime("%Y-%m-%d")
        self.ledger_path = os.path.join(assets_dir or ".", self.LEDGER)
        self.usage = self._load_ledger()
        self.by_cat = {}
        for c in clips:
            self.by_cat.setdefault(category_of(c), []).append(c)
        self.durations = {}
        # Seeded from the ledger, not empty: a clip already handed out earlier
        # TONIGHT is off the table even if this is a second process. An in-memory
        # set only holds within one run, so an interrupted-and-resumed night used
        # to hand the same clip to two pages (AR + TFW both drew random/IMG_5621
        # on 2026-08-17). take() already stamps last_used with the working date,
        # so the ledger on disk is the durable version of the same fact.
        self.used_tonight = {c for c in clips
                             if self._rec(c)["last_used"] == self.working_date}
        self.cat_order = sorted(self.by_cat, key=lambda c: self._cat_staleness(c))

    # ---- ledger ----------------------------------------------------------
    def _load_ledger(self):
        usage = {}
        if not os.path.exists(self.ledger_path):
            return usage
        try:
            with open(self.ledger_path, newline="", encoding="utf-8") as fh:
                for row in csv.DictReader(fh):
                    usage[row["clip"]] = {
                        "last_used": row.get("last_used", ""),
                        "times_used": int(row.get("times_used", 0) or 0),
                    }
        except Exception:
            pass
        return usage

    def save_ledger(self):
        try:
            with open(self.ledger_path, "w", newline="", encoding="utf-8") as fh:
                w = csv.writer(fh)
                w.writerow(["clip", "last_used", "times_used"])
                for clip, rec in sorted(self.usage.items()):
                    w.writerow([clip, rec["last_used"], rec["times_used"]])
        except Exception:
            pass

    def _rec(self, clip):
        return self.usage.get(clip_label(clip), {"last_used": "", "times_used": 0})

    def _staleness(self, clip):
        """Sort key: never-used first, then oldest last_used, then least used."""
        r = self._rec(clip)
        return (r["last_used"] or "", r["times_used"], self.rnd.random())

    def _cat_staleness(self, cat):
        recs = [self._rec(c) for c in self.by_cat[cat]]
        newest = max((r["last_used"] or "") for r in recs) if recs else ""
        return (newest, sum(r["times_used"] for r in recs), self.rnd.random())

    def _dur(self, clip):
        if clip not in self.durations:
            self.durations[clip] = clip_duration(clip)
        return self.durations[clip]

    # ---- selection -------------------------------------------------------
    def take(self, _retry=False):
        """
        Returns a plan dict:
            {"clips": [...], "offsets": [...], "mirror": bool}
        `offsets` is a per-clip start time, so a long clip does not always show
        the same seconds.

        `_retry` is internal: set on the one fallback pass taken when every
        folder is already used up for tonight. Callers never pass it.
        """
        if not self.cat_order:
            return None

        for cat in list(self.cat_order) + list(self.cat_order):
            pool = [c for c in self.by_cat[cat] if c not in self.used_tonight]
            if not pool:
                continue
            pool.sort(key=self._staleness)

            # Vary how many clips get joined, biased by what the folder holds.
            long_enough = [c for c in pool if self._dur(c) >= self.target + 1.0]
            if long_enough and self.rnd.random() < 0.35:
                chosen = [long_enough[0]]          # single long take
            else:
                want = self.rnd.choice([2, 2, 3, 3, 4])
                chosen, total = [], 0.0
                for c in pool:
                    chosen.append(c)
                    total += self._dur(c)
                    if len(chosen) >= want and total >= self.target:
                        break
                if total < self.target and len(pool) > len(chosen):
                    for c in pool[len(chosen):]:
                        chosen.append(c)
                        total += self._dur(c)
                        if total >= self.target:
                            break
            if not chosen:
                continue

            # Fresh start offset when a clip has spare length.
            offsets = []
            for c in chosen:
                spare = self._dur(c) - (self.target if len(chosen) == 1 else 2.0)
                offsets.append(round(self.rnd.uniform(0, spare), 2)
                               if spare > 1.0 else 0.0)

            for c in chosen:
                self.used_tonight.add(c)
                rec = self.usage.setdefault(
                    clip_label(c), {"last_used": "", "times_used": 0})
                rec["last_used"] = self.working_date
                rec["times_used"] += 1

            # Rotate this folder to the back so the next reel uses another one.
            if cat in self.cat_order:
                self.cat_order.remove(cat)
                self.cat_order.append(cat)

            return {"clips": chosen, "offsets": offsets,
                    "mirror": self.rnd.random() < 0.35}

        # Last resort: every folder is used up for tonight. Reusing a clip is a
        # variety cost; returning None drops the reel onto a flat generated
        # background, which under the hard rules is a BROKEN reel, not a variant.
        # So release the stalest folder and pick from it again. _retry bounds the
        # recursion to one extra pass per call, and it resets on the next take().
        if not _retry:
            for cat in self.cat_order:
                if self.by_cat.get(cat):
                    self.used_tonight -= set(self.by_cat[cat])
                    return self.take(_retry=True)

        return None


def build_broll_track(plan, duration, assets_dir, tmp_dir):
    """
    Turn a picker plan into ONE gapless 1080x1920 track covering `duration`.

    Everything is normalised here — scale, crop, fps, timestamps, and the
    optional mirror — so the encode step downstream can never receive mixed
    geometry. Mixed geometry in a concat is what produces a frozen segment.

    Returns (track_path, note) or (None, reason).
    """
    clips = plan["clips"]
    offsets = plan.get("offsets") or [0.0] * len(clips)
    mirror = plan.get("mirror", False)

    vf = (f"scale={W}:{H}:force_original_aspect_ratio=increase,"
          f"crop={W}:{H},setsar=1,fps={FPS}")
    if mirror:
        vf += ",hflip"

    parts = []
    for i, (clip, off) in enumerate(zip(clips, offsets)):
        seg = os.path.join(tmp_dir, f"seg{i}.mp4")
        cmd = ["ffmpeg", "-y", "-loglevel", "error"]
        if off and off > 0.05:
            cmd += ["-ss", f"{off:.2f}"]
        cmd += ["-i", clip, "-vf", vf, "-an",
                "-c:v", "libx264", "-preset", "veryfast", "-crf", "20",
                "-pix_fmt", "yuv420p", "-f", "mp4", seg]
        try:
            run(cmd)
        except Exception:
            continue
        if _decodes(seg):
            parts.append(seg)

    if not parts:
        return None, "every source clip failed to normalise"

    if len(parts) == 1:
        track = parts[0]
    else:
        listfile = os.path.join(tmp_dir, "concat.txt")
        with open(listfile, "w") as fh:
            for p_ in parts:
                fh.write(f"file '{os.path.abspath(p_)}'\n")
        track = os.path.join(tmp_dir, "broll_joined.mp4")
        try:
            run(["ffmpeg", "-y", "-loglevel", "error", "-fflags", "+genpts",
                 "-f", "concat", "-safe", "0", "-i", listfile,
                 "-vf", f"fps={FPS},setpts=N/{FPS}/TB", "-vsync", "cfr", "-an",
                 "-c:v", "libx264", "-preset", "veryfast", "-crf", "20",
                 "-pix_fmt", "yuv420p", "-f", "mp4", track])
        except Exception as exc:
            return None, f"concat failed: {exc}"

    have = clip_duration(track)
    if have < duration - 0.2:
        # Still short after joining everything available. Pad by looping the
        # track itself — a whole-track loop shows every clip again rather than
        # freezing, which is the failure we are engineering out.
        looped = os.path.join(tmp_dir, "broll_looped.mp4")
        try:
            run(["ffmpeg", "-y", "-loglevel", "error",
                 "-stream_loop", "-1", "-i", track, "-t", f"{duration:.2f}",
                 "-vf", f"fps={FPS},setpts=N/{FPS}/TB", "-vsync", "cfr", "-an",
                 "-c:v", "libx264", "-preset", "veryfast", "-crf", "20",
                 "-pix_fmt", "yuv420p", "-f", "mp4", looped])
            if _decodes(looped):
                track = looped
        except Exception:
            pass

    # GUARANTEE, not a warning: the track must be continuous before we build a
    # reel on it. A frozen stretch here becomes a frozen stretch on Facebook.
    frozen = detect_freezes(track, min_seconds=1.0)
    if frozen:
        return None, (f"source footage froze at "
                      + ", ".join(f"{s:.1f}s for {d:.1f}s" for s, d in frozen))
    if not _is_gapless(track, min(duration, clip_duration(track))):
        return None, "joined track has timestamp gaps"

    note = f"{len(parts)} clip(s)" + (" + mirrored" if mirror else "")
    return track, note


def _is_gapless(path, expected_seconds, tol=0.6):
    """
    True if `path` decodes to a continuous timeline of roughly the expected
    length. Guards against a join that looks fine to ffprobe's header but has
    a hole in the middle — which is what a frozen frame looks like on playback.
    """
    if not _decodes(path):
        return False
    dur = clip_duration(path)
    if dur < expected_seconds * (1 - tol):
        return False
    proc = subprocess.run(
        ["ffprobe", "-v", "error", "-select_streams", "v:0", "-count_frames",
         "-show_entries", "stream=nb_read_frames", "-of", "csv=p=0", path],
        capture_output=True, text=True)
    try:
        frames = int(proc.stdout.strip().rstrip(","))
    except ValueError:
        return False
    # A gapless CFR track has ~fps frames per second of runtime.
    return frames >= dur * FPS * 0.9


def background_for(reel, seed):
    """
    Background priority: the model's own still (dimmed, so text reads) first,
    then a generated gradient. B-roll video is intentionally out of scope here —
    the specs never name a clip ("the team chooses b-roll and audio").
    """
    src = reel["assets"].get("source_image")
    if src and os.path.exists(src):
        try:
            img = blurred_fill(Image.open(src).convert("RGBA"))
            return img, "model-still"
        except Exception:
            pass
    return gradient_background(seed), "gradient"


# ---------------------------------------------------------------- audio

def pick_music(assets_dir, seed):
    music_dir = os.path.join(assets_dir, "music")
    if not os.path.isdir(music_dir):
        return None
    tracks = sorted(f for f in os.listdir(music_dir)
                    if f.lower().endswith((".mp3", ".m4a", ".wav", ".aac")))
    if not tracks:
        return None
    return os.path.join(music_dir, random.Random(seed).choice(tracks))


# ---------------------------------------------------------------- segments

def plan_rows(reel, seed=None):
    """
    Turn a reel spec's on-screen field into the stack of rows.

    Format N's numbered lines are already one row each — that is exactly what
    the reference reels do. A single unnumbered block is split at sentence
    boundaries so it still reads as a ladder rather than one slab of text.
    """
    cards = [c.strip() for c in (reel.get("onscreen_cards") or []) if c.strip()]
    if not cards:
        return []

    spec_styles = reel.get("onscreen_styles") or []
    if len(cards) == 1:
        pieces = split_sentences(cards[0])
        # Split anything still too long for a two-line row.
        rows = []
        for p in pieces:
            rows.extend(chunk_text(p, limit=64) if len(p) > 64 else [p])
    else:
        rows = cards

    # If the spec tagged its lines with colours (Format A did), use those —
    # the writer already decided. Only invent a pattern when it did not.
    tagged = [t for t in spec_styles if t]
    if len(rows) == len(spec_styles) and len(tagged) == len(rows):
        return list(zip(rows, spec_styles))
    return list(zip(rows, assign_row_styles(len(rows), seed=seed)))


def plan_segments(reel, duration, punch_last=False):
    """
    ONE card, all of the spec's on-screen text, on screen from t=0 and held for
    the whole runtime (Alex, 2026-08-16). No timed reveals.

    `punch_last` optionally puts the closing sentence in the red box, matching
    one specific reference reel. It is OFF by default — the reference set has
    several different layouts and forcing every reel into white-box-over-red-box
    was wrong.
    """
    cards = reel.get("onscreen_cards") or []
    if not cards:
        return [{"main": None, "punch": None, "seconds": duration}]

    text = " ".join(c.strip() for c in cards if c.strip())

    punch = None
    if punch_last:
        sentences = split_sentences(text)
        if len(sentences) > 1 and len(sentences[-1]) <= 58:
            punch = sentences.pop()
            text = " ".join(sentences)

    return [{"main": text, "punch": punch, "seconds": duration}]


# ---------------------------------------------------------------- ffmpeg

def run(cmd):
    proc = subprocess.run(cmd, capture_output=True, text=True)
    if proc.returncode != 0:
        raise RuntimeError(f"ffmpeg failed:\n{' '.join(cmd)}\n{proc.stderr[-2500:]}")
    return proc


# Peak zoom of the slow push. Format S is deliberately gentle: the banked card
# fills most of the frame, so a hard push would crop the headline that IS the post.
ZOOM_MAX = {"S": 1.035}
ZOOM_DEFAULT = 1.09


def encode(frames, duration, music, out_path, fmt="B"):
    """
    frames: list of (png_path, seconds).
    One frame  -> slow push (zoompan) so it reads as video, not a stuck JPEG.
    Many frames-> concat at the planned durations; the text changes carry motion.
    """
    tmp = tempfile.mkdtemp(prefix="reelenc-")
    try:
        if len(frames) == 1:
            png, _ = frames[0]
            total = int(duration * FPS)
            zmax = ZOOM_MAX.get(fmt, ZOOM_DEFAULT)
            rate = (zmax - 1.0) / max(1, total)
            vf = (
                f"scale={W*2}:{H*2},"
                f"zoompan=z='min(1.0+{rate:.8f}*on,{zmax})':d={total}:"
                f"x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':s={W}x{H}:fps={FPS},"
                f"format=yuv420p"
            )
            vin = ["-loop", "1", "-t", f"{duration:.3f}", "-i", png]
            vfilter = ["-vf", vf]
        else:
            listfile = os.path.join(tmp, "concat.txt")
            with open(listfile, "w") as fh:
                for png, secs in frames:
                    fh.write(f"file '{png}'\nduration {secs:.3f}\n")
                fh.write(f"file '{frames[-1][0]}'\n")  # concat demuxer quirk
            vin = ["-f", "concat", "-safe", "0", "-i", listfile]
            vfilter = ["-vf", f"fps={FPS},scale={W}:{H},format=yuv420p"]

        cmd = ["ffmpeg", "-y", "-loglevel", "error"] + vin

        if music:
            fade_out = max(0.0, duration - 2.0)
            cmd += ["-stream_loop", "-1", "-i", music]
            cmd += vfilter
            cmd += ["-af", f"afade=t=in:st=0:d=1.5,afade=t=out:st={fade_out:.2f}:d=2.0,volume=0.65"]
            cmd += ["-map", "0:v:0", "-map", "1:a:0", "-c:a", "aac", "-b:a", "128k"]
        else:
            cmd += vfilter
            cmd += ["-map", "0:v:0"]

        cmd += [
            "-c:v", "libx264", "-preset", X264_PRESET, "-crf", "20",
            "-profile:v", "high", "-pix_fmt", "yuv420p",
            "-r", str(FPS), "-g", str(FPS * 2),
            "-movflags", "+faststart",
            "-t", f"{duration:.3f}",
            out_path,
        ]
        run(cmd)
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def encode_over_broll(broll, overlays, duration, music, out_path):
    """
    Composite timed text over real footage.

    broll    : path to a clip. Looped if shorter than `duration`.
    overlays : list of (png_path, start_s, end_s) transparent text layers.

    The clip is cover-scaled and centre-cropped to exactly 1080x1920 (9:16), so
    horizontal phone footage keeps its middle rather than being squashed. The
    clip's own audio is dropped entirely — these reels carry music only.
    """
    # Loop the source so a short clip still fills the full runtime.
    cmd = ["ffmpeg", "-y", "-loglevel", "error",
           "-stream_loop", "-1", "-i", broll]

    if music:
        cmd += ["-stream_loop", "-1", "-i", music]

    for png, _s, _e in overlays:
        cmd += ["-loop", "1", "-i", png]

    # Base: cover-scale -> centre-crop to 9:16 -> 30fps -> slight darken so the
    # type always reads over bright footage.
    chain = [
        f"[0:v]scale={W}:{H}:force_original_aspect_ratio=increase,"
        f"crop={W}:{H},setsar=1,fps={FPS},eq=brightness=-0.06:saturation=0.95[base]"
    ]

    overlay_input_offset = 2 if music else 1
    last = "base"
    for i, (_png, start, end) in enumerate(overlays):
        idx = overlay_input_offset + i
        label = f"v{i}"
        chain.append(
            f"[{last}][{idx}:v]overlay=0:0:"
            f"enable='between(t,{start:.3f},{end:.3f})'[{label}]"
        )
        last = label

    chain.append(f"[{last}]format=yuv420p[vout]")

    cmd += ["-filter_complex", ";".join(chain), "-map", "[vout]"]

    if music:
        fade_out = max(0.0, duration - 2.0)
        cmd += ["-map", "1:a:0",
                "-af", f"afade=t=in:st=0:d=1.5,"
                       f"afade=t=out:st={fade_out:.2f}:d=2.0,volume=0.65",
                "-c:a", "aac", "-b:a", "128k"]
    else:
        cmd += ["-an"]

    cmd += [
        "-c:v", "libx264", "-preset", X264_PRESET, "-crf", "20",
        "-profile:v", "high", "-pix_fmt", "yuv420p",
        "-r", str(FPS), "-g", str(FPS * 2),
        "-movflags", "+faststart",
        "-t", f"{duration:.3f}",
        out_path,
    ]
    run(cmd)


def detect_freezes(path, min_seconds=1.5):
    """
    Find frozen stretches in a finished reel using ffmpeg's freezedetect.

    A frozen segment is invisible to ffprobe — the container looks perfectly
    healthy, correct duration, correct frame count — so it has to be checked on
    the decoded picture. This exact failure shipped once (TFW 2026-08-10 froze
    from 12s to 25s) because a broken proxy fell back to raw 4K clips and the
    concat dropped a segment. Never trust the header alone.

    Returns a list of (start_seconds, duration_seconds).
    """
    proc = subprocess.run(
        ["ffmpeg", "-v", "info", "-i", path,
         "-vf", f"freezedetect=n=-60dB:d={min_seconds}", "-f", "null", "-"],
        capture_output=True, text=True)
    starts, out = [], []
    for line in proc.stderr.splitlines():
        if "freeze_start" in line:
            try:
                starts.append(float(line.rsplit(":", 1)[1].strip()))
            except ValueError:
                pass
        elif "freeze_duration" in line and starts:
            try:
                out.append((starts.pop(0), float(line.rsplit(":", 1)[1].strip())))
            except ValueError:
                pass
    return out


def probe(path):
    proc = subprocess.run(
        ["ffprobe", "-v", "error", "-show_entries",
         "format=duration,size", "-show_entries", "stream=codec_type,width,height",
         "-of", "json", path],
        capture_output=True, text=True)
    try:
        return json.loads(proc.stdout)
    except Exception:
        return {}


# ---------------------------------------------------------------- per reel

def render_reel(reel, index, out_dir, assets_dir, duration, broll_picker=None,
                punch_last=False, _retry=False):
    """Render one reel. Returns a QA record."""
    code = reel["page_code"]
    slug = reel["slug"][:60].strip().strip("-")
    fmt = reel["format"]
    name = f"{code}-{reel['working_date']}-reel{reel['reel_number']}-{fmt}-{slug}.mp4"
    name = "".join(c for c in name if c.isalnum() or c in "-_. ").replace(" ", "-")
    out_path = os.path.join(out_dir, name)

    qa = {
        "page_code": code, "reel_number": reel["reel_number"], "format": fmt,
        "ab_arm": "A" if fmt == "A" else "SNB",
        "slug": reel["slug"], "tier1": reel["tier1"],
        "model_id": reel["primary_model_id"],
        "output": None, "status": "pending", "flags": [], "background": None,
        "broll": None,
        "music": None, "segments": 0, "duration_s": None, "size_bytes": None,
        "caption_chars": len(reel.get("caption") or ""),
    }

    if not (reel.get("caption") or "").strip():
        qa["flags"].append("no caption in spec")

    seed = abs(hash((code, reel["working_date"], reel["reel_number"]))) % (2**31)
    segments = plan_segments(reel, duration, punch_last=punch_last)
    qa["segments"] = len(segments)

    music = pick_music(assets_dir, seed)
    qa["music"] = os.path.basename(music) if music else None
    if not music:
        qa["flags"].append("no music track available")

    tmp = tempfile.mkdtemp(prefix="reelframes-")
    try:
        if True:
            # Every format renders the same way: the spec's on-screen text as a
            # row stack over Alex's b-roll (Alex, 2026-08-16). Format S used to
            # branch off and hold a banked screenshot still instead, which meant
            # a reel died outright whenever that screenshot was not on the render
            # machine — and there is no fetch path for those stills. Text over
            # b-roll for everything; the still path is retired.
            plan = broll_picker.take() if broll_picker else None

            if plan:
                # Real footage: same-subject clips joined to cover the runtime,
                # with one transparent row-stack layer held over the whole thing.
                qa["background"] = "b-roll"
                qa["broll"] = " + ".join(clip_label(c) for c in plan["clips"])
                qa["mirrored"] = plan.get("mirror", False)
                clip, note = build_broll_track(plan, duration, assets_dir, tmp)
                if not clip:
                    raise RuntimeError(f"no usable b-roll track: {note}")
                qa["broll_note"] = note
                rows = plan_rows(reel, seed=seed)
                qa["segments"] = len(rows)
                overlays = []
                if rows:
                    if reel.get("layout") == "full":
                        layer, size, overflowed = text_overlay_full(rows)
                    else:
                        layer, size, overflowed = text_overlay(rows)
                    if overflowed:
                        qa["flags"].append(
                            f"stack of {len(rows)} rows does not fit at the "
                            f"{size}px floor \u2014 shorten the lines")
                    png = os.path.join(tmp, "stack.png")
                    layer.save(png)
                    overlays.append((png, 0.0, duration))
                encode_over_broll(clip, overlays, duration, music, out_path)
            else:
                # No footage available — flat background, and say so loudly.
                bg, bg_kind = background_for(reel, seed)
                qa["background"] = bg_kind
                qa["flags"].append(
                    "NO B-ROLL — rendered on a flat background. Drop clips into "
                    "assets/broll/ for the intended look.")
                frames = []
                for i, seg in enumerate(segments):
                    frame = bg.copy()
                    if seg["main"]:
                        size, overflowed = draw_caption_card(
                            frame, seg["main"], seg["punch"])
                        if overflowed:
                            qa["flags"].append(
                                f"card {i+1} still wraps past 2 lines at the {size}px "
                                f"floor ({len(seg['main'])} chars) — shorten the line")
                    png = os.path.join(tmp, f"seg{i}.png")
                    frame.convert("RGB").save(png)
                    frames.append((png, seg["seconds"]))
                encode(frames, duration, music, out_path, fmt=fmt)

        info = probe(out_path)
        dur = float(info.get("format", {}).get("duration", 0) or 0)
        qa["output"] = out_path
        qa["duration_s"] = round(dur, 2)
        qa["size_bytes"] = int(info.get("format", {}).get("size", 0) or 0)
        qa["status"] = "rendered"

        lo, hi = (9.0, 21.0) if reel.get("layout") == "full" else (29.0, 41.0)
        if not (lo <= dur <= hi):
            qa["flags"].append(
                f"duration {dur:.1f}s is outside the {lo:.0f}-{hi:.0f}s target")
        has_audio = any(s.get("codec_type") == "audio"
                        for s in info.get("streams", []))
        if not has_audio:
            qa["flags"].append("rendered without an audio track")

        # Frozen stretches are invisible to ffprobe, so check the decoded
        # picture — and FIX it rather than just reporting it. The source track
        # is already verified continuous, so a freeze here means the encode
        # went wrong; one clean retry on fresh footage resolves it.
        freezes = detect_freezes(out_path)
        if freezes and broll_picker is not None and not _retry:
            qa["flags"].append(
                f"freeze detected at {freezes[0][0]:.1f}s — re-rendered "
                f"automatically on different footage")
            retry = render_reel(reel, index, out_dir, assets_dir, duration,
                                broll_picker, punch_last, _retry=True)
            retry["flags"] = qa["flags"] + retry["flags"]
            return retry
        qa["freezes"] = [[round(s, 1), round(d, 1)] for s, d in freezes]
        for start, dur in freezes:
            qa["flags"].append(
                f"FROZEN PICTURE for {dur:.1f}s starting at {start:.1f}s — "
                f"still frozen after a retry; DO NOT POST")

    except Exception as exc:
        qa["status"] = "error"
        qa["flags"].append(f"render error: {exc}")
    finally:
        shutil.rmtree(tmp, ignore_errors=True)

    return qa


# ---------------------------------------------------------------- report

def write_report(manifest, records, out_dir, duration):
    wdate = manifest["working_date"]
    rendered = [r for r in records if r["status"] == "rendered"]
    blocked = [r for r in records if r["status"] == "blocked"]
    errored = [r for r in records if r["status"] == "error"]
    flagged = [r for r in rendered if r["flags"]]

    lines = []
    lines.append(f"# Reel Render QA — working date {wdate}")
    lines.append("")
    lines.append(f"Rendered {datetime.now().strftime('%Y-%m-%d %H:%M')} · "
                 f"target duration {duration:.0f}s · 1080x1920 @ {FPS}fps")
    lines.append("")
    lines.append("**RENDER ONLY — nothing here has been posted.** Review each file "
                 "before it goes anywhere near a page (CLAUDE.md §0).")
    lines.append("")
    arms = {}
    for r in rendered:
        arms[r.get("ab_arm", "?")] = arms.get(r.get("ab_arm", "?"), 0) + 1
    lines.append(f"- Rendered: **{len(rendered)}** of {len(records)}")
    if arms:
        lines.append("- A/B split: " + " · ".join(
            f"**{k}** {v}" for k, v in sorted(arms.items()))
            + "  (Format A ladder vs S/N/B — arms should be roughly even)")
    lines.append(f"- Blocked (missing source still): **{len(blocked)}**")
    lines.append(f"- Errors: **{len(errored)}**")
    lines.append(f"- Rendered but flagged for a look: **{len(flagged)}**")
    lines.append("")

    lines.append("## Rendered")
    lines.append("")
    if rendered:
        lines.append("| Page | # | Fmt | Tier-1 | Dur | Size | B-roll | Music | Slug |")
        lines.append("|---|---|---|---|---|---|---|---|---|")
        for r in rendered:
            mb = f"{r['size_bytes']/1_000_000:.1f} MB" if r["size_bytes"] else "—"
            bg = r["broll"] or r["background"]
            lines.append(
                f"| {r['page_code']} | {r['reel_number']} | {r['format']} | "
                f"{r.get('ab_arm','')} | "
                f"{'yes' if r['tier1'] else ''} | {r['duration_s']}s | {mb} | "
                f"{bg} | {r['music'] or '—'} | {r['slug'][:40]} |")
    else:
        lines.append("_Nothing rendered._")
    lines.append("")

    if blocked:
        lines.append("## Blocked — need the source screenshot")
        lines.append("")
        lines.append("Format S holds a banked still, so it cannot render without the "
                     "image. Drop these files into `_Brain/Data/reel-render/assets/` "
                     "(or wire a Drive credential) and re-run.")
        lines.append("")
        for r in blocked:
            lines.append(f"- **{r['page_code']} reel {r['reel_number']}** "
                         f"({r['model_id'] or 'no model id'}) — {r['slug']}")
            for f in r["flags"]:
                lines.append(f"  - {f}")
        lines.append("")

    if flagged:
        lines.append("## Flagged — rendered, but worth eyeballing")
        lines.append("")
        for r in flagged:
            lines.append(f"- **{r['page_code']} reel {r['reel_number']}** ({r['format']}) — {r['slug']}")
            for f in r["flags"]:
                lines.append(f"  - {f}")
        lines.append("")

    if errored:
        lines.append("## Errors")
        lines.append("")
        for r in errored:
            lines.append(f"- **{r['page_code']} reel {r['reel_number']}** — {'; '.join(r['flags'])}")
        lines.append("")

    lines.append("## Notes")
    lines.append("")
    _font = os.path.basename(FONT_PATH)
    if "Poppins" in FONT_PATH:
        lines.append(f"- ⚠️ **FONT FELL BACK TO POPPINS** (`{_font}`). Poppins has a "
                     "single-storey 'a'; the reference lettering is double-storey, so this "
                     "is NOT the right face. Drop the real .ttf/.otf into assets/fonts/ — "
                     "it wins over anything installed.")
    else:
        lines.append(f"- Font used: `{_font}`.")
    lines.append("- EVERY format is the spec's on-screen text over b-roll (Alex, "
                 "2026-08-16). Format S no longer holds a banked screenshot still.")
    lines.append("- Backgrounds fall back to a generated gradient only when no b-roll "
                 "is available. The specs deliberately never name a b-roll clip.")
    lines.append("- Captions live in the spec files and the handout, not in the video.")
    lines.append("")

    path = os.path.join(out_dir, f"_QA-Report-{wdate}.md")
    with open(path, "w", encoding="utf-8") as fh:
        fh.write("\n".join(lines))
    return path


# ---------------------------------------------------------------- main

def main():
    ap = argparse.ArgumentParser(description="Render reel manifest entries to MP4.")
    ap.add_argument("--manifest", required=True)
    ap.add_argument("--out", required=True, help="Output directory for MP4s.")
    ap.add_argument("--assets", default=None, help="Override the assets folder.")
    ap.add_argument("--duration", type=float, default=DEFAULT_DURATION)
    ap.add_argument("--only", default=None, help="Comma-separated page codes.")
    ap.add_argument("--limit", type=int, default=None)
    ap.add_argument("--dry-run", action="store_true",
                    help="Plan and report without encoding.")
    ap.add_argument("--punch-last", action="store_true",
                    help="Put the closing sentence in the red box (one reference layout only; off by default).")
    args = ap.parse_args()

    with open(args.manifest, encoding="utf-8") as fh:
        manifest = json.load(fh)

    # Manifests bake in an ABSOLUTE assets path, and under Cowork that path is
    # session-scoped (/sessions/<random-name>/mnt/...). A manifest written in one
    # session is therefore unusable in the next one, or on another computer: the
    # baked path silently does not exist, list_broll() returns [], and every reel
    # quietly renders on a flat gradient. That is a broken reel, not a variant
    # (task file 32, Hard rules). So: fall back to the assets/ folder that sits
    # next to THIS script, which is correct by construction wherever it runs.
    assets_dir = args.assets or manifest.get("assets_dir")
    script_assets = os.path.join(os.path.dirname(os.path.abspath(__file__)), "assets")
    if not assets_dir or not os.path.isdir(assets_dir):
        if os.path.isdir(script_assets):
            print(f"assets_dir from manifest is not present on this machine:\n"
                  f"  {assets_dir}\n"
                  f"falling back to the assets folder beside this script:\n"
                  f"  {script_assets}")
            assets_dir = script_assets
    os.makedirs(args.out, exist_ok=True)

    reels = manifest["reels"]
    if args.only:
        want = {p.strip().upper() for p in args.only.split(",")}
        reels = [r for r in reels if r["page_code"].upper() in want]
    if args.limit:
        reels = reels[:args.limit]

    if args.dry_run:
        for r in reels:
            segs = plan_segments(r, args.duration, punch_last=args.punch_last)
            print(f"\n{r['page_code']:4} #{r['reel_number']} Format {r['format']} "
                  f"— {len(segs)} card(s) — {r['slug'][:44]}")
            for s in segs:
                if not s["main"]:
                    print(f"     [{s['seconds']:5.1f}s] (still, no text)")
                    continue
                print(f"     [{s['seconds']:5.1f}s] {s['main']}")
                if s["punch"]:
                    print(f"              RED: {s['punch']}")
        return

    clips = list_broll(assets_dir)
    if not clips:
        # Never paper over missing footage with a generated background: a silent
        # or flat-background reel is broken, not a variant (task file 32, Hard
        # rules). Stop loudly instead of shipping 11 flat reels that look fine
        # in the QA table.
        sys.stderr.write(
            "\nSTOP: no b-roll clips found.\n"
            f"  looked in : {os.path.join(assets_dir or '?', 'broll')}\n"
            "  A flat-background reel is broken, not a variant, so this run is\n"
            "  refusing to render rather than producing them silently.\n"
            "  Fix: run drive_fetch.py --broll, or pass the right --assets path.\n")
        raise SystemExit(2)
    print(f"b-roll clips available: {len(clips)}"
          + f" ({', '.join(clip_label(c) for c in clips[:4])}"
          + (" ..." if len(clips) > 4 else "") + ")")
    picker = BrollPicker(clips, seed=hash(manifest["working_date"]) % 10000,
                         target_seconds=args.duration, assets_dir=assets_dir,
                         working_date=manifest["working_date"])

    records = []
    for i, reel in enumerate(reels):
        rec = render_reel(reel, i, args.out, assets_dir, args.duration, picker,
                          punch_last=args.punch_last)
        records.append(rec)
        mark = {"rendered": "ok", "blocked": "BLOCKED", "error": "ERROR"}[rec["status"]]
        flag = f"  [{len(rec['flags'])} flag(s)]" if rec["flags"] else ""
        print(f"{mark:8} {rec['page_code']:4} #{rec['reel_number']} "
              f"{rec['format']}  {rec['slug'][:44]}{flag}")

    picker.save_ledger()
    report = write_report(manifest, records, args.out, args.duration)
    with open(os.path.join(args.out, f"_render-log-{manifest['working_date']}.json"),
              "w", encoding="utf-8") as fh:
        json.dump(records, fh, indent=2, ensure_ascii=False)

    ok = sum(1 for r in records if r["status"] == "rendered")
    print(f"\n{ok}/{len(records)} rendered -> {args.out}")
    print(f"QA report: {report}")


if __name__ == "__main__":
    main()
