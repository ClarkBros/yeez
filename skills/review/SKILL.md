---
name: review
description: The Yeez weekly review. Collects the week's numbers, finds what won and what flopped on each site and social account, updates each site's headline rules for next week, logs earnings, and reports days on plan. Use when the user types /yeez:review, asks how the week went, wants to log earnings or views, or as part of the Monday /yeez:run.
---

# Yeez weekly review

Read [../core/rules.md](../core/rules.md) first: who Yeez is and the rules it never breaks.

Plain words, short lines. The buyer should finish knowing what worked, what changed for next week, and whether they're on plan.

## 0. The plan

Call `guarantee_status`. It returns their plan (articles a day per site), today's Learn pull and articles, and plan days so far (`plan_days` of `plan_days_needed`). Earnings and content costs aren't tracked; they're only sent with documents if the buyer ever claims.

## 1. Get this week's numbers in

Follow the **learn** skill in weekly mode first: it pulls NewsBreak and every other platform it can reach, and refreshes each site's veins, patterns and marching orders. Only if a platform can't be pulled or uploaded, ask (skip when unattended):
- **Views:** a CSV export or screenshot of per-article views. Save it as a CSV with title and views columns and fold it in with the learn skill's `yeez_data.py ingest`.
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
- their plan: days on plan so far, and anything that kept Learn or the articles from running (from `guarantee`)
- their dashboard: https://yeez.ai/dashboard

When this runs as a scheduled task with nobody watching, never stop to ask; review what Yeez already has and list at the top what the buyer should add (views, earnings).
