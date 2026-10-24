#!/usr/bin/env python3
"""
Yeez data — the buyer's performance numbers, kept in their own Yeez folder (never on yeez.ai).

  python3 yeez_data.py ingest FILE [FILE ...] --site example.com --platform newsbreak   # fold exports in
  python3 yeez_data.py report --site example.com [--veins veins.json] [--top 50]       # what's working (JSON)
  python3 yeez_data.py status                                                          # what's here, how fresh

Files live in <work>/data/ (default work folder: ./yeez-work, or set YEEZ_WORK):
  articles.csv  one row per article per platform, lifetime numbers, upserted on (platform, id)
  daily.csv     daily account totals per site and platform, upserted on (site, platform, day)
  pulls.csv     a line per ingest: when, what, how many

Accepts NewsBreak TSVs from newsbreak-pull.js and CSV/TSV exports from MSN, Yahoo, SmartNews,
Google Analytics, WordPress stats or anything with a title column and a views column. Daily
exports with one row per article per day are added up per article.
Views are the only score. Click-through rate is never computed.
"""
import argparse, csv, json, os, re, sys
from collections import defaultdict
from datetime import date, datetime, timezone

WORK = os.environ.get("YEEZ_WORK", os.path.join(os.getcwd(), "yeez-work"))
DATA = os.path.join(WORK, "data")
ART = os.path.join(DATA, "articles.csv")
DAY = os.path.join(DATA, "daily.csv")
PULLS = os.path.join(DATA, "pulls.csv")
ART_COLS = ["site", "platform", "id", "published", "title", "url", "impressions", "views", "status", "updated"]
DAY_COLS = ["site", "platform", "day", "views", "impressions"]
csv.field_size_limit(10_000_000)


def num(v):
    try:
        return int(float(re.sub(r"[,\s$%]", "", str(v or "")) or 0))
    except ValueError:
        return 0


def site_of(s):
    return re.sub(r"^https?://", "", (s or "").strip().lower()).rstrip("/")


def load(path, key):
    rows = {}
    if os.path.exists(path):
        with open(path, newline="", encoding="utf-8") as f:
            for r in csv.DictReader(f):
                rows[key(r)] = r
    return rows


def write(path, cols, rows):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    tmp = path + ".tmp"
    with open(tmp, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=cols, extrasaction="ignore")
        w.writeheader()
        w.writerows(rows)
    os.replace(tmp, path)


def read_table(path):
    raw = open(path, encoding="utf-8-sig", errors="replace").read()
    first = raw.split("\n", 1)[0]
    delim = "\t" if first.count("\t") > first.count(",") else ","
    rdr = csv.reader(raw.splitlines(), delimiter=delim)
    rows = list(rdr)
    if not rows:
        return [], []
    head = [h.strip().lower() for h in rows[0]]
    return head, rows[1:]


def col(head, *patterns):
    for p in patterns:
        for i, h in enumerate(head):
            if re.search(p, h):
                return i
    return -1


