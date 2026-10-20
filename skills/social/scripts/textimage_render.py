#!/usr/bin/env python3
"""
textimage_render.py — the text-image post card for Yeez (used by yeez_build.py).
Ported from the Clark Bros Media network's text-image renderer; the decorative verified badge is gone.

The format is a fake social post card: white background, the page's own logo +
name + handle top-left, black body text below. Posted as an IMAGE so it
monetises as image content.

GEOMETRY IS MEASURED, NOT GUESSED. From Alex's 5 reference cards (2026-08-16):

  canvas        1080x1080 for short copy, 1080x1350 when it needs the room
  logo          circle d=96 at x=32, y=68
  verified      d=45, immediately right of the page name
  body left     x=35   right margin 35
  body top      ~y=211 (tall card) / ~y=280 (square card)
  line pitch    ~60px on the dense card, ~78px on the short one
  para gap      ~2x the line pitch

The face size is NOT fixed — the reference cards scale type to fill the canvas,
so short copy is set large and long copy small. That is reproduced here by
auto-fitting between MAX and MIN.

RENDER ONLY. Writes PNGs to disk. Never posts, never uploads.

Usage:
    python3 textimage_render.py --date 2026-08-15 --brain /path/to/MediaCo-Brain
"""

import argparse
import json
import os
import re
import textwrap
from datetime import datetime

from PIL import Image, ImageDraw, ImageFont, ImageOps

W = 1080
H_SQUARE = 1080
H_TALL = 1350

MARGIN_X = 35
LOGO_X, LOGO_Y, LOGO_D = 32, 68, 96
BADGE_D = 45
HEADER_GAP = 46           # header block bottom -> first body line
NAME_SIZE = 46
HANDLE_SIZE = 40

BODY_MAX = 62
BODY_MIN = 30
LINE_RATIO = 1.30
PARA_RATIO = 2.0          # blank line between paragraphs ~= 2x line pitch

TEXT_BLACK = (15, 20, 25)
HANDLE_GREY = (110, 118, 125)
BADGE_BLUE = (29, 155, 240)
BG = (255, 255, 255)

HERE = os.path.dirname(os.path.abspath(__file__))
FONT_REG = os.path.join(HERE, "fonts", "Inter-Regular.ttf")
FONT_BOLD = os.path.join(HERE, "fonts", "Inter-Bold.ttf")

# Network hard rule (CLAUDE.md §5 / text-images-mechanics): NO emojis, ever.
# A card that slips one through renders it as tofu in most faces, so catch it
# here as a CONTENT flag rather than shipping a broken glyph.
EMOJI_RE = re.compile(
    "[\U0001F000-\U0001FAFF\U00002600-\U000027BF\U0001F1E6-\U0001F1FF"
    "\U00002190-\U000021FF\U00002B00-\U00002BFF️‍]")


# ---------------------------------------------------------------- text

BOLD_RE = re.compile(r"\*\*(.+?)\*\*", re.S)


def parse_runs(paragraph):
    """
    Split a paragraph into (text, bold) runs.

    The specs use markdown **bold**. Alex's current cards render those asterisks
    LITERALLY — two of the five reference images show "**The top 1 percent…**"
    with the stars visible on the finished post. Honour the intent instead:
    render bold and never print the markers.
    """
    runs, pos = [], 0
    for m in BOLD_RE.finditer(paragraph):
        if m.start() > pos:
            runs.append((paragraph[pos:m.start()], False))
        runs.append((m.group(1), True))
        pos = m.end()
    if pos < len(paragraph):
        runs.append((paragraph[pos:], False))
    return runs or [(paragraph, False)]


def wrap_runs(runs, fonts, max_w, draw):
    """Word-wrap a run list into lines of (text, bold) fragments."""
    reg, bold = fonts
    lines, cur, cur_w = [], [], 0.0
    for text, is_bold in runs:
        f = bold if is_bold else reg
        for word in text.split():
            ww = draw.textlength(word + " ", font=f)
            if cur and cur_w + ww > max_w:
                lines.append(cur)
                cur, cur_w = [], 0.0
            cur.append((word, is_bold))
            cur_w += ww
    if cur:
        lines.append(cur)
    return lines


def layout(paragraphs, size, max_w, draw):
    reg = ImageFont.truetype(FONT_REG, size)
    bold = ImageFont.truetype(FONT_BOLD, size)
    line_h = int(size * LINE_RATIO)
    blocks = []
    for p in paragraphs:
        # Each line inside a paragraph is its own row (bullet lists used to run together
        # because single newlines were swallowed by str.split()). "- " becomes a bullet.
        block = []
        for ln in p.split("\n"):
            ln = ln.strip()
            if not ln:
                continue
            if ln.startswith("- "):
                ln = "\u2022 " + ln[2:]
            block += wrap_runs(parse_runs(ln), (reg, bold), max_w, draw)
        blocks.append(block)
    total = sum(len(b) for b in blocks) * line_h
    total += int(line_h * (PARA_RATIO - 1)) * max(0, len(blocks) - 1)
    return blocks, (reg, bold), line_h, total


