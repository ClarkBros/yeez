---
name: run
description: The daily Yeez run. Picks today's headlines, writes, checks and schedules the articles for every connected site, posts to Facebook and Instagram, builds the next newsletter issue, and on Mondays runs the weekly review. Use when the user types /yeez:run, or from the buyer's daily scheduled task.
---

# Yeez daily run

1. Call `whoami`. If Yeez isn't connected or the license isn't active, stop and say so in one line.
1b. Follow the **learn** skill in daily mode: refresh NewsBreak if this app has a browser that's already logged in (never ask), then refresh each site's marching orders. On Mondays, the review's full learn replaces this.
2. For each connected site from `list_sites`, follow the **headlines** skill, then the **articles** skill.
3. If any Facebook Page or Instagram account is connected (`list_social_accounts`), follow the **social** skill: it writes, renders and posts the day's cards, gradient posts and stories for every account.
3b. If any site has search articles left this week (`get_search_ideas` → `left_this_week`), follow the **search** skill for one of them, and list anything waiting for the buyer's approval at the top of the summary.
4. **On Mondays** (in the buyer's timezone), follow the **review** skill before writing new articles, so this week's headlines use the updated rules.
5. If the newsletter is set up and tomorrow is a send day (from `get_newsletter_brief` settings), follow the **newsletter** skill for tomorrow's issue.
6. Finish with one short summary per site and account:
   - articles and posts scheduled, with times
   - anything held, and why
   - on Mondays, the weekly review highlights and the earn-back tracker
   - the review links: the site's `/wp-admin/edit.php?post_status=future` page, and `list_social_queue` for posts

When this runs as a scheduled task with nobody watching, never stop to ask questions. Make the most reasonable choice, hold what can't be verified, and put anything that needs the buyer's attention at the top of the summary.
