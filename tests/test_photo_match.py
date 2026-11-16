#!/usr/bin/env python3
"""Card photos: right match, a warning when unsure, the buyer's own photo, and flags that don't overcorrect.
python3 tests/test_photo_match.py   (offline: photo libraries and Facebook are stand-ins)

Louisa's case (2026-11-14): a whipped cream recall card got an empty-shelf photo and a granola bar, with no warning.
"""
import io, json, os, shutil, subprocess, sys, tempfile, threading, http.server, datetime as dt, importlib.util
HERE = os.path.dirname(os.path.abspath(__file__))
S = os.path.join(HERE, "..", "skills", "social", "scripts")
W = tempfile.mkdtemp(prefix="yeez-photo-")
os.environ["YEEZ_WORK"] = W
sys.path.insert(0, S)
import yeez_build as yb  # noqa: E402
from PIL import Image  # noqa: E402

fails = 0
def ok(c, m):
    global fails
    print(("PASS " if c else "FAIL ") + m); fails += 0 if c else 1

# stand-in photo library: what a search for anything returns
def R(i, title, tags=(), w=2400, h=1600, lic="cc0"):
    return {"id": i, "url": f"https://photos.example/{i}.jpg", "title": title, "tags": [{"name": t} for t in tags],
            "width": w, "height": h, "license": lic, "source": "openverse", "creator": "Someone", "foreign_landing_url": ""}
LIB = [R("shelf", "Empty grocery store shelves", ["store", "shelf", "supermarket", "grocery"]),
       R("granola", "Granola bar", ["snack", "cream", "bar", "grocery store"]),
       R("whip1", "Can of whipped cream on a kitchen counter", ["dessert", "can"]),
       R("whip2", "Whipped cream on a store shelf", ["grocery", "store", "shelf"]),
       R("cake", "Strawberry cake", ["whipped", "cream", "can", "dessert"])]
searched = []
def fake_search(q):
    searched.append(q)
    return [dict(r) for r in LIB]
yb.provider_searches = lambda: [("openverse", fake_search)]
buf = io.BytesIO(); Image.new("RGB", (2400, 1600), (200, 180, 160)).save(buf, "JPEG"); JPG = buf.getvalue()
real_http_get = yb.http_get
yb.http_get = lambda url, timeout=30: JPG if "photos.example" in url else real_http_get(url, timeout)

def pick(query, must=None, item="t1", page="FOODPL", lib=None):
    global LIB
    if lib is not None:
        LIB = lib
    yb.PHOTO_CHECKS.clear()
    p, notes = yb.find_photo(query, item, 1080 / 600, must=must, page=page)
    return (p or {}).get("id"), yb.PHOTO_CHECKS.get(item, [])

full = list(LIB)
full_lib = list(LIB)
# 1. what the old version picked
spec = importlib.util.spec_from_file_location("yb_old", os.path.join(HERE, "_yb_old.py"))
if os.path.exists(os.path.join(HERE, "_yb_old.py")):
    old = importlib.util.module_from_spec(spec); spec.loader.exec_module(old)
    old.provider_searches = yb.provider_searches; old.http_get = yb.http_get
    LIB = [r for r in LIB if r["id"] in ("shelf", "granola")]
    o, _ = old.find_photo("whipped cream can grocery store recall", "o1", 1080 / 600)
    print(f"     (old version, library without a whipped cream photo, picked: {(o or {}).get('id')})")
    LIB = list(full_lib)

# 2. the fix: the photo shows whipped cream
searched.clear()
pid, chk = pick("whipped cream can grocery store recall", "whipped cream")
ok(pid in ("whip1", "whip2") and not chk, f"whipped cream recall gets a whipped cream photo ({pid}), no warning needed")
ok(all("whipped" in q.lower() and "cream" in q.lower() for q in searched), "every search phrasing keeps 'whipped cream'")
pid, chk = pick("whipped cream can grocery store recall")
ok(chk and "no `must`" in chk[0], f"an older brief without `must` still gets a photo ({pid}) but is marked for a look")

# 3. no right photo: none rather than a wrong one, and a warning
pid, chk = pick("whipped cream can grocery store recall", "whipped cream", lib=[r for r in full if not r["id"].startswith("whip") and r["id"] != "cake"])
ok(pid is None, "with no whipped cream photo, no photo is used (not the shelf or the granola bar)")
pid, chk = pick("whipped cream can grocery store recall", "whipped cream", lib=[r for r in full if not r["id"].startswith("whip")])
ok(pid == "cake" and chk and "tags" in chk[0], f"a photo that only has the words in its tags is used but flagged ({chk[:1]})")

# 4. buyer's flags: block that photo; a rule only when given, and only where it applies
LIB = full
yb.save_feedback({"blocked": [{"url": "https://photos.example/whip1.jpg", "id": "whip1"}], "rules": []})
pid, _ = pick("whipped cream can grocery store recall", "whipped cream")
ok(pid == "whip2", f"a blocked photo is never picked again ({pid})")
yb.save_feedback({"blocked": [{"url": "https://photos.example/whip1.jpg", "id": "whip1"}],
                  "rules": [{"avoid": ["shelf"], "when": ["recall"], "page": "FOODPL", "reason": "no shelves on recall posts"}]})
