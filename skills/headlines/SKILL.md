---
name: headlines
description: Finds today's stories for each of the buyer's sites, writes headline candidates, and has Yeez rank them and pick the day's best. Use when the user types /yeez:headlines, asks for today's headlines, or as the first half of /yeez:run.
---

# Yeez headlines

Read [../core/rules.md](../core/rules.md) and [../core/platforms/README.md](../core/platforms/README.md) first, then the file in [../core/platforms/](../core/platforms/) for each platform the site publishes to. Every headline must pass the strictest of them (MSN: no exclamation points, no clickbait; Facebook money-safety framing for anything that may become a social post).

**Goal:** the stories and headlines most likely to get the most views on the platforms that pay this site, all true today.

Run this for each connected site (call `list_sites`), or only the site the user names.

## 1. Load the brief

Call `get_site_brief` for the site. It gives the site's settings, the buyer's saved voice, audience and goals, every headline from the last 14 days, and today's picks so far. If `still_to_write` already covers the day, say so and stop for that site.

`settings.profile` is what the **learn** skill found in this site's real numbers. Plan the day from it before searching:
- **marching_orders:** `ride` (breakouts to spin fresh sequels of today), `refresh` (proven evergreen veins due again), `highest_value` (veins worth the most views per article), `avoid` (veins below the site average and dead patterns). Honor these first.
- **veins:** give more of the day's slots to veins with the highest views per article and a rising or flat trend. Keep only a few slots for veins below the site average, and only with a fresh angle.
- **winning_patterns / losing_patterns:** the headline shapes that win and flop on this site. Write to the winners; never repeat a losing pattern.
- **voice_samples:** the site's best headlines by views. Match their shape, not their words.

**Needs:** marching orders dated today or yesterday. If they're missing or older, follow the **learn** skill in daily mode first (unattended: do it, don't ask). If there's still no profile (learn has never run in full for this site), say so at the top of the summary and write from the site's recent winners in the brief.

## 2. Know what kind of stories this site runs

Every story has a **story type** (`story_types` in the brief: `site_default`, `site_mix` and a `guide` per type). The type decides what counts as a good source and what the headline should look like, so a parenting, garden, celebrity or sports site never gets written like a government report.

- Split the day's slots by `site_mix` (or all `site_default` if there's no mix yet). Each type's `use_for` says which stories belong to it.
- Follow each type's `sourcing` when you look for stories and its `headline_style` when you write.
- Tag every candidate with its `story_type` in `score_headlines`.

## 3. Pull wide (with gatherer helpers)

Search the web for real, current stories in this site's niche, aimed at the veins in the marching orders. Gather at least 1.5 times as many stories as the site publishes per day.

