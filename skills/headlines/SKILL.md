---
name: headlines
description: Finds today's stories for each of the buyer's sites, writes headline candidates, and has Yeez rank them and pick the day's best. Use when the user types /yeez:headlines, asks for today's headlines, or as the first half of /yeez:run.
---

# Yeez headlines

Run this for each connected site (call `list_sites`), or only the site the user names.

## 1. Load the brief

Call `get_site_brief` for the site. It gives the site's settings, the buyer's saved voice, audience and goals, every headline from the last 14 days, and today's picks so far. If `still_to_write` already covers the day, say so and stop for that site.

`settings.profile` is what the **learn** skill found in this site's real numbers. Plan the day from it before searching:
- **marching_orders:** `ride` (breakouts to spin fresh sequels of today), `refresh` (proven evergreen veins due again), `highest_value` (veins worth the most views per article), `avoid` (veins below the site average and dead patterns). Honor these first.
- **veins:** give more of the day's slots to veins with the highest views per article and a rising or flat trend. Keep only a few slots for veins below the site average, and only with a fresh angle.
- **winning_patterns / losing_patterns:** the headline shapes that win and flop on this site. Write to the winners; never repeat a losing pattern.
- **voice_samples:** the site's best headlines by views. Match their shape, not their words.

If there's no profile yet, or its marching orders are more than 7 days old, say so at the top of the run summary and suggest `/yeez:learn`.

## 2. Pull wide from primary sources

Search the web for real, current stories in this site's niche. Gather at least 1.5 times as many stories as the site publishes per day. Prefer primary sources:
- agencies, regulators and courts
- official company notices
- recall and safety bodies
- the publishers of studies

Competitor and trend feeds tell you which stories exist. Never copy their wording.

Cut low-ceiling topics before you write anything:
- textbook how-tos
- single-town items
- minor-brand news
- police-blotter items
- small claims that need readers to take action
- statistics nobody feels

## 3. Settle the facts first

For each story, read the primary source and record exactly what every number, date and status is: cap or flat amount, estimate or final, cumulative or current, whose figure, which date, alleged or proven. Note the date you confirmed it is current, and the date the event happens.

## 4. Write the candidates

Write one headline per story:
- a plain statement in the third person
- a vivid verb
- the specific figure or date
- named after the institution or household name the story is actually about

Favor stories where something readers already have or rely on changes on a stated date.

Vary length, opening word and structure across the day. Never use any of these:
- ALL CAPS, emoji or clickbait
- false urgency
- "you"
- a promise that readers personally get money

Every number, name and claim in a headline must come from a fact you recorded. If it can't be sourced, take it out.

## 5. Rank with Yeez

Call `score_headlines` with all candidates. For each one, send:
- its `sources`
- its `facts` (each fact with its source URL; every number in the headline must appear there)
- `primary_source_url`, `current_as_of` and `event_date`
- a one-line `angle`

Yeez scores each headline, kills repeats and anything that breaks the rules, and picks the day's set in ranked order.

If a candidate comes back killed for a reason you can fix with sourced facts (a missing fact or date), fix it and score it once more. Never pad the day with weaker or duplicate stories.

If the result includes a `note` about missing site word lists, tell the user once that `/yeez:setup` can add them.

## 6. Report

In a short list per site, show the picked headlines with their scores, and how many were cut and why, in a few words each.
