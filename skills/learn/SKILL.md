---
name: learn
description: Pulls the buyer's real numbers (NewsBreak straight from the dashboard, MSN, Yahoo, SmartNews and analytics exports, Search Console), reads their sites, and works out what actually gets views on each site — topics, headline shapes, best articles, publish hours — then saves it as the site profile and this week's marching orders that every run follows. Use during setup (after sites are connected), when the user types /yeez:learn, says "pull my numbers" or "what's working", in the Monday review, and at the start of the daily run for a quick NewsBreak refresh.
---

# Yeez learn

Views are the only score. Never rank, report or reason from click-through rate: feed platforms even it out, so it hides what matters. A big view count means the platform pushed the article, which is the whole game.

Three modes:
- **Setup (full):** first time for a site. Pull everything, all time. Read the site. Present what you found and have the buyer confirm it.
- **Weekly (Monday review):** pull again, refresh veins, patterns and marching orders. Don't re-ask the buyer what they already confirmed.
- **Daily (start of /yeez:run):** NewsBreak refresh only, and only if a browser is available and already logged in. Never ask anything. Then refresh the marching orders from `learn_report`.

## 1. See what Yeez already has

Call `data_status`. Note each site's platforms and how old their numbers are. Numbers 3+ days old on a platform the site depends on are stale: say so at the top of the run summary, every run, until fixed.

Call `get_profile`: the `basics` section says which platforms each site syndicates to and how the buyer makes money. Pull every platform they use.

## 2. Pull NewsBreak (every site that publishes there)

Needs a browser you can run JavaScript in (see [browser.md](browser.md) for each app). For each site on NewsBreak:

1. Call `newsbreak_pull` with the site. It returns a `script`.
2. Open https://mp.newsbreak.com/home/content/post in the browser. Run `document.body.innerText.slice(0,80)` with your JavaScript tool. Logged in, it starts with `Welcome, <publisher name>`.
3. Not logged in:
   - **Someone is there:** ask them to log in to the NewsBreak account for that site in that browser, and to reply "done". Never type their login, never ask for their password in the chat.
   - **Unattended run:** skip NewsBreak, note it as stale, carry on.
4. Logged in: run the `script` with your JavaScript tool. Wait 10–20 seconds, then read `window.__yeez`. `ok: true` with `saved` means every article's lifetime impressions and views and the account's daily totals are in Yeez. A re-pull refreshes views; it never duplicates.
5. More than one NewsBreak account (one per site): ask the buyer to switch accounts, then repeat with the next site's script. Match the account to the site by the publisher name and the titles, never by guessing.

**mp.newsbreak.com never finishes loading for screenshot or page-reading tools.** Only use the JavaScript runner there. If your app can't run JavaScript on a page, send the buyer to https://yeez.ai/data: it has a one-click "Yeez · NewsBreak" bookmark button per site that does the same pull from their own Chrome.

## 3. Pull the other platforms

- **Search Console:** nothing to pull. Once the buyer has added Yeez's email (setup's search step), `search_console_status` and `get_search_performance` read it directly.
- **MSN, Yahoo, SmartNews, Google Analytics, WordPress stats:** these need an export file. How to get each one is in [platforms.md](platforms.md).
  - **Your app can drive the browser and read downloaded files:** open the dashboard (the buyer logs in if needed), download the export with the widest date range, read the file, and send it with `record_platform_stats` (up to 2,000 rows a call; call again for more). Title and views are required; add the platform's id, publish date and impressions when the export has them.
  - **Otherwise:** tell the buyer exactly which export to download (from [platforms.md](platforms.md)) and to drop it on https://yeez.ai/data. Carry on with what you have.
- Facebook numbers come from the **social** skill; you don't pull them here.

## 4. Read the site

For each site:
- Call `get_site_brief` for its settings and recent titles.
- Read the site itself: its home page, its category pages, and its post list. On WordPress the public `https://<site>/wp-json/wp/v2/posts?per_page=100`, `/wp-json/wp/v2/categories?per_page=100` and `/wp-json/wp/v2/users` give titles, categories and authors fast. Elsewhere, read the sitemap.
- Read the 10–15 best articles by views (from step 5's `top`) in full. That's how you learn the voice: length, structure, how they open, how they source, words they use and avoid.

## 5. Work it out

1. Call `learn_report` for the site. It gives views per platform, tier bands, the top articles, wasted-reach flops (shown thousands of times, barely read: the clearest headline failures), a sample of the low tail, views per article by publish hour and month, and daily totals.
2. Group the titles into 8–15 **veins**: repeatable topics or angles (a program, a kind of story, a product, a recurring event), each with the 2–10 keywords that identify it in a title. Use the top articles, the wasted reach and the tail sample.
3. Call `learn_report` again with those `veins`. Each comes back with views per article (VPA), its ratio to the site average, its 20K+ count and a month-by-month trend.
   - **VPA is the unit.** It answers "what is one article in this vein worth". A vein that produces one huge hit per 40 articles can beat one that reliably produces small wins.
   - Check the month-by-month trend before recommending a vein: rising, flat or decaying. The latest month is always biased low (less time to collect views); never call that a decline.
   - A vein below the site average costs the site views on every article in it.
   - Articles NewsBreak didn't make live (its `status`) are a distribution problem, not a headline problem: report them, don't learn from them.
4. Work out the profile:
   - **about** and **audience:** one or two plain sentences each, from the site and its winners.
   - **universal_entities:** the institutions, programs or agencies the whole audience depends on, ranked by how often they appear in winners.
   - **major_brands:** household names the audience recognizes on sight, from the titles.
   - **categories, default_category, authors:** from the site.
   - **voice_notes:** how the best articles are built and written, in a few short lines.
   - **voice_samples:** the best 30–50 articles by views (title, URL, views). Prefer ones published on this site, and keep several from each top vein.
   - **winning_patterns / losing_patterns:** headline shapes that win and lose here (what they open with, numbers, named entities, length, framing), each with its evidence ("9 of the top 20").
   - **veins:** name, keywords, VPA, ratio to average, trend.
   - **best_hours:** when this site's articles do best, converted to the site's timezone (the report's hours are UTC).
   - **marching_orders:**
     - `ride`: veins breaking out in the last 14 days
     - `refresh`: proven evergreen veins with high VPA that haven't run lately
     - `highest_value`: the top veins by VPA with their trend
     - `avoid`: veins below the site average and freshly confirmed dead patterns

## 6. Confirm (setup only)

Show the buyer one short message per site, plain words, no jargon:

> **Here's what we found for site.com.** Is this right?
> - It's about … and read by …
> - What wins: … (with the numbers)
> - What doesn't: …
> - Big subjects your readers follow: … · Brands they know: …
> - Categories … · Authors … · Default category …
> - Your voice: … (based on your 40 best articles, top one: "…", 212K views)
> - Best times to publish: …

Let them change anything ("tap the microphone and just talk" works too). Then call `save_site_profile` with everything and `confirmed_by_buyer: true`.

In weekly and daily mode, don't ask: call `save_site_profile` with the refreshed `veins`, `winning_patterns`, `losing_patterns`, `best_hours`, `voice_samples` and `marching_orders` only. Never overwrite what the buyer confirmed (about, audience, subjects, brands, categories, authors, voice notes). If the data says one of those has changed, suggest it in the summary instead.

## 7. Report

Per site, in short lines: what was pulled (articles per platform, how fresh), the top three veins with VPA and trend, the dead patterns, and this week's marching orders. Anything stale or blocked goes at the top.
