"""Fonts for Yeez cards.

Where a font is looked for, in order:
  1. yeez-work/fonts/   the buyer's own fonts (any .ttf / .otf / .ttc, subfolders included, e.g. a Google Fonts zip unpacked)
  2. the plugin's bundled fonts (scripts/fonts)
  3. Google Fonts: a family that isn't on the machine is downloaded once into yeez-work/fonts/google/

A font is named "Family" or "Family:weight" (weight 100-900, e.g. "Gaegu:700"). Static families with one file per
weight (Gaegu-Bold.ttf) get the file for that weight; variable fonts (Oswald.ttf, Family[wght].ttf) get the weight
set on their weight axis. A font that can't be found doesn't stop the build: the card uses a bundled font and the
problem is listed in WARNINGS so the run summary shows it.

Text that a font has no letters for (a Japanese photographer's name, Korean, Arabic, Greek ...) is drawn with a
fallback font for just those letters: the buyer's fonts, the bundled ones, the computer's own (Hiragino, Yu Gothic,
Noto CJK ...), then a Noto font downloaded once into yeez-work/fonts/fallback/.
"""
import glob, os, re, sys, unicodedata, urllib.error, urllib.parse, urllib.request
from PIL import Image, ImageDraw, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))
BUNDLED = [os.path.join(HERE, "fonts"), os.path.join(HERE, "..", "fonts")]
EXTS = (".ttf", ".otf", ".ttc")
DEFAULT = "Inter-Bold.ttf"
WARNINGS = []

STYLES = {100: ["thin", "hairline"], 200: ["extralight", "ultralight"], 300: ["light"], 400: ["regular", "normal", "book", ""],
          500: ["medium"], 600: ["semibold", "demibold"], 700: ["bold"], 800: ["extrabold", "ultrabold", "heavy"], 900: ["black", "heavy"]}


def work_dir():
    return os.path.abspath(os.environ.get("YEEZ_WORK", "yeez-work"))


def user_dir():
    return os.path.join(work_dir(), "fonts")


def warn(msg):
    if msg not in WARNINGS:
        WARNINGS.append(msg)
        print(f"FONT: {msg}", file=sys.stderr)


def _norm(s):
    return re.sub(r"[^a-z0-9]", "", s.lower())


def _files(dirs):
    out = []
    for d in dirs:
        if os.path.isdir(d):
            for p in sorted(glob.glob(os.path.join(d, "**", "*"), recursive=True)):
                if p.lower().endswith(EXTS) and os.path.isfile(p):
                    out.append(p)
    return out


def _stem(p):
    return os.path.splitext(os.path.basename(p))[0]


def parse(spec):
    """'Gaegu:700' -> ('Gaegu', 700). 'Inter-Bold.ttf' -> ('Inter-Bold.ttf', None)."""
    name, _, w = (spec or "").strip().partition(":")
    return name.strip(), (int(w) if w.strip().isdigit() else None)


def _match(name, weight, files):
    """Best file for a family + weight among files. Returns (path, is_variable, exact_weight)."""
    if name.lower().endswith(EXTS):
        for p in files:
            if os.path.basename(p).lower() == name.lower():
                return p, False, True
        return None, False, False
    fam = _norm(name)
    want = weight or 400
    static, variable = {}, []
    for p in files:
        stem = _stem(p)
        if "[" in stem:  # Family[wght].ttf, Family-Italic[wght].ttf
            base = stem.split("[")[0]
            if _norm(base) == fam:
                variable.append(p)
            continue
        n = _norm(stem)
        if not n.startswith(fam):
            continue
        rest = n[len(fam):]
        if "italic" in rest and "italic" not in fam:
            continue
        for w, names in STYLES.items():
            if rest in names:
                static.setdefault(w, p)
    if want in static:
        return static[want], False, True
    if variable:
        return variable[0], True, True
    if static:
        if len(static) == 1 and list(static)[0] == 400:  # a single plain file (Oswald.ttf, Anton.ttf): may be variable
            var = _is_variable(static[400])
            return static[400], var, var or weight in (None, 400)
        near = min(static, key=lambda w: (abs(w - want), -w))
        return static[near], False, False
    return None, False, False


