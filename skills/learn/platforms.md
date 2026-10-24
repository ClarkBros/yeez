# Getting each platform's numbers

Always take the widest date range the platform allows (all time if it offers it). Yeez merges re-uploads, so overlapping files are fine.

| Platform | How Yeez gets it |
|---|---|
| NewsBreak | `scripts/newsbreak-pull.js` in the logged-in https://mp.newsbreak.com tab. Every article, all time, plus daily totals. |
| Google Search Console | Read directly once the buyer adds Yeez's email as a Restricted user (setup's search step). |
| MSN | https://www.msn.com/en-us/partnerhub — the content analytics report, widest range, export CSV. |
| Yahoo | The Yahoo partner/creator dashboard the buyer was given at approval — article performance report, export. |
| SmartNews | The SmartNews publisher portal — article report, export. |
| Google Analytics (GA4) | https://analytics.google.com — Reports → Engagement → Pages and screens → widest date range → Share this report → Download file → CSV. |
| WordPress stats | Jetpack Stats (or the site's stats plugin) → Posts & pages → widest range → download CSV. |

What a usable export needs: a **title** column and a **views** (page views, or clicks) column. A publish date, impressions and the platform's own article id make it better. Daily exports with one row per article per day are fine: Yeez adds the days up per article.

Menus move. If an export isn't where this says, open the dashboard and look for "Export", "Download" or a download icon on the content or analytics report; the buyer can always ask their AI app to find it with them.

Every file goes through `scripts/yeez_data.py ingest` into the buyer's Yeez folder.
