#!/usr/bin/env python3
"""
beehiiv_post.py: puts a Yeez newsletter issue into the buyer's beehiiv publication through beehiiv's API,
for buyers without the beehiiv connector in their AI app. Needs a beehiiv Pro or Enterprise plan (or the trial).

    python3 beehiiv_post.py --check [--work yeez-work]
    python3 beehiiv_post.py --title "Subject" --preview "Preview text" --html issue.html [--schedule 2026-10-24T13:00:00Z] [--work yeez-work]

Keys: yeez-work/beehiiv.json  {"api_key": "...", "publication_id": "pub_..."}  (the buyer makes the key in
beehiiv: Settings -> Integrations -> API, and saves this file themselves). The key is never printed.
Without --schedule the post is saved as a DRAFT. --schedule sets it to send at that time (only when the buyer's
newsletter settings say Yeez may schedule sends). Prints JSON: {"ok", "post_id", "status", "web_url"}.
Python 3 standard library only.
"""
import argparse, json, os, sys, urllib.request, urllib.error

API = "https://api.beehiiv.com/v2"


def keys(work):
    p = os.path.join(work, "beehiiv.json")
    if not os.path.exists(p):
        sys.exit(json.dumps({"ok": False, "error": f"No {p}. The buyer saves their beehiiv API key and publication ID there (Settings -> Integrations -> API in beehiiv)."}))
    k = json.load(open(p, encoding="utf-8"))
    if not k.get("api_key") or not k.get("publication_id"):
        sys.exit(json.dumps({"ok": False, "error": f"{p} needs api_key and publication_id."}))
    return k


def call(k, method, path, body=None):
    req = urllib.request.Request(API + path, method=method, data=json.dumps(body).encode() if body is not None else None,
                                 headers={"Authorization": "Bearer " + k["api_key"], "Content-Type": "application/json", "Accept": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=60) as r:
            return json.loads(r.read() or b"{}")
    except urllib.error.HTTPError as e:
        msg = e.read().decode("utf-8", "replace")[:400].replace(k["api_key"], "***")
        hint = " (creating posts by API needs beehiiv Pro or Enterprise)" if e.code in (401, 403) else ""
        sys.exit(json.dumps({"ok": False, "error": f"beehiiv answered {e.code}{hint}: {msg}"}))
    except urllib.error.URLError as e:
        sys.exit(json.dumps({"ok": False, "error": f"Couldn't reach beehiiv ({e.reason}). Turn on network access for this app."}))


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--work", default=os.environ.get("YEEZ_WORK", "yeez-work"))
    ap.add_argument("--check", action="store_true")
    ap.add_argument("--title"); ap.add_argument("--preview", default=""); ap.add_argument("--html")
    ap.add_argument("--schedule", default=None, help="ISO time to send; omit for a draft")
    a = ap.parse_args()
    k = keys(a.work)
    pub = k["publication_id"]
    if a.check:
        r = call(k, "GET", f"/publications/{pub}")
        d = r.get("data", {})
        print(json.dumps({"ok": True, "publication": d.get("name"), "id": d.get("id")}))
        return
    if not a.title or not a.html:
        ap.error("--title and --html are needed")
    body = {"title": a.title, "subtitle": a.preview, "body_content": open(a.html, encoding="utf-8").read(),
            "status": "confirmed" if a.schedule else "draft",
            "email_settings": {"email_subject_line": a.title, "email_preview_text": a.preview}}
    if a.schedule:
        body["scheduled_at"] = a.schedule
    r = call(k, "POST", f"/publications/{pub}/posts", body)
    d = r.get("data", {})
    print(json.dumps({"ok": True, "post_id": d.get("id"), "status": d.get("status"), "web_url": d.get("web_url")}))


if __name__ == "__main__":
    main()
