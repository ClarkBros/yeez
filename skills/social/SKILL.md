---
name: social
description: Writes and schedules today's Facebook and Instagram posts for the buyer's connected Pages and accounts, learning from what worked on each one. Use when the user types /yeez:social, asks for today's social posts, or as part of /yeez:run.
---

# Yeez social

## 0. Connected?

Call `list_social_accounts`. If nothing is connected, call `connect_meta` and give the buyer the link. It walks them through creating their own Meta app (about 15 minutes, no Facebook review), then connecting their Pages and Instagram. Continue when they say it's done.

## For each connected account

1. **Learn.** Call `get_social_brief`. Look at `recent_posts`:
   - Rank them by shares, then comments, then reactions.
   - Note what the top quarter have in common: topic, opening line, length, format (link, photo, text).
   - Note what the bottom quarter share.

   Write today's posts more like the winners and less like the losers. Keep one or two posts that test something new.
2. **Plan the day.** The account's daily count is in `settings.per_day`. Lead with posts that share today's articles from `articles_to_share`, strongest first. Fill the rest with native posts on the same stories: a striking fact, a short explainer, or a question about the news.
3. **Write each post.**
   - Open with the most concrete fact in the first line: the figure, date, or who's affected.
   - Two to five short lines. Plain words, third person, no hype, no ALL CAPS, no emoji, no clickbait, no "share if you agree".
   - **Facebook:** for an article post, pass the article URL as `link` and don't paste it into the text.
   - **Instagram:** use the article's image (`image_url`, a JPEG works best) and end with a short line telling readers where to find the full story. Links in Instagram captions aren't clickable. Add three to five relevant hashtags at the end.
   - At most one post a day per account may ask readers to comment a keyword (see `/yeez:dm`). Phrase it as an offer ("Comment GUIDE and we'll message you the checklist"), only for a keyword that exists in `list_dm_flows`.
4. **Post.** Call `schedule_social_post` for each post. Facebook posts are scheduled through the account's posting window; Instagram posts go out right away. If it refuses, follow its reason and try again once.

## Report

For each account, list the posts with their local times (Instagram: the live link). Mention anything that failed, and that the buyer can review queued posts with `list_social_queue`, on their Page, or in Meta Business Suite.
