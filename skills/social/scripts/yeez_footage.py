#!/usr/bin/env python3
"""
yeez_footage.py — the buyer's own reel footage and music, from a shared Google Drive folder.

The buyer shares one folder ("Anyone with the link can view"). Inside it, each subfolder is a
footage mood (calm, drive, home, nature, … any names they like) holding their own clips, and a
folder named "music" holds their own tracks. No Google login or key is needed: the folder's
public link is enough.

    python3 yeez_footage.py --folder "https://drive.google.com/drive/folders/<id>" --list
    python3 yeez_footage.py --folder URL --mood calm --clips 4     # make sure 4 calm clips are on disk

Files land in yeez-work/footage/broll/<mood>/ and yeez-work/footage/music/, which is where the
reel renderer looks. Only the clips a reel needs are downloaded, least-used first, and the
local copy is trimmed to --max-gb (default 4) so a big library never fills the disk.
"""

import argparse
import csv
import html
import json
import os
import random
import re
import sys
import time
import urllib.request

UA = "Mozilla/5.0 (Yeez footage; +https://yeez.ai)"
VIDEO = (".mov", ".mp4", ".m4v", ".mkv", ".webm", ".avi")
AUDIO = (".mp3", ".m4a", ".wav", ".aac")


def folder_id(url_or_id):
    m = re.search(r"/folders/([A-Za-z0-9_-]{10,})", url_or_id) or re.search(r"[?&]id=([A-Za-z0-9_-]{10,})", url_or_id)
    if m:
        return m.group(1)
    if re.fullmatch(r"[A-Za-z0-9_-]{10,}", url_or_id.strip()):
        return url_or_id.strip()
    raise SystemExit("That doesn't look like a Google Drive folder link.")


def _get(url, timeout=60):
    return urllib.request.urlopen(urllib.request.Request(url, headers={"User-Agent": UA}), timeout=timeout)


def list_folder(fid):
    """[(id, name, is_folder)] for a folder shared with 'Anyone with the link'."""
    try:
        page = _get(f"https://drive.google.com/embeddedfolderview?id={fid}").read().decode("utf-8", "replace")
    except Exception as e:
        raise RuntimeError(f"can't open the Drive folder ({e}). Share it as 'Anyone with the link can view', "
                           "and make sure this AI app has internet access.")
    out = []
    for m in re.finditer(r'<div class="flip-entry" id="entry-([^"]+)".*?<a href="([^"]+)".*?<div class="flip-entry-title">(.*?)</div>', page, re.S):
        out.append((m.group(1), html.unescape(m.group(3)).strip(), "/folders/" in m.group(2)))
    return out


def build_index(root_url, work):
    """Walk the shared folder (mood folders, one level of subfolders inside each, and 'music')."""
    idx = {"folder": root_url, "listed_at": time.time(), "moods": {}, "music": []}
    for fid, name, is_dir in list_folder(folder_id(root_url)):
        if not is_dir:
            continue
        key = name.strip()
        files, todo = [], [fid]
        while todo:
            for cid, cname, cdir in list_folder(todo.pop()):
                if cdir:
                    todo.append(cid)
                elif cname.lower().endswith(AUDIO if key.lower() == "music" else VIDEO):
                    files.append({"id": cid, "name": cname})
        if key.lower() == "music":
            idx["music"] = files
        elif files:
            idx["moods"][key] = files
    os.makedirs(os.path.join(work, "footage"), exist_ok=True)
    json.dump(idx, open(os.path.join(work, "footage", "index.json"), "w"), indent=1)
    return idx


def load_index(root_url, work, max_age_h=24):
    p = os.path.join(work, "footage", "index.json")
    try:
        idx = json.load(open(p))
        if idx.get("folder") == root_url and time.time() - idx.get("listed_at", 0) < max_age_h * 3600:
            return idx
    except Exception:
        pass
    return build_index(root_url, work)


