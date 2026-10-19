---
name: run
description: The daily Yeez run. Picks today's headlines, writes, checks and schedules the articles for every connected site, then schedules the Facebook and Instagram posts that share them and builds the next newsletter issue. Use when the user types /yeez:run, or from the buyer's daily scheduled task.
---

# Yeez daily run

1. Call `whoami`. If Yeez isn't connected or the license isn't active, stop and say so in one line.
2. For each connected site from `list_sites`, follow the **headlines** skill, then the **articles** skill.
3. If any Facebook Page or Instagram account is connected (`list_social_accounts`), follow the **social** skill so today's articles get shared.
4. If the newsletter is set up and tomorrow is a send day (from `get_newsletter_brief` settings), follow the **newsletter** skill for tomorrow's issue.
5. Finish with one short summary per site and account:
   - articles and posts scheduled, with times
   - anything held, and why
   - the review links: the site's `/wp-admin/edit.php?post_status=future` page, and `list_social_queue` for posts

When this runs as a scheduled task with nobody watching, never stop to ask questions. Make the most reasonable choice, hold what can't be verified, and put anything that needs the buyer's attention at the top of the summary.
