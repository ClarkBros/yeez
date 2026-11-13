---
name: review
description: The Yeez weekly review. Pulls the week's numbers, then does a deep views review for every site - where views stand against the buyer's goal, what is driving them up or down, which rules help or cost views, and the options that would move views most - and walks the buyer through it so they decide the big changes. Also tunes headline rules, logs earnings, and reports days on plan. Use when the user types /yeez:review, asks how the week went, asks why views are flat or down, wants more views, wants to set or change a views goal, wants to log earnings or views, or as part of the Monday /yeez:run.
---

# Yeez weekly review

Read [../core/rules.md](../core/rules.md) first: who Yeez is and the rules it never breaks.

## What this review is for

The buyer runs Yeez themselves. The daily tasks write and publish, and Learn makes small headline tweaks every day. **This review is where the big steering happens, and the buyer is the one steering.** Your job is to do all the analysis an expert operator would do, present it so they can see exactly what is moving their views, and help them pick the one change most likely to get them to their goal. They make the call; you do the work on both sides of it.

The method is the one the Yeez team uses on its own network, and it has turned flat sites around within days:

1. **Start from the outcome number.** Views per day against the goal. Not "how did the week feel".
2. **Real numbers only, the full history.** Every platform, all time, compared month by month. Never estimate a number you can pull.
3. **Find the cause, not the symptom.** Break views down by headline shape, story type, volume, publish hour, how articles open, and whether the platform even distributed them. Compare posts inside the same month so one good or bad month can't fake a pattern.
4. **Question every rule.** Each saved rule exists for a reason; check whether the numbers still back it. "Why only one of these a day?" "Is longer really better here?" A rule that costs views is the cheapest fix there is.
5. **Do the arithmetic of the goal.** How many views per post, or how many more hits a week, closes the gap, and has the site ever done that.
6. **One test at a time.** Pick one change, run it long enough, judge it on views, then grow, hold or end it. Two changes at once and nobody knows which one worked.
7. **Check the result.** The next review opens with how the running test did, before anything else.

## Where things are kept

Everything stays on the buyer's computer, in their Yeez folder. Nothing in this review is saved to yeez.ai.
- `yeez-work/goals.json`: each site's views goal (see step 1).
- `yeez-work/tests.json`: every test, running and finished.
- `yeez-work/reviews/<date>-<site>.md`: each week's full review.
- `yeez-work/data/`: the numbers Learn pulls.

## Doing the work properly

This review is only worth anything if the analysis is complete. Hold yourself to this:
- **Read every row the script gives you.** `last_4_weeks_every_post` lists every post of the last four weeks that is old enough to judge, best to worst. Read every title, not the top few. The same goes for every shape, every vein, every week and every test.
- **No sampling, no shortcuts.** Don't summarize a list you only skimmed. If a list is too long for one read, read it in parts until you have read all of it.
- **Every claim carries its number**, with how many posts it rests on ("person-first headlines: 1.74x the month average across 189 posts").
- **Small groups don't count.** Under 15 posts is a hunch, not a finding. Say so.
- **The current month is always low** because its posts have had less time to collect views. Never call that a decline.
- **When the numbers can't answer a question, say what would**, and get it if you can (pull a platform, read the posts).
- **Never invent numbers.** If a platform couldn't be pulled, say which and carry on with the rest.
- End the review with a short **"What I checked"** line: platforms pulled and how fresh, posts read, shapes, veins, rules and tests checked, and how many outside-the-box ideas you checked (step 4k). If any count is lower than it should be, go back and finish before reporting.

## 0. The plan

Call `guarantee_status`. It returns their plan (articles a day per site), today's Learn pull and articles, and plan days so far (`plan_days` of `plan_days_needed`). Earnings and content costs aren't tracked; they're only sent with documents if the buyer ever claims.

## 1. The goal

Read `yeez-work/goals.json`. Each site needs a goal before the review can tell anyone whether things are on track:

```json
{"sites": {"example.com": {"views_per_day": 80000, "platform": "newsbreak", "by": "2027-02-01",
  "why": "replace my VA's cost and grow income", "wants": ["more views per post", "get The Tonic Edit going again"],
  "set": "2026-11-16", "history": []}}}
```

