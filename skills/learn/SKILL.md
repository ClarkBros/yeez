---
name: learn
description: Pulls the buyer's real numbers (NewsBreak straight from the dashboard, MSN, Yahoo, SmartNews and analytics exports, Search Console), reads their sites, and works out what actually gets views on each site — topics, headline shapes, best articles, publish hours — then saves it as the site profile and this week's marching orders that every run follows. Use during setup (after sites are connected), when the user types /yeez:learn, says "pull my numbers" or "what's working", in the Monday review, and at the start of the daily run for a quick NewsBreak refresh.
---

# Yeez learn

Read [../core/rules.md](../core/rules.md) first: who Yeez is and the rules it never breaks.

Views are the only score. Never rank, report or reason from click-through rate: feed platforms even it out, so it hides what matters. A big view count means the platform pushed the article, which is the whole game.

**Goal:** know what gets the most views on the platforms that pay this buyer, so every headline and article tomorrow is aimed at it. Weigh each platform by what it pays them (`business.makes_money_from` in the basics, with each source's share): a vein that wins on the platform paying 70% of their income outranks one that wins on a platform paying nothing.

Prompts: `/yeez:learn` (setup mode when a site has no confirmed profile yet, otherwise weekly), `/yeez:learn daily`, `/yeez:learn pull` (steps 1–3 only).

Modes:
- **Setup (full):** first time for a site. Pull everything, all time. Read the site. Present what you found and have the buyer confirm it.
- **Weekly (Monday review):** pull again, refresh veins, patterns and marching orders. Don't re-ask the buyer what they already confirmed.
- **Daily (start of /yeez:run):** NewsBreak refresh only, and only if a browser is available and already logged in. Never ask anything. Then refresh the marching orders from `yeez_data.py report`.

## Where the numbers live

Every number stays in the buyer's own **Yeez folder** on their computer (`yeez-work/data/`), never on yeez.ai. The scripts in this skill's `scripts/` folder do the work:
- `scripts/newsbreak-pull.js`: runs in the logged-in NewsBreak tab and downloads every article and the daily totals as two files.
- `scripts/yeez_data.py ingest FILE… --site SITE --platform PLATFORM`: folds any pulled file or export into the folder (re-pulls refresh views, never duplicate).
- `scripts/yeez_data.py report --site SITE [--veins veins.json]`: the analysis.
- `scripts/yeez_data.py status`: what's in the folder and how fresh.

Run them from the buyer's Yeez work folder (the parent of `yeez-work`), or set `YEEZ_WORK` to it. Apps that can't run scripts or drive a browser (ChatGPT in the browser, grok.com) can't do this skill: tell the buyer to run it from the Claude desktop app or the ChatGPT desktop app (Codex) once a week, and carry on with the saved profile.

After each platform is folded in, call `log_data_pull` with the site, platform and article count (counts only).

## 1. See what's there

Run `yeez_data.py status`. Note each site's platforms and how old their numbers are. Numbers 3+ days old on a platform the site depends on are stale: say so at the top of the run summary, every run, until fixed.

Call `get_profile`: the basics say which platforms each site syndicates to (`channels.syndication`) and how the buyer makes money (`business.makes_money_from`, each with what it rewards). Pull every platform they're approved on.

## 2. Pull NewsBreak (every site that publishes there)

Needs a browser you can run JavaScript in ([browser.md](browser.md) has how to turn it on in each app). For each site on NewsBreak:

1. Open https://mp.newsbreak.com/home/content/post. Run `document.body.innerText.slice(0,80)` with your JavaScript tool. Logged in, it starts with `Welcome, <publisher name>`.
2. Not logged in:
   - **Someone is there:** ask them to log in to that site's NewsBreak account in that browser and reply "done". Never type their login, never ask for a password in the chat.
   - **Unattended run:** skip NewsBreak, note it as stale, carry on.
3. Read `scripts/newsbreak-pull.js`, replace `SITE_LABEL` with the site (e.g. `example.com`), and run it with your JavaScript tool in that tab. After 10–20 seconds read `window.__yeez`: `ok: true` lists the files it downloaded.
4. Find the two files in the computer's Downloads folder, then run `yeez_data.py ingest <both files> --site SITE --platform newsbreak`. Move the files into `yeez-work/data/inbox/done/`.
5. More than one NewsBreak account (one per site): ask the buyer to switch accounts, then repeat with the next site. Match account to site by the publisher name and the titles, never by guessing.

**mp.newsbreak.com never finishes loading for screenshot or page-reading tools.** Use only the JavaScript runner there.

## 3. Pull the other platforms

For each other platform the site is approved on, drive the browser yourself. The buyer only logs in.

1. Open the dashboard from [platforms.md](platforms.md). Not logged in: ask the buyer to log in (unattended: skip and note it stale).
2. Find the article or content performance report. Set the widest date range it allows (all time if offered). Turn on every column that has views, page views, impressions or publish date.
3. Click its export or download button (CSV preferred). If the dashboard has no export, read the table page by page and save it as a CSV with title, published and views columns.
4. Ingest the file with `yeez_data.py ingest FILE --site SITE --platform PLATFORM` (`msn`, `yahoo`, `smartnews`, `ga`, `wordpress`, `flipboard`, `other`).
5. Note in [platforms.md](platforms.md)'s style, in `yeez-work/data/how-to-pull.md`, the exact clicks that worked for this buyer, so next week's pull goes straight there.

Search Console needs no pull: once the buyer has added Yeez's email (setup's search step), `search_console_status` and `get_search_performance` read it directly. Facebook numbers come from the **social** skill.

## 4. Read the site

For each site:
- Call `get_site_brief` for its settings and recent titles.
- Read the site itself: its home page, its category pages, and its post list. On WordPress the public `https://<site>/wp-json/wp/v2/posts?per_page=100`, `/wp-json/wp/v2/categories?per_page=100` and `/wp-json/wp/v2/users` give titles, categories and authors fast. Elsewhere, read the sitemap.
- Read the 10–15 best articles by views (from the report's `top`) in full. That's how you learn the voice: length, structure, how they open, how they source, words they use and avoid.

## 5. Work it out

1. Run `yeez_data.py report --site SITE`. It gives views per platform, tier bands, the top articles, wasted-reach flops (shown thousands of times, barely read: the clearest headline failures), a sample of the low tail, views per article by publish hour and month, and daily totals.
2. Group the titles into 8–15 **veins**: repeatable topics or angles (a program, a kind of story, a product, a recurring event), each with the 2–10 keywords that identify it in a title. Use the top articles, the wasted reach and the tail sample.
3. Save them as `yeez-work/data/veins-SITE.json` (`[{"name": …, "keywords": […]}]`) and run the report again with `--veins`. Each comes back with views per article (VPA), its ratio to the site average, its 20K+ count and a month-by-month trend.
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
