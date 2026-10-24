#!/usr/bin/env python3
"""
yeez_post.py — posts the day's built queue straight to Facebook and Instagram from the buyer's AI app.

Ported from the Clark Bros Media network's own publisher (fb_publish.py): the same Graph calls, the same
three-step reel upload, the same 15-minute lead rule. The keys come from the buyer's own keys file
(yeez-work/yeez-keys.json); nothing is uploaded to yeez.ai.

    python3 yeez_post.py --fetch-keys "<one-time link from get_social_keys_link>" [--work yeez-work]
    python3 yeez_post.py --date 2026-10-21 [--page CODE] [--work yeez-work] [--due-within 30] [--dry-run]

Stories, and everything on Instagram, can't be scheduled, so they're posted only once their time is less than
--due-within minutes away (default 30); until then they stay "built" and the next run posts them. Run it again
during the day (the "social now" task) to post them on time. Facebook feed posts are always scheduled at once.

Queue: yeez-work/queue/<date>/<CODE>.json (built by yeez_build.py). Each page file names its "account"
(the id or name in the keys file). Items with status "built" are posted:
  news_image, text_image  Facebook: scheduled photo at item.time.   Instagram: published now.
  gradient                Facebook only: scheduled text on the brand gradient (130 characters max).
  link                    Facebook only: scheduled link post (item.link).
  story                   Facebook and Instagram: published now (stories can't be scheduled).
  reel, image_reel        Facebook: uploaded to Facebook's upload server, scheduled at item.time.
                          Instagram: uploaded and published once Instagram finishes processing.
Instagram needs a public image link, so photos for Instagram go up first as an unpublished Facebook photo
on the linked Page and Instagram takes the image from there.

Writes yeez-work/queue/<date>/_to_record.json: this run's posts, to pass to the record_social_posts tool.
Keys are never printed. Python 3 standard library only.
"""
import argparse
import datetime as dt
import json
import mimetypes
import os
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
import uuid
from zoneinfo import ZoneInfo

API_VER = "v25.0"
API = os.environ.get("YEEZ_GRAPH_BASE", f"https://graph.facebook.com/{API_VER}").rstrip("/")
RUPLOAD = os.environ.get("YEEZ_RUPLOAD_BASE", "https://rupload.facebook.com").rstrip("/")
GRADIENT_PRESET = "303063890126415"     # the brand yellow→orange→purple background, verified live 2026-09-28
MIN_LEAD = dt.timedelta(minutes=15)
BUMP_TO = dt.timedelta(minutes=20)
PHOTO_TYPES = ("news_image", "text_image")
REEL_TYPES = ("reel", "image_reel")
UA = "Yeez-post/1.0 (+https://yeez.ai)"
_SECRETS = set()
DRY = False


class PubError(Exception):
    pass


def scrub(s):
    s = str(s)
    for t in _SECRETS:
        if t:
            s = s.replace(t, "***")
    return s


def graph(method, path, params=None, files=None, token=None, headers=None, raw_body=None, base=None):
    """Call Graph. Returns parsed JSON or raises PubError (keys scrubbed). files: {field: path} -> multipart."""
    params = dict(params or {})
    if token and raw_body is None:
        params["access_token"] = token
    url = (base if base is not None else API) + path
    if DRY:
        print(scrub(f"[dry-run] {method} {path or url} {sorted(k for k in params if k != 'access_token')}"), flush=True)
        return {"id": "DRY_" + uuid.uuid4().hex[:8], "post_id": "DRY_POST", "video_id": "DRY_VID", "success": True,
                "uri": RUPLOAD + "/ig-api-upload/DRY", "status_code": "FINISHED", "images": [{"source": "https://example.com/x.jpg", "width": 1}]}
    hdrs = {"User-Agent": UA, **(headers or {})}
    data = None
    if raw_body is not None:
        data = raw_body
    elif method == "GET":
        url += "?" + urllib.parse.urlencode(params)
    elif files:
        b = "----yeez" + uuid.uuid4().hex
        parts = []
        for k, v in params.items():
            parts.append(f'--{b}\r\nContent-Disposition: form-data; name="{k}"\r\n\r\n'.encode() + str(v).encode("utf-8") + b"\r\n")
        for k, p in files.items():
            with open(p, "rb") as fh:
                blob = fh.read()
            mime = mimetypes.guess_type(p)[0] or "application/octet-stream"
            parts.append(f'--{b}\r\nContent-Disposition: form-data; name="{k}"; filename="{os.path.basename(p)}"\r\n'
                         f"Content-Type: {mime}\r\n\r\n".encode() + blob + b"\r\n")
        data = b"".join(parts) + f"--{b}--\r\n".encode()
        hdrs["Content-Type"] = "multipart/form-data; boundary=" + b
    else:
        data = urllib.parse.urlencode(params).encode()
        hdrs["Content-Type"] = "application/x-www-form-urlencoded"
    req = urllib.request.Request(url, data=data, headers=hdrs, method=method)
    try:
        with urllib.request.urlopen(req, timeout=600 if (files or raw_body) else 90) as r:
            body = r.read().decode("utf-8", "replace")
    except urllib.error.HTTPError as e:
        body = e.read().decode("utf-8", "replace")
        try:
            err = json.loads(body).get("error", {})
            msg = f"HTTP {e.code} code={err.get('code')}: {err.get('error_user_msg') or err.get('message')}"
        except Exception:
            msg = f"HTTP {e.code}: {body[:300]}"
        raise PubError(scrub(msg))
    except urllib.error.URLError as e:
        raise PubError(f"can't reach Facebook ({e.reason}). Your AI app needs internet access turned on (see the setup video).")
    except Exception as e:
        raise PubError(scrub(f"network error on {method} {path}: {e}"))
    try:
        return json.loads(body)
    except ValueError:
        return {"raw": body[:500]}


