#!/usr/bin/env python3
"""
pin_build.py — renders Pinterest pins (1000x1500) from a pins file.

    python3 pin_build.py --pins yeez-work/pins/2026-11-09.json [--out yeez-work/pins/out] [--only ID]

pins file:
{
  "brand": {"accent": "#B5482B", "site_label": "foodpluswords.com", ...},     # overrides brand_defaults
  "pins": [
    {"id": "dumplings-a", "template": "center_box",
     "title": "Stovetop Chicken and Dumplings", "kicker": "No Crockpot!",
     "photos": ["photos/stovetop-chicken-and-dumplings.jpg"],
     "style": {"box_y": 600}},                                              # optional per-pin tweaks
    {"id": "fall-desserts", "template": "roundup_grid", "number": "25", "title": "Fall Desserts",
     "kicker": "cozy & easy", "photos": [...6], "labels": ["Apple Tart", ...]},
    {"id": "card", "template": "recipe_card", "title": "...", "facts": ["30 min", "Serves 6"],
     "items": ["Chicken breast", "Carrots", ...], "photos": ["..."]}
  ]
}

Templates and every size/colour/font live in pin-templates.json next to this file, so a look can be
changed once for every buyer, per site ("brand"), or per pin ("style"). Photos can be local paths or
URLs (downloaded to yeez-work/pins/cache).
"""
import argparse, hashlib, json, os, re, sys, urllib.request
from PIL import Image, ImageDraw, ImageFont, ImageFilter, ImageOps
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import fonts

HERE = os.path.dirname(os.path.abspath(__file__))
W, H = 1000, 1500


# ---------- basics ----------
def rgb(h):
    h = h.lstrip("#")
    return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4))


def font(spec, size):
    """spec 'Oswald:700', 'Gaegu:700' or 'Anton' -> sized font. Looks in yeez-work/fonts, the bundled fonts, then
    Google Fonts (fonts.py). Static families get the file for the weight; variable fonts get the weight set."""
    return fonts.get(spec, size)


def fetch(src):
    if re.match(r"https?://", src):
        cache = os.path.join("yeez-work", "pins", "cache")
        os.makedirs(cache, exist_ok=True)
        fn = os.path.join(cache, hashlib.sha1(src.encode()).hexdigest()[:16] + os.path.splitext(src.split("?")[0])[1][:5])
        if not os.path.exists(fn):
            req = urllib.request.Request(src, headers={"User-Agent": "Mozilla/5.0 (Yeez pins)"})
            open(fn, "wb").write(urllib.request.urlopen(req, timeout=60).read())
        src = fn
    return Image.open(src).convert("RGB")


def cover(img, w, h, focus=(0.5, 0.5)):
    return ImageOps.fit(img, (w, h), Image.LANCZOS, centering=focus)


def cased(text, mode):
    if mode == "upper":
        return text.upper()
    if mode == "title":
        small = {"and", "or", "of", "the", "a", "an", "in", "on", "with", "for", "to"}
        words = text.split()
        return " ".join(w if (i and w.lower() in small) else (w[:1].upper() + w[1:]) for i, w in enumerate(words))
    return text


def text_w(draw, s, f):
    return fonts.textlength(draw, s, f)  # counts fallback letters (e.g. Japanese) at their real width


def wrap_balanced(draw, text, f, max_w, max_lines):
    words = text.split()
    if not words:
        return []
    best = None
    for n in range(1, max_lines + 1):
        # greedy target width = total / n, then check fit
        total = text_w(draw, " ".join(words), f)
        target = total / n
        lines, cur = [], []
        for w in words:
            trial = " ".join(cur + [w])
            if cur and text_w(draw, trial, f) > max(target * 1.18, 1) and len(lines) < n - 1:
                lines.append(" ".join(cur)); cur = [w]
            else:
                cur.append(w)
        lines.append(" ".join(cur))
        if len(lines) <= max_lines and all(text_w(draw, l, f) <= max_w for l in lines):
            best = lines
            break
    return best