_var_cache = {}
def _is_variable(path):
    if path not in _var_cache:
        try:
            axes = ImageFont.truetype(path, 20).get_variation_axes()
            _var_cache[path] = any(str(a.get("name", b"")).lower().find("weight") >= 0 for a in axes)
        except Exception:
            _var_cache[path] = False
    return _var_cache[path]


def _fetch(url, timeout=30):
    """Bytes at url; None for a missing file; raises OSError when the internet can't be reached."""
    try:
        data = urllib.request.urlopen(url, timeout=timeout).read()
    except urllib.error.HTTPError:
        return None
    return data if len(data) > 1000 else None


def _google(name, weight):
    """Download a Google Fonts family/weight into yeez-work/fonts/google/. Returns the file path or None."""
    if name.lower().endswith(EXTS):
        return None
    dest = os.path.join(user_dir(), "google")
    want = weight or 400
    fam = re.sub(r"\s+", " ", name).strip()
    # Google Fonts CSS API: an old browser string gets plain .ttf links.
    try:
        q = urllib.parse.quote(fam).replace("%20", "+")
        req = urllib.request.Request(f"https://fonts.googleapis.com/css2?family={q}:wght@{want}", headers={"User-Agent": "Mozilla/4.0"})
        css = urllib.request.urlopen(req, timeout=20).read().decode("utf8", "replace")
        m = re.search(r"url\((https://fonts\.gstatic\.com/[^)]+\.ttf)\)", css)
        if m:
            data = urllib.request.urlopen(m.group(1), timeout=60).read()
            if len(data) > 1000:
                os.makedirs(dest, exist_ok=True)
                style = STYLES[want][0].capitalize() if STYLES[want][0] else "Regular"
                style = {"Extralight": "ExtraLight", "Semibold": "SemiBold", "Extrabold": "ExtraBold"}.get(style, style)
                p = os.path.join(dest, f"{fam.replace(' ', '')}-{style}.ttf")
                open(p, "wb").write(data)
                return p
    except Exception:
        pass
    # GitHub copy of the Google Fonts library (static file for the weight, then the variable font)
    folder, stem = _norm(fam), fam.replace(" ", "")
    style = {100: "Thin", 200: "ExtraLight", 300: "Light", 400: "Regular", 500: "Medium", 600: "SemiBold", 700: "Bold", 800: "ExtraBold", 900: "Black"}[want]
    for lic in ("ofl", "apache", "ufl"):
        for fn in (f"{stem}-{style}.ttf", f"{stem}[wght].ttf", f"{stem}[wdth,wght].ttf", f"{stem}[opsz,wght].ttf"):
            url = f"https://raw.githubusercontent.com/google/fonts/main/{lic}/{folder}/{urllib.parse.quote(fn)}"
            try:
                data = _fetch(url)
            except Exception:
                return None  # no internet: stop trying
            if data:
                os.makedirs(dest, exist_ok=True)
                p = os.path.join(dest, fn)
                open(p, "wb").write(data)
                return p
    return None


_path_cache = {}
def find(spec):
    """Font file for 'Family:weight'. Returns (path, variable, weight) or (None, ...)."""
    if spec in _path_cache:
        return _path_cache[spec]
    name, weight = parse(spec)
    res = (None, False, weight)
    if name:
        user, bundled = _files([user_dir()]), _files(BUNDLED)
        p, var, exact = _match(name, weight, user)
        if not p or not exact:
            p2, var2, exact2 = _match(name, weight, bundled)
            if p2 and (exact2 or not p):
                p, var, exact = p2, var2, exact2
        if not p or not exact:
            g = _google(name, weight)
            if g:
                p, var, exact = g, "[" in os.path.basename(g), True
        if p and not exact:
            warn(f"{name} has no weight {weight or 400} file; used {os.path.basename(p)}. Put the {weight or 400} file in yeez-work/fonts to fix.")
        res = (p, var, weight)
    _path_cache[spec] = res
    return res


def _set_weight(f, weight):
    try:
        axes = f.get_variation_axes()
    except Exception:
        return
    vals = []
    for a in axes:
        nm = a.get("name")
        nm = nm.decode("latin-1") if isinstance(nm, bytes) else str(nm)
        if nm.lower().startswith("weight") and weight:
            vals.append(max(a["minimum"], min(a["maximum"], weight)))
        else:
            vals.append(a.get("default", a["minimum"]))
    try:
        f.set_variation_by_axes(vals)
    except Exception:
        pass


