---
name: articles
description: Writes, checks and schedules an article for each of today's picked headlines on the buyer's WordPress sites. Use when the user types /yeez:articles, asks Yeez to write today's articles, or as the second half of /yeez:run.
---

# Yeez articles

For each connected site, call `get_headlines` and write one article per picked headline, strongest first.

## For each headline

1. **Verify it is true today, before writing.** Re-open the primary sources from the headline's facts. Check that:
   - the rule is in effect, or is clearly labeled as a proposal
   - deadlines are still open
   - events are recent (about 30 days)
   - figures are current for the year stated
   - company status is current

   If the story fails, call `hold_headline` with the reason and move on.
2. **Gather sources.** Use at least five, mostly primary or official, from at least two different sites, and at most one mainstream news site.
3. **Write in the buyer's voice** (from `get_site_brief`). Write like a reporter talking to a reader:
   - Open with a short intro paragraph of two to four sentences.
   - Then three to five `<h2>` sections named for this story.
   - Keep paragraphs short.
   - Link each fact inline to its source, once per source.
   - Name the person or institution behind the central claim ("said", "according to").
   - Write in the third person, with no "I", "we" or "you".
   - No research narration, no stock filler, no hype, no tables, no `<h1>`, and no source list at the end.

   The body must state every specific the headline promises: each number, each named source, each item in a counted list. The title must equal the picked headline.
4. **Check it.** Call `check_article` with the title, the HTML and the source URLs.
   - **fix:** rewrite what the findings name, then check again, up to three times.
   - **hold:** call `hold_headline` with the reason.
   - **pass:** continue.

   If the headline overstates its own sources, make the smallest sourced correction to the title instead of holding a true story.
5. **Pick an image.** Call `find_images` with a short description of the story's actual subject (a building, product, place or document), not an abstract idea. Choose one that is recognizable at thumbnail size.
6. **Schedule it.** Call `schedule_article` with:
   - the `headline_id`, title, HTML and sources
   - a one-sentence `excerpt`
   - the chosen `image_url`, `image_credit` and `image_alt`

   Yeez re-checks the article, places it in the site's next publish slot, adds the image credit and the AI-assistance line, and sets the author and category. If it refuses, follow its findings.

## Report

Per site, give one short line per article: the headline, the local publish time, and the edit link. Then list anything held, with the reason. Remind the user they can review or change anything before it publishes, with `/yeez:scheduled` or in WordPress.