def ingest(files, site, platform):
    site = site_of(site)
    arts = load(ART, lambda r: (r["platform"], r["id"]))
    days = load(DAY, lambda r: (r["site"], r["platform"], r["day"]))
    now = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    report = []
    for path in files:
        head, rows = read_table(path)
        name = os.path.basename(path).lower()
        if "daily" in name and col(head, r"^date$") >= 0 and col(head, r"^title$") < 0:
            iD, iV, iI = col(head, r"^date$"), col(head, r"^page_?views?$", r"^views$"), col(head, r"^impressions?$")
            n = 0
            for c in rows:
                if iD < 0 or len(c) <= iD or not re.match(r"\d{4}-\d{2}-\d{2}", c[iD]):
                    continue
                k = (site, platform, c[iD][:10])
                days[k] = {"site": site, "platform": platform, "day": c[iD][:10], "views": num(c[iV]) if iV >= 0 else 0, "impressions": num(c[iI]) if iI >= 0 else ""}
                n += 1
            report.append({"file": path, "daily_rows": n})
            continue
        iT = col(head, r"^title$", r"headline", r"^page title", r"^post title", r"title")
        iV = col(head, r"^page_?views?$", r"^views$", r"pageviews", r"^total views", r"views", r"^clicks$")
        iI = col(head, r"^impressions?$", r"impression")
        iDt = col(head, r"^date$", r"publish", r"^posted", r"created", r"launch")
        iId = col(head, r"^doc_?id$", r"^docid$", r"^id$", r"content id", r"article id")
        iU = col(head, r"^url$", r"^link$", r"page path", r"landing page", r"^page$")
        iS = col(head, r"^status$", r"^state$")
        if iT < 0 or iV < 0:
            report.append({"file": path, "error": "no title and views columns", "columns": head})
            continue
        merged = {}
        for c in rows:
            if len(c) <= max(iT, iV) or not c[iT].strip():
                continue
            ident = (c[iId] if iId >= 0 and len(c) > iId and c[iId] else (c[iU] if iU >= 0 and len(c) > iU and c[iU] else c[iT])).strip()
            m = merged.get(ident)
            pub = c[iDt][:19] if iDt >= 0 and len(c) > iDt else ""
            if m:
                m["views"] += num(c[iV])
                if iI >= 0: m["impressions"] = num(m["impressions"]) + num(c[iI])
                if pub and (not m["published"] or pub < m["published"]): m["published"] = pub
            else:
                merged[ident] = {"site": site, "platform": platform, "id": ident[:200], "published": pub, "title": re.sub(r"\s+", " ", c[iT]).strip()[:300],
                                 "url": c[iU] if iU >= 0 and len(c) > iU else "", "impressions": num(c[iI]) if iI >= 0 else "", "views": num(c[iV]),
                                 "status": c[iS] if iS >= 0 and len(c) > iS else "", "updated": now}
        added = refreshed = 0
        for r in merged.values():
            k = (platform, r["id"])
            if k in arts:
                old = arts[k]
                r["views"] = max(num(old["views"]), r["views"])
                r["published"] = r["published"] or old.get("published", "")
                refreshed += 1
            else:
                added += 1
            arts[k] = r
        report.append({"file": path, "articles": len(merged), "added": added, "refreshed": refreshed})
    write(ART, ART_COLS, sorted(arts.values(), key=lambda r: (r["site"], r["platform"], r["published"])))
    write(DAY, DAY_COLS, sorted(days.values(), key=lambda r: (r["site"], r["platform"], r["day"])))
    new = not os.path.exists(PULLS)
    with open(PULLS, "a", newline="") as f:
        w = csv.writer(f)
        if new: w.writerow(["at", "site", "platform", "files", "summary"])
        w.writerow([datetime.now(timezone.utc).isoformat(timespec="seconds"), site, platform, len(files), json.dumps(report)])
    print(json.dumps({"ok": True, "site": site, "platform": platform, "results": report}, indent=1))


def pct(a, p):
    if not a: return 0
    s = sorted(a)
    return s[min(len(s) - 1, int(p * (len(s) - 1)))]


