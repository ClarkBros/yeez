---
name: social
description: Writes, renders and posts the day's Facebook and Instagram content for the buyer's connected Pages and accounts (news image cards, text image cards, gradient posts and stories), learning from what worked on each one. Use when the user types /yeez:social, asks for today's social posts, or as part of /yeez:run.
---

# Yeez social

The day's posts for every connected Page and Instagram account: written here, rendered by the script in this folder, uploaded to yeez.ai, then scheduled on Facebook (or published on Instagram). Read [format-rules.md](format-rules.md) before writing anything; it is the house style and it binds every post.

## 0. Ready?

1. Call `list_social_accounts`. If nothing is connected, call `connect_meta`, give the buyer the link (it walks them through their own Meta app, about 15 minutes), and continue when they say it's done.
2. Make sure the render script can run: `python3 -c "import PIL"`. If that fails, `pip install pillow` (add `--break-system-packages` if pip asks for it).
3. Call `get_media_upload_url` and keep `upload_url` for step 4.

## 1. Learn, per account

Call `get_social_brief` for the account. Keep its `brand`, `logo_url`, `timezone` and `today`.

From `recent_posts`, rank by shares, then comments, then reactions. Note what the top quarter share: topic, the person named, the number, the ending type, the format. Note what the bottom quarter share. Write today more like the winners. Keep one or two posts that test something new.

The first time you see an account, if its name has no "verified" status and the buyer hasn't been told, tell them once: "Getting this Page verified (Meta Verified) helps it get trusted and shown. The cards never fake a badge."

## 2. Plan the day

- **Slots:** from [grids.json](grids.json). Use `settings.grid` if the account has one; otherwise `core` for a Facebook Page posting 8+ a day, `starter` for fewer, `instagram` for Instagram. If `settings.mix` is set, it overrides the counts. Skip reel slots for now (reels arrive in an update). Add the account's offset (grids.json `offset_rule`).
- **Topics:** today's scheduled articles in `articles_to_share` first, strongest first, then the other strong stories from today's headline research (`get_headlines` for the buyer's sites). Spread the day across topics; never the same topic twice in a row on one Page. Several Pages can share a story, but each gets its own wording.
- **Calls to action:** about half the feed posts, only where an offer or keyword fits (format-rules.md → Calls to action).
- Instagram: news_image, text_image and story only (no gradient, no link posts). Captions end with where to find the full story (links aren't clickable) and 3–5 hashtags.

## 3. Write the queue

Work in a folder named `yeez-work` (create it next to where you run commands).

1. Write `yeez-work/brands.json`: a list with one entry per account, built from each brief's `brand` plus `logo_url`:
   `[{"code": "<brand.code>", "name": "<brand.name>", "c1": "...", "c2": "...", "c3": "...", "icon": "...", "logo_url": "<logo_url>"}]`
2. For each account, write `yeez-work/queue/<today>/<CODE>.json`:

```json
{
  "page": "<CODE>",
  "account": "<the account name, for schedule_social_post>",
  "timezone": "<brief.timezone>",
  "audience": "older | general",
  "items": [
    {
      "id": "<code>-<MMDD>-01",
      "type": "news_image | text_image | gradient | story",
      "time": "<today>T20:00:00<offset>",
      "topic": "...",
      "source_urls": ["https://..."],
      "caption": "...",
      "overlay": "... (news_image)",
      "text": "... (text_image, gradient, story)",
      "image_brief": {"format": "T", "subject": "person: <Full Name> official portrait", "query": "4-7 concrete words"},
      "cta": {"mode": "KEYWORD | LINK | none", "keyword": "WORD", "pill": "the thing we send", "first_comment": "One sentence: https://yeez.ai/r/..."},
      "status": "written"
    }
  ]
}
```

Set `audience` to `older` when the buyer's audience is mostly 55+; the photo search then skips young-adult and crypto stock.

3. Check every item against format-rules.md before rendering: word counts (overlay 20–45, story ≤25, text_image ≤45, gradient ≤130 characters), the ending, no emoji, every number in `source_urls`. Fix misses; never shrink text to make it fit.

## 4. Render and upload

From the folder that contains `yeez-work`, run the script that sits next to this file (one command per account if a run takes long):

```
python3 <this skill's folder>/scripts/yeez_build.py --date <today> --work yeez-work --upload "<upload_url>" [--page CODE]
```

It finds a licensed photo for each card (Wikimedia Commons and Openverse; Pexels, Unsplash, Pixabay or Freepik too if the buyer added keys to `yeez-work/image-keys.json`), renders each card, uploads it, and writes `media_url` and the photo credit back into the queue file. Then **look at every rendered image** in `yeez-work/queue/<today>/media/`:
- the photo must show what the card is about (the named person, the actual thing), with no text, logos or watermarks fighting the headline;
- nothing cut off.

For a bad photo, change `image_brief` (a better `subject` or `query`), set the item back to `"status": "written"`, and run the script again with `--rebuild --page CODE`. Two tries, then use the card without a photo or drop the item.

If the upload step says it's blocked, the AI app isn't allowed to reach yeez.ai. Tell the buyer: "Turn on network access for your AI app (Claude: Settings → Capabilities, allow network access, or add yeez.ai to the allowed domains). It's in the setup video." Then stop the social part of the run; the articles still go out.

## 5. Post

For every built item, in time order, call `schedule_social_post`:
- `account`: the queue file's `account`
- `format`: `photo` for news_image and text_image, `gradient`, or `story`
- `image_url`: the item's `media_url` (photo and story)
- `caption`: the item's `caption` (for gradient: its `text`)
- `first_comment`: `cta.first_comment` on Facebook LINK posts
- `publish_at`: the item's `time` (Facebook feed posts only; Meta schedules them. Instagram posts and all stories go out the moment you post them.)

Mark each item `"status": "scheduled"` (or `"held"` with the reason) in the queue file as you go. If a call fails, read its error, fix the item once and retry; otherwise hold it.

## Report

Per account: how many of each type were scheduled or posted, with local times; anything held and why; and that the buyer can review everything with `list_social_queue`, on the Page, or in Meta Business Suite before it goes live.