**No goal yet for a site, and someone is there:** set it with them before going further. Run step 2 first so you know where they stand, then ask in plain words:
- What do they want each site doing per day in views, and by when? Offer three choices from their own numbers: their best month's daily views, about 1.5x today, and about 2x today.
- What is it for (money they want to replace or reach), and what would they most like improved?

Then reality-check it with the goal math (step 2): show how many views per post or extra hits a week it takes and whether the site has ever done that. If it has never been done, say so plainly and suggest a first step goal on the way. Save what they choose.

**No goal and nobody there (scheduled run):** run everything with the best month as a stand-in goal, and put "Set your views goal: reply here or type /yeez:review" at the top.

When they change a goal, keep the old one in `history` with the date.

## 2. Get the numbers in

Follow the **learn** skill in weekly mode first: it pulls NewsBreak and every other platform it can reach and refreshes each site's veins, patterns and marching orders. Only if a platform can't be pulled or uploaded, ask (skip when unattended):
- **Views:** a CSV export or screenshot of per-article views. Save it as a CSV with title and views columns and fold it in with the learn skill's `yeez_data.py ingest`.
- **Earnings:** what each source paid this week. Call `record_earnings` once per source (see the **offers** skill).

Then, for each site, run the analysis (from the buyer's Yeez work folder, using the learn skill's scripts and the site's veins file):

`python3 <learn skill>/scripts/yeez_data.py review --site SITE --veins yeez-work/data/veins-SITE.json`

It returns, per platform: views by calendar month and by week, the last 28 days, the goal math, hit bands from the site's own numbers, headline shapes with their lift, publish hours, veins (value vs slots), every post of the last four weeks, proven winners to re-run, posts the platform didn't make live, and every test's result. Lift means an article's views compared with the average of articles published the same month on the same platform (1.0 = average, 2.0 = twice as many views).

Work from the platform that pays them most (`business.makes_money_from` in `get_profile`). Report the others in a line each unless they matter.

## 3. The running test comes first

If `tests.json` has a running test for this site, judge it before anything else:
- **Enough to judge?** A test on one kind of headline or story needs at least 10 of those posts old enough to count. A whole-site change (volume, mix) needs at least 7 days and 20 posts since it started. Not enough: say "too early" and when it will be ready.
- **The call:**
  - **Grow:** clearly above the rest (about 1.3x the lift, or a clearly higher hit rate) on enough posts. Offer to give it more of the day.
  - **Hold:** too close to call, or good but on too few posts. Keep it running another week.
  - **End:** clearly below. Offer to undo it, and log what was learned.
- When the buyer agrees (or the end date has passed and nobody is there, in which case hold and ask), update the test's `status`, `result` and `ended` in `tests.json`. A finished test's lesson goes into the site's `winning_patterns` or `losing_patterns` with `save_site_profile`.

## 4. The deep look (every site)

Go through all of it, in this order. Write down what you find as you go; the options in step 6 come from here.

**a. The scoreboard.** Views per day: last 7 days, the 7 before, the 4 weeks before, the best week ever. Each of the last 6 calendar months: posts, views per post, hits, daily views. Is the site going up, flat or down, and since when? Did anything change around then (volume, a rule, the mix, a platform demotion)? Check the review files and `tests.json` for dated changes.

**b. Path to the goal.** From `goal_math`: today's views per day vs the goal, the gap, views per post needed at today's volume (and whether the site has ever done it), posts per day needed at today's views per post, hits per week now and extra hits needed. Say which path the history supports: more posts, better posts, or more hits. Volume only helps while views per post holds, so check the weekly table: in weeks with more posts, did views per post fall?

**c. Where the hits came from.** Go through `last_4_weeks_every_post`. For every hit (at or above the `hit` band) note its story type, headline shape and source. Then group them: which story types and shapes produce hits, and at what **rate** (hits divided by posts of that kind), not just the count. Do the same for the bottom quarter: which kinds take the most slots and return the least.

**d. Headline shape.** From `headline_shapes`: the shapes with clearly higher lift and hit rate than their opposite, on 15+ posts, and how much of the last four weeks used them (`share_of_last_28_days`). A winning shape used rarely is an opportunity; a losing shape used often is a leak. Check length bands especially: what length wins here can differ by site and platform.

**e. Story types (veins).** From `veins_value_vs_slots`: each vein's lift against its share of recent slots. Flag winners getting few slots, losers getting many, and any vein whose lift has fallen month over month (a vein that is wearing out). If a top vein is dying, run the learn skill's competitor step for fresh angles in that vein.

**f. The articles themselves.** Open the 5 best and 5 worst posts of the last four weeks on the site (on WordPress, `https://SITE/wp-json/wp/v2/posts?search=<words from the title>&_fields=title,content,link`). Read the first three paragraphs of each. Do the winners open with the person and the moment while the losers open dry? Are the losers padded, off-topic for the site, or written like a press release? Note what you see, with an example of each.

**g. Volume and timing.** From `by_week_old_enough_to_judge` and `by_publish_hour`: did the daily count land every day (posts per day vs the plan)? Which hours do best here?

**h. Distribution.** From `not_made_live_by_month`, and in the platform's dashboard if needed: posts the platform didn't make live or flagged. That's a distribution problem, not a headline problem; find the cause (feed box not ticked, flagged images, links, quality flags) before judging anything else.

**i. Proven winners not used.** From `proven_winners_to_rerun`: past big hits that could run again with today's facts and a new headline. Note how many there are and whether the site is using them.

**j. The rules, one by one.** Call `get_site_brief`. List every `buyer_rules` line, the `story_mix`, the articles a day, and any `mix_warnings`. For each rule: what part of the day it controls, and what the numbers say about it, for and against. Flag every rule the numbers say is costing views and how many. Support notes from the Yeez team stay as they are; don't propose changing them.

**k. Everything else: the things nobody thought to check.** Every buyer's setup is different, and the thing holding a site back is often something no checklist names. Before building options, step back and look at the whole operation from every angle, as if you were a sharp outsider seeing this site for the first time. Go through each area below, write down anything that could plausibly be affecting views, then check each idea against the data or the site itself. Most ideas won't hold up; that's fine, say so and move on. Keep only what the evidence supports.
- **The site itself:** speed and errors on a phone, broken or slow pages, pop-ups or ads covering the article, featured images (missing, repeated, cropped badly, off-topic), headline on the page vs the headline in the feed, author pages, categories, duplicate or near-duplicate posts, posts that went out without images or with broken formatting, internal links and what readers see at the end of an article.
- **The feed and the platform account:** what the feed actually sends (open the site's feed and look), the account's profile, follower count and its trend, any warnings, strikes, demotions or policy emails, categories or tags set on the platform, which posts the platform featured and which it buried.
- **Timing:** what else happened when views moved (a platform change, a holiday, a news cycle, the season for this niche, a change the buyer made, a task that stopped running, a run time that moved).
- **The audience:** who actually reads this site, judging by the winners and the comments, and whether today's stories still speak to them or have drifted toward what's easy to find.
- **Competitors and the niche:** what similar sites that are clearly winning are publishing right now that this site isn't, and whether a whole kind of story is rising or fading across the niche.
- **The buyer's setup:** other plugins or tools on the site, other people posting to it, other sites sharing the same platform account, anything in their saved basics that no longer matches how they run things.
- **The other channels:** newsletter, Facebook, Instagram and search, and whether any of them is helping or hurting the site's main platform.
- **Anything that looks odd** in the numbers: a single day that spiked or died, a platform whose numbers stopped, a run of posts with zero views, a story type that suddenly works on one site and not another.

Put what you found under "Other things I checked" in the review: each idea, what you checked, and whether it held up. Anything that held up goes into the repairs or the options.

## 5. Small tuning (automatic)

For each site, call `save_site_learnings` with up to five changes:
- A phrase or topic that showed up in two or more winners: weight +3 to +6.
- One that showed up in two or more losers and no winners: weight −3 to −6.
- A phrase that has kept winning for three weeks or more can go to +8; never past ±10.
- Phrases are short and specific (a subject, brand, program or number type), never generic words like "new" or "how".
- Remove a learned rule that the week's results contradict.
Give each a `why` of ten words or fewer, with the evidence ("3 of top 5, avg 41k views"). With fewer than five articles that have views, skip this step.

These are the only changes the review makes on its own. Anything bigger is the buyer's decision.

## 6. The options

From everything in step 4, build **the 3 to 5 changes most likely to raise views toward the goal**, biggest first. A change can be anything the data points to, for example: change the story mix, cut or end a losing rule, give a winning story type more of the day, change headline length or voice, change the daily count, re-run proven winners, test a competitor's angle, fix a distribution problem, change publish hours. Use the buyer's own ideas too: if they've said what they want to try, it's on the list with the numbers for and against.

For each option give, in plain words:
- **What's happening:** the finding, with its number and how many posts it rests on.
- **The change:** exactly what would change, in their words (e.g. "Garden site: people stories go from 12 to 16 of the 20 a day; tips go from 6 to 2").
- **What it could do:** the arithmetic in views per day, from this site's own numbers ("these 4 slots average 0.4x; moved to people stories at 1.9x, that's about +6,000 views a day"). Say clearly that it's an estimate from their history, not a promise.
- **The risk**, and how to undo it.

Mark the one you would test first and why. **Only one test runs at a time per site.** If a test is already running and not finished, the options are for after it ends, unless a distribution problem or a broken rule needs fixing now; those aren't tests, they're repairs.

Distribution problems and things that are plainly broken (a feed box not ticked, a task not running, the daily count short) go first as **repairs**, separate from the options.

## 7. Save the review and report

Write the full review to `yeez-work/reviews/<date>-<site>.md`: scoreboard, path to the goal, test result, every finding from step 4 with its numbers, the rules check, other things I checked (each idea and whether it held up), the small tuning done, the repairs, the options, and "What I checked".

Then tell the buyer in the chat, short and plain:
- Each site in two lines: views per day vs goal (and vs last week), going up, flat or down.
- The running test's result and your call.
- Repairs, if any, and what they need to do.
- The options for their biggest site (or the site furthest from its goal), numbered, with your pick marked. Other sites: their top option in one line each.
- Their plan: days on plan so far, and anything that kept Learn or the articles from running (from `guarantee_status`).
- One closing line: "Pick a number to start that test, ask me anything about your numbers, or tell me what you want to try. The full review is in your Yeez folder: reviews/<file>."

When this runs as a scheduled task with nobody watching, never stop to ask. Do steps 0 to 7, apply only step 5, and put anything the buyer must do (set a goal, log in somewhere, pick an option) at the top.

## 8. Talking it through

The buyer can reply in that same chat any time, or type /yeez:review.
- **Questions:** answer from their data, not from memory. Re-run `yeez_data.py review` or read `yeez-work/data/articles.csv` directly for the exact slice they ask about (one story type, one month, one platform, one headline shape). Show the numbers and the posts behind them.
- **Teaching:** when they ask why something works or how to think about it, explain it simply and point them to the help answer **How do I get more views?** (https://yeez.ai/help/get-more-views).
- **Their own idea:** check it against the numbers, say honestly what the data says, and if they still want it, it becomes the next test.
- **Picking an option:** confirm the exact change in one line, then:
  1. Apply it with the Yeez tools: `save_site_profile` (`buyer_rules`, sending the full list; `story_mix`), or `save_site_settings` (articles a day, publish times). Never edit a scheduled task.
  2. Add it to `tests.json`: `id`, `site`, `name`, `hypothesis`, `change` (what changed, from and to), `started` (today), `ends` (7 days for a whole-site change, 14 for a headline or story-type test), `match` (the keywords or shape that pick out the test posts; leave it out for whole-site changes), `status: "running"`.
  3. Tell them what changed, when the first read is due, and that the next review opens with the result.
- **Undo:** put the rule back as it was, mark the test `ended` with the reason.
- **A new goal:** update `goals.json` (keep the old one in `history`) and redo the path to the goal.

## 9. The rest of the week (same as always)

After the views review, cover these briefly:
- **Social:** the posts with the most reactions, comments and shares per account, and what they had in common. Social accounts already learn from their top posts on every `get_social_brief`.
- **DMs:** which keywords got comments and messages sent.
- **Money:** earnings this period vs the previous one, and offer clicks by channel.
- **Search:** from `search` (Search Console, per site): clicks and impressions by Web, Discover and Google News vs last week; pages that grew; refresh candidates (ranking 8–20 with many impressions); high-impression, low-click results (rewrite their search title and description). Run `check_indexing` once per site; if fewer than about half of last week's articles are indexed, say so and recommend fewer, deeper articles. Run `check_search_gate` for each site; if a site's search articles turned on or off this week, say so in one line with the reason.