def fit(draw, text, spec, max_w, max_h, max_size, min_size, max_lines, lh=1.04):
    for size in range(max_size, min_size - 1, -2):
        f = font(spec, size)
        lines = wrap_balanced(draw, text, f, max_w, max_lines)
        if lines:
            asc, desc = f.getmetrics()
            line_h = int((asc + desc) * lh)
            if line_h * len(lines) <= max_h:
                return f, lines, line_h
    f = font(spec, min_size)
    return f, wrap_balanced(draw, text, f, max_w, max_lines + 2) or [text], int(sum(f.getmetrics()) * lh)


def draw_center_lines(draw, lines, f, line_h, cx, y, color):
    for l in lines:
        w = text_w(draw, l, f)
        fonts.draw_text(draw, (cx - w / 2, y), l, f, color)
        y += line_h
    return y


def spaced(s):
    return " ".join(s.upper())


# ---------- templates ----------
VKEYS = ("box_y", "band_y", "band_h", "fade_h", "panel_h", "head_h")
HKEYS = ("box_w", "panel_w")


class Ctx:
    def __init__(self, t, brand, style, size=(1000, 1500)):
        self.p = {**t, **(style or {})}
        self.b = brand
        sx, sy = size[0] / 1000, size[1] / 1500
        for k in VKEYS:
            if isinstance(self.p.get(k), (int, float)):
                self.p[k] = int(self.p[k] * sy)
        for k in HKEYS:
            if isinstance(self.p.get(k), (int, float)):
                self.p[k] = int(self.p[k] * sx)

    def c(self, key):
        v = self.p.get(key, key)
        v = self.b.get(v, v)
        return rgb(v) if isinstance(v, str) and v.startswith("#") else v

    def f(self, key):
        v = self.p.get(key, key)
        return self.b.get(v, v)


def tag(draw, cx, y, text, f, fill, color, pad=(22, 10)):
    w = text_w(draw, text, f)
    asc, desc = f.getmetrics()
    box = [cx - w / 2 - pad[0], y, cx + w / 2 + pad[0], y + asc + desc + pad[1] * 2]
    if fill is not None:
        draw.rectangle(box, fill=fill)
    fonts.draw_text(draw, (cx - w / 2, y + pad[1]), text, f, color)
    return box[3]


