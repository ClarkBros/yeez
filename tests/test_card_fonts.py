#!/usr/bin/env python3
"""Card fonts end to end: python3 tests/test_card_fonts.py (needs internet for the Google Fonts and Noto checks).

Covers: every bundled template font still resolves to the same file; Gaegu Bold (bundled) really is bold on the
top_title kicker; a Page's saved fonts reach the card through brands.json in a real yeez_build run; a buyer's own
font in yeez-work/fonts; a Google Fonts family fetched once; an unknown font doesn't stop the build and shows at the top
of the summary; Japanese / Korean photo credits print as letters, not boxes (computer's own font, then a downloaded Noto).
"""
import json, os, shutil, subprocess, sys, tempfile
HERE = os.path.dirname(os.path.abspath(__file__))
S = os.path.join(HERE, "..", "skills", "social", "scripts")
sys.path.insert(0, S)
WORK = tempfile.mkdtemp(prefix="yeez-fonts-")
os.environ["YEEZ_WORK"] = WORK
import fonts, pin_build  # noqa: E402
from PIL import Image, ImageDraw, ImageFont, ImageChops  # noqa: E402

fails = 0
def ok(c, m):
    global fails
    print(("PASS " if c else "FAIL ") + m)
    fails += 0 if c else 1

def ink(img):
    """Amount of dark-on-light ink, a proxy for stroke weight."""
    g = img.convert("L")
    return sum(255 - p for p in g.tobytes()) / 255

def text_img(f, s, size=(900, 160)):
    im = Image.new("L", size, 255)
    fonts.draw_text(ImageDraw.Draw(im), (10, 10), s, f, 0)
    return im

def reset():
    for c in (fonts._path_cache, fonts._font_cache, fonts._fb_cache):
        c.clear()
    fonts.WARNINGS.clear()

# 1. bundled template fonts: same files as the old resolver, no warnings
old = {}
for spec in ["Oswald:700", "Oswald:500", "Anton", "PlayfairDisplay:800", "DancingScript:700", "BebasNeue", "GreatVibes", "Montserrat-Bold"]:
    name = spec.split(":")[0]
    old[spec] = next(os.path.join(S, "fonts", c) for c in (f"{name}.ttf", f"{name}-Regular.ttf") if os.path.exists(os.path.join(S, "fonts", c)))
same = all(os.path.samefile(fonts.find(s)[0], p) for s, p in old.items())
ok(same and not fonts.WARNINGS, "every bundled template font resolves to the same file as before")
w5, w7 = ink(text_img(fonts.get("Oswald:500", 80), "WEIGHT")), ink(text_img(fonts.get("Oswald:700", 80), "WEIGHT"))
ok(w7 > w5 * 1.1, f"variable fonts still get their weight (Oswald 700 ink {w7:.0f} > 500 ink {w5:.0f})")

# 2. Gaegu: bundled Bold, and Bold is really bold (the old resolver drew Regular for 'Gaegu:700')
p, var, _ = fonts.find("Gaegu:700")
ok(p and os.path.basename(p) == "Gaegu-Bold.ttf" and not var, "Gaegu:700 is the bundled Gaegu-Bold.ttf")
reg = fonts.find("Gaegu")[0]
ok(reg and "Regular" in os.path.basename(reg), f"plain 'Gaegu' gets Regular (fetched from Google Fonts: {os.path.relpath(reg, WORK)})")
gb, gr = ink(text_img(fonts.get("Gaegu:700", 80), "so good")), ink(text_img(fonts.get("Gaegu", 80), "so good"))
ok(gb > gr * 1.1, f"Gaegu Bold draws heavier than Regular ({gb:.0f} vs {gr:.0f})")

# 3. the top_title kicker uses the brand's script font
photo = os.path.join(WORK, "p.jpg")
Image.new("RGB", (1200, 1600), (190, 160, 120)).save(photo)
pin = {"id": "t", "template": "top_title", "title": "Crispy Air Fryer Potatoes", "kicker": "so easy!", "photos": [photo]}
a = pin_build.render(dict(pin), {}, None, (1080, 1350))
b = pin_build.render(dict(pin), {"script_font": "Gaegu:700"}, None, (1080, 1350))
diff = ImageChops.difference(a.convert("RGB"), b.convert("RGB")).getbbox()
ok(diff is not None and diff[3] < 1350 * 0.6, f"top_title kicker changes with script_font Gaegu:700 (changed area {diff})")

# 4. a real yeez_build run: Page fonts saved on yeez.ai -> brands.json -> card
day = "2026-11-17"
q = os.path.join(WORK, "queue", day); os.makedirs(q)
json.dump([{"code": "FOODPL", "name": "Food Plus Words", "c1": "#C0392B", "c2": "#222222", "c3": "#FFF5EE", "icon": "check",
            "fonts": {"script_font": "Gaegu:700"}},
           {"code": "FOODIG", "name": "foodpluswords", "c1": "#C0392B", "c2": "#222222", "c3": "#FFF5EE", "icon": "check",
            "fonts": {"script_font": "NoSuchFontXyz:700"}}], open(os.path.join(WORK, "brands.json"), "w"))
