---
name: review
description: The Yeez weekly review. Collects the week's numbers, finds what won and what flopped on each site and social account, updates each site's headline rules for next week, logs earnings, and updates the 90-day earn-back tracker. Use when the user types /yeez:review, asks how the week went, wants to log earnings or views, sets their before-Yeez baseline, or as part of the Monday /yeez:run.
---

# Yeez weekly review

Plain words, short lines. The buyer should finish knowing what worked, what changed for next week, and where they stand on the 90-day earn-back.

## 0. Baseline (once)

Call `guarantee_status`. If `before_total_90_days` is empty, or the user said "baseline":
1. Explain in one line: the guarantee compares what their sites earn in the 90 days after starting Yeez with the 90 days before.
2. Ask what each income source paid in the 90 days before they started, from their own dashboards: ad networks (NewsBreak, MSN, Mediavine, AdSense…), syndication, affiliates, products, newsletter sponsors. One number per source is enough; a screenshot works too.
3. Call `save_baseline` with one entry per source. Only pass `start_date` if they started on a day other than their first scheduled article.

If this runs unattended, skip this step and put "Add your before-Yeez baseline with /yeez:review baseline" at the top of the summary.

## 1. Get this week's numbers in

Follow the **learn** skill in weekly mode first: it pulls NewsBreak and every other platform it can reach, and refreshes each site's veins, patterns and marching orders. Only if a platform can't be pulled or uploaded, ask (skip when unattended):
- **Views:** a paste, CSV or screenshot of per-article views. Read titles and view counts from it and call `record_platform_stats` for the site and platform.
- **Earnings:** what each source paid this week. Call `record_earnings` once per source (see the **offers** skill).

Never invent numbers. If they have none, carry on with what Yeez already tracks (clicks, social engagement, DMs).

## 2. Read the week

Call `get_weekly_review_data`. For each site, sort articles by views (then offer clicks, then headline score) and find:
- **Winners:** the top 3–5. What they share: topic, named entity, number type, angle, headline shape.
- **Losers:** the bottom 3–5 that were scheduled at least 48 hours ago.
- **Held and cut:** the most common reasons. If one rule cut lots of strong stories, say so.
- **Social:** the posts with the most reactions, comments and shares per account, and what they had in common.
- **DMs:** which keywords got comments and messages sent.
- **Money:** earnings this period vs the previous one, and offer clicks by channel.
- **Search:** from `search` (Search Console, per site): clicks and impressions by Web, Discover and Google News vs last week; the pages that grew; refresh candidates (ranking 8–20 with many impressions: expand or update those pages); high-impression, low-click results (rewrite their search title and description). Run `check_indexing` once per site; if fewer than about half of last week's articles are indexed, say so and recommend fewer, deeper articles.

Base every claim on a number from the data. With fewer than five articles that have views, say it's too early to change rules and skip step 3.

## 3. Change next week's rules

For each site, call `save_site_learnings` with up to five changes:
- A phrase or topic that showed up in two or more winners: weight +3 to +6.
- One that showed up in two or more losers and no winners: weight −3 to −6.
- A phrase that has kept winning for three weeks or more can go to +8; never past ±10.
- Phrases are short and specific (a subject, brand, program or number type), never generic words like "new" or "how".
- Remove a learned rule that the week's results contradict.
Give each a `why` of ten words or fewer, with the evidence ("3 of top 5, avg 41k views").

Social accounts already learn from their top posts on every `get_social_brief`; no rules to save for them.

## 4. Save and report

Call `save_weekly_review` with `week_ending` (the last day of the period), a summary of four to six plain sentences, winners and losers as short lines with their numbers, the rule changes as plain sentences, and `numbers` (articles, views, clicks, social posts, DMs sent, earnings).

Then tell the buyer, briefly:
- the two or three things that mattered most this week
- the rules that changed
- the earn-back tracker: day X of 90, extra so far vs what they paid, on pace or not (from `guarantee`)
- their dashboard: https://yeez.ai/dashboard

When this runs as a scheduled task with nobody watching, never stop to ask; review what Yeez already has and list at the top what the buyer should add (views, earnings, baseline).
