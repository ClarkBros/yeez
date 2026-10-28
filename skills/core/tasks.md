# The Yeez tasks

Yeez runs as scheduled tasks in the buyer's AI app, each with a clear job: Learn in the early afternoon while the buyer is usually at the computer, then the writing chain one task after another in the evening. Every task first checks that what it needs is ready. If it isn't, it does the missing step itself (or holds and says so), so a slow or skipped task never breaks the next one.

| Order | Task (prompt) | Goal | Needs | Produces |
|---|---|---|---|---|
| 1 | **Learn** (`/yeez:learn daily`), around 2 PM | Pull the latest numbers, grade the tests, know what's winning right now | The computer on, the app open, NewsBreak and the other dashboards logged in in the app's browser (the buyer is usually there to log in if asked); the Yeez folder | Fresh numbers in the folder; graded tests; today's marching orders in each site profile |
| 2 | **Headlines** (`/yeez:headlines`) | Pick tomorrow's stories and headlines most likely to get views, with about a quarter of the day as tests | Today's marching orders (if missing or older than a day: run Learn's daily mode first) | Ranked, sourced headlines saved per site, up to each site's daily count |
| 3 | **Articles** (`/yeez:articles`) | Turn every picked headline into a verified, sourced, scheduled article | Today's picked headlines (if none: run Headlines first) | Scheduled posts on each site at its publish times; held stories with reasons |
| 3b | **Search** (`/yeez:search`), only when the buyer turned on search articles | One article built to rank on Google, waiting for the buyer's approval | Search articles turned on for a site (`search_per_week` above 0) and left this week | One search article pending approval |
| 4a | **Social learn** (`/yeez:social learn`) | Know what's getting shares and reach on each Page | Connected Pages | Learn notes per Page in the Yeez folder |
| 4b | **Social write** (`/yeez:social write`) | Tomorrow's posts for every Page, within the money-safety and repost rules | Today's learn notes; tomorrow's scheduled articles (for news cards and first-comment links) | A written queue per Page |
| 4c | **Social build** (`/yeez:social build`) | Render every card and reel, check every image | The written queue | Rendered media |
| 4d | **Social post** (`/yeez:social post`) | Schedule every post natively on Facebook and Instagram | Built items | Scheduled posts, recorded on the dashboard |
| Hourly, daytime | **Social now** (`/yeez:social now`) | Post stories and Instagram items at their times (they can't be scheduled ahead) | Today's built queue | Those items posted; only created when the buyer has stories or Instagram |
| 5 | **Newsletter** (`/yeez:newsletter`, on send days) | The next issue from the best stories | Newsletter settings; the day's articles | A finished issue (beehiiv draft via API, or ready to paste) |
| Mondays, after Learn | **Weekly review** (`/yeez:review`) | Learn the week, update the rules, report days on plan | The week's numbers (runs Learn's weekly mode itself) | Updated site profiles, learned headline rules, the weekly review on the dashboard |

`/yeez:run` runs the whole chain in one session, for apps that can only schedule one task or when the buyer wants to run it all now.

## Timing

Set up in setup's last step. **Learn runs at 2:00 PM** in the buyer's timezone (it pulls the dashboards in the browser, so it runs when the buyer is usually at the computer and can log in if asked). Start the evening chain at least 3 hours before bedtime and before the first publish time, and leave a gap after each task so it can finish before the next one starts:

- **Learn:** at 2:00 PM, 30 minutes per site with NewsBreak (pulls, tests and marching orders). Learn has to finish before Headlines starts, since Headlines reads the marching orders Learn saves.
- **Headlines:** 10 minutes plus 1 minute per article across all sites.
- **Articles:** 3 minutes per article across all sites, plus 20 minutes. One Articles task handles every site's articles, however many there are.
- **Search:** 20 minutes, right after Articles. Only when the buyer said yes to search articles (setup asks); otherwise there is no Search task.
- **Social:** learn 5 minutes per Page plus 5; write 5 minutes per Page plus 10; build 4 minutes per Page plus 2 per reel; post 3 minutes per Page plus 5. Under 3 Pages, one `/yeez:social` task (all four steps) is fine: give it 15 minutes per Page plus 15.
- **Newsletter:** 20 minutes, only on the day before each send day.
- **Weekly review:** Monday, after Learn has finished: Learn's start time plus 30 minutes per site, plus 15 minutes (one site: 2:45 PM; three sites: 3:45 PM). Give it 45 minutes before Headlines, so the week's rules are updated before the night's headlines.

Example, one site at 30 articles a day and 3 Pages, first publish at 6:00 AM: Learn 2:00 PM (Mondays: Weekly review 2:45 PM). Evening: Headlines 7:00 PM → Articles 8:00 PM → Social learn 9:50 PM → write 10:10 PM → build 10:35 PM → post 10:55 PM → Newsletter 11:10 PM (send days only).

Facebook posts are scheduled for tomorrow, so the social tasks can also run in the morning if the evening is crowded.

**Learn needs the computer:** it opens NewsBreak and the other dashboards in the AI app's browser, so the buyer's computer must be on, the app open, and the buyer logged in to each dashboard in that browser. That's why it runs at 2 PM, not overnight. Tell the buyer this when the tasks are set up.

Each app schedules differently (Claude scheduled tasks, Codex automations, Cursor Automations, cron); `app_guide` says how, and whether tasks run only while the computer is on and the app is open.

## Task instructions hold only the command

Each scheduled task's instructions are exactly its prompt from the table (`/yeez:headlines`, and so on), nothing else. Yeez updates reach the buyer only through the skills and their yeez.ai account, so anything written into a task would freeze an old version or fight a newer rule. The buyer's own standing rules for a site ("no celebrity gossip", "always link our recipe page") are saved with `save_site_profile` as `buyer_rules`, and every run reads them from `get_site_brief`.

## Every task, every time

1. Read [rules.md](rules.md).
2. Check its inputs are ready (the "Needs" column). Missing: do the earlier step itself, or hold and say so.
3. Do its job, within [platforms/](platforms/) for every platform the site publishes to.
4. Never ask anything when unattended. Put anything the buyer needs to know at the top of its short summary.