def download(file_id, dest):
    """Public Drive file to disk (confirm=t skips the large-file warning page)."""
    tmp = dest + ".part"
    r = _get(f"https://drive.usercontent.google.com/download?id={file_id}&export=download&confirm=t", timeout=300)
    if "text/html" in (r.headers.get("Content-Type") or ""):
        raise RuntimeError("Drive returned a web page instead of the file; check the folder's sharing.")
    os.makedirs(os.path.dirname(dest), exist_ok=True)
    with open(tmp, "wb") as f:
        while True:
            b = r.read(1 << 20)
            if not b:
                break
            f.write(b)
    os.replace(tmp, dest)
    return dest


def _usage(work):
    p = os.path.join(work, "footage", "broll-usage.csv")
    out = {}
    try:
        for row in csv.DictReader(open(p, newline="", encoding="utf-8")):
            out[os.path.basename(row["clip"])] = row.get("last_used", "")
    except Exception:
        pass
    return out


def trim(work, max_gb):
    """Delete the oldest downloaded clips (and their proxies) once the local copy passes max_gb."""
    root = os.path.join(work, "footage", "broll")
    files = []
    for d, _, fs in os.walk(root):
        for f in fs:
            p = os.path.join(d, f)
            files.append((os.path.getatime(p), os.path.getsize(p), p))
    total = sum(s for _, s, _ in files)
    for _, s, p in sorted(files):
        if total <= max_gb * 1e9:
            break
        os.remove(p)
        total -= s


def ensure_clips(root_url, work, mood, k=4, max_gb=4.0):
    """Make sure k clips of this mood are on disk; returns (mood folder used, local clip paths)."""
    idx = load_index(root_url, work)
    if not idx["moods"]:
        raise RuntimeError("the footage folder has no clip folders yet (one folder per mood, e.g. calm, drive, home)")
    names = {m.lower(): m for m in idx["moods"]}
    m = names.get((mood or "").lower()) or names.get("calm") or random.choice(list(idx["moods"]))
    local_dir = os.path.join(work, "footage", "broll", re.sub(r"[\\/:]+", "-", m).strip())
    have = {f for f in (os.listdir(local_dir) if os.path.isdir(local_dir) else []) if f.lower().endswith(VIDEO)}
    used = _usage(work)
    want = sorted(idx["moods"][m], key=lambda f: (f["name"] in have and 0 or 1, used.get(f["name"], ""), random.random()))
    # keep the clips already here that haven't been used lately, then fill up with fresh ones
    for f in want:
        if len(have) >= k:
            break
        if f["name"] not in have:
            download(f["id"], os.path.join(local_dir, f["name"]))
            have.add(f["name"])
    trim(work, max_gb)
    return m, [os.path.join(local_dir, f) for f in sorted(have) if os.path.exists(os.path.join(local_dir, f))]


def ensure_music(root_url, work, limit=12):
    idx = load_index(root_url, work)
    d = os.path.join(work, "footage", "music")
    for f in idx["music"][:limit]:
        p = os.path.join(d, f["name"])
        if not os.path.exists(p):
            download(f["id"], p)
    return [os.path.join(d, f) for f in (os.listdir(d) if os.path.isdir(d) else []) if f.lower().endswith(AUDIO)]


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--folder", required=True)
    ap.add_argument("--work", default=os.environ.get("YEEZ_WORK", "yeez-work"))
    ap.add_argument("--list", action="store_true")
    ap.add_argument("--mood")
    ap.add_argument("--clips", type=int, default=4)
    a = ap.parse_args()
    if a.list:
        idx = build_index(a.folder, a.work)
        print(json.dumps({"moods": {k: len(v) for k, v in idx["moods"].items()}, "music_tracks": len(idx["music"])}, indent=1))
        if not idx["music"]:
            print("No 'music' folder with tracks found: reels need the buyer's own music.", file=sys.stderr)
        return
    m, clips = ensure_clips(a.folder, a.work, a.mood, a.clips)
    print(f"{m}: {len(clips)} clips on disk")
    print(f"music: {len(ensure_music(a.folder, a.work))} tracks on disk")


if __name__ == "__main__":
    main()
