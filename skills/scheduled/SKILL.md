---
name: scheduled
description: Shows the posts Yeez has scheduled on the buyer's sites, with publish times and edit links, so they can review anything before it goes out. Use when the user types /yeez:scheduled or asks what's scheduled.
---

# Yeez scheduled posts

Call `list_scheduled` for each connected site (`list_sites`), or for the site the user names.

Show a short list per site: the local publish time, the title, and the edit link. If there's nothing scheduled, say so.

Tell the user they can open any edit link to change or unschedule a post in their site's editor, and that anything they don't touch publishes on schedule.