# ---------------------------------------------------------------- drawing

def circle_logo(path, d):
    im = Image.open(path).convert("RGBA").resize((d, d), Image.LANCZOS)
    mask = Image.new("L", (d, d), 0)
    ImageDraw.Draw(mask).ellipse([0, 0, d - 1, d - 1], fill=255)
    out = Image.new("RGBA", (d, d), (0, 0, 0, 0))
    out.paste(im, (0, 0), mask)
    return out


def render_card(page_name, handle, logo_path, body, out_path, heights=(H_SQUARE, H_TALL), body_max=BODY_MAX):
    """Render one card. Returns (path, height, font_size, flags)."""
    flags = []
    paragraphs = [p.strip() for p in re.split(r"\n\s*\n", body.strip()) if p.strip()]
    max_w = W - MARGIN_X * 2

    if not paragraphs:
        raise ValueError("empty on-image text — nothing to render")
    bad = sorted(set(EMOJI_RE.findall(body)))
    if bad:
        flags.append("EMOJI in the on-image text (" + " ".join(bad) +
                     ") — network hard rule is no emojis; fix the spec")

    probe = Image.new("RGB", (10, 10))
    pd = ImageDraw.Draw(probe)

    body_top = LOGO_Y + LOGO_D + HEADER_GAP

    # Pick the canvas that lets the type stay LARGEST, not the smallest canvas
    # that the type can be squeezed into. The reference cards grow to 1080x1350
    # rather than shrink the words — long copy is still set big.
    best = None
    for h in heights:
        avail = h - body_top - MARGIN_X
        for size in range(body_max, BODY_MIN - 1, -2):
            blocks, fonts, line_h, total = layout(paragraphs, size, max_w, pd)
            if total <= avail:
                if best is None or size > best[0]:
                    best = (size, h, blocks, fonts, line_h)
                break
    chosen = None
    if best:
        size, height, blocks, fonts, line_h = best
        chosen = (blocks, fonts, line_h, size)
    if not chosen:
        blocks, fonts, line_h, total = layout(paragraphs, BODY_MIN, max_w, pd)
        chosen, height = (blocks, fonts, line_h, BODY_MIN), H_TALL
        flags.append("copy is too long for a 1080x1350 card even at the "
                     f"{BODY_MIN}px floor — shorten it")
    blocks, (reg, bold), line_h, size = chosen

    img = Image.new("RGB", (W, height), BG)
    dr = ImageDraw.Draw(img)

    if logo_path and os.path.exists(logo_path):
        img.paste(circle_logo(logo_path, LOGO_D), (LOGO_X, LOGO_Y),
                  circle_logo(logo_path, LOGO_D))
    else:
        dr.ellipse([LOGO_X, LOGO_Y, LOGO_X + LOGO_D, LOGO_Y + LOGO_D],
                   fill=(220, 224, 228))
        flags.append("no logo found for this page")

    name_f = ImageFont.truetype(FONT_BOLD, NAME_SIZE)
    handle_f = ImageFont.truetype(FONT_REG, HANDLE_SIZE)
    tx = LOGO_X + LOGO_D + 22
    dr.text((tx, LOGO_Y + 2), page_name, font=name_f, fill=TEXT_BLACK)
    dr.text((tx, LOGO_Y + 52), handle, font=handle_f, fill=HANDLE_GREY)

    y = body_top
    for i, lines in enumerate(blocks):
        for frags in lines:
            x = MARGIN_X
            for word, is_bold in frags:
                f = bold if is_bold else reg
                dr.text((x, y), word, font=f, fill=TEXT_BLACK)
                x += dr.textlength(word + " ", font=f)
            y += line_h
        if i < len(blocks) - 1:
            y += int(line_h * (PARA_RATIO - 1))

    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    img.save(out_path)

    # Density is a CONTENT signal, not a render fault: per text-images-mechanics
    # the sweet spot is 3-6 short paragraphs, and the fitter only drops under
    # ~46px when the copy is long enough to start reading like a wall.
    if size < 46:
        flags.append(f"DENSE — fitted to {size}px ({len(paragraphs)} paragraphs); "
                     "the sweet spot is 3-6 short ones, so this reads like a "
                     "wall. Shorten the copy rather than shrinking the type")
    # The font is a run-level fact, not a per-card one — reported once in the QA
    # header instead of repeated on every card, so real flags stay visible.
    return out_path, height, size, flags


def handle_for(name):
    return "@" + re.sub(r"[^A-Za-z0-9]", "", name)
