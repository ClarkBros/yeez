---
name: run
description: The daily Yeez run. Picks today's headlines and then writes, checks and schedules the articles for every connected site. Use when the user types /yeez:run, or from the buyer's daily scheduled task.
---

# Yeez daily run

1. Call `whoami`. If Yeez isn't connected or the license isn't active, stop and say so in one line.
2. For each connected site from `list_sites`, follow the **headlines** skill, then the **articles** skill.
3. Finish with one short summary per site: articles scheduled (with publish times), anything held and why, and the review link: the site's `/wp-admin/edit.php?post_status=future` page.

When this runs as a scheduled task with nobody watching, never stop to ask questions. Make the most reasonable choice, hold what can't be verified, and put anything that needs the buyer's attention at the top of the summary.
