#!/usr/bin/env python3
"""
Yeez data — the buyer's performance numbers, kept in their own Yeez folder (never on yeez.ai).

  python3 yeez_data.py ingest FILE [FILE ...] --site example.com --platform newsbreak   # fold exports in
  python3 yeez_data.py report --site example.com [--veins veins.json] [--top 50]       # what's working (JSON)
  python3 yeez_data.py review --site example.com [--veins veins.json] [--weeks 8]      # the weekly views analysis (JSON)
  python3 yeez_data.py income add --site example.com --source newsbreak --month 2026-10 --amount 812.40 [--views N]   # log income
  python3 yeez_data.py income import --file earnings.csv [--site example.com]          # source, month, amount (+views) columns
  python3 yeez_data.py income articles --file statement.csv --site example.com --source newsbreak [--month 2026-10]   # per-article earnings
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
from datetime import date, datetime, timedelta, timezone

WORK = os.environ.get("YEEZ_WORK", os.path.join(os.getcwd(), "yeez-work"))
DATA = os.path.join(WORK, "data")
ART = os.path.join(DATA, "articles.csv")
DAY = os.path.join(DATA, "daily.csv")
PULLS = os.path.join(DATA, "pulls.csv")
INC = os.path.join(DATA, "income.csv")
INC_COLS = ["site", "source", "month", "amount", "views", "note", "updated"]
EARN = os.path.join(DATA, "earnings_articles.csv")
EARN_COLS = ["site", "source", "id", "title", "month", "amount", "views", "updated"]
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



# ---------------------------------------------------------------------------
# income: what each source paid, month by month (platform revenue share, ads, newsletter,
# sponsors, affiliates, own products). Optional; the review uses it for real RPMs and money per slot.
# ---------------------------------------------------------------------------
def income_add(site, source, month, amount, views, note):
    rows = load(INC, lambda r: (r["site"], r["source"].lower(), r["month"]))
    site = site_of(site); m = month[:7]
    if not re.match(r"\d{4}-\d{2}$", m): print(json.dumps({"ok": False, "error": "month must be YYYY-MM"})); return
    rows[(site, source.lower(), m)] = {"site": site, "source": source, "month": m, "amount": f"{float(re.sub(r'[,$]', '', str(amount))):.2f}",
                                       "views": num(views) if views else "", "note": note or "", "updated": datetime.now(timezone.utc).strftime("%Y-%m-%d")}
    write(INC, INC_COLS, sorted(rows.values(), key=lambda r: (r["site"], r["month"], r["source"])))
    print(json.dumps({"ok": True, "saved": rows[(site, source.lower(), m)]}))


def income_import(path, site):
    head, rows = read_table(path)
    iS, iM, iA = col(head, r"source", r"platform", r"stream"), col(head, r"month", r"date", r"period"), col(head, r"amount", r"earn", r"revenue", r"paid", r"income")
    iV, iSite = col(head, r"views", r"pageviews"), col(head, r"^site")
    if min(iS, iM, iA) < 0: print(json.dumps({"ok": False, "error": "need source, month and amount columns", "columns": head})); return
    n = 0
    for c in rows:
        if len(c) <= max(iS, iM, iA) or not c[iA].strip(): continue
        income_add((c[iSite] if iSite >= 0 and c[iSite] else site) or "", c[iS], c[iM][:7], c[iA], c[iV] if iV >= 0 and len(c) > iV else "", "imported")
        n += 1
    print(json.dumps({"ok": True, "imported": n}))


def income_articles(path, site, source, month):
    """Per-article (or per-headline) earnings from a statement export: title + earnings columns, optional views, date, id."""
    head, rows = read_table(path)
    iT = col(head, r"^title$", r"headline", r"title", r"content name")
    iA = col(head, r"earn", r"revenue", r"rev share", r"payout", r"amount", r"income", r"\$")
    iV = col(head, r"^page_?views?$", r"^views$", r"views", r"impressions")
    iD = col(head, r"month", r"date", r"period", r"publish")
    iI = col(head, r"doc_?id", r"^id$", r"content id", r"article id")
    if iT < 0 or iA < 0: print(json.dumps({"ok": False, "error": "need title and earnings columns", "columns": head})); return
    have = load(EARN, lambda r: (r["site"], r["source"].lower(), r["id"], r["month"]))
    site = site_of(site); n = 0; now = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    for c in rows:
        if len(c) <= max(iT, iA) or not c[iT].strip(): continue
        try: amt = float(re.sub(r"[,$\s]", "", c[iA]) or 0)
        except ValueError: continue
        m = (c[iD][:7] if iD >= 0 and len(c) > iD and re.match(r"\d{4}-\d{2}", c[iD]) else (month or "")[:7])
        ident = (c[iI] if iI >= 0 and len(c) > iI and c[iI] else c[iT]).strip()[:200]
        k = (site, source.lower(), ident, m)
        old = have.get(k)
        have[k] = {"site": site, "source": source, "id": ident, "title": re.sub(r"\s+", " ", c[iT]).strip()[:300], "month": m,
                   "amount": f"{amt + (float(old['amount']) if old and old.get('updated') == now else 0):.4f}",
                   "views": num(c[iV]) if iV >= 0 and len(c) > iV else "", "updated": now}
        n += 1
    write(EARN, EARN_COLS, sorted(have.values(), key=lambda r: (r["site"], r["source"], r["month"], r["title"])))
    print(json.dumps({"ok": True, "rows": n, "file": EARN}))


def _income(site, plat_views):
    rows = [r for r in load(INC, lambda r: (r["site"], r["source"].lower(), r["month"])).values() if r["site"] == site]
    if not rows: return None
    by_m = defaultdict(dict)
    for r in rows: by_m[r["month"]][r["source"]] = float(r["amount"] or 0)
    months = []
    for m in sorted(by_m):
        rpms = {}
        for src, amt in by_m[m].items():
            row = next(x for x in rows if x["month"] == m and x["source"] == src)
            v = num(row["views"]) or plat_views.get((src.lower(), m), 0)
            if v: rpms[src] = round(amt / v * 1000, 2)
        months.append({"month": m, "total": round(sum(by_m[m].values()), 2), "by_source": by_m[m], "rpm_by_source": rpms})
    return {"by_month": months[-12:], "sources": sorted({r["source"] for r in rows})}


# ---------------------------------------------------------------------------
# review: the weekly views analysis. Everything the weekly review reasons from,
# computed over every article, not a sample. Read-only on the data.
# ---------------------------------------------------------------------------
GOALS = os.path.join(WORK, "goals.json")
TESTS = os.path.join(WORK, "tests.json")
FEEL = ["shock", "stun", "heartbreak", "devastat", "furious", "outrage", "terrif", "horrif", "tragic", "emotional", "tears",
        "brave", "hero", "miracle", "incredible", "unbeliev", "surpris", "secret", "myster", "revealed", "reveal", "finally",
        "warning", "warns", "urgent", "never", "nobody", "no one", "what happened", "the reason", "why ", "how ", "this is",
        "you won't", "can't believe", "turns out", "instead", "but then", "until", "refused", "slammed", "banned"]


def _d(s):
    try:
        return date.fromisoformat((s or "")[:10])
    except ValueError:
        return None


def _feats(t):
    tl = t.lower(); words = t.split(); n = len(t)
    f = {}
    f["length " + ("under 50" if n < 50 else "50-69" if n < 70 else "70-89" if n < 90 else "90-109" if n < 110 else "110+") + " chars"] = True
    f["words " + ("under 8" if len(words) < 8 else "8-12" if len(words) <= 12 else "13-18" if len(words) <= 18 else "19+")] = True
    f["opens with a number"] = bool(re.match(r"^[\$]?\d", t))
    f["has a number"] = bool(re.search(r"\d", t))
    f["has a dollar amount"] = "$" in t
    f["question"] = "?" in t
    f["has a colon"] = ":" in t
    f["has a comma"] = "," in t
    f["has a quote"] = bool(re.search(r"[\"'‘’“”].{3,}[\"'‘’“”]", t))
    f["opens with a quote"] = bool(re.match(r"^[\"'‘“]", t))
    f["emotion or curiosity word"] = any(w in tl for w in FEEL)
    f["says / according to"] = bool(re.search(r"\b(says|said|say|according to|reports?)\b", tl))
    f["you / your"] = bool(re.search(r"\byou(r|'re)?\b", tl))
    f["opens with a person's name"] = bool(re.match(r"^[A-Z][a-z]+ (?:[A-Z]\.? )?[A-Z][a-z'\-]+[,\s]", t)) and not re.match(r"^(The|This|These|A|An|New|How|Why|What|When|Your|After|Here)\b", t)
    f["opens with 'A' or 'An' (unnamed person)"] = bool(re.match(r"^(A|An) ", t))
    f["two sentences"] = bool(re.search(r"[a-z0-9]\. [A-Z]", t))
    return f


def _avg(xs):
    return sum(xs) / len(xs) if xs else 0


def _med(xs):
    return pct(xs, .5) if xs else 0


INCOME = None


def review(site, veins_path, weeks, min_age):
    site = site_of(site)
    today = date.today()
    allarts = [r for r in load(ART, lambda r: (r["platform"], r["id"])).values() if r["site"] == site]
    if not allarts:
        print(json.dumps({"ok": False, "site": site, "note": "No numbers for this site yet. Pull or ingest first (learn skill)."})); return
    days = [r for r in load(DAY, lambda r: (r["site"], r["platform"], r["day"])).values() if r["site"] == site]
    goals = json.load(open(GOALS)).get("sites", {}).get(site) if os.path.exists(GOALS) else None
    tests = [t for t in (json.load(open(TESTS)).get("tests", []) if os.path.exists(TESTS) else []) if site_of(t.get("site", site)) == site]
    veins = json.load(open(veins_path)) if veins_path and os.path.exists(veins_path) else []
    out = {"ok": True, "site": site, "today": today.isoformat(), "min_age_days": min_age, "goal": goals, "platforms": []}
    pv = defaultdict(int)
    for r in days:
        if _d(r["day"]): pv[(r["platform"].lower(), r["day"][:7])] += num(r["views"])
    global INCOME
    INCOME = _income(site, pv)
    if INCOME:
        posts_m = defaultdict(int)
        for r in allarts:
            if _d(r["published"]): posts_m[r["published"][:7]] += 1
        for mrow in INCOME["by_month"]:
            n = posts_m.get(mrow["month"], 0)
            mrow["posts"] = n; mrow["money_per_post_all_sources"] = round(mrow["total"] / n, 2) if n else None
        out["income"] = INCOME
    for plat in sorted({r["platform"] for r in allarts}):
        arts = [r for r in allarts if r["platform"] == plat]
        for r in arts:
            r["v"] = num(r["views"]); r["d"] = _d(r["published"])
        dated = [r for r in arts if r["d"]]
        aged = [r for r in dated if (today - r["d"]).days >= min_age]
        P = {"platform": plat, "articles": len(arts), "articles_with_dates": len(dated), "aged_articles": len(aged)}
        if len(aged) < 20:
            P["note"] = "Fewer than 20 articles old enough to judge on this platform; skip its analysis."
            out["platforms"].append(P); continue
        # lift: views vs the mean of the same calendar month (so one good or bad month can't fake a pattern)
        mon = defaultdict(list)
        for r in aged: mon[r["d"].strftime("%Y-%m")].append(r["v"])
        mmean = {m: _avg(v) for m, v in mon.items() if len(v) >= 10}
        for r in aged:
            mm = mmean.get(r["d"].strftime("%Y-%m")); r["lift"] = (r["v"] / mm) if mm else None
        L = [r for r in aged if r["lift"] is not None]
        recent180 = [r for r in aged if (today - r["d"]).days <= 180] or aged
        v180 = [r["v"] for r in recent180]
        bands = {"hit": pct(v180, .90), "big_hit": pct(v180, .97), "monster": pct(v180, .99)}
        P["hit_bands_from_last_180_days"] = bands
        hit = bands["hit"]
        # 1. the outcome: discrete calendar months, then the last weeks
        months = defaultdict(list)
        for r in dated: months[r["d"].strftime("%Y-%m")].append(r["v"])
        dmon = defaultdict(list)
        for r in days:
            if r["platform"] == plat and _d(r["day"]): dmon[r["day"][:7]].append(num(r["views"]))
        mrows = []
        for m in sorted(set(months) | set(dmon))[-18:]:
            v = months.get(m, [])
            mrows.append({"month": m, "posts": len(v), "views_of_those_posts": sum(v), "views_per_post": round(_avg(v)), "median_post": _med(v),
                          "hits": sum(x >= hit for x in v), "hit_rate": round(sum(x >= hit for x in v) / len(v), 3) if v else 0,
                          "avg_daily_views_dashboard": round(_avg(dmon[m])) if dmon.get(m) else None, "days_in_dashboard": len(dmon.get(m, []))})
        full = [x for x in mrows if x["month"] < today.strftime("%Y-%m")]
        P["by_month"] = mrows
        P["best_month_by_views_per_post"] = max(full, key=lambda x: x["views_per_post"])["month"] if full else None
        P["best_month_by_daily_views"] = max([x for x in full if x["avg_daily_views_dashboard"]], key=lambda x: x["avg_daily_views_dashboard"], default={}).get("month")
        dd = sorted([(r["day"], num(r["views"])) for r in days if r["platform"] == plat])
        if dd:
            vals = [v for _, v in dd]
            l7, p7, p28 = _avg(vals[-7:]), _avg(vals[-14:-7]), _avg(vals[-35:-7])
            best7 = max((_avg(vals[i:i + 7]), dd[i][0]) for i in range(0, max(1, len(vals) - 6)))
            P["daily"] = {"last_7_avg": round(l7), "prev_7_avg": round(p7), "prev_28_avg": round(p28), "best_7_day_avg_ever": round(best7[0]), "best_7_day_week_starting": best7[1],
                          "last_28_days": [{"day": d, "views": v} for d, v in dd[-28:]], "days_on_record": len(dd), "first_day": dd[0][0]}
        # weekly: posts, views per post, hits (posts old enough only)
        wk = []
        for i in range(weeks, 0, -1):
            end = today - timedelta(days=7 * (i - 1) + min_age); start = end - timedelta(days=7)
            w = [r for r in dated if start < r["d"] <= end]
            wv = [r["v"] for r in w]
            dv = [num(r["views"]) for r in days if r["platform"] == plat and _d(r["day"]) and start < _d(r["day"]) <= end]
            wk.append({"week_ending": end.isoformat(), "posts": len(w), "posts_per_day": round(len(w) / 7, 1), "views_per_post": round(_avg(wv)), "median_post": _med(wv),
                       "hits": sum(x >= bands["hit"] for x in wv), "big_hits": sum(x >= bands["big_hit"] for x in wv), "monsters": sum(x >= bands["monster"] for x in wv),
                       "avg_daily_views_dashboard": round(_avg(dv)) if dv else None})
        P["by_week_old_enough_to_judge"] = wk
        # 2. goal math (steady state: daily views ~= posts per day x views per post)
        last14 = [r for r in dated if 0 <= (today - r["d"]).days < 14]
        ppd = len(last14) / 14
        recent_aged = [r["v"] for r in aged if (today - r["d"]).days <= min_age + 28]
        vpp = _avg(recent_aged)
        best_vpp = max((x["views_per_post"] for x in full if x["posts"] >= 30), default=0)
        cur = P.get("daily", {}).get("last_7_avg") or round(ppd * vpp)
        G = {"current_views_per_day": cur, "current_from": "dashboard daily totals" if P.get("daily") else "posts x views per post (no daily totals pulled)",
             "posts_per_day_last_14": round(ppd, 1), "views_per_post_last_4_weeks": round(vpp), "best_month_views_per_post": best_vpp}
        # older posts keep earning: k = today's daily views / what new posts alone would explain
        k = (cur / (ppd * vpp)) if (P.get("daily") and ppd and vpp) else 1.0
        G["older_posts_factor"] = round(k, 2)
        rpm = float((goals or {}).get("rpm", {}).get(plat) or 0)
        if not rpm and INCOME:
            for mrow in reversed([m_ for m_ in INCOME["by_month"] if m_["month"] < today.strftime("%Y-%m")] or INCOME["by_month"]):
                hit_r = next((v for k2, v in mrow["rpm_by_source"].items() if k2.lower() == plat), None)
                if hit_r: rpm = hit_r; G["rpm_from"] = "income log, " + mrow["month"]; break
        if rpm:
            G["rpm"] = rpm; G["money_per_day_now"] = round(cur * rpm / 1000, 2); G["money_per_post_now"] = round(vpp * k * rpm / 1000, 2)
        gv = (goals or {}).get("views_per_day")
        if not gv and rpm and (goals or {}).get("money_per_month"):
            gv = float(goals["money_per_month"]) / 30.4 / rpm * 1000
            G["goal_from_money"] = {"money_per_month": goals["money_per_month"], "rpm": rpm, "views_per_day_it_takes": round(gv)}
        if gv:
            g = float(gv)
            G["goal_views_per_day"] = g; G["gap_per_day"] = round(g - cur); G["goal_vs_now"] = round(g / cur, 2) if cur else None
            need_vpp = (g / (ppd * k)) if ppd else None
            G["views_per_post_needed_at_current_volume"] = round(need_vpp) if need_vpp else None
            G["views_per_post_needed_vs_now"] = round(need_vpp / vpp, 2) if need_vpp and vpp else None
            G["that_has_been_done"] = bool(need_vpp and need_vpp <= best_vpp)
            G["posts_per_day_needed_at_current_views_per_post"] = round(g / (vpp * k), 1) if vpp else None
            hv = [r["v"] for r in aged if r["v"] >= bands["hit"] and (today - r["d"]).days <= 180]
            G["avg_views_of_a_hit"] = round(_avg(hv))
            G["hits_per_week_now"] = round(_avg([w["hits"] for w in wk[-4:]]), 1)
            G["extra_hits_per_week_needed"] = round(max(0, g - cur) * 7 / (_avg(hv) * k), 1) if hv else None
            if goals.get("by"):
                bd = _d(goals["by"]); G["days_left"] = (bd - today).days if bd else None
        P["goal_math"] = G
        # 3. headline shape: every aged article, lift within its month
        feat = defaultdict(lambda: {"with": [], "without": []})
        for r in L:
            fs = _feats(r["title"])
            for k in set(list(fs.keys())):
                feat[k]["with" if fs[k] else "without"].append(r)
        shapes = []
        for k, g2 in feat.items():
            a, b = g2["with"], g2["without"]
            if len(a) < 15: continue
            row = {"shape": k, "posts": len(a), "lift": round(_avg([r["lift"] for r in a]), 2), "median_lift": round(_med([r["lift"] for r in a]), 2),
                   "hit_rate": round(sum(r["v"] >= hit for r in a) / len(a), 3),
                   "share_of_last_28_days": round(sum(1 for r in a if (today - r["d"]).days <= 28 + min_age) / max(1, sum(1 for r in L if (today - r["d"]).days <= 28 + min_age)), 2)}
            if len(b) >= 15:
                row["without_lift"] = round(_avg([r["lift"] for r in b]), 2); row["without_hit_rate"] = round(sum(r["v"] >= hit for r in b) / len(b), 3)
            shapes.append(row)
        P["headline_shapes"] = sorted(shapes, key=lambda x: -x["lift"])
        P["site_hit_rate"] = round(sum(r["v"] >= hit for r in L) / len(L), 3)
        # hours
        hrs = defaultdict(list)
        for r in L:
            m = re.match(r"\d{4}-\d{2}-\d{2}[ T](\d{2})", r["published"] or "")
            if m: hrs[int(m.group(1))].append(r)
        P["by_publish_hour"] = [{"hour": h, "posts": len(v), "lift": round(_avg([r["lift"] for r in v]), 2), "hit_rate": round(sum(r["v"] >= hit for r in v) / len(v), 3)}
                                for h, v in sorted(hrs.items()) if len(v) >= 10]
        # real earnings per article, where a statement gave them
        earn = defaultdict(float)
        for e in load(EARN, lambda r: (r["site"], r["source"].lower(), r["id"], r["month"])).values():
            if e["site"] == site and e["source"].lower() == plat: earn[e["title"].lower()] += float(e["amount"] or 0)
        for r in L: r["earned"] = earn.get(r["title"].lower())
        paid = [r for r in L if r["earned"] is not None]
        if paid:
            P["earnings_per_article"] = {"articles_matched": len(paid), "avg_per_article": round(_avg([r["earned"] for r in paid]), 2),
                                         "top_earners": [{"title": r["title"], "earned": round(r["earned"], 2), "views": r["v"]} for r in sorted(paid, key=lambda r: -r["earned"])[:25]],
                                         "real_rpm": round(sum(r["earned"] for r in paid) / max(1, sum(r["v"] for r in paid)) * 1000, 2)}
        # veins: value vs slots
        if veins:
            vr = []; seen = set()
            rec = [r for r in L if (today - r["d"]).days <= 28 + min_age]
            for vn in veins:
                kws = [k.lower() for k in vn.get("keywords", []) if k]
                h = [r for r in L if any(k in r["title"].lower() for k in kws)]
                for r in h: seen.add(id(r))
                if not h: continue
                hr = [r for r in rec if any(k in r["title"].lower() for k in kws)]
                lm = defaultdict(list)
                for r in h: lm[r["d"].strftime("%Y-%m")].append(r["lift"])
                vr.append({"vein": vn["name"], "posts": len(h), "lift": round(_avg([r["lift"] for r in h]), 2),
                           "dollars_per_post": round(_avg([r["v"] for r in h]) * rpm / 1000, 2) if rpm else None,
                           "actual_dollars_per_post": round(_avg([r["earned"] for r in h if r.get("earned") is not None]), 2) if any(r.get("earned") is not None for r in h) else None, "hit_rate": round(sum(r["v"] >= hit for r in h) / len(h), 3),
                           "share_of_recent_slots": round(len(hr) / max(1, len(rec)), 3), "recent_lift": round(_avg([r["lift"] for r in hr]), 2) if hr else None,
                           "lift_by_month": [{"month": m, "posts": len(v), "lift": round(_avg(v), 2)} for m, v in sorted(lm.items())[-6:]],
                           "best": max(h, key=lambda r: r["v"])["title"]})
            un = [r for r in L if id(r) not in seen]
            if un: vr.append({"vein": "(not in any vein)", "posts": len(un), "lift": round(_avg([r["lift"] for r in un]), 2), "hit_rate": round(sum(r["v"] >= hit for r in un) / len(un), 3)})
            P["veins_value_vs_slots"] = sorted(vr, key=lambda x: -x["lift"])
        # every post of the last 4 weeks old enough to judge, best to worst: the review reads all of them
        P["last_4_weeks_every_post"] = [{"published": r["published"][:16], "views": r["v"], "lift": round(r["lift"], 2) if r["lift"] else None, "title": r["title"]}
                                        for r in sorted([r for r in L if (today - r["d"]).days <= 28 + min_age], key=lambda r: -r["v"])]
        # re-run candidates: proven winners not repeated lately
        old = sorted([r for r in aged if (today - r["d"]).days > 45 and r["v"] >= bands["big_hit"]], key=lambda r: -r["v"])
        P["proven_winners_to_rerun"] = [{"published": r["published"][:10], "views": r["v"], "title": r["title"]} for r in old[:40]]
        # distribution: posts the platform did not make live
        nl = defaultdict(int)
        for r in dated:
            if r["status"] and r["status"] not in ("2", "1", "live", "published"): nl[r["d"].strftime("%Y-%m")] += 1
        P["not_made_live_by_month"] = dict(sorted(nl.items())[-6:])
        # tests
        tres = []
        for t in tests:
            st = _d(t.get("started")); en = _d(t.get("ends"))
            if not st: continue
            kws = [k.lower() for k in t.get("match", {}).get("keywords", [])]; shp = t.get("match", {}).get("shape")
            win = [r for r in L if r["d"] >= st]
            res = {"id": t.get("id"), "name": t.get("name"), "started": t.get("started"), "ends": t.get("ends"), "status": t.get("status", "running")}
            if kws or shp:
                inn = [r for r in win if (kws and any(k in r["title"].lower() for k in kws)) or (shp and _feats(r["title"]).get(shp))]
                outn = [r for r in win if r not in inn]
                res.update({"test_posts_old_enough": len(inn), "test_lift": round(_avg([r["lift"] for r in inn]), 2), "rest_lift": round(_avg([r["lift"] for r in outn]), 2),
                            "test_hit_rate": round(sum(r["v"] >= hit for r in inn) / len(inn), 3) if inn else None,
                            "rest_hit_rate": round(sum(r["v"] >= hit for r in outn) / len(outn), 3) if outn else None})
            else:
                before = [num(r["views"]) for r in days if r["platform"] == plat and _d(r["day"]) and st - timedelta(days=28) <= _d(r["day"]) < st]
                after = [num(r["views"]) for r in days if r["platform"] == plat and _d(r["day"]) and _d(r["day"]) >= st]
                bp = [r["v"] for r in aged if st - timedelta(days=28) <= r["d"] < st]; ap_ = [r["v"] for r in aged if r["d"] >= st]
                res.update({"daily_views_28_days_before": round(_avg(before)), "daily_views_since": round(_avg(after)), "days_since": len(after),
                            "views_per_post_before": round(_avg(bp)), "views_per_post_since": round(_avg(ap_)), "posts_since_old_enough": len(ap_)})
            res["enough_to_judge"] = bool((res.get("test_posts_old_enough", 0) >= 10) or (res.get("posts_since_old_enough", 0) >= 20 and res.get("days_since", 0) >= 7))
            res["past_end_date"] = bool(en and today >= en)
            tres.append(res)
        P["tests"] = tres
        out["platforms"].append(P)
    out["note"] = ("lift = an article's views / the average of articles published the same calendar month on the same platform (1.0 = average). "
                   "Only articles at least min_age_days old are judged. Hit bands come from this site's own last 180 days. "
                   "The current month is always biased low. Read every list; nothing here is a sample.")
    print(json.dumps(out, indent=1, default=str))


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)
    a = sub.add_parser("ingest"); a.add_argument("files", nargs="+"); a.add_argument("--site", required=True); a.add_argument("--platform", required=True)
    b = sub.add_parser("report"); b.add_argument("--site", required=True); b.add_argument("--veins"); b.add_argument("--top", type=int, default=50)
    c = sub.add_parser("review"); c.add_argument("--site", required=True); c.add_argument("--veins"); c.add_argument("--weeks", type=int, default=8); c.add_argument("--min-age", type=int, default=7)
    i = sub.add_parser("income"); i.add_argument("action", choices=["add", "import", "articles", "show"]); i.add_argument("--site", default=""); i.add_argument("--source"); i.add_argument("--month")
    i.add_argument("--amount"); i.add_argument("--views"); i.add_argument("--note"); i.add_argument("--file")
    sub.add_parser("status")
    x = ap.parse_args()
    if x.cmd == "ingest": ingest(x.files, x.site, x.platform)
    elif x.cmd == "report": report(x.site, x.veins, x.top)
    elif x.cmd == "review": review(x.site, x.veins, x.weeks, x.min_age)
    elif x.cmd == "income":
        if x.action == "add": income_add(x.site, x.source, x.month, x.amount, x.views, x.note)
        elif x.action == "import": income_import(x.file, x.site)
        elif x.action == "articles": income_articles(x.file, x.site, x.source, x.month)
        else: print(json.dumps(_income(site_of(x.site), {}) or {"ok": False, "note": "no income logged"}, indent=1))
    else: status()