def upload_binary(upload_url, token, path):
    """Facebook's resumable upload server: the whole file in one request (offset 0), like fb_publish.py."""
    size = os.path.getsize(path)
    blob = b"" if DRY else open(path, "rb").read()
    res = graph("POST", "", headers={"Authorization": f"OAuth {token}", "offset": "0", "file_size": str(size)}, raw_body=blob, base=upload_url)
    if not DRY and not (res.get("success") in (True, "true")):
        raise PubError(f"video upload did not report success: {scrub(json.dumps(res))[:300]}")


# ---------------------------------------------------------------- keys and queue

def keys_path(work):
    return os.path.join(work, "yeez-keys.json")


def load_keys(work):
    p = keys_path(work)
    if not os.path.exists(p):
        raise SystemExit(f"No keys file at {p}. Save yeez-keys.json there (from the Facebook connect page), "
                         "or fetch it with --fetch-keys and a link from get_social_keys_link.")
    k = json.load(open(p, encoding="utf-8"))
    for a in k.get("accounts", []):
        _SECRETS.add(a.get("token"))
    return k["accounts"]


def account_for(accounts, name_or_id):
    want = str(name_or_id or "").lower().lstrip("@")
    for a in accounts:
        if str(a["id"]) == str(name_or_id) or a["name"].lower().lstrip("@") == want:
            return a
    raise PubError(f"account {name_or_id!r} isn't in yeez-keys.json (reconnect Facebook, then fetch the keys file again)")