Split the searching across `yeez-gatherer` helpers, following [../core/helpers.md](../core/helpers.md) (call `get_model_plan` once; the plan's `gather` model named on every hand-off; never more than `max_helpers_at_once` at the same time). One helper per slice: a vein from the marching orders or a story type from the mix, with how many stories to bring back. Give each the site's niche and audience, the story-type guide, the `avoid` list and `buyer_rules`, the competitor examples for that slice, and the stories already found. They return stories with every fact recorded (steps 3 and 4 below are their job). Merge what comes back, drop duplicates, and check the facts on anything that looks off before you write. If this app can't start helpers, do steps 3 and 4 yourself.

- Look where this site's kind of story is actually reported. Money and rule changes: agencies, regulators, courts, company notices, studies. People stories: local TV and newspaper sites, national outlets that interview the person, court and police records. Celebrities and sports: the outlets that broke it, plus the official announcement.
- `profile.competitor_examples` lists stories from competing sites that fit this site's veins. Use them as models for the angles and shapes to look for, never as text to copy.
- Never use Reddit, forums or anonymous posts as a source. A viral post counts only when a named outlet reported it and named or interviewed the person; then cite the outlet.
- Stay in the site's niche (`about` and `buyer_rules` in the brief). On a niche site the niche must be the heart of the story: on a garden site the garden, plants or harvest, not just something that happened in a yard; on a parenting site the parent or child. A strong story outside the niche is still cut.
- If the niche's news runs thin today, don't leave slots empty: fill them from the site's other story types in its mix (seasonal guides and tips from expert sources where the mix has them), then from other outlets. Never fill with weak, off-niche or duplicate stories.
- Cut what this site's numbers say doesn't win (the `avoid` list and the veins below the site average). For money and rule stories, also cut textbook how-tos, minor-brand news and statistics nobody feels. For people stories, a single-town story is fine when the person and the stakes are strong.

## 4. Settle the facts first

For each story, read the primary source and record exactly what every number, date and status is: cap or flat amount, estimate or final, cumulative or current, whose figure, which date, alleged or proven. Note the date you confirmed it is current, and the date the event happens.

Drop a story here, before writing anything, when (the shared currency and claim-state rules):
- it's time-anchored (a sentencing, charge, settlement, refund, recall, failure, or anything "just" or "now") and the event is more than about 30 days old;
- a claim window or deadline has passed or can't be confirmed open;
- it's a bill that died, stalled or ended with the session, or a rule proposed, repealed or vacated (a live proposal can run only as "would", "could", "bill" or "proposal");
- it says money "is being sent", "approved" or "starts" with no current page from the agency that runs it;
- the figure is last year's.

## 5. Write the candidates

Write one headline per story, in the shape of this site's own winners (`voice_samples` and `winning_patterns`) and its story type's `headline_style`. Read three or four of the site's top titles before you start and match how they're built: who they lead with, how long they run, how they carry the emotion and the detail. A people story reads like the site's best people stories, not like an agency notice.

Always:
- third person
- a vivid verb
- the specific detail that makes it this story (the person, the place, the figure or the date)
- a hook that makes people want the story: an outcome, a stake, or a cliffhanger the article pays off in its first two paragraphs

For money and rule stories, favor ones where something readers already have or rely on changes on a stated date, named after the institution or household brand the story is about.

Vary length, opening word and structure across the day. Never use any of these:
- ALL CAPS, emoji or clickbait
- false urgency
- "you"
- a promise that readers personally get money
- exclamation points
- the "stat — em-dash — twist" shape more than once a day (or any one shape across most of the set)

Intensity is good: long, emotional and as strong as the true facts allow. Never water a true story down.

Every number, name and claim in a headline must come from a fact you recorded. If it can't be sourced, take it out.

## 5b. Run the test lane

About a quarter of every day is tests (`test_lane.slots_per_day` in the brief). A test is a real, verified story run to find out what gets more views here, never a made-up one. Each test changes one thing against what the site already proves, so the result means something:
- a headline shape the site hasn't run (a cliffhanger, a question, a quote lead, a list count, person-first vs place-first, shorter or longer)
- an angle or vein from `competitor_examples` or the marching orders' `ride` list
- a story type the site hasn't tried
- an untested publish slot or topic

Mark each test candidate with `test: {hypothesis, kind}` in `score_headlines` (kind is a short label like "cliffhanger" or "new vein: HOA", so learn can grade them together). Tests compete for the test slots among themselves, so a new shape isn't crowded out by proven ones. Keep running a kind until learn grades it (3+ runs), and don't repeat a kind learn marked as a loser.

## 6. Rank with Yeez

Call `score_headlines` with all candidates. For each one, send:
- its `sources`
- its `facts` (each fact with its source URL; every number in the headline must appear there)
- `primary_source_url`, `current_as_of` and `event_date`
- a one-line `angle`

Send each candidate's `story_type` too. Yeez scores each headline by its type, kills repeats and anything that breaks the rules, picks the day's set in ranked order, and keeps the next best as **reserves**. When the articles task holds a pick, the top reserve takes its place, so the day still fills.

If a candidate comes back killed for a reason you can fix with sourced facts (a missing fact or date), fix it and score it once more. Never pad the day with weaker or duplicate stories.

If the result includes a `note` about missing site word lists, tell the user once that `/yeez:setup` can add them.

## 7. Report

In a short list per site, show the picked headlines with their scores, and how many were cut and why, in a few words each.