_font_cache = {}
def get(spec, size):
    """Sized font for a spec. Never stops the build: an unknown font becomes the bundled default, with a warning."""
    key = (spec, int(size))
    if key in _font_cache:
        return _font_cache[key]
    p, var, weight = find(spec)
    if not p:
        warn(f'"{spec}" wasn\'t found in yeez-work/fonts, the bundled fonts or Google Fonts; used Inter Bold. Check the name or put the font file in yeez-work/fonts.')
        p, var, weight = find(DEFAULT)
    f = ImageFont.truetype(p, int(size))
    if var and weight:
        _set_weight(f, weight)
    f.yeez_path = p
    _font_cache[key] = f
    return f


# ---------------------------------------------------------------- letters a font doesn't have

_sig_cache, _probe_cache = {}, {}
def _probe(path):
    if path not in _probe_cache:
        _probe_cache[path] = ImageFont.truetype(path, 40)
    return _probe_cache[path]


def _sig(path, ch):
    k = (path, ch)
    if k not in _sig_cache:
        im = Image.new("L", (90, 90))
        try:
            ImageDraw.Draw(im).text((20, 10), ch, font=_probe(path), fill=255)
        except Exception:
            _sig_cache[k] = None
            return None
        _sig_cache[k] = im.tobytes()
    return _sig_cache[k]


def has(path, ch):
    """True when the font file draws ch as a real letter (not its empty-box 'missing' glyph)."""
    if ch.isspace() or unicodedata.category(ch) in ("Cc", "Cf", "Mn"):
        return True
    s = _sig(path, ch)
    return s is not None and s != _sig(path, "\U0010FFFD")


def _script(ch):
    o = ord(ch)
    if 0xAC00 <= o <= 0xD7AF or 0x1100 <= o <= 0x11FF or 0x3130 <= o <= 0x318F:
        return "kr"
    if 0x3040 <= o <= 0x30FF or 0x3400 <= o <= 0x9FFF or 0x3000 <= o <= 0x303F or 0xFF00 <= o <= 0xFFEF or 0x31F0 <= o <= 0x31FF or 0xF900 <= o <= 0xFAFF:
        return "cjk"
    if 0x0600 <= o <= 0x06FF or 0x0750 <= o <= 0x077F or 0xFB50 <= o <= 0xFDFF or 0xFE70 <= o <= 0xFEFF:
        return "arabic"
    if 0x0590 <= o <= 0x05FF:
        return "hebrew"
    if 0x0E00 <= o <= 0x0E7F:
        return "thai"
    if 0x0900 <= o <= 0x097F:
        return "devanagari"
    return "other"


SYSTEM = {
    "cjk": ["/System/Library/Fonts/ヒラギノ角ゴシック W6.ttc", "/System/Library/Fonts/Hiragino Sans GB.ttc", "/System/Library/Fonts/PingFang.ttc",
            "C:/Windows/Fonts/YuGothB.ttc", "C:/Windows/Fonts/meiryob.ttc", "C:/Windows/Fonts/msyhbd.ttc", "C:/Windows/Fonts/msgothic.ttc",
            "/usr/share/fonts/opentype/noto/NotoSansCJK-Bold.ttc", "/usr/share/fonts/noto-cjk/NotoSansCJK-Bold.ttc", "/usr/share/fonts/google-noto-cjk/NotoSansCJK-Bold.ttc"],
    "kr": ["/System/Library/Fonts/AppleSDGothicNeo.ttc", "C:/Windows/Fonts/malgunbd.ttf", "/usr/share/fonts/opentype/noto/NotoSansCJK-Bold.ttc"],
    "arabic": ["/System/Library/Fonts/GeezaPro.ttc", "C:/Windows/Fonts/arialbd.ttf", "/usr/share/fonts/truetype/noto/NotoSansArabic-Bold.ttf"],
    "hebrew": ["/System/Library/Fonts/SFHebrew.ttf", "C:/Windows/Fonts/arialbd.ttf", "/usr/share/fonts/truetype/noto/NotoSansHebrew-Bold.ttf"],
    "thai": ["/System/Library/Fonts/Thonburi.ttc", "C:/Windows/Fonts/tahomabd.ttf", "/usr/share/fonts/truetype/noto/NotoSansThai-Bold.ttf"],
    "devanagari": ["/System/Library/Fonts/Kohinoor.ttc", "C:/Windows/Fonts/Nirmala.ttf", "/usr/share/fonts/truetype/noto/NotoSansDevanagari-Bold.ttf"],
    "other": ["/System/Library/Fonts/Supplemental/Arial Unicode.ttf", "C:/Windows/Fonts/seguisym.ttf", "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"],
}
NOTO = {"cjk": ["NotoSansJP", "NotoSansSC"], "kr": ["NotoSansKR"], "arabic": ["NotoSansArabic"], "hebrew": ["NotoSansHebrew"],
        "thai": ["NotoSansThai"], "devanagari": ["NotoSansDevanagari"], "other": ["NotoSans"]}


