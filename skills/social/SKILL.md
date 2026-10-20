---
name: social
description: Writes, renders and posts the day's Facebook and Instagram content for the buyer's connected Pages and accounts (news image cards, text image cards, gradient posts, stories and reels over the buyer's own footage), learning from what worked on each one. Use when the user types /yeez:social, asks for today's social posts, or as part of /yeez:run.
---

# Yeez social

The day's posts for every connected Page and Instagram account: written here, rendered and posted by the scripts in this folder straight to Facebook and Instagram with the buyer's own keys file. No images or videos go through yeez.ai. Read [format-rules.md](format-rules.md) before writing anything; it is the house style and it binds every post.

## 0. Ready?

1. Call `list_social_accounts`. If nothing is connected, call `connect_meta`, give the buyer the link (it walks them through their own Meta app, about 15 minutes), and continue when they say it's done.
2. Make sure the render script can run: `python3 -c "import PIL"`. If that fails, `pip install pillow` (add `--break-system-packages` if pip asks for it).
3. **The keys file.** Posting uses `yeez-work/yeez-keys.json` (the buyer's own Facebook and Instagram keys). If it's missing, or an account isn't in it: call `get_social_keys_link` and save the file straight into the folder with `python3 <this skill's folder>/scripts/yeez_post.py --fetch-keys "<link>" --work yeez-work`. Never print the file or paste its contents into the chat. If that command can't reach the internet, the AI app needs network access turned on (Claude: Settings → Capabilities; it's in the setup video); the buyer can also download the file from the Facebook connect page and drop it in the folder.
4. **Reels** need the account's `settings.footage_folder` (the buyer's shared Google Drive folder) and ffmpeg (`ffmpeg -version`; if missing: `apt-get install -y ffmpeg`, or `pip install imageio-ffmpeg` and put its binary on PATH). List the folders once: `python3 <this skill's folder>/scripts/yeez_footage.py --folder "<footage_folder>" --list`. Its folder names are the moods you can use for `reel_mood`. No footage folder, no music, or no ffmpeg: write the reel slots as news_image cards and tell the buyer once what's missing.

## 1. Learn, per account

Call `get_social_brief` for the account. Keep its `brand`, `logo_url`, `timezone` and `today`.

From `recent_posts`, rank by shares, then comments, then reactions. Note what the top quarter share: topic, the person named, the number, the ending type, the format. Note what the bottom quarter share. Write today more like the winners. Keep one or two posts that test something new.

The first time you see an account, if its name has no "verified" status and the buyer hasn't been told, tell them once: "Getting this Page verified (Meta Verified) helps it get trusted and shown. The cards never fake a badge."

## 2. Plan the day

- **Slots:** from [grids.json](grids.json). Use `settings.grid` if the account has one; otherwise `core` for a Facebook Page posting 8+ a day, `starter` for fewer, `instagram` for Instagram. If `settings.mix` is set, it overrides the counts. Add the account's offset (grids.json `offset_rule`).
- **Topics:** today's scheduled articles in `articles_to_share` first, strongest first, then the other strong stories from today's headline research (`get_headlines` for the buyer's sites). Spread the day across topics; never the same topic twice in a row on one Page. Several Pages can share a story, but each gets its own wording.
- **Calls to action:** about half the feed posts, only where an offer or keyword fits (format-rules.md → Calls to action).
- Instagram: news_image, text_image, story, reel and image_reel (no gradient, no link posts). Captions end with where to find the full story (links aren't clickable) and 3–5 hashtags.

## 3. Write the queue

Work in a folder named `yeez-work` (create it next to where you run commands).

1. Write `yeez-work/brands.json`: a list with one entry per account, built from each brief's `brand` plus `logo_url`:
   `[{"code": "<brand.code>", "name": "<brand.name>", "c1": "...", "c2": "...", "c3": "...", "icon": "...", "logo_url": "<logo_url>"}]`
2. For each account, write `yeez-work/queue/<today>/<CODE>.json`:

```json
{
  "page": "<CODE>",
  "account": "<the account's id or name, as in yeez-keys.json>",
  "timezone": "<brief.timezone>",
  "audience": "older | general",
  "footage_folder": "<settings.footage_folder, for reels>",
  "items": [
    {
      "id": "<code>-<MMDD>-01",
      "type": "news_image | text_image | gradient | story | reel | image_reel",
      "time": "<today>T20:00:00<offset>",
      "topic": "...",
      "source_urls": ["https://..."],
      "caption": "...",
      "overlay": "... (news_image)",
      "text": "... (text_image, gradient, story)",
      "image_brief": {"format": "T", "subject": "person: <Full Name> official portrait", "query": "4-7 concrete words"},
      "reel_format": "R | P (reels)", "reel_mood": "<a footage folder name> (reel R)", "source_item": "<a card's id> (image_reel)",
      "cta": {"mode": "KEYWORD | LINK | none", "keyword": "WORD", "pill": "the thing we send", "first_comment": "One sentence: https://yeez.ai/r/..."},
      "status": "written"
    }
  ]
}
```

Set `audience` to `older` when the buyer's audience is mostly 55+; the photo search then skips young-adult and crypto stock.

3. Check every item against format-rules.md before rendering: word counts (overlay 20–45, story ≤25, text_image ≤45, gradient ≤130 characters, reel R 6–10 lines and 35–80 words, reel P 20–45 words), the ending, no emoji, every number in `source_urls`. Fix misses; never shrink text to make it fit.

## 4. Render

From the folder that contains `yeez-work`, run the script that sits next to this file (one command per account if a run takes long):

```
python3 <this skill's folder>/scripts/yeez_build.py --date <today> --work yeez-work [--page CODE]
```

A reel takes about a minute to render (it downloads only the clips it needs from the buyer's Drive folder); run reels with `--type reel,image_reel --page CODE` in their own command if a command would run long. It finds a licensed photo for each card (Wikimedia Commons and Openverse; Pexels, Unsplash, Pixabay or Freepik too if the buyer added keys to `yeez-work/image-keys.json`), renders each card, and writes the media path and the photo credit back into the queue file. Then **look at every rendered image** in `yeez-work/queue/<today>/media/`:
- the photo must show what the card is about (the named person, the actual thing), with no text, logos or watermarks fighting the headline;
- nothing cut off;
- for reels, pull one frame (`ffmpeg -ss 4 -i <reel>.mp4 -frames:v 1 frame.png`) and check the lines are readable and the footage fits the story.

For a bad photo, change `image_brief` (a better `subject` or `query`), set the item back to `"status": "written"`, and run the script again with `--rebuild --page CODE`. Two tries, then use the card without a photo or drop the item.

## 5. Post

```
python3 <this skill's folder>/scripts/yeez_post.py --date <today> --work yeez-work [--page CODE]
```

It posts every built item straight to the account in its queue file, with the keys file:
- Facebook news image and text image cards, gradient posts, link posts and reels are **scheduled** at their `time` with Meta's own scheduler (anything due in under 15 minutes moves to 20 minutes out).
- Stories, and everything on Instagram, are **published now** (Instagram reels wait for Instagram to finish processing, up to about 4 minutes).

Then call `record_social_posts` with the list the script saved in `yeez-work/queue/<today>/_to_record.json`. That puts the posts in the buyer's queue and dashboard, and any LINK post's `first_comment` is added by yeez.ai the moment Facebook says the post is live.

If an item failed, read its `error` in the queue file, fix it once (shorten, re-render, or re-fetch the keys) and run the post script again: it only posts items still marked `built`. Otherwise set it to `"held"` with the reason.

## Report

Per account: how many of each type were scheduled or posted, with local times; anything held and why; and that the buyer can review everything with `list_social_queue`, on the Page, or in Meta Business Suite before it goes live.