pid, _ = pick("whipped cream can grocery store recall", "whipped cream")
ok(pid not in ("whip2", "shelf"), f"the buyer's rule (no shelves on recall cards) skips shelf photos on a recall card ({pid})")
pid, _ = pick("whipped cream grocery store shelf display", "whipped cream")
ok(pid == "whip2", "the same rule doesn't touch a card that isn't about a recall")
pid, _ = pick("whipped cream can grocery store recall", "whipped cream", page="FOODIG")
ok(pid == "whip2", "a rule for one Page doesn't touch another Page")
yb.save_feedback({"blocked": [], "rules": []})

# 5. people cards are unchanged (no anchor on person: briefs)
yb._PERSON_QUERIES.add("Jane Doe")
pid, chk = pick("Jane Doe", lib=[R("jd", "Jane Doe official portrait", ["portrait"])])
ok(pid == "jd" and not chk, "person photos work as before")
LIB = full

# 6. the buyer's own photo (find_site_images url): used as is, no search
class H(http.server.BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200); self.send_header("Content-Type", "image/jpeg"); self.end_headers(); self.wfile.write(JPG)
    def log_message(self, *a): pass
srv = http.server.ThreadingHTTPServer(("127.0.0.1", 0), H); threading.Thread(target=srv.serve_forever, daemon=True).start()
own = f"http://127.0.0.1:{srv.server_address[1]}/wp-content/uploads/whipped-cream.jpg"
searched.clear(); yb.PHOTO_CHECKS.clear()
p, notes, q = yb.brief_photo({"image_url": own, "image_alt": "Homemade whipped cream", "must": "whipped cream", "query": "x"}, "own1", 1080 / 600)
ok(p and p["source"] == "own" and p["license_label"] == "own photo" and not searched, "own-site photo is used directly, nothing searched")

# 7. a real build: a weak photo is marked, listed at the top, and held by the post script
day = "2026-11-17"; qd = os.path.join(W, "queue", day); os.makedirs(qd)
json.dump([{"code": "FOODPL", "name": "Food Plus Words", "c1": "#C0392B", "c2": "#222222", "c3": "#FFF5EE", "icon": "check"}], open(os.path.join(W, "brands.json"), "w"))
ov = "A whipped cream brand is pulled from 9 states after a bacteria test, the company said Friday. Check your fridge for lot 42?"
soon = (dt.datetime.now(dt.timezone.utc) + dt.timedelta(minutes=5)).isoformat()
items = [{"id": "c1", "type": "news_image", "status": "written", "overlay": ov, "caption": "x", "time": soon,
          "image_brief": {"format": "T", "must": "whipped cream", "query": "whipped cream can grocery store recall"}},
         {"id": "c2", "type": "news_image", "status": "written", "overlay": ov, "caption": "x", "time": soon,
          "image_brief": {"format": "T", "must": "aerosol topping", "query": "aerosol topping grocery store recall"}}]
json.dump({"page": "FOODPL", "account": "pg1", "timezone": "America/Chicago", "items": items}, open(os.path.join(qd, "FOODPL.json"), "w"))
open(os.path.join(W, "logos.skip"), "w").close()
yb.set_work(W)
out = io.StringIO(); so = sys.stdout; sys.stdout = out
try:
    yb.ALL_CHECKS.clear()
    _, counts = yb.process_page_file(os.path.join(qd, "FOODPL.json"))
    if yb.ALL_CHECKS:
        print("PHOTO CHECK"); [print(c) for c in yb.ALL_CHECKS]
finally:
    sys.stdout = so
data = json.load(open(os.path.join(qd, "FOODPL.json")))
c1, c2 = data["items"]
ok(c1["status"] == "built" and not c1.get("photo_check") and c1["photo_credit"]["url"].endswith(("whip1.jpg", "whip2.jpg")), "c1 built with a whipped cream photo, not marked")
ok(c2["status"] == "built" and "no photo matched" in (c2.get("photo_check") or ""), "c2 (nothing shows the thing) uses the brand background and is marked for a check")
ok("PHOTO CHECK" in out.getvalue(), "marked cards are listed under PHOTO CHECK")

# 8. post script: holds the marked card, posts the other; photo_ok releases it
calls = []
class G(http.server.BaseHTTPRequestHandler):
    def _r(self):
        n = int(self.headers.get("Content-Length") or 0); self.rfile.read(n); calls.append(f"{self.command} {self.path.split('?')[0]}")
        b = json.dumps({"id": f"p{len(calls)}", "post_id": f"123_{len(calls)}", "success": True}).encode()
        self.send_response(200); self.send_header("Content-Type", "application/json"); self.end_headers(); self.wfile.write(b)
    do_GET = do_POST = do_DELETE = _r
    def log_message(self, *a): pass