for code in ("FOODPL", "FOODIG"):
    json.dump({"page": code, "items": [{"id": f"{code}-1", "type": "news_image", "status": "written", "caption": "x",
               "design": {"template": "top_title", "title": "Crispy Air Fryer Potatoes", "kicker": "so easy!", "photos": [photo]}}]},
              open(os.path.join(q, f"{code}.json"), "w"))
r = subprocess.run([sys.executable, os.path.join(S, "yeez_build.py"), "--date", day, "--work", WORK], capture_output=True, text=True)
out = r.stdout
ok(r.returncode == 0 and "built 2" in out, "yeez_build built both cards (an unknown font doesn't stop the run)")
top = out.split("FONT PROBLEMS")[1].split("\nbuilt ")[0] if "FONT PROBLEMS" in out else ""
ok("NoSuchFontXyz" in top and out.index("FONT PROBLEMS") < out.index("built 2"), "the unknown font is listed in FONT PROBLEMS above the totals")
ok("Gaegu" not in top, "Gaegu caused no font problem")
c1 = Image.open(os.path.join(q, "media", "FOODPL-1.jpg")).convert("RGB")
ref = pin_build.render(dict(pin), {"accent": "#C0392B", "script_font": "Gaegu:700"}, None, (1080, 1350)).convert("RGB")
d = ImageChops.difference(c1, ref).getbbox()
small = d is None or ImageChops.difference(c1, ref).convert("L").point(lambda v: 255 if v > 40 else 0).getbbox() is None
ok(small, "the built card matches a Gaegu Bold render (the Page's font reached the card)")

# 5. the buyer's own font file in yeez-work/fonts (any subfolder, any spacing in the name)
reset()
os.makedirs(os.path.join(WORK, "fonts", "My Fonts", "static"))
shutil.copy(os.path.join(S, "fonts", "GreatVibes.ttf"), os.path.join(WORK, "fonts", "My Fonts", "static", "Brand Script-Bold.ttf"))
ok(fonts.find("Brand Script:700")[0].endswith("Brand Script-Bold.ttf") and not fonts.WARNINGS, "a buyer's own font in yeez-work/fonts/... is found by its name")

# 6. any Google Fonts family, fetched once
reset()
p1 = fonts.find("Lobster")[0]
ok(p1 and p1.startswith(os.path.join(WORK, "fonts", "google")), f"a Google Fonts family not on the machine is fetched once ({os.path.basename(p1 or '')})")
reset()
import urllib.request
real = urllib.request.urlopen
urllib.request.urlopen = lambda *a, **k: (_ for _ in ()).throw(OSError("offline"))
ok(fonts.find("Lobster")[0] == p1, "the next run uses the saved copy without the internet")
p3 = fonts.find("Pacifico")[0]
reset()
f = fonts.get("Pacifico:700", 40)
ok(p3 is None and any("Pacifico" in w for w in fonts.WARNINGS), "offline and not installed: a clear warning, not a crash")
urllib.request.urlopen = real

# 7. Japanese and Korean credits: letters, not boxes
reset()
sys.path.insert(0, S)
import yeez_build  # noqa: E402
inter = os.path.join(S, "fonts", "Inter-Medium.ttf")
ok(not fonts.has(inter, "山") and fonts.has(inter, "A"), "Inter has no Japanese letters (why credits printed as boxes)")
def credit_png(text):
    im = Image.new("RGB", (900, 60), (20, 20, 20)).convert("RGBA")
    yeez_build.credit_text(im, text, 10, 30, (240, 240, 240), 22, 880)
    return im.convert("L")
box = Image.new("L", (900, 60))
bf = ImageFont.truetype(inter, 22)
ImageDraw.Draw(box).text((10, 18), "Photo: \U0010FFFD\U0010FFFD \U0010FFFD\U0010FFFD", font=bf, fill=255)
jp = credit_png("Photo: 山田 太郎 / CC BY 2.0")
ok(fonts.fallback_path("山") is not None and jp.getbbox() is not None, f"Japanese credit drawn with {os.path.basename(fonts.fallback_path('山'))}")
glyphs = [jp.crop((x, 0, x + 1, 60)).getbbox() for x in range(0, 900)]
ok(ImageChops.difference(jp.crop((60, 0, 160, 60)), box.crop((60, 0, 160, 60))).getbbox() is not None, "the Japanese name isn't the empty-box glyph")
# force the download path: no system fonts
reset(); saved = dict(fonts.SYSTEM)
for k in fonts.SYSTEM: fonts.SYSTEM[k] = []
fp = fonts.fallback_path("田"); kp = fonts.fallback_path("김")
ok(fp and "NotoSansJP" in fp and fp.startswith(WORK), f"no system font: Noto Sans JP fetched once into yeez-work/fonts/fallback")
ok(kp and "NotoSansKR" in kp, "Korean letters get Noto Sans KR")
w_mixed = fonts.textlength(ImageDraw.Draw(Image.new("L", (1, 1))), "Photo: 山田 太郎", fonts.get("Inter:500", 22))
ok(w_mixed > fonts.textlength(ImageDraw.Draw(Image.new("L", (1, 1))), "Photo: ", fonts.get("Inter:500", 22)) + 60, "credit width counts the Japanese letters (ellipsis lands right)")
fonts.SYSTEM.update(saved)

shutil.rmtree(WORK, ignore_errors=True)
print(f"\n{'ALL PASS' if not fails else str(fails) + ' FAILED'}")
sys.exit(1 if fails else 0)
