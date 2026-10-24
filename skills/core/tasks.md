# The Yeez tasks

Yeez runs as a chain of scheduled tasks in the buyer's AI app, one after another each evening, each with a clear job. Every task first checks that what it needs is ready. If it isn't, it does the missing step itself (or holds and says so), so a slow or skipped task never breaks the next one.

| Order | Task (prompt) | Goal | Needs | Produces |
|---|---|---|---|---|
| 1 | **Learn** (`/yeez:learn daily`) | Know what's winning right now | A browser logged in to NewsBreak (optional); the Yeez folder | Fresh numbers in the folder; today's marching orders in each site profile |
| 2 | **Headlines** (`/yeez:headlines`) | Pick tomorrow's stories and headlines most likely to get views | Today's marching orders (if missing or older than a day: run Learn's daily mode first) | Ranked, sourced headlines saved per site, up to each site's daily count |
| 3 | **Articles** (`/yeez:articles`) | Turn every picked headline into a verified, sourced, scheduled article | Today's picked headlines (if none: run Headlines first) | Scheduled posts on each site at its publish times; held stories with reasons |
| 3b | **Search** (`/yeez:search`) | One article built to rank on Google, waiting for the buyer's approval | Search Console connected; search articles left this week | One search article pending approval |
| 4a | **Social learn** (`/yeez:social learn`) | Know what's getting shares and reach on each Page | Connected Pages | Learn notes per Page in the Yeez folder |
| 4b | **Social write** (`/yeez:social write`) | Tomorrow's posts for every Page, within the money-safety and repost rules | Today's learn notes; tomorrow's scheduled articles (for news cards and first-comment links) | A written queue per Page |
| 4c | **Social build** (`/yeez:social build`) | Render every card and reel, check every image | The written queue | Rendered media |
| 4d | **Social post** (`/yeez:social post`) | Schedule every post natively on Facebook and Instagram | Built items | Scheduled posts, recorded on the dashboard |
| Hourly, daytime | **Social now** (`/yeez:social now`) | Post stories and Instagram items at their times (they can't be scheduled ahead) | Today's built queue | Those items posted; only created when the buyer has stories or Instagram |
| 5 | **Newsletter** (`/yeez:newsletter`, on send days) | The next issue from the best stories | Newsletter settings; the day's articles | A finished issue (beehiiv draft via API, or ready to paste) |
| Mondays, first | **Weekly review** (`/yeez:review`) | Learn the week, update the rules, update the earn-back tracker | The week's numbers (runs Learn's weekly mode itself) | Updated site profiles, learned headline rules, the weekly review on the dashboard |

`/yeez:run` runs the whole chain in one session, for apps that can only schedule one task or when the buyer wants to run it all now.

## Timing

Set up in setup's last step. Start the chain in the evening before the first publish time, and leave a gap after each task so it can finish before the next one starts:

- **Learn:** 20 minutes.
- **Headlines:** 10 minutes plus 1 minute per article across all sites.
- **Articles:** 3 minutes per article across all sites, plus 20 minutes. Above 40 articles a night, add a second Articles task (same prompt) after the first one's window: it picks up every picked headline the first didn't finish, so nothing is written twice.
- **Search:** 20 minutes, right after Articles. Skip it when no site has Search Console connected.
- **Social:** learn 5 minutes per Page plus 5; write 5 minutes per Page plus 10; build 4 minutes per Page plus 2 per reel; post 3 minutes per Page plus 5. Under 3 Pages, one `/yeez:social` task (all four steps) is fine: give it 15 minutes per Page plus 15.
- **Newsletter:** 20 minutes, only on the day before each send day.
- **Weekly review:** Monday, starting an hour before Learn, so the week's rules are updated before the night's headlines.

Example, one site at 30 articles a day and 3 Pages, first publish at 6:00 AM: Learn 7:00 PM → Headlines 7:20 PM → Articles 8:00 PM → Search 9:50 PM → Social learn 10:10 PM → write 10:30 PM → build 10:55 PM → post 11:15 PM → Newsletter 11:30 PM (send days only).

Facebook posts are scheduled for tomorrow, so the social tasks can also run in the morning if the evening is crowded.

Each app schedules differently (Claude scheduled tasks, Codex automations, Cursor Automations, cron); `app_guide` says how, and whether tasks run only while the computer is on and the app is open.

## Every task, every time

1. Read [rules.md](rules.md).
2. Check its inputs are ready (the "Needs" column). Missing: do the earlier step itself, or hold and say so.
3. Do its job, within [platforms/](platforms/) for every platform the site publishes to.
4. Never ask anything when unattended. Put anything the buyer needs to know at the top of its short summary.
