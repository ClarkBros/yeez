---
name: newsletter
description: Builds the buyer's newsletter issue from the day's best story, with one fitting offer or paid recommendation, and puts it in their email platform (beehiiv directly) or a copy-ready page. Use when the user types /yeez:newsletter, asks for today's issue, or from /yeez:run on send days.
---

# Yeez newsletter

Read [../core/rules.md](../core/rules.md) and [../core/platforms/newsletter.md](../core/platforms/newsletter.md) first. **Yeez never sends an issue**: it saves a draft (or schedules it only when the buyer said Yeez may). Runs on the day before each send day.

**Needs:** newsletter settings and the last two days' articles. If no articles were scheduled in the last two days, there's nothing to build: say so and stop.

1. Call `get_newsletter_brief`. If the newsletter isn't set up, ask for these, then call `save_newsletter_settings`:
   - its name and platform
   - its signup page
   - send days and send time
   - timezone
2. **Pick the story.** Choose the top story from `stories`: the highest score that has been or will be published. Skip any story a subject in `recent_subjects` already covered.
3. **Write the issue.** Keep it short and useful. Readers should finish it in about two minutes.
   - **Subject:** under 70 characters, specific, plain words, no emoji, no all-caps, no money promises, no fake "RE:" or false urgency. Name the exact thing that changes.
   - **Preview text:** one line that adds a second fact rather than repeating the subject.
   - **Body:**
     - a two-to-three-sentence summary of the story with its key figure and date
     - a short section on who it affects and what changes for them
     - a link to the full story
   - **One offer at most,** from `offers`, and only when it genuinely fits the story. Use its link exactly as given (it's a tracked link), its `cta`, and a plain sentence from its `blurb`. A `recommendation` offer goes in a short "Also worth reading" line at the end.
   - Sign off with the newsletter's name, not a person's.
   - Format as simple email-safe HTML: paragraphs, one heading, links. No scripts or forms.
4. **Save it.** Call `save_newsletter_issue`. If it lists problems, fix them and save again.
5. **Put it on the platform.** Try these in order:
   - **The beehiiv connector** in this app: create the post there as a draft (or scheduled for the next send day and time, only if the buyer has said Yeez may schedule sends). Then call `save_newsletter_issue` again with `platform_ref` set to the beehiiv post ID.
   - **beehiiv by API** (Pro or Enterprise plans), when `yeez-work/beehiiv.json` exists: save the HTML to `yeez-work/newsletter/<date>.html` and run `python3 <this skill's folder>/scripts/beehiiv_post.py --title "<subject>" --preview "<preview>" --html yeez-work/newsletter/<date>.html` (add `--schedule <ISO time>` only with the buyer's standing OK). It prints the post ID; save it as `platform_ref`. Never print or read out the key file.
   - **Anything else:** give the buyer the `review_link`. It shows the issue and a Copy HTML button for their platform.
   - On beehiiv with neither set up, tell them once: add the beehiiv connector in their AI app, or (Pro and Enterprise) make an API key in beehiiv (Settings → Integrations → API) and save it with the publication ID in `yeez-work/beehiiv.json` as `{"api_key": "…", "publication_id": "pub_…"}`. They do this themselves; never take the key in the chat.

Report the subject, the story, the offer used (if any), and where the issue is (beehiiv link or review link).