g = http.server.ThreadingHTTPServer(("127.0.0.1", 0), G); threading.Thread(target=g.serve_forever, daemon=True).start()
env = {**os.environ, "YEEZ_GRAPH_BASE": f"http://127.0.0.1:{g.server_address[1]}"}
json.dump({"accounts": [{"platform": "fb", "id": "pg1", "page_id": "pg1", "name": "Food Plus Words", "token": "T"}]}, open(os.path.join(W, "yeez-keys.json"), "w"))
POST = os.path.join(S, "yeez_post.py"); BUILD = os.path.join(S, "yeez_build.py")
r = subprocess.run([sys.executable, POST, "--date", day, "--work", W], capture_output=True, text=True, env=env)
data = json.load(open(os.path.join(qd, "FOODPL.json")))
ok(data["items"][0]["status"] == "scheduled" and data["items"][1]["status"] == "built" and "held for a photo check" in r.stdout, "post script posts c1 and holds c2")
data["items"][1]["photo_ok"] = True; json.dump(data, open(os.path.join(qd, "FOODPL.json"), "w"))
r = subprocess.run([sys.executable, POST, "--date", day, "--work", W], capture_output=True, text=True, env=env)
ok(json.load(open(os.path.join(qd, "FOODPL.json")))["items"][1]["status"] == "scheduled", "after a look (photo_ok) it posts")

# 9. the buyer flags c1 after it was scheduled: photo blocked, card rebuilt, scheduled post swapped
used = json.load(open(os.path.join(qd, "FOODPL.json")))["items"][0]["photo_credit"]["url"]
old_fb = json.load(open(os.path.join(qd, "FOODPL.json")))["items"][0]["fb_id"]
r = subprocess.run([sys.executable, BUILD, "--date", day, "--work", W, "--flag", "c1", "--reason", "that's a cake, not the recalled can"], capture_output=True, text=True)
fb = json.load(open(os.path.join(W, "photo-feedback.json")))
it = json.load(open(os.path.join(qd, "FOODPL.json")))["items"][0]
ok(r.returncode == 0 and any(b["url"] == used for b in fb["blocked"]) and not fb["rules"], "flag blocks that photo and adds no rule on its own")
ok(it["status"] == "written" and it["replace_post_id"] == old_fb, "the card goes back to be rebuilt, set to replace its scheduled post")
c2_before = json.load(open(os.path.join(qd, "FOODPL.json")))["items"][1]
out = io.StringIO(); sys.stdout = out
try:
    yb.process_page_file(os.path.join(qd, "FOODPL.json"))
finally:
    sys.stdout = so
it = json.load(open(os.path.join(qd, "FOODPL.json")))["items"][0]
c2_after = json.load(open(os.path.join(qd, "FOODPL.json")))["items"][1]
ok(it["status"] == "built" and it["photo_credit"]["url"] != used, f"rebuilt with a different photo ({it['photo_credit']['url'].rsplit('/', 1)[-1]})")
ok(c2_after == c2_before, "nothing else in the day changed")
calls.clear()
r = subprocess.run([sys.executable, POST, "--date", day, "--work", W], capture_output=True, text=True, env=env)
rec = json.load(open(os.path.join(qd, "_to_record.json")))
ok(calls and calls[0] == f"DELETE /{old_fb}" and rec and rec[0].get("replaces") == old_fb, f"post run deletes the old scheduled post, then schedules the new card ({calls[:2]})")
# the lesson from a flag: one narrow adjustment for that kind of card
r = subprocess.run([sys.executable, BUILD, "--date", day, "--work", W, "--flag", "c1", "--reason", "empty shelf, not the product",
                    "--lesson", "recall cards show the recalled product itself, not store shelves", "--avoid", "shelf", "--when", "recall"], capture_output=True, text=True)
fb = json.load(open(os.path.join(W, "photo-feedback.json")))
ok(len(fb["rules"]) == 1 and fb["rules"][0]["page"] == "FOODPL" and fb["rules"][0]["avoid"] == ["shelf"] and "product itself" in fb["rules"][0]["lesson"], "the lesson is saved, scoped to this Page and topic")
r = subprocess.run([sys.executable, BUILD, "--work", W, "--lessons", "--page", "FOODPL"], capture_output=True, text=True)
r2 = subprocess.run([sys.executable, BUILD, "--work", W, "--lessons", "--page", "FOODIG"], capture_output=True, text=True)
ok("product itself" in r.stdout and not r2.stdout.strip(), "--lessons shows it for this Page only (read before writing briefs)")
# already live
data = json.load(open(os.path.join(qd, "FOODPL.json"))); data["items"][1]["status"] = "published"; json.dump(data, open(os.path.join(qd, "FOODPL.json"), "w"))
r = subprocess.run([sys.executable, BUILD, "--date", day, "--work", W, "--flag", "c2", "--reason", "bad"], capture_output=True, text=True)
ok("already live" in r.stdout and json.load(open(os.path.join(qd, "FOODPL.json")))["items"][1]["status"] == "published", "a live post isn't touched; the buyer is told")

shutil.rmtree(W, ignore_errors=True)
print(f"\n{'ALL PASS' if not fails else str(fails) + ' FAILED'}")
sys.exit(1 if fails else 0)
