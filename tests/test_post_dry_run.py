#!/usr/bin/env python3
"""yeez_post.py --dry-run changes nothing: python3 tests/test_post_dry_run.py

Louisa's report: a dry run wrote "scheduled" into the queue files and a _to_record.json with fake ids, so the real run
afterwards skipped those posts. Checks the dry run leaves every file byte-for-byte as it was, then that a real run
(against a stand-in Facebook) still posts everything and writes _to_record.json with real ids.
"""
import hashlib, http.server, json, os, shutil, subprocess, sys, tempfile, threading, datetime as dt
HERE = os.path.dirname(os.path.abspath(__file__))
POST = os.path.join(HERE, "..", "skills", "social", "scripts", "yeez_post.py")
fails = 0
def ok(c, m):
    global fails
    print(("PASS " if c else "FAIL ") + m); fails += 0 if c else 1

calls = []
class G(http.server.BaseHTTPRequestHandler):
    def _r(self):
        n = int(self.headers.get("Content-Length") or 0); self.rfile.read(n)
        calls.append(self.command + " " + self.path.split("?")[0])
        body = {"id": f"real_{len(calls)}", "post_id": f"123_{len(calls)}", "success": True}
        if "fields=images" in self.path: body = {"images": [{"source": "https://example.com/a.jpg", "width": 1080}]}
        if "fields=status_code" in self.path: body = {"status_code": "FINISHED"}
        if "fields=permalink" in self.path: body = {"permalink": "https://instagram.com/p/x"}
        b = json.dumps(body).encode(); self.send_response(200); self.send_header("Content-Type", "application/json"); self.end_headers(); self.wfile.write(b)
    do_GET = do_POST = _r
    def log_message(self, *a): pass
srv = http.server.ThreadingHTTPServer(("127.0.0.1", 0), G); threading.Thread(target=srv.serve_forever, daemon=True).start()
base = f"http://127.0.0.1:{srv.server_address[1]}"

W = tempfile.mkdtemp(prefix="yeez-post-")
day = "2026-11-17"; q = os.path.join(W, "queue", day); os.makedirs(os.path.join(q, "media"))
open(os.path.join(q, "media", "a.jpg"), "wb").write(b"\xff\xd8fakejpeg" * 50)
json.dump({"accounts": [{"platform": "fb", "id": "pg1", "page_id": "pg1", "name": "Food Plus Words", "token": "SECRET_FB"},
                        {"platform": "ig", "id": "ig1", "page_id": "pg1", "name": "@foodpluswords", "token": "SECRET_IG"}]},
          open(os.path.join(W, "yeez-keys.json"), "w"))
soon = (dt.datetime.now(dt.timezone.utc) + dt.timedelta(minutes=5)).isoformat()
later = (dt.datetime.now(dt.timezone.utc) + dt.timedelta(hours=5)).isoformat()
json.dump({"page": "FOODPL", "account": "pg1", "timezone": "America/Chicago", "items": [
    {"id": "a1", "type": "news_image", "status": "built", "media": "media/a.jpg", "caption": "one", "time": soon},
    {"id": "a2", "type": "gradient", "status": "built", "text": "Short line", "time": later},
    {"id": "a3", "type": "link", "status": "built", "caption": "read", "link": "https://foodpluswords.com/x", "time": later}]},
    open(os.path.join(q, "FOODPL.json"), "w"), indent=2)
json.dump({"page": "FOODPLIG", "account": "ig1", "timezone": "America/Chicago", "items": [
    {"id": "b1", "type": "news_image", "status": "built", "media": "media/a.jpg", "caption": "ig", "time": soon}]},
    open(os.path.join(q, "FOODPLIG.json"), "w"), indent=2)
json.dump([{"note": "an earlier real run's list"}], open(os.path.join(q, "_to_record.json"), "w"))

def snapshot():
    out = {}
    for root, _, files in os.walk(W):
        for f in files:
            p = os.path.join(root, f); out[os.path.relpath(p, W)] = hashlib.sha1(open(p, "rb").read()).hexdigest()
    return out

before = snapshot()
env = {**os.environ, "YEEZ_GRAPH_BASE": base, "YEEZ_RUPLOAD_BASE": base}
r = subprocess.run([sys.executable, POST, "--date", day, "--work", W, "--dry-run"], capture_output=True, text=True, env=env)
ok(r.returncode == 0 and "DRY RUN: nothing was posted" in r.stdout, "dry run finishes and says nothing was posted")
ok("3 would post" in r.stdout or "would post" in r.stdout, "dry run reports what would post")
ok(not calls, f"dry run made no calls to Facebook ({len(calls)})")
ok(snapshot() == before, "every file is byte-for-byte unchanged (queue statuses, times, _to_record.json)")
ok("SECRET_" not in r.stdout + r.stderr, "no access token printed")

r = subprocess.run([sys.executable, POST, "--date", day, "--work", W], capture_output=True, text=True, env=env)
qa = json.load(open(os.path.join(q, "FOODPL.json"))); qb = json.load(open(os.path.join(q, "FOODPLIG.json")))
rec = json.load(open(os.path.join(q, "_to_record.json")))
ok(r.returncode == 0 and calls and all(i["status"] == "scheduled" and not str(i.get("fb_id")).startswith("DRY") for i in qa["items"]) and qb["items"][0]["status"] == "published",
   "the real run after the dry run still posts every item")
ok(len(rec) == 4 and not any(str(x.get("post_id", "")).startswith("DRY") for x in rec), f"_to_record.json has the 4 real posts ({[x['post_id'] for x in rec]})")

shutil.rmtree(W, ignore_errors=True)
print(f"\n{'ALL PASS' if not fails else str(fails) + ' FAILED'}")
sys.exit(1 if fails else 0)
