---
name: search
description: The Yeez search lane. For sites Google already trusts (decided from each site's own Search Console data), plans and writes this week's articles built for Google search, saves them for the buyer's approval, and reports how the buyer's sites do in Google Search, Discover and Google News. Use when the user types /yeez:search, asks about SEO, Google, search traffic or Search Console, or from the Articles task and daily run when a site has search articles left this week.
---

# Yeez search lane

Read [../core/rules.md](../core/rules.md) first: who Yeez is and the rules it never breaks.

Most Yeez articles follow the news for feeds (NewsBreak, MSN, Facebook). The search lane is different: a few articles a week, each answering one question people actually search, built deeper, and **approved by the buyer before they go live**. That's Google's own rule for AI-assisted content (manual review before publishing), and the network's own experience: volume serves the feeds, a selected slice serves search.

## 1. Ideas

For each connected site, call `get_search_ideas` (add one or two topics from this week's best stories). It returns:
- `left_this_week`: how many search articles the site still has this week (0 when the site doesn't qualify yet or the buyer turned them off; `search_gate.reasons` says why). If 0, stop for that site and don't mention search articles unless asked.
- `search_console.questions` and `refresh_candidates`: what people already search to find the site. An existing page ranking 8–20 for a question is better improved than duplicated: tell the buyer which page to expand instead of writing a new one.
- `google_suggestions`: what people type into Google about the site's big subjects.
- `already_written`: never write the same question twice.

Pick the questions with real demand that the site can answer better than anyone: specific, current, about the site's audience ("How does the Medicare Part B late penalty work?"), not a broad topic ("Medicare").

## 2. Write it deeper than a news article

Follow the **articles** skill's verification and voice rules, plus:
- **Answer the question in the first two sentences**, with the number or the rule, then explain.
- Cover the questions a reader asks next (the "people also ask" around it), each under its own `<h2>` phrased the way people ask it.
- Primary sources for every figure (the agency, the law, the official table), linked where stated. Add one thing a quick rewrite wouldn't have: a worked example with real numbers, a comparison, a dated table of the official figures, or a checklist.
- 2–4 links to the site's own related articles (`get_related_posts`), never in the first two paragraphs.
- Title: the question or its answer, plainly ("How the Medicare Part B Late Enrollment Penalty Works"). No hype.
- Search fields as in [../articles/seo.md](../articles/seo.md); all four are required here.
- Featured image 1200px+ (`find_images`).

Check with `check_article` (`search: true`), then call `schedule_article` with `search: true`. It's saved on the site as waiting (WordPress: **Pending**; other platforms: a draft) and does not publish.

## 3. Approval

Tell the buyer, per site: the title, the question it answers, and the edit link. They read it, change anything they want, and approve it on their yeez.ai dashboard (one button), by telling you in chat, or on WordPress from Posts → Pending, in which case call `approve_search_article`. Never approve on their behalf. `list_search_articles` shows what's waiting.

## 4. How search is doing (on request, and in the Monday review)

`get_search_performance` per site: clicks, impressions, click rate and position this week vs last, for Web, Discover, Google News and the News tab; top pages; refresh candidates; and results with many impressions but few clicks (rewrite those pages' search title and description). `check_indexing` samples whether the newest articles made it into Google's index; a growing share of "crawled, not indexed" is an early warning that Google sees too many thin pages, so slow the volume or deepen the articles.

Say it plainly: what grew, what shrank, the 3 best next moves. Never promise rankings or traffic.

## 5. Setup checks

If `site_seo_status` lists fixes (plugin not installed, crawlers blocked, missing trust pages, author bios, Search Console not connected), walk the buyer through them one at a time; see the **setup** skill's search step.
