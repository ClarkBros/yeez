---
name: articles
description: Writes, checks and schedules an article (or a numbered gallery) for each of today's picked headlines on the buyer's sites. Use when the user types /yeez:articles, asks Yeez to write today's articles, or as the second half of /yeez:run.
---

# Yeez articles

Read [../core/rules.md](../core/rules.md) and [../core/platforms/README.md](../core/platforms/README.md) first, then the file in [../core/platforms/](../core/platforms/) for every platform the site publishes to (its `platforms` setting, or `channels.syndication` in the buyer's basics). Those rules bind every article.

**Needs:** today's picked headlines. For each connected site, call `get_headlines`; it returns only headlines still waiting for an article. If it returns none, call it again with `include_done: true`: if that's empty too, no headlines were picked today, so follow the **headlines** skill for that site first (unattended: do it, don't ask); if they're all written or held, this site is done. Write one article per waiting headline, strongest first. When you hold one, write the replacement `hold_headline` returns, so the site still gets its full day.

If the site's settings have `galleries_per_day` above 0, that many of the day's picks are galleries instead: follow [gallery.md](gallery.md) for those. **Never galleries on a NewsBreak site** (NewsBreak pays on article page views only): if a NewsBreak site has `galleries_per_day` set, write articles and say so once in the report.

## For each headline

1. **Verify it is true today, before writing.** Re-open the primary sources from the headline's facts. Check that:
   - the rule is in effect, or is clearly labeled as a proposal
   - deadlines are still open
   - events are recent (about 30 days)
   - figures are current for the year stated
   - company status is current

   If the story fails, call `hold_headline` with the reason. It returns a `replacement` headline when there's a reserve: write that one next.
2. **Gather sources** the way this headline's story type says (`story_type` on the headline, `sourcing` in the brief's `story_types.guide`). Money and rule stories: at least five, mostly primary or official, from at least two sites. People, local, celebrity and sports stories: the named outlet that reported it plus at least one more that confirms it. Never Reddit, forums or anonymous posts. If a site blocks the automated check (the check says so), read it yourself in the browser; that's not an error.
3. **Write in the buyer's voice** (from `get_site_brief`). Before the first article of the run, read two or three of `settings.profile.voice_samples` in full, from the same vein as today's stories where possible, and follow `voice_notes`: their length, how they open, how they're broken up, how they source. Write like a reporter talking to a reader:
   - Open with a short intro paragraph of two to four sentences.
   - Then three to five `<h2>` sections named for this story.
   - Keep paragraphs short.
   - Link each fact inline to its source, once per source.
   - Name the person or institution behind the central claim ("said", "according to").
   - Write in the third person, with no "I", "we" or "you".
   - People stories: tell it as the story of the person, warmly, in the order it happened, with what the outlet reported them saying (attributed and linked). Never invent a quote, a feeling or a detail.
   - No research narration, no stock filler, no hype, no tables, no `<h1>`, and no source list at the end.

   The body must state every specific the headline promises: each number, each named source, each item in a counted list. If the headline holds something back (a cliffhanger), answer it in the first two paragraphs. The title must equal the picked headline.
4. **Check it.** Call `check_article` with the title, the HTML and the source URLs.
   - **fix:** rewrite what the findings name, then check again, up to three times.
   - **hold:** call `hold_headline` with the reason, then write the `replacement` it returns.
   - **pass:** continue.

   If the headline overstates its own sources, make the smallest sourced correction to the title instead of holding a true story: change only the wrong element (cap vs flat, alleged vs found, the right state, date or year) to the specific the sources support, never to something vaguer, and never tone it down. Note every correction (original → corrected, with the source) for the report. Hold only when the story itself fails; aim for no more than 3 holds per 50.
5. **Link the site's own articles.** Call `get_related_posts` with the story's main subject. Link 2–4 that genuinely fit, with natural anchor text ("the 2027 premium change"), never in the first two paragraphs. Skip it when nothing fits. These don't count as sources.
6. **Place an offer, only if one fits.** Call `match_offers` with the article text, `place: "article"`, and the headline as `ref`. If there's a match, add one short sentence near the end that links its tracked `link` with its `cta`. Follow its allowed and banned claims, and never promise money. If nothing matches, add nothing.
7. **Pick an image.** Call `find_images` with a short description of the story's actual subject (a building, product, place or document), not an abstract idea. It must be at least 1200px wide (Google Discover); pick one that is recognizable at thumbnail size, and never a logo or a picture full of text. Write `image_alt` as a plain description of what the photo shows.
8. **Write the search fields** (see [seo.md](seo.md)): `seo_title`, `meta_description`, `slug`, `focus_keyword`, and up to 3 `tags` from the site's own tag list.
9. **Schedule it.** Call `schedule_article` with:
   - the `headline_id`, title, HTML and sources
   - the `category` that fits best from the site's own categories, and the `author` from the site's authors whose subjects fit that category best (never by rotation)
   - the search fields from step 8
   - the chosen `image_url`, `image_credit` and `image_alt`

   If the reply has `newsbreak_flag` NOT SET, put it at the top of the report (the article won't reach NewsBreak) and keep going.

   Yeez re-checks the article, places it in the site's next publish slot, adds the image credit, the newsletter signup line (if set up) and the AI-assistance line, and sets the author and category. If it refuses, follow its findings.

## Across the night's set

Keep a running list, as you go, of each article's opening sentence pattern and its section headings. Before writing the next one, look at the list: no two articles in a run may share an opening pattern, a repeated sentence or paragraph, or the same section shape, and no headline formula may repeat across the set. Vary them as you write; it's too late once they're scheduled.

## Report

Per site, give one short line per article: the headline, the local publish time, and the edit link. Then list headline corrections (original → corrected) and anything held, with the reason. NewsBreak sites: say how many posts got the NewsBreak flag (it should be all of them). Remind the user they can review or change anything before it publishes, with `/yeez:scheduled` or in their site's editor.