def _noto(fam):
    dest = os.path.join(user_dir(), "fallback")
    for p in _files([dest]):
        if _stem(p).split("[")[0] == fam:
            return p
    folder = fam.lower()
    for fn in (f"{fam}[wght].ttf", f"{fam}[wdth,wght].ttf"):
        try:
            data = _fetch(f"https://raw.githubusercontent.com/google/fonts/main/ofl/{folder}/{urllib.parse.quote(fn)}", 120)
        except Exception:
            return None
        if data:
            os.makedirs(dest, exist_ok=True)
            p = os.path.join(dest, fn)
            open(p, "wb").write(data)
            return p
    return None


_fb_cache = {}
def fallback_path(ch):
    """A font file that has ch, or None."""
    sc = _script(ch)
    key = (sc, ch) if sc == "other" else sc
    cached = _fb_cache.get(key)
    if cached and has(cached, ch):
        return cached
    # plain sans fonts first (the computer's own, then Noto), so a name doesn't come out in a display or script face;
    # any other installed font that has the letter is the last resort (e.g. offline)
    for p in [p for p in SYSTEM[sc] if os.path.exists(p)]:
        if has(p, ch):
            _fb_cache[key] = p
            return p
    for fam in NOTO[sc]:
        p = _noto(fam)
        if p and has(p, ch):
            _fb_cache[key] = p
            return p
    for p in _files([user_dir()]) + _files(BUNDLED):
        if has(p, ch):
            _fb_cache[key] = p
            return p
    return None


def _sized(path, size, like):
    k = ("fb", path, size)
    if k not in _font_cache:
        f = ImageFont.truetype(path, size)
        if _is_variable(path):
            main = os.path.basename(getattr(like, "yeez_path", None) or getattr(like, "path", "") or "").lower()
            _set_weight(f, 700 if any(k in main for k in ("bold", "black", "heavy")) else 500)
        _font_cache[k] = f
    return _font_cache[k]


def runs(text, font):
    """Split text into (piece, font) runs: the main font where it has the letters, a fallback where it doesn't."""
    path = getattr(font, "yeez_path", None) or font.path
    size = int(font.size)
    out, cur, cur_f = [], "", font
    for ch in text:
        f = font
        if not has(path, ch):
            fp = fallback_path(ch)
            if fp:
                f = _sized(fp, size, font)
            else:
                warn(f"no installed font has the letter {ch!r} (U+{ord(ch):04X}); it may print as a box")
        if ch.isspace() and cur:
            f = cur_f
        if f is not cur_f and cur:
            out.append((cur, cur_f)); cur = ""
        cur_f = f; cur += ch
    if cur:
        out.append((cur, cur_f))
    return out


def textlength(draw, text, font):
    return sum(draw.textlength(t, font=f) for t, f in runs(text, font))


def draw_text(draw, xy, text, font, fill):
    """Like draw.text(xy, text, font=font, fill=fill) with the top-left anchor, using fallback fonts for missing letters."""
    rs = runs(text, font)
    if len(rs) <= 1 and (not rs or rs[0][1] is font):
        draw.text(xy, text, font=font, fill=fill)
        return
    x, y = xy
    base = y + font.getmetrics()[0]
    for t, f in rs:
        draw.text((x, base), t, font=f, fill=fill, anchor="ls")
        x += draw.textlength(t, font=f)
