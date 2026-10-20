#!/usr/bin/env python3
"""
yeez_build.py — renders the day's Facebook and Instagram media for Yeez, in the buyer's AI app.

Ported from the Clark Bros Media network's own Build step (fb_build.py + textimage_render.py):
the same news-image card, text-image card, story and photo search, with every network-specific
path, library and badge taken out.

    python3 yeez_build.py --date 2026-10-21 [--page CODE] [--work yeez-work] [--rebuild]

Inputs (the social skill writes them):
  yeez-work/brands.json                      [{code, name, c1, c2, c3, icon, logo_url}] one per Page / account
  yeez-work/queue/<date>/<CODE>.json         {page, timezone, audience, items:[...]}  (QUEUE-SPEC shape)
Outputs:
  yeez-work/queue/<date>/media/<id>.png|jpg  and each item gets status "built", media, photo credit.
  Then yeez_post.py posts them straight to Facebook and Instagram with the buyer's own keys file.

Types
  news_image  1080x1350 post card: logo + Page name + handle, the headline in heavy black type, the
              story's photo filling the bottom (two people side by side when image_brief.subject2 is set).
              image_brief.format A / B give the older colour-block and full-bleed layouts.
  text_image  1080x1350 white post card, type sized to fill the card, **bold** supported.
  story       1080x1920, white (brand) or yellow→magenta gradient, optional photo band and a
              "Reply WORD for …" button when cta.mode is KEYWORD.
  gradient    Facebook draws the background: nothing to render.
  link        article link card: nothing to render.
  reel, image_reel  arrive in the next update; left untouched.

Pillow only. Fonts are bundled in ./fonts (Inter + Merriweather, SIL OFL). RENDER ONLY:
never posts anything. Posting is yeez_post.py.
"""

import argparse
import csv
import io
import json
import os
import re
import sys
import time
import traceback
import urllib.parse
import urllib.request
from datetime import datetime, timedelta, timezone

from PIL import Image, ImageDraw, ImageFilter, ImageFont, ImageOps

HERE = os.path.dirname(os.path.abspath(__file__))
FONT_DIR = os.path.join(HERE, "fonts")
# Everything the run writes lives in the buyer's work folder (default ./yeez-work), set by --work.
WORK = os.path.abspath(os.environ.get("YEEZ_WORK", "yeez-work"))
QUEUE_ROOT = os.path.join(WORK, "queue")
BRANDS_JSON = os.path.join(WORK, "brands.json")
LOGO_DIR = os.path.join(WORK, "logos")
LEDGER = os.path.join(WORK, "photo-ledger.csv")
PHOTO_CACHE = os.path.join(WORK, "photo-cache")   # photo search results, 7-day TTL

OPENVERSE = "https://api.openverse.org/v1/images/"
UA = "Yeez-render/1.0 (+https://yeez.ai)"
REUSE_DAYS = 30
MIN_PHOTO_PX = 1000          # long edge

GRADIENT_STOPS = [(0.0, "#F6D05A"), (0.45, "#EE7B4E"), (0.72, "#D8577A"), (1.0, "#A935A8")]

LEDGER_FIELDS = ["date_used", "item_id", "page", "openverse_id", "url",
                 "landing_url", "creator", "license", "query"]

# Titles/tags that make a photo wrong for a retirement-money card (spec §2: no
# politics, no protest signs; no illustrations/vintage/clip art).
# 2026-10-12 (Alex): a post about a named person shows THAT person. The politics words
# below are skipped only when the query came from image_brief.subject "person:"/"official:".
POLITICS_WORDS = (r"congress|senat\w*|trump|biden|obama|harris|democrat\w*|republican\w*|gop|"
                  r"vote|voting|election|campaign|politic\w*|president|governor|mayor|")
_REST_BAD = (r"rally|protest\w*|march|sign|poster|quote|"
    r"hands off|for all|lame duck|"
    r"illustration|clip ?art|cartoon|drawing|vector|icon|logo|infographic|"
    r"meme|vintage|1[89]\d\d|screenshot|certificate|naturali[sz]ation|passport|nude|naked|funeral|dead|death|gun|police|"
    # 2026-09-29: no children (spec), no archival/black-and-white shots
    r"boy|boys|girl|girls|child|children|kid|kids|baby|babies|toddler|teen|teens|teenager\w*|student\w*|school\w*|"
    # (audience-specific words like "young" are added by --audience older; see AUDIENCE_AVOID)
    r"black and white|b&w|monochrome|archiv\w*|historic\w*")
AUDIENCE_AVOID = {"older": r"young|youth|millennial\w*|twenty\w*|thirty\w*|college|bitcoin|crypto\w*|"}
BAD_WORDS = re.compile(r"\b(" + POLITICS_WORDS + _REST_BAD + r")\b", re.I)
BAD_WORDS_PERSON = re.compile(r"\b(" + _REST_BAD + r")\b", re.I)


def set_audience(aud):
    """--audience older adds the retiree-network filters (no young adults, no crypto stock)."""
    global BAD_WORDS, BAD_WORDS_PERSON
    extra = AUDIENCE_AVOID.get((aud or "").lower(), "")
    BAD_WORDS = re.compile(r"\b(" + POLITICS_WORDS + extra + _REST_BAD + r")\b", re.I)
    BAD_WORDS_PERSON = re.compile(r"\b(" + extra + _REST_BAD + r")\b", re.I)
_PERSON_QUERIES = set()

STOP = set("a an the and or of to in on at for with by from as is are be this that "
           "their his her its our your my".split())

try:
    from zoneinfo import ZoneInfo
    TZ = ZoneInfo(os.environ.get("YEEZ_TZ", "America/Chicago"))   # the page file's timezone (set by main)
except Exception:
    TZ = None


def now_local():
    return datetime.now(TZ) if TZ else datetime.now(timezone.utc).astimezone()


TODAY = now_local().date()


def now_iso():
    return now_local().isoformat(timespec="seconds")


def log_line(msg):
    return f"{now_iso()} build: {msg}"


# ------------------------------------------------------------------ fonts

def font(name, size):
    return ImageFont.truetype(os.path.join(FONT_DIR, name), int(size))


F_HEAD = "Inter-ExtraBold.ttf"
F_BLACK = "Inter-Black.ttf"
F_BOLD = "Inter-Bold.ttf"
F_MED = "Inter-Medium.ttf"
F_SERIF = "Merriweather-Black.ttf"


# ------------------------------------------------------------------ colors

def hex_rgb(h):
    h = h.lstrip("#")
    return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4))


def shade(rgb, f):
    """f<1 darkens, f>1 lightens toward white."""
    if f <= 1:
        return tuple(int(c * f) for c in rgb)
    t = f - 1
    return tuple(int(c + (255 - c) * t) for c in rgb)


def _lum(rgb):
    def ch(c):
        c = c / 255.0
        return c / 12.92 if c <= 0.03928 else ((c + 0.055) / 1.055) ** 2.4
    r, g, b = rgb[:3]
    return 0.2126 * ch(r) + 0.7152 * ch(g) + 0.0722 * ch(b)


def contrast(a, b):
    la, lb = _lum(a), _lum(b)
    hi, lo = max(la, lb), min(la, lb)
    return (hi + 0.05) / (lo + 0.05)


def readable(fg, bg, need=4.5):
    """2026-10-12: brand accents were landing on look-alike backgrounds (red on blue, orange on
    brown, orange on orange), so key numbers and story keywords could not be read. Keep the brand
    colour when it is readable; otherwise try lighter/darker shades of it, then white or near-black."""
    fg, bg = tuple(fg[:3]), tuple(bg[:3])
    if contrast(fg, bg) >= need:
        return fg
    for f in (1.35, 1.55, 1.75, 0.6, 0.45, 0.3):
        c = shade(fg, f)
        if contrast(c, bg) >= need:
            return c
    white, ink = (255, 255, 255), (17, 17, 17)
    return white if contrast(white, bg) >= contrast(ink, bg) else ink


def highlight(fg, bg, text=(255, 255, 255), need=3.5):
    """A highlighted number must be readable on the panel AND stand apart from the white body text.
    When the brand accent can only pass by fading toward white, use a strong yellow instead.
    A brand accent that is already readable is always kept as it is."""
    if contrast(tuple(fg[:3]), tuple(bg[:3])) >= need:
        return tuple(fg[:3])
    c = readable(fg, bg, need)
    if contrast(c, text) < 1.6:
        for alt in ((255, 211, 77), (255, 236, 140), (17, 17, 17)):
            if contrast(alt, bg) >= need and contrast(alt, text) >= 1.25:
                return alt
    return c


# ------------------------------------------------------------------ brand

def load_brands():
    return {b["code"].lower(): b for b in json.load(open(BRANDS_JSON, encoding="utf-8"))}


def product_short_name(cta):
    """The thing the story's reply button promises. The skill writes it as cta.pill."""
    return (cta.get("product_short") or cta.get("pill") or "the link").strip()


# ------------------------------------------------------------------ icons
# Pillow ports of the Brand-Kit gen.py SVG icons (100x100 viewBox), drawn 4x
# supersampled for clean edges.

def _qbez(p0, p1, p2, n=40):
    return [((1 - t) ** 2 * p0[0] + 2 * (1 - t) * t * p1[0] + t * t * p2[0],
             (1 - t) ** 2 * p0[1] + 2 * (1 - t) * t * p1[1] + t * t * p2[1])
            for t in (i / n for i in range(n + 1))]


def _cbez(p0, p1, p2, p3, n=40):
    out = []
    for i in range(n + 1):
        t = i / n
        a, b, c, d = (1 - t) ** 3, 3 * (1 - t) ** 2 * t, 3 * (1 - t) * t * t, t ** 3
        out.append((a * p0[0] + b * p1[0] + c * p2[0] + d * p3[0],
                    a * p0[1] + b * p1[1] + c * p2[1] + d * p3[1]))
    return out