def fetch_keys(link, work):
    os.makedirs(work, exist_ok=True)
    req = urllib.request.Request(link, headers={"User-Agent": UA})
    try:
        with urllib.request.urlopen(req, timeout=60) as r:
            data = json.loads(r.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        raise SystemExit(f"keys link didn't work (HTTP {e.code}): it's one-time and lasts an hour; ask for a new one.")
    p = keys_path(work)
    with open(p, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)
    try:
        os.chmod(p, 0o600)
    except Exception:
        pass
    print(f"saved {p}: {len(data.get('accounts', []))} accounts ({', '.join(a['platform'] + ':' + a['name'] for a in data.get('accounts', []))})")


def now(tz):
    return dt.datetime.now(tz)


def sched_time(item, tz):
    t = dt.datetime.fromisoformat(item["time"]) if item.get("time") else now(tz)
    if t.tzinfo is None:
        t = t.replace(tzinfo=tz)
    if t - now(tz) < MIN_LEAD:
        t = (now(tz) + BUMP_TO).replace(second=0, microsecond=0)
        item["time"] = t.isoformat()
    return t


def media_path(qfile, item):
    p = os.path.join(os.path.dirname(qfile), item.get("media") or "")
    if not item.get("media") or not os.path.exists(p):
        raise PubError(f"{item.get('id')}: no built media (run yeez_build.py first)")
    return p


# ---------------------------------------------------------------- Facebook

def fb_post(qfile, item, acc, tz):
    pid, tok, typ = acc["id"], acc["token"], item.get("type")
    if typ == "story":
        ph = graph("POST", f"/{pid}/photos", {"published": "false"}, files={"source": media_path(qfile, item)}, token=tok)
        res = graph("POST", f"/{pid}/photo_stories", {"photo_id": ph["id"]}, token=tok)
        return {"format": "story", "post_id": str(res.get("post_id") or ph["id"]), "status": "published"}
    when = sched_time(item, tz)
    ts = int(when.timestamp())
    sched = {"published": "false", "scheduled_publish_time": ts}
    cap = item.get("caption") or ""
    if typ in PHOTO_TYPES:
        res = graph("POST", f"/{pid}/photos", {"caption": cap, **sched}, files={"source": media_path(qfile, item)}, token=tok)
        return {"format": "photo", "post_id": str(res.get("post_id") or res.get("id")), "status": "scheduled", "publish_at": when.isoformat()}
    if typ == "gradient":
        text = (item.get("text") or "").strip()
        if not text or len(text) > 130:
            raise PubError(f"gradient text must be 1–130 characters (has {len(text)})")
        res = graph("POST", f"/{pid}/feed", {"message": text, "text_format_preset_id": GRADIENT_PRESET, **sched}, token=tok)
        return {"format": "gradient", "post_id": str(res["id"]), "status": "scheduled", "publish_at": when.isoformat(), "caption": text}
    if typ == "link":
        if not item.get("link"):
            raise PubError("link post has no link")
        res = graph("POST", f"/{pid}/feed", {"message": cap, "link": item["link"], **sched}, token=tok)
        return {"format": "link", "post_id": str(res["id"]), "status": "scheduled", "publish_at": when.isoformat(), "link": item["link"]}
    if typ in REEL_TYPES:
        mp = media_path(qfile, item)
        st = graph("POST", f"/{pid}/video_reels", {"upload_phase": "start"}, token=tok)
        vid = st.get("video_id")
        if not vid:
            raise PubError(f"reel start returned no video_id: {scrub(json.dumps(st))[:200]}")
        upload_binary(st.get("upload_url") or f"{RUPLOAD}/video-upload/{API_VER}/{vid}", tok, mp)
        fin = graph("POST", f"/{pid}/video_reels", {"upload_phase": "finish", "video_id": vid, "video_state": "SCHEDULED",
                                                    "scheduled_publish_time": ts, "description": cap}, token=tok)
        if not (fin.get("success") in (True, "true") or fin.get("id")):
            raise PubError(f"reel finish not successful: {scrub(json.dumps(fin))[:200]}")
        return {"format": "reel", "post_id": str(vid), "status": "scheduled", "publish_at": when.isoformat()}
    raise PubError(f"unknown type {typ!r}")


# ---------------------------------------------------------------- Instagram

def ig_wait(cid, tok, seconds):
    end = time.time() + seconds
    while True:
        st = graph("GET", f"/{cid}", {"fields": "status_code,status"}, token=tok)
        if st.get("status_code") == "FINISHED":
            return
        if st.get("status_code") in ("ERROR", "EXPIRED"):
            raise PubError(f"Instagram couldn't process it ({st.get('status') or st.get('status_code')})")
        if time.time() > end:
            raise PubError("Instagram is still processing; run the post step again later to publish it")
        time.sleep(0 if DRY else 4)


def public_image_url(path, acc, accounts):
    """Instagram fetches images by URL: put the file on the linked Facebook Page as an unpublished photo first."""
    page = next((a for a in accounts if a["platform"] == "fb" and str(a["id"]) == str(acc.get("page_id"))), None)
    pid, tok = (page["id"], page["token"]) if page else (acc.get("page_id"), acc["token"])
    ph = graph("POST", f"/{pid}/photos", {"published": "false", "temporary": "true"}, files={"source": path}, token=tok)
    info = graph("GET", f"/{ph['id']}", {"fields": "images"}, token=tok)
    best = max(info.get("images") or [], key=lambda i: i.get("width", 0), default=None)
    if not best:
        raise PubError("couldn't get a link for the image from Facebook")
    return best["source"]


def ig_post(qfile, item, acc, accounts):
    igid, tok, typ = acc["id"], acc["token"], item.get("type")
    cap = item.get("caption") or ""
    if typ in PHOTO_TYPES + ("story",):
        url = public_image_url(media_path(qfile, item), acc, accounts)
        params = {"image_url": url} if typ != "story" else {"image_url": url, "media_type": "STORIES"}
        if typ != "story":
            params["caption"] = cap
        c = graph("POST", f"/{igid}/media", params, token=tok)
        ig_wait(c["id"], tok, 60)
    elif typ in REEL_TYPES:
        c = graph("POST", f"/{igid}/media", {"media_type": "REELS", "upload_type": "resumable", "caption": cap, "share_to_feed": "true"}, token=tok)
        upload_binary(c.get("uri") or f"{RUPLOAD}/ig-api-upload/{API_VER}/{c['id']}", tok, media_path(qfile, item))
        ig_wait(c["id"], tok, 240)
    else:
        raise PubError(f"Instagram has no {typ} posts")
    pub = graph("POST", f"/{igid}/media_publish", {"creation_id": c["id"]}, token=tok)
    link = graph("GET", f"/{pub['id']}", {"fields": "permalink"}, token=tok).get("permalink")
    return {"format": "story" if typ == "story" else ("reel" if typ in REEL_TYPES else "photo"), "post_id": str(pub["id"]), "status": "published", "permalink": link}


# ---------------------------------------------------------------- main

def main():
    global DRY
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--work", default=os.environ.get("YEEZ_WORK", "yeez-work"))
    ap.add_argument("--fetch-keys", default=None)
    ap.add_argument("--date", default=None)
    ap.add_argument("--page", default=None)
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--due-within", type=int, default=30)
    a = ap.parse_args()
    if a.fetch_keys:
        return fetch_keys(a.fetch_keys, a.work)
    if not a.date:
        ap.error("--date is required")
    DRY = a.dry_run
    accounts = load_keys(a.work)
    ddir = os.path.join(a.work, "queue", a.date)
    files = sorted(f for f in os.listdir(ddir) if f.endswith(".json") and not f.startswith("_"))
    if a.page:
        files = [f for f in files if os.path.splitext(f)[0].upper() == a.page.upper()]
    posted, failed, waiting = [], 0, 0
    for f in files:
        qfile = os.path.join(ddir, f)
        q = json.load(open(qfile, encoding="utf-8"))
        tz = ZoneInfo(q.get("timezone") or "America/Chicago")
        try:
            acc = account_for(accounts, q.get("account") or q.get("page"))
        except PubError as e:
            print(f"{f}: {e}")
            failed += 1
            continue
        print(f"{f} -> {acc['platform']}:{acc['name']}")
        for item in sorted(q.get("items", []), key=lambda i: i.get("time") or ""):
            if item.get("status") != "built":
                continue
            if (acc["platform"] != "fb" or item.get("type") == "story") and item.get("time"):
                try:
                    due = dt.datetime.fromisoformat(item["time"])
                    if due.tzinfo is None:
                        due = due.replace(tzinfo=tz)
                    if due > dt.datetime.now(dt.timezone.utc) + dt.timedelta(minutes=a.due_within):
                        waiting += 1
                        print(f"  ..  {item['id']:16} {item.get('type'):11} waits for {item['time']} (can't be scheduled ahead)")
                        continue
                except ValueError:
                    pass
            try:
                r = fb_post(qfile, item, acc, tz) if acc["platform"] == "fb" else ig_post(qfile, item, acc, accounts)
                item["status"], item["fb_id"], item["error"] = r["status"], r["post_id"], None
                rec = {k: v for k, v in {"account": acc["id"], "caption": item.get("caption") or r.get("caption"), **r}.items() if v not in (None, "")}
                fc = ((item.get("cta") or {}).get("first_comment") or "").strip()
                if fc and acc["platform"] == "fb" and r["status"] == "scheduled":
                    rec["first_comment"] = fc
                posted.append(rec)
                print(f"  ok  {item['id']:16} {item.get('type'):11} {r['status']} {r.get('publish_at') or r.get('permalink') or ''}")
            except PubError as e:
                item["status"], item["error"] = "failed", str(e)
                failed += 1
                print(f"  ERR {item['id']:16} {item.get('type'):11} {e}")
            with open(qfile + ".tmp", "w", encoding="utf-8") as fh:
                json.dump(q, fh, indent=2, ensure_ascii=False)
            os.replace(qfile + ".tmp", qfile)
    out = os.path.join(ddir, "_to_record.json")
    with open(out, "w", encoding="utf-8") as fh:
        json.dump(posted, fh, indent=1)
    print(f"\nposted {len(posted)} · failed {failed} · waiting {waiting}. Now call record_social_posts with the list in {out}")
    if waiting:
        print(f"{waiting} stories/Instagram items wait for their time: run this again during the day (the social now task).")
    sys.exit(1 if failed else 0)


if __name__ == "__main__":
    main()