def t_center_box(pin, x):
    img = cover(fetch(pin["photos"][0]), W, H, tuple(pin.get("focus", (0.5, 0.5))))
    over = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(over)
    bw = x.p["box_w"]; pad = x.p["box_pad"]
    probe = ImageDraw.Draw(img)
    title = cased(pin["title"], x.p["title_case"])
    tf, lines, lh = fit(probe, title, x.f("title_font"), bw - pad * 2, 420, x.p["title_max"], x.p["title_min"], x.p["title_lines"])
    kf = font(x.f("kicker_font"), x.p["kicker_size"]) if pin.get("kicker") else None
    kh = int(sum(kf.getmetrics()) * 1.0) if kf else 0
    bh = pad * 2 + kh + lh * len(lines)
    by = x.p["box_y"] if pin.get("box_y") is None else pin["box_y"]
    by = min(max(by - bh // 2, 120), H - bh - 160)
    bx = (W - bw) // 2
    d.rectangle([bx, by, bx + bw, by + bh], fill=x.c("box_fill") + (x.p["box_alpha"],))
    i = x.p["border_inset"]
    d.rectangle([bx + i, by + i, bx + bw - i, by + bh - i], outline=x.c("border") + (255,), width=x.p["border_w"])
    img = Image.alpha_composite(img.convert("RGBA"), over)
    d = ImageDraw.Draw(img)
    y = by + pad
    if kf:
        kw = text_w(d, pin["kicker"], kf)
        fonts.draw_text(d, (W / 2 - kw / 2, y - 6), pin["kicker"], kf, x.c("kicker_color"))
        y += kh
    draw_center_lines(d, lines, tf, lh, W / 2, y, x.c("title_color"))
    if x.p.get("tag"):
        sf = font(x.f("small_font"), x.p["tag_size"])
        tag(d, W / 2, by + bh - 4, spaced(x.b["site_label"]), sf, x.c("tag_fill"), x.c("tag_color"))
    return img


def t_split_band(pin, x):
    photos = pin["photos"]
    by, bh = x.p["band_y"], x.p["band_h"]
    img = Image.new("RGB", (W, H), x.c("band_fill"))
    if len(photos) == 1 or photos[0] == photos[1]:
        # one photo: top and bottom show different parts of it, never the same crop twice
        src = fetch(photos[0]); sw, sh = src.size
        top = src.crop((0, 0, sw, int(sh * 0.55))); bot = src.crop((0, int(sh * 0.45), sw, sh))
        img.paste(cover(top, W, by, (0.5, 0.4)), (0, 0))
        img.paste(cover(bot, W, H - by - bh, (0.5, 0.6)), (0, by + bh))
    else:
        img.paste(cover(fetch(photos[0]), W, by, tuple(pin.get("focus", (0.5, 0.45)))), (0, 0))
        img.paste(cover(fetch(photos[1]), W, H - by - bh, tuple(pin.get("focus_2", (0.5, 0.5)))), (0, by + bh))
    d = ImageDraw.Draw(img)
    title = cased(pin["title"], x.p["title_case"])
    kf = font(x.f("kicker_font"), x.p["kicker_size"]) if pin.get("kicker") else None
    kh = int(sum(kf.getmetrics())) if kf else 0
    sf = font(x.f("small_font"), x.p["tag_size"])
    th = bh - 60 - kh - 40
    tf, lines, lh = fit(d, title, x.f("title_font"), W - 120, th, x.p["title_max"], x.p["title_min"], x.p["title_lines"], lh=1.0)
    block = kh + lh * len(lines) + 46
    y = by + (bh - block) // 2
    if kf:
        kw = text_w(d, pin["kicker"], kf)
        fonts.draw_text(d, (W / 2 - kw / 2, y - 8), pin["kicker"], kf, x.c("kicker_color"))
        y += kh
    y = draw_center_lines(d, lines, tf, lh, W / 2, y, x.c("title_color"))
    lab = spaced(x.b["site_label"])
    lw = text_w(d, lab, sf)
    if x.p.get("rule"):
        d.line([W / 2 - lw / 2 - 70, y + 22, W / 2 - lw / 2 - 18, y + 22], fill=x.c("tag_color"), width=2)
        d.line([W / 2 + lw / 2 + 18, y + 22, W / 2 + lw / 2 + 70, y + 22], fill=x.c("tag_color"), width=2)
    fonts.draw_text(d, (W / 2 - lw / 2, y + 8), lab, sf, x.c("tag_color"))
    return img


def t_top_title(pin, x):
    img = cover(fetch(pin["photos"][0]), W, H, tuple(pin.get("focus", (0.5, 0.7)))).convert("RGBA")
    fh = x.p["fade_h"]; solid = x.p["fade_solid"]
    fade = Image.new("RGBA", (W, fh), x.c("fade_color") + (0,))
    px = fade.load()
    col = x.c("fade_color")
    for yy in range(fh):
        t = yy / fh
        a = 255 if t < solid else int(255 * max(0, 1 - (t - solid) / (1 - solid)) ** 1.6)
        for xx in range(W):
            px[xx, yy] = col + (a,)
    img.alpha_composite(fade, (0, 0))
    d = ImageDraw.Draw(img)
    y = 54
    if pin.get("kicker"):
        kf = font(x.f("kicker_font"), x.p["kicker_size"])
        kw = text_w(d, pin["kicker"], kf)
        fonts.draw_text(d, (W / 2 - kw / 2, y), pin["kicker"], kf, x.c("kicker_color"))
        y += int(sum(kf.getmetrics()) * 0.92)
    title = cased(pin["title"], x.p["title_case"])
    tf, lines, lh = fit(d, title, x.f("title_font"), W - 110, int(fh * solid) + 60 - y + 40, x.p["title_max"], x.p["title_min"], x.p["title_lines"], lh=0.98)
    draw_center_lines(d, lines, tf, lh, W / 2, y, x.c("title_color"))
    if x.p.get("tag"):
        sf = font(x.f("small_font"), x.p["tag_size"])
        tag(d, W / 2, H - 92, spaced(x.b["site_label"]), sf, x.c("tag_fill"), x.c("tag_color"))
    return img


def t_roundup_collage(pin, x):
    ph = (pin["photos"] * 4)[:4]
    g = x.p["gap"]
    img = Image.new("RGB", (W, H), (255, 255, 255))
    cw, chh = (W - g) // 2, (H - g) // 2
    for i, p in enumerate(ph):
        img.paste(cover(fetch(p), cw, chh), ((i % 2) * (cw + g), (i // 2) * (chh + g)))
    pw, phh = x.p["panel_w"], x.p["panel_h"]
    px0, py0 = (W - pw) // 2, (H - phh) // 2
    over = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    od = ImageDraw.Draw(over)
    od.rectangle([px0, py0, px0 + pw, py0 + phh], fill=x.c("panel_fill") + (x.p["panel_alpha"],))
    od.rectangle([px0 + 12, py0 + 12, px0 + pw - 12, py0 + phh - 12], outline=x.c("accent_2") + (255,), width=3)
    img = Image.alpha_composite(img.convert("RGBA"), over)
    d = ImageDraw.Draw(img)
    nf = font(x.f("number_font"), x.p["number_size"])
    num = str(pin.get("number", ""))
    sf = font(x.f("small_font"), x.p["tag_size"])
    title = cased(pin["title"], x.p["title_case"])
    nh = int(nf.getmetrics()[0] * 0.86) if num else 0
    tf, lines, lh = fit(d, title, x.f("title_font"), pw - 90, phh - nh - 110, x.p["title_max"], x.p["title_min"], x.p["title_lines"], lh=1.08)
    block = nh + lh * len(lines) + 44
    y = py0 + (phh - block) // 2
    if num:
        bb = d.textbbox((0, 0), num, font=nf)
        fonts.draw_text(d, (W / 2 - (bb[2] - bb[0]) / 2 - bb[0], y - bb[1]), num, nf, x.c("number_color"))
        y += nh + 10
    y = draw_center_lines(d, lines, tf, lh, W / 2, y, x.c("title_color"))
    lab = spaced(x.b["site_label"]); lw = text_w(d, lab, sf)
    fonts.draw_text(d, (W / 2 - lw / 2, y + 8), lab, sf, x.c("tag_color"))
    return img


def t_roundup_grid(pin, x):
    ph = pin["photos"]
    labels = pin.get("labels", [])
    hh = x.p["head_h"]; g = x.p["gap"]; cols = x.p["cols"]
    rows = max(1, (len(ph) + cols - 1) // cols)
    img = Image.new("RGB", (W, H), x.c("head_fill"))
    d = ImageDraw.Draw(img)
    # header: big number left, title right
    nf = font(x.f("number_font"), x.p["number_size"])
    num = str(pin.get("number", ""))
    nb = d.textbbox((0, 0), num, font=nf) if num else (0, 0, 0, 0)
    nw = nb[2] - nb[0]
    left = 54
    if num:
        fonts.draw_text(d, (left - nb[0], (hh - (nb[3] - nb[1])) // 2 - nb[1] - 10), num, nf, x.c("number_color"))
    tx = left + nw + (36 if num else 0); tw = W - tx - 50
    y0 = 70
    if pin.get("kicker"):
        kf = font(x.f("kicker_font"), x.p["kicker_size"])
        fonts.draw_text(d, (tx, y0 - 10), pin["kicker"], kf, x.c("kicker_color"))
        y0 += int(sum(kf.getmetrics()) * 0.9)
    title = cased(pin["title"], x.p["title_case"])
    tf, lines, lh = fit(d, title, x.f("title_font"), tw, hh - y0 - 70, x.p["title_max"], x.p["title_min"], x.p["title_lines"] + 1, lh=1.0)
    for l in lines:
        fonts.draw_text(d, (tx, y0), l, tf, x.c("title_color")); y0 += lh
    sf = font(x.f("small_font"), x.p["tag_size"])
    fonts.draw_text(d, (tx, y0 + 8), spaced(x.b["site_label"]), sf, x.c("tag_color"))
    # grid
    gy = hh; cw = (W - g * (cols + 1)) // cols; chh = (H - gy - g * (rows + 1)) // rows
    bf = font(x.f("display_font"), x.p["badge_size"])
    lf = font(x.f("label_font"), x.p["label_size"])
    for i, p in enumerate(ph):
        cx0 = g + (i % cols) * (cw + g); cy0 = gy + g + (i // cols) * (chh + g)
        img.paste(cover(fetch(p), cw, chh), (cx0, cy0))
        d = ImageDraw.Draw(img)
        r = 30
        d.ellipse([cx0 + 14, cy0 + 14, cx0 + 14 + 2 * r, cy0 + 14 + 2 * r], fill=x.c("badge_fill"))
        s = str(i + 1); bb = d.textbbox((0, 0), s, font=bf)
        fonts.draw_text(d, (cx0 + 14 + r - (bb[2] - bb[0]) / 2 - bb[0], cy0 + 14 + r - (bb[3] - bb[1]) / 2 - bb[1]), s, bf, x.c("badge_color"))
        if i < len(labels) and labels[i]:
            lab = labels[i].upper()
            while text_w(d, lab, lf) > cw - 40 and len(lab) > 4:
                lab = lab[:-2].rstrip() + "…"
            lw = text_w(d, lab, lf); asc, desc = lf.getmetrics()
            ly = cy0 + chh - (asc + desc) - 26
            d.rectangle([cx0 + cw / 2 - lw / 2 - 16, ly - 8, cx0 + cw / 2 + lw / 2 + 16, ly + asc + desc + 8], fill=x.c("label_fill"))
            fonts.draw_text(d, (cx0 + cw / 2 - lw / 2, ly), lab, lf, x.c("label_color"))
    return img


def t_recipe_card(pin, x):
    m = x.p["card_margin"]
    probe = ImageDraw.Draw(Image.new("RGB", (W, H)))
    inner = W - 2 * m - 80
    title = cased(pin["title"], x.p["title_case"])
    tf, lines, lh = fit(probe, title, x.f("title_font"), inner, 200, x.p["title_max"], x.p["title_min"], x.p["title_lines"], lh=1.05)
    ff = font(x.f("facts_font"), x.p["facts_size"])
    lf = font(x.f("list_font"), x.p["list_size"])
    sf = font(x.f("small_font"), x.p["tag_size"])
    items = pin.get("items", [])[: x.p["list_max"]]
    row_h = int(sum(lf.getmetrics()) * 1.35)
    card_h = 40 + lh * len(lines) + (int(sum(ff.getmetrics())) + 30 if pin.get("facts") else 0) + 24 + row_h * ((len(items) + 1) // 2) + 20 + int(sum(sf.getmetrics())) + 36
    cy = H - m - card_h
    # the photo fills the space above the card (plus a little under its top edge), so the food is never hidden
    img = Image.new("RGBA", (W, H), x.c("paper") + (255,))
    img.paste(cover(fetch(pin["photos"][0]), W, cy + 90, tuple(pin.get("focus", (0.5, 0.5)))), (0, 0))
    over = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    od = ImageDraw.Draw(over)
    od.rounded_rectangle([m, cy, W - m, H - m], radius=x.p["card_radius"], fill=x.c("card_fill") + (250,))
    shadow = over.filter(ImageFilter.GaussianBlur(14))
    img.alpha_composite(Image.eval(shadow, lambda v: v // 3))
    img.alpha_composite(over)
    d = ImageDraw.Draw(img)
    y = draw_center_lines(d, lines, tf, lh, W / 2, cy + 40, x.c("title_color"))
    if pin.get("facts"):
        s = "  \u2022  ".join(f.upper() for f in pin["facts"])
        sw = text_w(d, s, ff)
        fonts.draw_text(d, (W / 2 - sw / 2, y + 10), s, ff, x.c("facts_color"))
        y += int(sum(ff.getmetrics())) + 30
    d.line([m + 60, y, W - m - 60, y], fill=x.c("accent_2"), width=3)
    y += 24
    colw = inner // 2
    for i, it in enumerate(items):
        cx0 = m + 50 + (i % 2) * colw; yy = y + (i // 2) * row_h
        d.ellipse([cx0, yy + 13, cx0 + 12, yy + 25], fill=x.c("accent"))
        t = it
        while text_w(d, t, lf) > colw - 40 and len(t) > 4:
            t = t[:-2].rstrip() + "\u2026"
        fonts.draw_text(d, (cx0 + 24, yy), t, lf, x.c("list_color"))
    lab = spaced(x.b["site_label"]); lw = text_w(d, lab, sf)
    fonts.draw_text(d, (W / 2 - lw / 2, H - m - int(sum(sf.getmetrics())) - 26), lab, sf, x.c("tag_color"))
    return img


TEMPLATES = {"center_box": t_center_box, "split_band": t_split_band, "top_title": t_top_title,
             "roundup_collage": t_roundup_collage, "roundup_grid": t_roundup_grid, "recipe_card": t_recipe_card}


def load_config(path=None):
    return json.load(open(path or os.path.join(HERE, "pin-templates.json")))


def render(pin, brand=None, style=None, size=None, cfg=None):
    """One pin (or a Facebook/Instagram image in a pin design) -> PIL image.
    size: (w, h); pins are 1000x1500, Facebook/Instagram feed images 1080x1350."""
    global W, H
    cfg = cfg or load_config()
    b = {**cfg["brand_defaults"], **(brand or {})}
    W, H = tuple(size or pin.get("size") or cfg["size"])
    t = cfg["templates"][pin["template"]]
    x = Ctx(t, b, {**(style or {}), **pin.get("style", {})}, (W, H))
    return TEMPLATES[pin["template"]](pin, x).convert("RGB")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--pins", required=True)
    ap.add_argument("--out", default=os.path.join("yeez-work", "pins", "out"))
    ap.add_argument("--only")
    ap.add_argument("--templates")
    a = ap.parse_args()
    cfg = load_config(a.templates)
    spec = json.load(open(a.pins))
    os.makedirs(a.out, exist_ok=True)
    for pin in spec["pins"]:
        if a.only and pin["id"] != a.only:
            continue
        img = render(pin, spec.get("brand"), spec.get("style", {}).get(pin["template"]), None, cfg)
        fn = os.path.join(a.out, f"{pin['id']}.jpg")
        img.save(fn, quality=90, optimize=True, progressive=True)
        pin["media"] = fn
        print("built", fn)
    json.dump(spec, open(a.pins, "w"), indent=1)
    if fonts.WARNINGS:  # put this first when reporting to the buyer
        print("\nFONT PROBLEMS (pins were still built with a stand-in font):")
        for w in fonts.WARNINGS:
            print(f"  - {w}")


if __name__ == "__main__":
    main()