def icon_image(kind, color, size):
    S = 4
    big = size * S
    k = big / 100.0
    im = Image.new("RGBA", (big, big), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    col = color + (255,) if len(color) == 3 else color

    def P(pts):
        return [(x * k, y * k) for x, y in pts]

    def stroke(pts, w, closed=False):
        pts = P(pts)
        if closed:
            pts = pts + [pts[0]]
        d.line(pts, fill=col, width=int(w * k), joint="curve")
        r = w * k / 2
        for x, y in (pts[0], pts[-1]):
            d.ellipse([x - r, y - r, x + r, y + r], fill=col)

    if kind == "eye":
        pts = _qbez((5, 50), (50, 10), (95, 50)) + _qbez((95, 50), (50, 90), (5, 50))[1:]
        stroke(pts, 7, closed=True)
        d.ellipse([34 * k, 34 * k, 66 * k, 66 * k], fill=col)
    elif kind == "cross":
        d.rounded_rectangle([38 * k, 10 * k, 62 * k, 90 * k], radius=5 * k, fill=col)
        d.rounded_rectangle([10 * k, 38 * k, 90 * k, 62 * k], radius=5 * k, fill=col)
    elif kind == "bars":
        for x, y in ((10, 55), (41, 35), (72, 15)):
            d.rectangle([x * k, y * k, (x + 18) * k, 90 * k], fill=col)
    elif kind == "check":
        stroke([(15, 52), (40, 76), (86, 24)], 12)
    elif kind == "clock":
        w = 8 * k
        d.ellipse([10 * k, 10 * k, 90 * k, 90 * k], outline=col, width=int(w))
        stroke([(50, 26), (50, 50), (66, 60)], 8)
    elif kind == "chat":
        d.polygon(P([(12, 18), (88, 18), (88, 68), (44, 68), (24, 86), (24, 68), (12, 68)]), fill=col)
    elif kind == "book":
        pts = (_qbez((50, 22), (30, 10), (8, 16)) + [(8, 82)] + _qbez((8, 82), (30, 76), (50, 88))
               + _qbez((50, 88), (70, 76), (92, 82)) + [(92, 16)] + _qbez((92, 16), (70, 10), (50, 22)))
        stroke(pts, 7, closed=True)
        stroke([(50, 22), (50, 88)], 7)
    elif kind == "egg":
        pts = (_cbez((50, 8), (24, 8), (14, 52), (14, 64)) + _cbez((14, 64), (14, 84), (30, 94), (50, 94))
               + _cbez((50, 94), (70, 94), (86, 84), (86, 64)) + _cbez((86, 64), (86, 52), (76, 8), (50, 8)))
        d.polygon(P(pts), fill=col)
    else:
        d.ellipse([10 * k, 10 * k, 90 * k, 90 * k], fill=col)
    return im.resize((size, size), Image.LANCZOS)


def paste_rgba(base, im, xy):
    base.alpha_composite(im, (int(xy[0]), int(xy[1])))


# ------------------------------------------------------------------ text

HILITE_RE = re.compile(r"^[\"'(\[]*(\$[\d,.]+[A-Za-z%]*|\d[\d,.]*%?|[A-Z]{2,}[A-Z'’]*)[\"')\].,;:!?—-]*$")
MONTHS = re.compile(r"^(jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)[a-z]*\.?$", re.I)
YEAR_RE = re.compile(r"^(19|20)\d\d$")


def is_hilite(word):
    m = HILITE_RE.match(word)
    if not m:
        return False
    core = m.group(1).rstrip(".,")
    if YEAR_RE.match(core) or re.fullmatch(r"\d", core):
        return False            # years are context, not the number that hits the check
    # ALL-CAPS emphasis words only (RAISE, HALF, CUT); skip common acronyms
    # that are not emphasis.
    if core.isalpha() and core in {"SSA", "IRS", "IRA", "RMD", "COLA", "SSI", "SNAP", "VA", "US", "USA", "AARP", "CMS", "ID"}:
        return False
    return True


def wrap(words, fnt, max_w, draw):
    lines, cur = [], []
    for w in words:
        trial = " ".join(cur + [w])
        if cur and draw.textlength(trial, font=fnt) > max_w:
            lines.append(cur)
            cur = [w]
        else:
            cur.append(w)
    if cur:
        lines.append(cur)
    return lines


def balanced_wrap(words, fnt, max_w, draw):
    """Greedy wrap, then shrink the measure while the line count holds, so the
    last line is not a lonely word (balanced rag)."""
    base = wrap(words, fnt, max_w, draw)
    n = len(base)
    if n <= 1:
        return base
    lo, hi = max_w * 0.5, max_w
    best = base
    for _ in range(14):
        mid = (lo + hi) / 2
        t = wrap(words, fnt, mid, draw)
        if len(t) <= n and all(draw.textlength(" ".join(l), font=fnt) <= max_w for l in t):
            best, hi = t, mid
        else:
            lo = mid
    return best


def glue(words):
    """Non-breaking joins so a line never starts with a stray short number
    ("January 1.") or ends on a lone "a"/"the" before it."""
    out = []
    for w in words:
        if out and re.fullmatch(r"\d{1,2}[.,;:?!]?", w) and not re.search(r"[.?!:;]$", out[-1]):
            out[-1] = out[-1] + "\u00a0" + w
        else:
            out.append(w)
    return out


def fit_text(text, font_name, box_w, box_h, max_size, min_size, line_ratio=1.14, step=2):
    """Largest size whose balanced wrap fits box_w x box_h. Returns
    (size, lines, line_h, total_h, fits)."""
    probe = ImageDraw.Draw(Image.new("RGB", (8, 8)))
    paras = [glue(p.split()) for p in re.split(r"\n+", text.strip()) if p.strip()]
    for size in range(int(max_size), int(min_size) - 1, -step):
        fnt = font(font_name, size)
        lines = []
        for p in paras:
            lines += balanced_wrap(p, fnt, box_w, probe)
        widest = max(probe.textlength(" ".join(l), font=fnt) for l in lines)
        # any single word wider than the box -> this size cannot work
        lh = int(size * line_ratio)
        total = lh * len(lines)
        if widest <= box_w and total <= box_h:
            return size, lines, lh, total, True
    fnt = font(font_name, min_size)
    lines = []
    for p in paras:
        lines += balanced_wrap(p, fnt, box_w, probe)
    lh = int(min_size * line_ratio)
    return min_size, lines, lh, lh * len(lines), False


def draw_lines(img, lines, font_name, size, x, y, lh, color, accent=None,
               shadow=None, align="left", box_w=None):
    """Draw pre-wrapped lines word by word; numbers/CAPS emphasis in accent.
    shadow = (rgba, dx, dy, blur) draws a soft drop shadow under the text."""
    fnt = font(font_name, size)
    probe = ImageDraw.Draw(img)
    space = probe.textlength(" ", font=fnt)

    def runs():
        for i, line in enumerate(lines):
            lw = probe.textlength(" ".join(line), font=fnt)
            cx = x + ((box_w - lw) / 2 if align == "center" and box_w else 0)
            cy = y + i * lh
            for w in line:
                parts = w.split("\u00a0")
                is_date = len(parts) > 1 and MONTHS.match(parts[0])
                for part in parts:
                    c = accent if (accent and not is_date and is_hilite(part)) else color
                    yield cx, cy, part, c
                    cx += probe.textlength(part, font=fnt) + space

    if shadow:
        sh = Image.new("RGBA", img.size, (0, 0, 0, 0))
        sd = ImageDraw.Draw(sh)
        for cx, cy, part, _ in runs():
            sd.text((cx + shadow[1], cy + shadow[2]), part, font=fnt, fill=shadow[0])
        img.alpha_composite(sh.filter(ImageFilter.GaussianBlur(shadow[3])))
    d = ImageDraw.Draw(img)
    for cx, cy, part, c in runs():
        d.text((cx, cy), part, font=fnt, fill=c)


def ellipsize(text, fnt, max_w, draw):
    if draw.textlength(text, font=fnt) <= max_w:
        return text
    while text and draw.textlength(text + "…", font=fnt) > max_w:
        text = text[:-1]
    return text.rstrip() + "…"


# ------------------------------------------------------------------ photos

def ledger_rows():
    if not os.path.exists(LEDGER):
        return []
    with open(LEDGER, newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def recently_used(item_id):
    cutoff = TODAY - timedelta(days=REUSE_DAYS)
    used = set()
    for r in ledger_rows():
        if r.get("item_id") == item_id:
            continue          # an item may reuse its own photo on a rebuild
        try:
            d = datetime.strptime(r["date_used"][:10], "%Y-%m-%d").date()
        except Exception:
            continue
        if d >= cutoff:
            used.add(r.get("url"))
            used.add(r.get("openverse_id"))
    used.discard(None)
    used.discard("")
    return used


def ledger_add(photo, item_id, page, query):
    rows = [r for r in ledger_rows() if r.get("item_id") != item_id]
    rows.append({"date_used": TODAY.isoformat(), "item_id": item_id, "page": page,
                 "openverse_id": photo["id"], "url": photo["url"],
                 "landing_url": photo.get("landing_url", ""),
                 "creator": photo.get("creator", ""), "license": photo.get("license_label", ""),
                 "query": query})
    tmp = LEDGER + ".tmp"
    with open(tmp, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=LEDGER_FIELDS)
        w.writeheader()
        for r in rows:
            w.writerow({k: r.get(k, "") for k in LEDGER_FIELDS})
    os.replace(tmp, LEDGER)


def http_get(url, timeout=30):
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    for attempt in range(3):
        try:
            with urllib.request.urlopen(req, timeout=timeout) as r:
                return r.read()
        except urllib.error.HTTPError as e:
            if e.code == 429 and attempt < 2:
                time.sleep(15 * (attempt + 1))
                continue
            raise
        except Exception:
            if attempt < 2:
                time.sleep(3)
                continue
            raise


def license_label(r):
    if r.get("license_label"):
        return r["license_label"]
    lic = (r.get("license") or "").lower()
    ver = r.get("license_version") or ""
    if lic == "cc0":
        return "CC0"
    if lic == "pdm":
        return "Public domain"
    if lic in _STOCK_LICENSES:
        return _STOCK_LICENSES[lic]
    return f"CC {lic.upper()} {ver}".strip()


def query_variants(q):
    """Openverse matches all terms, so long briefs return nothing. Order:
    the full brief, then 3-word windows, then every adjacent 2-word pair
    (the productive ones), then the first content word."""
    words = re.findall(r"[A-Za-z0-9']+", q)
    content = [w for w in words if w.lower() not in STOP]
    out = [" ".join(words)]
    n = len(content)
    if n > 3:
        out += [" ".join(content[:3]), " ".join(content[-3:])]
    if n > 2:
        pairs = [" ".join(content[i:i + 2]) for i in range(n - 1)]
        # outside-in: first pair, last pair, then the middle ones
        order = []
        while pairs:
            order.append(pairs.pop(0))
            if pairs:
                order.append(pairs.pop())
        out += order
    if content:
        out.append(content[0])
    seen, res = set(), []
    for o in out:
        if o and o.lower() not in seen:
            seen.add(o.lower())
            res.append(o)
    return res


_LAST_CALL = [0.0]
CACHE_DAYS = 7


def openverse_search(q):
    """Anonymous Openverse allows 20 calls/min and 200/day, so results are
    cached on disk for CACHE_DAYS and calls are spaced ~3.2s apart. Set
    OPENVERSE_TOKEN for a registered client's higher limits."""
    import hashlib
    os.makedirs(PHOTO_CACHE, exist_ok=True)
    key = hashlib.sha1(q.lower().encode()).hexdigest()[:16]
    cp = os.path.join(PHOTO_CACHE, f"ov-{key}.json")
    if os.path.exists(cp) and time.time() - os.path.getmtime(cp) < CACHE_DAYS * 86400:
        try:
            return json.load(open(cp, encoding="utf-8"))["results"]
        except Exception:
            pass
    params = {"q": q, "license_type": "commercial,modification", "page_size": 20,
              "mature": "false"}
    url = OPENVERSE + "?" + urllib.parse.urlencode(params)
    wait = 3.2 - (time.time() - _LAST_CALL[0])
    if wait > 0:
        time.sleep(wait)
    headers = {"User-Agent": UA}
    if os.environ.get("OPENVERSE_TOKEN"):
        headers["Authorization"] = "Bearer " + os.environ["OPENVERSE_TOKEN"]
    req = urllib.request.Request(url, headers=headers)
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            data = json.loads(r.read().decode("utf-8"))
    finally:
        _LAST_CALL[0] = time.time()
    results = data.get("results", [])
    json.dump({"q": q, "fetched": now_iso(), "results": results},
              open(cp, "w", encoding="utf-8"))
    return results



# ------------------------------------------------------------------ more photo providers (2026-09-29, Alex)
# Every provider returns Openverse-shaped dicts (id, url, foreign_landing_url, creator, license,
# license_version, title, tags[{name}], width, height, filetype, source) so the existing filters,
# relevance scoring and ledger work unchanged. Order per query: keyed stock (Pexels / Pixabay /
# Unsplash -- only when _Brain/Data/image-api-credentials.json has keys, the same file the article
# image step reads), then Wikimedia Commons (no key), then Openverse.

IMAGE_KEYS_JSON = os.path.join(WORK, "image-keys.json")
STOCK_BONUS = {"pexels": 1.6, "freepik": 1.5, "unsplash": 1.4, "pixabay": 1.0, "network_library": 1.2,
               "wikimedia_commons": 0.0}
_STOCK_LICENSES = {"pexels": "Pexels License", "unsplash": "Unsplash License", "pixabay": "Pixabay License",
                   "freepik": "Freepik License"}


def image_keys():
    """Optional stock photo keys: env PEXELS_API_KEY / FREEPIK_API_KEY / UNSPLASH_ACCESS_KEY / PIXABAY_API_KEY,
    or yeez-work/image-keys.json. Without keys the run uses Wikimedia Commons and Openverse."""
    try:
        d = json.load(open(IMAGE_KEYS_JSON, encoding="utf-8"))
    except Exception:
        d = {}
    for k, env in (("pexels", "PEXELS_API_KEY"), ("freepik", "FREEPIK_API_KEY"), ("unsplash", "UNSPLASH_ACCESS_KEY"), ("pixabay", "PIXABAY_API_KEY")):
        if os.environ.get(env):
            d[k] = os.environ[env]
    out = {}
    for k in ("pexels", "freepik", "unsplash", "pixabay"):
        v = d.get(k) or {}
        key = (v.get("api_key") or v.get("access_key") or "") if isinstance(v, dict) else str(v)
        if key and "..." not in key and "PLACEHOLDER" not in key.upper():
            out[k] = key
    return out


def _cached(provider, q, fetch):
    import hashlib
    os.makedirs(PHOTO_CACHE, exist_ok=True)
    key = hashlib.sha1(f"{provider}|{q.lower()}".encode()).hexdigest()[:16]
    cp = os.path.join(PHOTO_CACHE, f"{provider[:2]}-{key}.json")
    if os.path.exists(cp) and time.time() - os.path.getmtime(cp) < CACHE_DAYS * 86400:
        try:
            return json.load(open(cp, encoding="utf-8"))["results"]
        except Exception:
            pass
    results = fetch()
    json.dump({"q": q, "provider": provider, "fetched": now_iso(), "results": results},
              open(cp, "w", encoding="utf-8"))
    return results


def _jget(url, headers=None, timeout=30):
    h = {"User-Agent": UA}
    h.update(headers or {})
    with urllib.request.urlopen(urllib.request.Request(url, headers=h), timeout=timeout) as r:
        return json.loads(r.read().decode("utf-8"))


def _tags(text):
    return [{"name": t} for t in re.findall(r"[A-Za-z']+", text or "")]


def pexels_search(q, key):
    def f():
        d = _jget("https://api.pexels.com/v1/search?" + urllib.parse.urlencode({"query": q, "per_page": 30}),
                  {"Authorization": key})
        return [dict(id=f"pexels:{r['id']}", url=r["src"].get("large2x") or r["src"]["original"],
                     foreign_landing_url=r.get("url", ""), creator=r.get("photographer") or "Pexels",
                     license="pexels", license_version="", title=r.get("alt") or "", tags=_tags(r.get("alt")),
                     width=r.get("width"), height=r.get("height"), filetype="jpg", source="pexels")
                for r in d.get("photos", [])]
    return _cached("pexels", q, f)


def pixabay_search(q, key):
    def f():
        d = _jget("https://pixabay.com/api/?" + urllib.parse.urlencode(
            {"key": key, "q": q, "image_type": "photo", "per_page": 30, "safesearch": "true"}))
        return [dict(id=f"pixabay:{r['id']}", url=r.get("largeImageURL") or r.get("webformatURL"),
                     foreign_landing_url=r.get("pageURL", ""), creator=r.get("user") or "Pixabay",
                     license="pixabay", license_version="", title=r.get("tags") or "", tags=_tags(r.get("tags")),
                     width=r.get("imageWidth"), height=r.get("imageHeight"), filetype="jpg", source="pixabay")
                for r in d.get("hits", [])]
    return _cached("pixabay", q, f)


def unsplash_search(q, key):
    def f():
        d = _jget("https://api.unsplash.com/search/photos?" + urllib.parse.urlencode({"query": q, "per_page": 30}),
                  {"Authorization": "Client-ID " + key, "Accept-Version": "v1"})
        out = []
        for r in d.get("results", []):
            t = r.get("description") or r.get("alt_description") or ""
            tag_txt = " ".join(x.get("title", "") for x in (r.get("tags") or []) if isinstance(x, dict))
            out.append(dict(download_location=(r.get("links") or {}).get("download_location", ""),
                            id=f"unsplash:{r['id']}", url=(r.get("urls") or {}).get("full", "") + "&w=2400",
                            foreign_landing_url=(r.get("links") or {}).get("html", ""),
                            creator=(r.get("user") or {}).get("name") or "Unsplash", license="unsplash",
                            license_version="", title=t, tags=_tags(t + " " + tag_txt),
                            width=r.get("width"), height=r.get("height"), filetype="jpg", source="unsplash"))
        return out
    return _cached("unsplash", q, f)


def freepik_search(q, key):
    """Freepik stock photos. Two filters are NOT optional: content_type=photo and ai-generated
    EXCLUDED -- _Shared/Image-Selection-Standards.md bans AI/CGI renders network-wide, and Freepik's
    library is full of them. Everything returned here is a real photograph under the Freepik License,
    credited to its author."""
    def f():
        d = _jget("https://api.freepik.com/v1/resources?" + urllib.parse.urlencode({
            "term": q, "limit": 30, "filters[content_type][photo]": 1,
            "filters[ai-generated][excluded]": 1}), {"x-freepik-api-key": key})
        out = []
        for r in d.get("data", []):
            img = (r.get("image") or {}).get("source") or {}
            url = img.get("url")
            if not url:
                continue
            w = h = None
            m = re.match(r"(\d+)\s*x\s*(\d+)", str(img.get("size") or ""))
            if m:
                w, h = int(m.group(1)), int(m.group(2))
            title = r.get("title") or ""
            out.append(dict(id=f"freepik:{r.get('id')}", url=url, foreign_landing_url=r.get("url", ""),
                            creator=((r.get("author") or {}).get("name") or "Freepik"), license="freepik",
                            license_version="", title=title, tags=_tags(title),
                            width=w, height=h, filetype="jpg", source="freepik"))
        return out
    return _cached("freepik", q, f)


_COMMONS_OK = re.compile(r"^(cc0|public domain|pd|cc by(-sa)? ?[\d.]*|cc-by(-sa)?-[\d.]+)", re.I)


def commons_search(q):
    def f():
        d = _jget("https://commons.wikimedia.org/w/api.php?" + urllib.parse.urlencode({
            "action": "query", "format": "json", "generator": "search", "gsrnamespace": 6,
            "gsrsearch": f"{q} filetype:bitmap", "gsrlimit": 30, "prop": "imageinfo|categories",
            "iiprop": "url|size|mime|extmetadata", "iiurlwidth": 2400, "cllimit": 50, "clshow": "!hidden"}))
        out = []
        for pg in (d.get("query") or {}).get("pages", {}).values():
            ii = (pg.get("imageinfo") or [{}])[0]
            meta = ii.get("extmetadata") or {}
            lic = (meta.get("LicenseShortName") or {}).get("value", "")
            if not _COMMONS_OK.match(lic.strip()) or "image/" not in (ii.get("mime") or ""):
                continue
            creator = re.sub(r"<[^>]+>", "", (meta.get("Artist") or {}).get("value", "")).strip() or "Wikimedia Commons"
            title = re.sub(r"^File:|\.[A-Za-z]{3,4}$", "", pg.get("title", "")).replace("_", " ")
            desc = re.sub(r"<[^>]+>", " ", (meta.get("ImageDescription") or {}).get("value", ""))[:300]
            cats = " ".join(c.get("title", "").replace("Category:", "") for c in pg.get("categories") or [])
            lv = re.search(r"([\d.]+)$", lic)
            lk = "cc0" if lic.lower().startswith("cc0") else ("pdm" if "public" in lic.lower() or lic.lower().startswith("pd")
                  else ("by-sa" if "sa" in lic.lower() else "by"))
            out.append(dict(id=f"commons:{pg.get('pageid')}", url=ii.get("thumburl") or ii.get("url"),
                            foreign_landing_url=ii.get("descriptionurl", ""), creator=creator[:80],
                            license=lk, license_version=lv.group(1) if lv else "", title=title,
                            tags=_tags(desc + " " + cats), width=ii.get("width"), height=ii.get("height"),
                            filetype=(ii.get("mime") or "image/jpeg").split("/")[-1], source="wikimedia_commons"))
        return out
    return _cached("commons", q, f)



_RATE_LIMITED = set()


def _guard(name, fn, q, key):
    """A provider that rate-limits us (Unsplash demo keys allow 50 calls/hour) is dropped for the
    rest of the run instead of failing items; cached queries still come back free."""
    try:
        return fn(q, key)
    except urllib.error.HTTPError as e:
        if e.code in (401, 403, 429):
            _RATE_LIMITED.add(name)          # 401 = key rejected: drop it, don't fail the item
        raise


def provider_searches():
    """[(name, fn(q))] in priority order for this run."""
    keys = image_keys()
    out = []
    for name, fn in (("pexels", pexels_search), ("freepik", freepik_search), ("unsplash", unsplash_search),
                     ("pixabay", pixabay_search)):
        if name in keys and name not in _RATE_LIMITED:
            out.append((name, (lambda fn, k, n: (lambda q: _guard(n, fn, q, k)))(fn, keys[name], name)))
    out.append(("commons", commons_search))
    out.append(("openverse", openverse_search))
    return out


SYN = {"senior": ["elderly", "retiree", "older", "grandparent", "grandmother", "grandfather", "aged"],
       "elderly": ["senior", "retiree", "older", "aged"], "retiree": ["senior", "elderly", "retired"],
       "older": ["senior", "elderly"], "bill": ["invoice", "paperwork", "bills"], "cash": ["money", "dollar", "currency"],
       "money": ["cash", "dollar", "currency"], "dollar": ["money", "cash"], "doctor": ["physician"],
       "pharmacy": ["pharmacist", "drugstore"], "medicine": ["prescription", "pills", "medication"]}


def _norm(w):
    w = w.lower().strip("'’").replace("’", "'")
    if w.endswith("'s"):
        return w            # possessive = usually a name ("Bill's"), not the noun
    if len(w) > 3 and w.endswith("s") and not w.endswith("ss"):
        w = w[:-1]
    return w


def _words(text):
    return {_norm(w) for w in re.findall(r"[A-Za-z0-9'’]+", text or "")}


def relevance(r, qwords):
    """(title_hits, tag_hits): query words (or synonyms) found in title / tags."""
    title = _words(r.get("title"))
    tags = set()
    for t in (r.get("tags") or []):
        if isinstance(t, dict):
            tags |= _words(t.get("name", ""))
    th = gh = 0
    for q in qwords:
        forms = {q} | {_norm(s) for s in SYN.get(q, [])}
        if forms & title:
            th += 1
        elif forms & tags:
            gh += 1
    return th, gh


PEOPLE = {"senior", "elderly", "retiree", "retired", "older", "couple", "grandmother", "grandfather",
          "grandparent", "woman", "man", "people", "aged", "pensioner"}
MONEY = {"bill", "check", "cheque", "money", "cash", "dollar", "medicare", "security", "pharmacy",
         "prescription", "card", "tax", "calculator", "budget", "paperwork", "letter", "mail", "mailbox",
         "bank", "wallet", "receipt", "grocery", "groceries", "invoice", "pill", "medicine", "doctor"}


def _hits(r):
    ws = _words(r.get("title"))
    for t in (r.get("tags") or []):
        if isinstance(t, dict):
            ws |= _words(t.get("name", ""))
    return ws


def group_match(r, qwords):
    """How many of the brief's concept groups (people / money moment) the
    photo covers; a 'senior couple paying bills' brief wants both."""
    want = [g for g in (PEOPLE, MONEY) if set(qwords) & g]
    ws = _hits(r)
    return sum(1 for g in want if ws & g), len(want)


def score_candidate(r, qwords, want_ratio):
    w, h = r.get("width") or 0, r.get("height") or 0
    th, gh = relevance(r, qwords)
    rel = th * 1.5 + gh * 0.6 + group_match(r, qwords)[0] * 1.2
    lic = (r.get("license") or "").lower()
    lic_bonus = {"cc0": 0.6, "pdm": 0.6, "by": 0.5, "by-sa": 0.2}.get(lic, 0)
    # how much of the frame we keep when cover-cropping to the target ratio,
    # and how much we must upscale
    ratio = w / h if h else 1
    keep = min(ratio, want_ratio) / max(ratio, want_ratio)
    return rel * 2 + keep * 1.5 + lic_bonus + min(max(w, h), 3000) / 3000


def usable(r, used, person=False):
    w, h = r.get("width") or 0, r.get("height") or 0
    if max(w, h) < MIN_PHOTO_PX or min(w, h) < 600:
        return False
    if (r.get("license") or "").lower() in ("by-nd", "by-nc", "by-nc-sa", "by-nc-nd", "nc-sampling+", "sampling+"):
        return False
    if (r.get("filetype") or "jpg").lower() not in ("jpg", "jpeg", "png", "webp"):
        return False
    text = (r.get("title") or "") + " " + " ".join(
        t.get("name", "") for t in (r.get("tags") or []) if isinstance(t, dict))
    if (BAD_WORDS_PERSON if person else BAD_WORDS).search(text):
        return False
    if r.get("url") in used or r.get("id") in used:
        return False
    return True


def find_photo(query, item_id, want_ratio, max_queries=8, exclude=()):
    """Search Openverse with progressively looser queries, pool the usable
    candidates, rank by relevance (title hits > tag hits, synonyms count),
    crop fit and license, then download the best. Returns (photo|None, notes)."""
    notes = []
    used = recently_used(item_id) | set(exclude)
    person = query in _PERSON_QUERIES
    qwords = [_norm(w) for w in re.findall(r"[A-Za-z0-9']+", query) if w.lower() not in STOP]
    need = 2 if len(qwords) >= 2 else 1
    pool = {}
    for n, q in enumerate(query_variants(query)[:max_queries]):
        for pname, search in provider_searches():
            if pname in ("unsplash", "pexels", "pixabay") and n >= 3:
                continue        # keyed stock is rate-limited: only the 3 tightest phrasings
            try:
                results = search(q)
            except Exception as e:
                notes.append(f"{pname} '{q}' error: {e}")
                continue
            good = 0
            for r in results:
                if r.get("id") in pool or not usable(r, used, person):
                    continue
                th, gh = relevance(r, qwords)
                if th + gh < need or th == 0 and gh < need + 1:
                    continue
                r["_q"] = q
                r["_score"] = (score_candidate(r, qwords, want_ratio) - n * 0.15
                               + STOCK_BONUS.get(r.get("source") or "", 0))
                pool[r["id"]] = r
                good += 1
            notes.append(f"{pname} '{q}': {len(results)} results, {good} relevant")
        strong = [r for r in pool.values()
                  if relevance(r, qwords)[0] >= min(3, len(qwords))
                  or (group_match(r, qwords)[1] >= 2 and relevance(r, qwords)[0] >= 1
                      and group_match(r, qwords)[0] == group_match(r, qwords)[1])]
        if strong:
            break
    for r in sorted(pool.values(), key=lambda r: r["_score"], reverse=True)[:12]:
        try:
            raw = http_get(r["url"], timeout=40)
            im = Image.open(io.BytesIO(raw))
            im = ImageOps.exif_transpose(im).convert("RGB")
        except Exception as e:
            notes.append(f"download failed {r.get('url')}: {e}")
            continue
        if max(im.size) < MIN_PHOTO_PX:
            notes.append(f"too small after download {im.size}")
            continue
        if max(im.size) > 2600:
            im.thumbnail((2600, 2600), Image.LANCZOS)
        if r.get("source") == "unsplash" and r.get("download_location"):
            try:   # Unsplash API guideline: register the download of a photo we use
                _jget(r["download_location"], {"Authorization": "Client-ID " + image_keys().get("unsplash", "")})
            except Exception:
                pass
        return {"id": r.get("id"), "url": r.get("url"),
                "landing_url": r.get("foreign_landing_url") or "",
                "creator": (r.get("creator") or "Unknown").strip(),
                "license_label": license_label(r), "title": r.get("title") or "",
                "source": r.get("source") or "", "query": r["_q"], "image": im}, notes
    return None, notes


def cover(im, w, h, centering=(0.5, 0.42)):
    return ImageOps.fit(im, (w, h), Image.LANCZOS, centering=centering)


def brief_query(brief):
    if not brief:
        return ""
    subj = (brief.get("subject") or "").strip()
    if subj.lower().startswith(("official:", "person:")):
        name = subj.split(":", 1)[1].strip()
        if name:
            _PERSON_QUERIES.add(name)
            return name
    return (brief.get("query") or "").strip()


# ------------------------------------------------------------------ backgrounds

def brand_fallback(w, h, brand, icon_frac=0.55, icon_alpha=34):
    c1 = hex_rgb(brand["c1"])
    c2 = hex_rgb(brand["c2"])
    bg = Image.new("RGBA", (w, h), c1 + (255,))
    # soft radial lift
    glow = Image.new("L", (w, h), 0)
    gd = ImageDraw.Draw(glow)
    r = int(max(w, h) * 0.55)
    gd.ellipse([w // 2 - r, h // 2 - r, w // 2 + r, h // 2 + r], fill=70)
    glow = glow.filter(ImageFilter.GaussianBlur(r // 3))
    lift = Image.new("RGBA", (w, h), shade(c1, 1.35) + (255,))
    bg = Image.composite(lift, bg, glow)
    size = int(min(w, h) * icon_frac)
    ic = icon_image(brand.get("icon", "check"), c2, size)
    a = ic.getchannel("A").point(lambda v: v * icon_alpha // 255)
    ic.putalpha(a)
    bg.alpha_composite(ic, ((w - size) // 2, (h - size) // 2))
    return bg


def vertical_gradient(w, h, stops):
    col = Image.new("RGB", (1, h))
    px = col.load()
    stops = [(p, hex_rgb(c)) for p, c in stops]
    for y in range(h):
        t = y / (h - 1)
        for i in range(len(stops) - 1):
            p0, c0 = stops[i]
            p1, c1 = stops[i + 1]
            if p0 <= t <= p1:
                u = (t - p0) / (p1 - p0) if p1 > p0 else 0
                px[0, y] = tuple(int(c0[j] + (c1[j] - c0[j]) * u) for j in range(3))
                break
    return col.resize((w, h)).convert("RGBA")


def dark_gradient(w, h, start, end_alpha=235, power=1.6):
    """Transparent above `start` (fraction of h), easing to black at bottom."""
    mask = Image.new("L", (1, h), 0)
    px = mask.load()
    s = int(h * start)
    for y in range(h):
        if y >= s:
            t = min(1.0, (y - s) / max(1, h - s) * power / 1.6)
            ease = t * t * (3 - 2 * t)          # smoothstep: no visible onset edge
            px[0, y] = int(end_alpha * ease)
    mask = mask.resize((w, h))
    black = Image.new("RGBA", (w, h), (0, 0, 0, 255))
    black.putalpha(mask)
    return black


# ------------------------------------------------------------------ brand strip

def brand_tag(img, brand, right_x, center_y, color, icon_color, name_size=32, icon_size=44):
    d = ImageDraw.Draw(img)
    f = font(F_HEAD, name_size)
    name = brand["name"]
    tw = d.textlength(name, font=f)
    x = right_x - tw
    ic = icon_image(brand.get("icon", "check"), icon_color, icon_size)
    img.alpha_composite(ic, (int(x - icon_size - 14), int(center_y - icon_size / 2)))
    bb = f.getbbox("Hg")
    d.text((x, center_y - (bb[1] + bb[3]) / 2), name, font=f, fill=color)
    return x - icon_size - 14


def credit_text(img, text, left_x, center_y, color, size=22, max_w=520):
    d = ImageDraw.Draw(img)
    f = font(F_MED, size)
    text = ellipsize(text, f, max_w, d)
    bb = f.getbbox("Hg")
    d.text((left_x, center_y - (bb[1] + bb[3]) / 2), text, font=f, fill=color)


def photo_credit(photo):
    if not photo:
        return ""
    creator = re.sub(r"\s+", " ", photo.get("creator") or "Unknown")
    return f"Photo: {creator} / {photo['license_label']}"


# ------------------------------------------------------------------ renderers

W_NEWS, H_NEWS = 1080, 1350
W_STORY, H_STORY = 1080, 1920


def render_news_a(item, brand, photo, out):
    c1, c2, c3 = hex_rgb(brand["c1"]), hex_rgb(brand["c2"]), hex_rgb(brand["c3"])
    text = (item.get("overlay") or item.get("text") or "").strip()
    pad = 64
    strip_h = 92
    box_w = W_NEWS - 2 * pad
    # pick the photo share that keeps the overlay big (60% preferred)
    choice = None
    for share in (0.60, 0.56, 0.52, 0.48):
        photo_h = int(H_NEWS * share)
        box_h = H_NEWS - strip_h - photo_h - 60 - 40
        fit = fit_text(text, F_HEAD, box_w, box_h, 84, 40, line_ratio=1.16)
        if choice is None or fit[0] > choice[1][0]:
            choice = (photo_h, fit, box_h)
        if fit[4] and fit[0] >= 58:
            choice = (photo_h, fit, box_h)
            break
    photo_h, (size, lines, lh, total, fits), box_h = choice
    img = Image.new("RGBA", (W_NEWS, H_NEWS), c1 + (255,))
    if photo:
        img.paste(cover(photo["image"], W_NEWS, photo_h), (0, 0))
        # gentle darken at the seam
        img.alpha_composite(dark_gradient(W_NEWS, photo_h, 0.75, 90), (0, 0))
    else:
        img.alpha_composite(brand_fallback(W_NEWS, photo_h, brand, 0.5, 40), (0, 0))
    d = ImageDraw.Draw(img)
    d.rectangle([0, photo_h, W_NEWS, photo_h + 10], fill=c2)
    # headline, vertically centered in its block
    top = photo_h + 10 + 50
    avail = H_NEWS - strip_h - top - 30
    y = top + max(0, (avail - total) // 2)
    draw_lines(img, lines, F_HEAD, size, pad, y, lh, (255, 255, 255), accent=highlight(c2, c1))
    # bottom strip
    sy = H_NEWS - strip_h
    d = ImageDraw.Draw(img)
    d.rectangle([0, sy, W_NEWS, H_NEWS], fill=shade(c1, 0.72))
    left = brand_tag(img, brand, W_NEWS - pad, sy + strip_h / 2, c3, c2)
    cr = photo_credit(photo)
    if cr:
        credit_text(img, cr, pad, sy + strip_h / 2, shade(c3, 0.78), 22, max(200, left - pad - 30))
    img.convert("RGB").save(out, optimize=True)
    return size, fits


def circle_inset(im, d, border=8, border_col=(255, 255, 255)):
    ph = cover(im, d, d, (0.5, 0.45)).convert("RGBA")
    S = 4
    m = Image.new("L", (d * S, d * S), 0)
    ImageDraw.Draw(m).ellipse([0, 0, d * S - 1, d * S - 1], fill=255)
    m = m.resize((d, d), Image.LANCZOS)
    out = Image.new("RGBA", (d + 2 * border, d + 2 * border), (0, 0, 0, 0))
    bm = Image.new("L", ((d + 2 * border) * S,) * 2, 0)
    ImageDraw.Draw(bm).ellipse([0, 0, (d + 2 * border) * S - 1, (d + 2 * border) * S - 1], fill=255)
    bm = bm.resize((d + 2 * border,) * 2, Image.LANCZOS)
    ring = Image.new("RGBA", out.size, border_col + (255,))
    out.paste(ring, (0, 0), bm)
    out.paste(ph, (border, border), m)
    return out


def render_news_b(item, brand, photo, out, inset=None):
    c1, c2, c3 = hex_rgb(brand["c1"]), hex_rgb(brand["c2"]), hex_rgb(brand["c3"])
    text = (item.get("overlay") or item.get("text") or "").strip()
    pad = 64
    strip_h = 96
    box_w = W_NEWS - 2 * pad
    box_h = int(H_NEWS * 0.46)
    size, lines, lh, total, fits = fit_text(text, F_HEAD, box_w, box_h, 76, 40, line_ratio=1.15)
    if photo:
        img = cover(photo["image"], W_NEWS, H_NEWS).convert("RGBA")
    else:
        img = brand_fallback(W_NEWS, int(H_NEWS * 0.62), brand, 0.5, 40)
        full = Image.new("RGBA", (W_NEWS, H_NEWS), hex_rgb(brand["c1"]) + (255,))
        full.alpha_composite(img, (0, 0))
        img = full
    text_top = H_NEWS - strip_h - 30 - total
    if photo:
        img.alpha_composite(Image.new("RGBA", img.size, (0, 0, 0, 38)))   # overall -15%
    start = max(0.12, (text_top - 380) / H_NEWS)
    img.alpha_composite(dark_gradient(W_NEWS, H_NEWS, start, 248, 2.2))
    if inset is not None:
        dd = 300
        ci = circle_inset(inset["image"], dd)
        img.alpha_composite(ci, (W_NEWS - pad - ci.width + 8, 70))
    d = ImageDraw.Draw(img)
    d.rectangle([pad, text_top - 34, pad + 110, text_top - 26], fill=c2)
    draw_lines(img, lines, F_HEAD, size, pad, text_top, lh, (255, 255, 255), accent=highlight(c2, (18, 18, 18)),
               shadow=((0, 0, 0, 170), 0, 3, 6))
    sy = H_NEWS - strip_h
    d = ImageDraw.Draw(img)
    d.line([pad, sy, W_NEWS - pad, sy], fill=(255, 255, 255, 60), width=2)
    left = brand_tag(img, brand, W_NEWS - pad, sy + strip_h / 2, (255, 255, 255), c2)
    creds = [photo_credit(photo)] if photo else []
    if inset is not None:
        creds.append("Inset: " + photo_credit(inset)[len("Photo: "):])
    cr = " · ".join(c for c in creds if c)
    if cr:
        credit_text(img, cr, pad, sy + strip_h / 2, (225, 225, 225), 22, max(200, left - pad - 30))
    img.convert("RGB").save(out, optimize=True)
    return size, fits


def render_news_t(item, page_code, brand, photo, out, photo2=None):
    """Format T (2026-10-12, Alex: "look at the competitors"): the post card the top political pages
    use (Red Wave, Raging Americans, Republican Patriots, America First, God Bless America, Patriots
    United). White top with the page's logo, name, check and handle; the story in heavy black type;
    the photo of the person (or two people, side by side) filling the bottom. No brand colours on the
    card, so no colour can ever be hard to read."""
    ti = textimage_module()
    text = (item.get("overlay") or item.get("text") or "").strip()
    name = brand.get("name") or page_code
    logo = logo_path(page_code, brand)
    W, H = W_NEWS, H_NEWS
    pad = 40
    body_top = ti.LOGO_Y + ti.LOGO_D + 30
    best = None
    for photo_h in (620, 580, 540, 500, 460):
        box_h = H - photo_h - body_top - 34
        fit = fit_text(text, F_HEAD, W - 2 * pad, box_h, 76, 40, line_ratio=1.17)
        if best is None or fit[0] > best[1][0]:
            best = (photo_h, fit)
        if fit[4] and fit[0] >= 56:
            best = (photo_h, fit)
            break
    photo_h, (size, lines, lh, total, fits) = best
    img = Image.new("RGBA", (W, H), (255, 255, 255, 255))
    d = ImageDraw.Draw(img)
    if logo and os.path.exists(logo):
        cl = ti.circle_logo(logo, ti.LOGO_D)
        img.alpha_composite(cl, (ti.LOGO_X, ti.LOGO_Y))
    else:
        d.ellipse([ti.LOGO_X, ti.LOGO_Y, ti.LOGO_X + ti.LOGO_D, ti.LOGO_Y + ti.LOGO_D], fill=(220, 224, 228))
    nf = font(F_HEAD, 44)
    hf = font(F_MED, 36)
    tx = ti.LOGO_X + ti.LOGO_D + 22
    d.text((tx, ti.LOGO_Y + 4), name, font=nf, fill=(15, 20, 25))
    # No verified badge: Yeez never draws one (the setup recommends Meta Verified instead).
    d.text((tx, ti.LOGO_Y + 56), ti.handle_for(name), font=hf, fill=(110, 118, 125))
    top = H - photo_h
    y = body_top + max(0, (top - 34 - body_top - total) // 2)
    draw_lines(img, lines, F_HEAD, size, pad, y, lh, (15, 20, 25))
    if photo and photo2:
        half = (W - 6) // 2
        img.paste(cover(photo["image"], half, photo_h, (0.5, 0.3)), (0, top))
        img.paste(cover(photo2["image"], W - half - 6, photo_h, (0.5, 0.3)), (half + 6, top))
    elif photo:
        img.paste(cover(photo["image"], W, photo_h, (0.5, 0.3)), (0, top))
    else:
        img.alpha_composite(brand_fallback(W, photo_h, brand, 0.5, 40), (0, top))
    creds = [c for c in ([photo_credit(photo)] if photo else []) + ([photo_credit(photo2)] if photo2 else []) if c]
    if creds:
        cf = font(F_MED, 20)
        cr = ellipsize(" · ".join(creds), cf, W - 60, d)
        tw = d.textlength(cr, font=cf)
        chip = Image.new("RGBA", (int(tw + 24), 34), (0, 0, 0, 130))
        img.alpha_composite(chip, (16, H - 50))
        d = ImageDraw.Draw(img)
        d.text((28, H - 45), cr, font=cf, fill=(240, 240, 240))
    img.convert("RGB").save(out, optimize=True)
    return size, fits


def rounded_photo(im, w, h, r):
    ph = cover(im, w, h).convert("RGBA")
    S = 3
    m = Image.new("L", (w * S, h * S), 0)
    ImageDraw.Draw(m).rounded_rectangle([0, 0, w * S - 1, h * S - 1], radius=r * S, fill=255)
    ph.putalpha(m.resize((w, h), Image.LANCZOS))
    return ph


def render_story(item, brand, mode, photo, out):
    c1, c2, c3 = hex_rgb(brand["c1"]), hex_rgb(brand["c2"]), hex_rgb(brand["c3"])
    grad = mode == "gradient"
    if grad:
        img = vertical_gradient(W_STORY, H_STORY, GRADIENT_STOPS)
        fg, hl, icol = (255, 255, 255), None, (255, 255, 255)
        pill_bg, pill_fg, pill_hl = (255, 255, 255), hex_rgb("#A935A8"), hex_rgb("#D8577A")
        shadow = ((0, 0, 0, 60), 0, 3, 7)
    else:
        # 2026-10-12 (Alex): no page colours on the cards -- the competitors' cards are plain white with
        # black type. Brand mode is now a white story, black type, a black reply button with white words.
        c1 = (255, 255, 255)
        img = Image.new("RGBA", (W_STORY, H_STORY), c1 + (255,))
        fg, hl, icol = (15, 20, 25), None, (15, 20, 25)
        pill_bg = (15, 20, 25)
        pill_fg = pill_hl = (255, 255, 255)
        shadow = None
    d = ImageDraw.Draw(img)
    pad = 80
    # header: icon + page name (gen.py: top 120, icon 84, 44px ExtraBold)
    ic = icon_image(brand.get("icon", "check"), icol, 84)
    img.alpha_composite(ic, (pad, 120))
    hf = font(F_HEAD, 44)
    name = ellipsize(brand["name"], hf, W_STORY - 2 * pad - 110, d)
    bb = hf.getbbox("Hg")
    d.text((pad + 84 + 26, 120 + 42 - (bb[1] + bb[3]) / 2), name, font=hf, fill=fg if not grad else (255, 255, 255))

    # CTA pill (KEYWORD only)
    cta = item.get("cta") or {}
    pill_top = None
    if (cta.get("mode") or "").upper() == "KEYWORD" and cta.get("keyword"):
        kw = cta["keyword"].strip().upper()
        # 2026-10-12 (Alex): short button. Write supplies cta.pill (the thing we send, 6 words or fewer);
        # without it, fall back to the product's short name.
        thing = (cta.get("pill") or "").strip().rstrip(".") or product_short_name(cta)
        pill_text = f"Reply {kw} for {thing}"
        pw = W_STORY - 2 * pad
        psize, plines, plh, ptot, _ = fit_text(pill_text, F_HEAD, pw - 100, 250, 56, 38, line_ratio=1.2)
        ph = ptot + 88
        pill_bottom = H_STORY - 250
        pill_top = pill_bottom - ph
        d.rounded_rectangle([pad, pill_top, W_STORY - pad, pill_bottom], radius=36, fill=pill_bg)
        # keyword itself in the stronger tone
        pf = font(F_HEAD, psize)
        yy = pill_top + 44 - (pf.getbbox("Hg")[1]) * 0.35
        space = d.textlength(" ", font=pf)
        for line in plines:
            lw = d.textlength(" ".join(line), font=pf)
            x = pad + (pw - lw) / 2
            for w in line:
                is_kw = re.sub(r"\W", "", w) == kw
                col = pill_fg
                if is_kw and grad:
                    col = pill_hl
                f2 = font(F_BLACK, psize) if is_kw else pf
                d.text((x, yy), w, font=f2, fill=col)
                x += d.textlength(w, font=f2) + space
            yy += plh

    # optional photo band
    y_top = 330
    if photo:
        bw, bh = W_STORY - 2 * pad, 600
        img.alpha_composite(rounded_photo(photo["image"], bw, bh, 36), (pad, 290))
        cr = photo_credit(photo)
        cf = font(F_MED, 22)
        d = ImageDraw.Draw(img)
        cr = ellipsize(cr, cf, bw - 40, d)
        # credit chip on the photo's bottom-left
        tw = d.textlength(cr, font=cf)
        chip = Image.new("RGBA", (int(tw + 28), 40), (0, 0, 0, 140))
        img.alpha_composite(chip, (pad + 20, 290 + bh - 60))
        d = ImageDraw.Draw(img)
        d.text((pad + 34, 290 + bh - 60 + 8), cr, font=cf, fill=(240, 240, 240))
        y_top = 290 + bh + 70

    bottom = (pill_top - 70) if pill_top else (H_STORY - 330)
    avail = bottom - y_top
    text = (item.get("text") or item.get("overlay") or "").strip()
    size, lines, lh, total, fits = fit_text(text, F_SERIF, W_STORY - 2 * pad, avail,
                                            104 if not photo else 88, 48, line_ratio=1.18)
    # place in the upper third of the free region (gen.py puts it at y=470)
    if photo:
        y = y_top + max(0, (avail - total) // 3)
    elif pill_top is None:
        y = y_top + max(0, int((avail - total) * 0.42))     # optical centre
    else:
        y = max(y_top, min(470, bottom - total)) if total <= avail - 140 else y_top + max(0, (avail - total) // 3)
    draw_lines(img, lines, F_SERIF, size, pad, y, lh, fg, accent=hl, shadow=shadow)
    img.convert("RGB").save(out, optimize=True)
    return size, fits



# ------------------------------------------------------------------ reels (ffmpeg) — the network's reel engine, buyer's own footage

import shutil
import subprocess
import tempfile

REEL_FPS = 30
FOOTAGE_FOLDER = [None]      # the buyer's shared Google Drive folder (page file "footage_folder")


def _ffmpeg():
    exe = shutil.which("ffmpeg")
    if not exe:
        raise RuntimeError("ffmpeg isn't installed in this AI app (install it: apt-get install -y ffmpeg, or pip install imageio-ffmpeg)")
    return exe


def _run_ff(args):
    r = subprocess.run([_ffmpeg(), "-y", "-loglevel", "error"] + args, capture_output=True, text=True)
    if r.returncode != 0:
        raise RuntimeError("ffmpeg failed: " + (r.stderr or "")[-400:])


def _compose_vertical(card_png, out_png):
    """1080x1920 frame: blurred, darkened cover of the card + the card centred."""
    card = Image.open(card_png).convert("RGB")
    bg = ImageOps.fit(card, (W_STORY, H_STORY), centering=(0.5, 0.5)).filter(ImageFilter.GaussianBlur(40))
    bg = Image.blend(bg, Image.new("RGB", bg.size, (0, 0, 0)), 0.35)
    cw = W_STORY
    ch = int(card.height * cw / card.width)
    if ch > H_STORY - 160:
        ch = H_STORY - 160
        cw = int(card.width * ch / card.height)
    card = card.resize((cw, ch), Image.LANCZOS)
    bg.paste(card, ((W_STORY - cw) // 2, (H_STORY - ch) // 2))
    bg.save(out_png)


def _static_with_music(png, out_mp4, seconds, track):
    """Image->Reel: the exact image held STATIC (no motion) as a vertical video over calm music."""
    audio = ["-i", track] if track else ["-f", "lavfi", "-i", "anullsrc=r=44100:cl=stereo"]
    af = ["-af", f"afade=t=in:d=0.6,afade=t=out:st={max(0, seconds - 1.2)}:d=1.2,volume=0.8"] if track else []
    _run_ff(["-loop", "1", "-i", png] + audio +
            ["-vf", f"scale={W_STORY}:{H_STORY},fps={REEL_FPS},format=yuv420p"] + af +
            ["-t", str(seconds), "-shortest", "-c:v", "libx264", "-preset", "veryfast", "-crf", "20",
             "-c:a", "aac", "-b:a", "128k", "-movflags", "+faststart", out_mp4])


_RR = None


def reel_render_module():
    global _RR
    if _RR is None:
        sys.path.insert(0, HERE)
        os.environ.setdefault("REEL_X264_PRESET", "faster")
        import reel_render as rr   # noqa: E402
        _RR = rr
    return _RR


def footage_dir():
    return os.path.join(WORK, "footage")


def _need_folder():
    if not FOOTAGE_FOLDER[0]:
        raise RuntimeError("no footage folder: reels use the buyer's own clips and music from a shared Google Drive "
                           "folder (save it with save_social_settings footage_folder)")
    sys.path.insert(0, HERE)
    import yeez_footage as yf   # noqa: E402
    return yf


def music_tracks():
    yf = _need_folder()
    tracks = yf.ensure_music(FOOTAGE_FOLDER[0], WORK)
    if not tracks:
        raise RuntimeError("the footage folder has no 'music' folder with tracks; reels need the buyer's own music")
    return tracks


def _music_track(key):
    import hashlib
    tracks = sorted(music_tracks())
    return tracks[int(hashlib.md5(key.encode()).hexdigest(), 16) % len(tracks)]


def build_image_reel(item, page_code, brand, media_dir, date_dir):
    """The exact image of one of today's built cards (source_item), held static over the buyer's music for 10s."""
    iid = item["id"]
    tmp = tempfile.mkdtemp(prefix="reel-")
    extra = {}
    try:
        src = None
        if item.get("source_item"):
            cand = os.path.join(media_dir, f"{item['source_item']}.png")
            src = cand if os.path.exists(cand) else None
            if not src:
                raise RuntimeError(f"source_item {item['source_item']} has no built image yet (build it first)")
        if not src:
            brief = item.get("image_brief") or {}
            q = brief_query(brief)
            photo, notes = (find_photo(q, iid, W_NEWS / 600) if q else (None, []))
            src = os.path.join(tmp, "card.png")
            size, fits = render_news_t(item, page_code, brand, photo, src)
            if not fits:
                raise RuntimeError("image_reel overlay too long to fit")
            if photo:
                ledger_add(photo, iid, page_code, q)
                extra["photo_credit"] = credit_of(photo)
        frame = os.path.join(tmp, "frame.png")
        _compose_vertical(src, frame)
        out = os.path.join(media_dir, f"{iid}.mp4")
        track = _music_track(iid)
        _static_with_music(frame, out, 10, track)
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
    return f"media/{iid}.mp4", f"image_reel rendered 1080x1920 10s static from {item.get('source_item') or 'a new card'} + music {os.path.basename(track)}", extra


def build_text_reel(item, page_code, brand, media_dir, idx):
    """Format R ("read it on screen"): every line on screen from the first frame, white type on dark
    boxes, over ONE of the buyer's footage folders (picked by reel_mood) with their own music, 12s."""
    iid = item["id"]
    fmt = (item.get("reel_format") or "R").upper()[:1]
    if fmt == "P":
        return build_person_reel(item, page_code, brand, media_dir)
    rr = reel_render_module()
    import reel_parse as rp
    raw = (item.get("text") or "").strip()
    lines = [re.sub(r"^\s*(?:[-*]|\d+[.)])\s*", "", l.strip()) for l in raw.split("\n") if l.strip()]
    if not lines:
        raise RuntimeError("reel has no on-screen text")
    cards, styles = rp.split_style_tags(lines)
    styles = ["black"] * len(cards)
    duration = float(item.get("duration_s") or 12.0)
    yf = _need_folder()
    mood, clips = yf.ensure_clips(FOOTAGE_FOLDER[0], WORK, item.get("reel_mood"), k=4)
    if not clips:
        raise RuntimeError(f"no clips in the '{mood}' footage folder")
    music_tracks()
    assets = footage_dir()
    wdate = now_local().strftime("%Y-%m-%d")
    picker = rr.BrollPicker(clips, seed=abs(hash(iid)) % 10000, target_seconds=duration, assets_dir=assets, working_date=wdate)
    reel = {"page_code": page_code, "working_date": wdate, "reel_number": idx + 1, "slug": iid, "format": "R",
            "tier1": False, "primary_model_id": "", "model_ids": [""], "caption": item.get("caption") or "",
            "onscreen_mode": "sequence" if len(cards) > 1 else "single", "onscreen_cards": cards,
            "onscreen_styles": styles, "assets": {}, "layout": "full"}
    tmp = tempfile.mkdtemp(prefix="reel-")
    try:
        qa = rr.render_reel(reel, 0, tmp, assets, duration, picker)
        picker.save_ledger()
        if qa["status"] != "rendered" or not qa.get("output"):
            raise RuntimeError("reel render failed: " + "; ".join(qa.get("flags") or []))
        bad = [f for f in qa["flags"] if "DO NOT POST" in f or "NO B-ROLL" in f or "without an audio" in f]
        if bad:
            raise RuntimeError("; ".join(bad))
        out = os.path.join(media_dir, f"{iid}.mp4")
        shutil.move(qa["output"], out)
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
    note = f"reel rendered Format R {qa.get('duration_s')}s over '{mood}' footage [{qa.get('broll')}] + music {qa.get('music')} ({len(cards)} lines)"
    if qa["flags"]:
        note += " | flags: " + "; ".join(qa["flags"])
    return f"media/{iid}.mp4", note, {}


def build_person_reel(item, page_code, brand, media_dir):
    """Format P ("named person"): the post card on top (logo, name, handle, the story in heavy black
    type) and the person's photo below with a slow push-in, 9 seconds, the buyer's music. No badge."""
    iid = item["id"]
    ti = textimage_module()
    brief = item.get("image_brief") or {}
    q = brief_query(brief)
    photo, notes = find_photo(q, iid, 1080 / 1060) if q else (None, ["no image_brief"])
    if photo is None:
        raise RuntimeError("person reel needs a photo: " + "; ".join(notes[-3:]))
    ledger_add(photo, iid, page_code, q)
    text = re.sub(r"^\s*(?:[-*]|\d+[.)])\s*", "", (item.get("text") or item.get("overlay") or "").strip(), flags=re.M)
    W, H, PH = 1080, 1920, 1060
    top_h = H - PH
    panel = Image.new("RGBA", (W, top_h), (255, 255, 255, 255))
    d = ImageDraw.Draw(panel)
    name = (brand or {}).get("name") or page_code
    logo = logo_path(page_code, brand)
    y0 = 240
    if logo and os.path.exists(logo):
        panel.alpha_composite(ti.circle_logo(logo, ti.LOGO_D), (ti.LOGO_X + 8, y0))
    else:
        d.ellipse([ti.LOGO_X + 8, y0, ti.LOGO_X + 8 + ti.LOGO_D, y0 + ti.LOGO_D], fill=(220, 224, 228))
    nf, hf = font(F_HEAD, 44), font(F_MED, 36)
    tx = ti.LOGO_X + 8 + ti.LOGO_D + 22
    d.text((tx, y0 + 4), name, font=nf, fill=(15, 20, 25))
    d.text((tx, y0 + 56), ti.handle_for(name), font=hf, fill=(110, 118, 125))
    body_top = y0 + ti.LOGO_D + 34
    size, lines, lh, total, fits = fit_text(text, F_HEAD, W - 96, top_h - body_top - 40, 64, 38, line_ratio=1.17)
    draw_lines(panel, lines, F_HEAD, size, 48, body_top + max(0, (top_h - body_top - 40 - total) // 2), lh, (15, 20, 25))
    music = _music_track(iid)
    tmp = tempfile.mkdtemp(prefix="preel-")
    try:
        ppng = os.path.join(tmp, "panel.png"); panel.convert("RGB").save(ppng)
        ph = cover(photo["image"], int(W * 1.15), int(PH * 1.15), (0.5, 0.3))
        cr = photo_credit(photo)
        if cr:
            dd = ImageDraw.Draw(ph); cf = font(F_MED, 22)
            dd.rectangle([0, ph.height - 46, int(dd.textlength(cr, font=cf) + 40), ph.height], fill=(0, 0, 0))
            dd.text((20, ph.height - 38), cr, font=cf, fill=(235, 235, 235))
        pjpg = os.path.join(tmp, "photo.jpg"); ph.convert("RGB").save(pjpg, quality=92)
        dur = float(item.get("duration_s") or 9.0)
        fps = 30
        out = os.path.join(media_dir, f"{iid}.mp4")
        frames = int(dur * fps)
        fc = (f"color=c=white:s={W}x{H}:d={dur}:r={fps}[bg];"
              f"[1:v]zoompan=z='min(zoom+0.0009,1.13)':x='iw/2-(iw/zoom/2)':y='ih/3-(ih/zoom/3)':"
              f"d={frames}:s={W}x{PH}:fps={fps}[ph];"
              f"[bg][ph]overlay=0:{top_h}[v1];[v1][2:v]overlay=0:0,format=yuv420p[vout]")
        cmd = [_ffmpeg(), "-y", "-loglevel", "error", "-f", "lavfi", "-i", "anullsrc=r=44100:cl=stereo",
               "-loop", "1", "-i", pjpg, "-loop", "1", "-i", ppng, "-stream_loop", "-1", "-i", music,
               "-filter_complex", fc, "-map", "[vout]", "-map", "3:a:0",
               "-af", f"afade=t=out:st={max(0, dur - 1.5):.2f}:d=1.5,volume=0.65",
               "-c:v", "libx264", "-preset", os.environ.get("REEL_X264_PRESET", "faster"), "-crf", "20",
               "-pix_fmt", "yuv420p", "-r", str(fps), "-c:a", "aac", "-b:a", "128k",
               "-movflags", "+faststart", "-t", f"{dur:.2f}", out]
        subprocess.run(cmd, check=True)
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
    return (f"media/{iid}.mp4", f"reel rendered Format P (person card + push-in) {dur:.0f}s; photo [{photo.get('source')}]; music {os.path.basename(music)}",
            {"photo_credit": credit_of(photo)})


# ------------------------------------------------------------------ Yeez: logos, text image, queue

def logo_path(page_code, brand):
    """The Page's own profile picture, downloaded once from brand.logo_url into yeez-work/logos/."""
    p = os.path.join(LOGO_DIR, f"{page_code.upper()}.png")
    if os.path.exists(p):
        return p
    url = (brand or {}).get("logo_url")
    if not url:
        return None
    try:
        os.makedirs(LOGO_DIR, exist_ok=True)
        im = Image.open(io.BytesIO(http_get(url, timeout=20))).convert("RGBA")
        im.save(p)
        return p
    except Exception:
        return None


_TI = None


def textimage_module():
    global _TI
    if _TI is None:
        sys.path.insert(0, HERE)
        import textimage_render as ti   # noqa: E402
        _TI = ti
    return _TI


def render_text_image(item, page_code, brand, out):
    ti = textimage_module()
    name = (brand or {}).get("name") or page_code
    body = (item.get("text") or "").strip()
    # Every proven text-image winner is 4:5 with the copy filling the card: always 1080x1350, type up to 96px.
    path, h, size, flags = ti.render_card(name, ti.handle_for(name), logo_path(page_code, brand), body, out,
                                          heights=(ti.H_TALL,), body_max=96)
    return h, size, flags


def atomic_write_json(path, data):
    tmp = path + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
        f.write("\n")
    os.replace(tmp, path)


def credit_of(p):
    return {k: p[k] for k in ("url", "landing_url", "creator", "license_label", "source", "title")}


def build_item(item, idx_story, page_code, brand, media_dir):
    """Returns (new_status, media_rel or None, note, extra dict)."""
    t = (item.get("type") or "").lower()
    iid = item["id"]
    out = os.path.join(media_dir, f"{iid}.png")
    rel = f"media/{iid}.png"
    brief = item.get("image_brief") or {}

    if t in ("gradient", "link"):
        return "built", None, f"{t}: nothing to render", {}

    if t == "image_reel":
        rel_, note, extra = build_image_reel(item, page_code, brand, media_dir, os.path.dirname(media_dir))
        return "built", rel_, note, extra

    if t == "reel":
        rel_, note, extra = build_text_reel(item, page_code, brand, media_dir, idx_story)
        return "built", rel_, note, extra

    if t == "text_image":
        h, size, flags = render_text_image(item, page_code, brand, out)
        note = f"text_image rendered 1080x{h} ({size}px body)"
        if flags:
            note += " | flags: " + "; ".join(flags)
        return "built", rel, note, {"flags": flags} if flags else {}

    if t == "news_image":
        fmt = (brief.get("format") or "T").strip().upper()
        fmt = "B" if fmt.startswith("B") else ("A" if fmt.startswith("A") else "T")
        q = brief_query(brief)
        photo, notes = (None, ["no image_brief.query"])
        if q:
            ratio = {"A": W_NEWS / (H_NEWS * 0.6), "B": W_NEWS / H_NEWS, "T": W_NEWS / 600}[fmt]
            photo, notes = find_photo(q, iid, ratio)
        photo2 = None
        q2 = brief_query({"subject": brief.get("subject2") or ""}) if brief.get("subject2") else ""
        if fmt == "T" and q2 and photo:
            photo2, n3 = find_photo(q2, iid + "#2", (W_NEWS / 2) / 600, exclude={photo["url"]})
            notes += n3
            if photo2 is None:
                notes.append(f"second person photo not found for {q2!r}; one photo used")
        inset = None
        iq = (brief.get("inset_query") or "").strip()
        if fmt == "B" and iq and not iq.lower().startswith(("person:", "official:")):
            notes.append(f"inset dropped (not a person): {iq!r}")
            iq = ""
        if iq:
            iq = brief_query({"subject": iq})
        if fmt == "B" and iq:
            inset, n2 = find_photo(iq, iid + "#inset", 1.0, exclude={photo["url"]} if photo else set())
            notes += n2
        if fmt == "T":
            size, fits = render_news_t(item, page_code, brand, photo, out, photo2)
        elif fmt == "A":
            size, fits = render_news_a(item, brand, photo, out)
        else:
            size, fits = render_news_b(item, brand, photo, out, inset)
        extra = {}
        if photo:
            ledger_add(photo, iid, page_code, q)
            extra["photo_credit"] = credit_of(photo)
            src = f"photo {photo['id']} [{photo['source']}] ({photo['creator']} / {photo['license_label']}, query '{photo['query']}')"
            if photo2 is not None:
                ledger_add(photo2, iid + "#2", page_code, q2)
                extra["photo2_credit"] = credit_of(photo2)
                src += f" + photo2 {photo2['id']} [{photo2['source']}]"
        else:
            src = "NO usable photo -> brand background (" + " | ".join(notes[-3:]) + ")"
        if inset:
            ledger_add(inset, iid + "#inset", page_code, iq)
            extra["inset_credit"] = credit_of(inset)
        note = f"news_image format {fmt} rendered ({size}px overlay{'' if fits else ', OVERFLOW at min size'}); {src}"
        if not fits:
            raise RuntimeError(f"overlay too long to fit even at min size: shorten it. {note}")
        return "built", rel, note, extra

    if t == "story":
        mode = (brief.get("format") or "").strip().lower()
        if mode not in ("brand", "gradient"):
            mode = "brand" if idx_story % 2 == 0 else "gradient"
        photo, notes = None, []
        q = brief_query(brief)
        if q:
            photo, notes = find_photo(q, iid, (W_STORY - 160) / 600)
        size, fits = render_story(item, brand, mode, photo, out)
        extra, src = {}, ""
        if photo:
            ledger_add(photo, iid, page_code, q)
            extra["photo_credit"] = credit_of(photo)
            src = f"; photo band {photo['id']} [{photo['source']}]"
        elif q:
            src = "; no usable photo, band omitted"
        if not fits:
            raise RuntimeError(f"story headline too long to fit at min size ({size}px): shorten it")
        cta = item.get("cta") or {}
        pill = f"pill Reply {cta.get('keyword', '').upper()}" if (cta.get("mode") or "").upper() == "KEYWORD" else "no pill"
        return "built", rel, f"story rendered ({mode}, {size}px headline, {pill}){src}", extra

    raise ValueError(f"unknown item type '{t}'")


def process_page_file(path, rebuild=False, only_types=None):
    data = json.load(open(path, encoding="utf-8"))
    page_code = (data.get("page") or os.path.splitext(os.path.basename(path))[0]).upper()
    brands = load_brands() if os.path.exists(BRANDS_JSON) else {}
    brand = brands.get(page_code.lower())
    date_dir = os.path.dirname(path)
    media_dir = os.path.join(date_dir, "media")
    os.makedirs(media_dir, exist_ok=True)
    todo_status = {"written"} | ({"built", "failed"} if rebuild else set())
    counts = {"built": 0, "failed": 0, "skipped": 0, "left": 0}
    story_idx = 0
    FOOTAGE_FOLDER[0] = data.get("footage_folder")
    items = data.get("items", [])
    order = [i for i in items if (i.get("type") or "").lower() != "image_reel"] + [i for i in items if (i.get("type") or "").lower() == "image_reel"]
    for item in order:
        t = (item.get("type") or "").lower()
        this_story_idx = story_idx
        if t == "story":
            story_idx += 1
        if only_types and t not in only_types:
            counts["skipped"] += 1
            continue
        if item.get("status") not in todo_status:
            counts["skipped"] += 1
            continue
        item.setdefault("log", [])
        try:
            if True:
                if brand is None and t in ("news_image", "story", "text_image"):
                    raise ValueError(f"page code {page_code} is not in yeez-work/brands.json")
                status, media, note, extra = build_item(item, this_story_idx, page_code, brand, media_dir)
                if status is None:
                    counts["left"] += 1
                    print(f"  --  {item['id']:16} {t:11} {note}")
                    continue
                item.update(extra)
                item["media"], item["status"], item["error"] = media, status, None
                item["log"].append(log_line(note))
                counts["built"] += 1
                print(f"  ok  {item['id']:16} {t:11} {note}")
        except Exception as e:
            item["status"] = "failed"
            item["error"] = f"{type(e).__name__}: {e}"
            item["log"].append(log_line(f"FAILED {item['error']}"))
            counts["failed"] += 1
            print(f"  ERR {item.get('id')} {t}: {item['error']}")
            traceback.print_exc(limit=2)
        atomic_write_json(path, data)       # save progress after every item
    return page_code, counts


def main():
    global TZ, TODAY
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--date", default=None)
    ap.add_argument("--page", default=None, help="one page code from brands.json")
    ap.add_argument("--work", default=None, help="work folder (default ./yeez-work or $YEEZ_WORK)")
    ap.add_argument("--rebuild", action="store_true", help="also re-render built/failed items")
    ap.add_argument("--type", default=None, help="only these item types, comma-separated")
    args = ap.parse_args()
    if not args.date:
        ap.error("--date is required")
    if args.work:
        set_work(args.work)
    date_dir = os.path.join(QUEUE_ROOT, args.date)
    if not os.path.isdir(date_dir):
        raise SystemExit(f"no queue folder {date_dir}")
    files = sorted(f for f in os.listdir(date_dir) if f.endswith(".json") and not f.startswith("_"))
    if args.page:
        files = [f for f in files if os.path.splitext(f)[0].upper() == args.page.upper()]
    if not files:
        raise SystemExit("no page files to build")
    total = {"built": 0, "failed": 0, "skipped": 0, "left": 0}
    for f in files:
        meta = json.load(open(os.path.join(date_dir, f), encoding="utf-8"))
        if meta.get("timezone"):
            try:
                TZ = ZoneInfo(meta["timezone"])
                TODAY = now_local().date()
            except Exception:
                pass
        set_audience(meta.get("audience"))
        print(f"{f}:")
        code, c = process_page_file(os.path.join(date_dir, f), args.rebuild,
                                    {t.strip().lower() for t in args.type.split(",")} if args.type else None)
        for k in total:
            total[k] += c[k]
    print(f"\nbuilt {total['built']} · failed {total['failed']} · left for later {total['left']} · untouched {total['skipped']}")
    sys.exit(1 if total["failed"] else 0)


def set_work(path):
    global WORK, QUEUE_ROOT, BRANDS_JSON, LOGO_DIR, LEDGER, PHOTO_CACHE, IMAGE_KEYS_JSON
    WORK = os.path.abspath(path)
    QUEUE_ROOT = os.path.join(WORK, "queue")
    BRANDS_JSON = os.path.join(WORK, "brands.json")
    LOGO_DIR = os.path.join(WORK, "logos")
    LEDGER = os.path.join(WORK, "photo-ledger.csv")
    PHOTO_CACHE = os.path.join(WORK, "photo-cache")
    IMAGE_KEYS_JSON = os.path.join(WORK, "image-keys.json")


if __name__ == "__main__":
    main()