def report(site, veins_path, top):
    site = site_of(site)
    arts = [r for r in load(ART, lambda r: (r["platform"], r["id"])).values() if r["site"] == site]
    if not arts:
        print(json.dumps({"ok": False, "site": site, "note": "No numbers for this site yet. Pull or ingest first."})); return
    for r in arts: r["v"] = num(r["views"])
    allv = [r["v"] for r in arts]
    site_mean = sum(allv) / len(allv)
    plats = []
    for p in sorted({r["platform"] for r in arts}):
        rs = [r for r in arts if r["platform"] == p]; v = [r["v"] for r in rs]
        hours, months = defaultdict(lambda: [0, 0]), defaultdict(lambda: [0, 0])
        for r in rs:
            m = re.match(r"(\d{4}-\d{2})-\d{2}[ T](\d{2})", r["published"] or "")
            if m:
                hours[int(m.group(2))][0] += 1; hours[int(m.group(2))][1] += r["v"]
            if r["published"][:7]:
                months[r["published"][:7]][0] += 1; months[r["published"][:7]][1] += r["v"]
        live = [r for r in rs if not r["status"] or r["status"] in ("2", "1", "live", "published")]
        plats.append({"platform": p, "articles": len(rs), "not_live": len(rs) - len(live), "total_views": sum(v), "mean_views": round(sum(v) / len(v)),
                      "bands": {"top1pct": pct(v, .99), "top5pct": pct(v, .95), "top10pct": pct(v, .9), "top25pct": pct(v, .75), "median": pct(v, .5)},
                      "count_20k": sum(x >= 20000 for x in v), "count_100k": sum(x >= 100000 for x in v),
                      "by_hour_as_published": [{"hour": h, "articles": n, "views_per_article": round(t / n)} for h, (n, t) in sorted(hours.items())],
                      "by_month": [{"month": m, "articles": n, "views_per_article": round(t / n)} for m, (n, t) in sorted(months.items())[-12:]]})
    arts.sort(key=lambda r: -r["v"])
    out = {"ok": True, "site": site, "articles": len(arts), "site_mean_views": round(site_mean), "platforms": plats,
           "top": [{"title": r["title"], "views": r["v"], "platform": r["platform"], "url": r["url"], "published": r["published"][:10]} for r in arts[:top]],
           "wasted_reach": [{"title": r["title"], "impressions": num(r["impressions"]), "views": r["v"], "platform": r["platform"]}
                            for r in arts if num(r["impressions"]) > 5000 and r["v"] < num(r["impressions"]) * 0.02][:40]}
    med = pct(allv, .5); tail = [r for r in arts if r["v"] <= med]; step = max(1, len(tail) // 120)
    out["flops_sample"] = [{"title": r["title"], "views": r["v"], "platform": r["platform"]} for r in tail[::step][:120]]
    cutoff = (date.today().toordinal() - 14)
    recent = [r for r in arts if r["published"][:10] and date.fromisoformat(r["published"][:10]).toordinal() >= cutoff]
    out["last_14_days_top"] = [{"title": r["title"], "views": r["v"], "platform": r["platform"], "published": r["published"][:10]} for r in recent[:25]]
    if veins_path and os.path.exists(veins_path):
        veins = json.load(open(veins_path))
        res = []
        for vn in veins:
            kws = [k.lower() for k in vn.get("keywords", []) if k]
            hit = [r for r in arts if any(k in r["title"].lower() for k in kws)]
            v = [r["v"] for r in hit]; months = defaultdict(lambda: [0, 0])
            for r in hit:
                if r["published"][:7]: months[r["published"][:7]][0] += 1; months[r["published"][:7]][1] += r["v"]
            vpa = round(sum(v) / len(v)) if v else 0
            res.append({"name": vn["name"], "keywords": vn.get("keywords", []), "articles": len(hit), "views_per_article": vpa,
                        "vs_site_average": round(vpa / site_mean, 2) if site_mean else None, "median": pct(v, .5), "count_20k": sum(x >= 20000 for x in v),
                        "share_of_views": round(sum(v) / max(1, sum(allv)), 3),
                        "by_month": [{"month": m, "articles": n, "views_per_article": round(t / n)} for m, (n, t) in sorted(months.items())[-6:]],
                        "example": hit[0]["title"] if hit else None})
        out["veins"] = sorted(res, key=lambda x: -x["views_per_article"])
    days = [r for r in load(DAY, lambda r: (r["site"], r["platform"], r["day"])).values() if r["site"] == site]
    out["daily_last_120"] = [{"platform": r["platform"], "day": r["day"], "views": num(r["views"])} for r in sorted(days, key=lambda r: r["day"])[-120:]]
    out["note"] = "Views are the only score. The latest month is biased low (less time to collect views). Hours are as the platform reported them."
    print(json.dumps(out, indent=1))


def status():
    arts = load(ART, lambda r: (r["platform"], r["id"])).values()
    g = defaultdict(lambda: {"articles": 0, "updated": ""})
    for r in arts:
        k = (r["site"], r["platform"]); g[k]["articles"] += 1; g[k]["updated"] = max(g[k]["updated"], r.get("updated", ""))
    print(json.dumps({"ok": True, "folder": DATA, "data": [{"site": s, "platform": p, **v} for (s, p), v in sorted(g.items())]}, indent=1))


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)
    a = sub.add_parser("ingest"); a.add_argument("files", nargs="+"); a.add_argument("--site", required=True); a.add_argument("--platform", required=True)
    b = sub.add_parser("report"); b.add_argument("--site", required=True); b.add_argument("--veins"); b.add_argument("--top", type=int, default=50)
    sub.add_parser("status")
    x = ap.parse_args()
    if x.cmd == "ingest": ingest(x.files, x.site, x.platform)
    elif x.cmd == "report": report(x.site, x.veins, x.top)
    else: status()
