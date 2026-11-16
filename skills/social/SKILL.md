---
name: social
description: Writes, renders and posts the day's Facebook, Instagram and Pinterest content for the buyer's connected Pages and accounts (news image cards, text image cards, designed recipe and product cards, gradient posts, stories, reels and pins over the buyer's own footage), learning from what worked on each one. Use when the user types /yeez:social, asks for today's social posts, or as part of /yeez:run.
---

# Yeez social

The day's posts for every connected Page and Instagram account: written here, rendered and posted by the scripts in this folder straight to Facebook and Instagram with the buyer's own keys file. No images or videos go through yeez.ai. Read [format-rules.md](format-rules.md) before writing anything; it is the house style and it binds every post. If the buyer has Pinterest, [pinterest.md](pinterest.md) adds its steps to each mode below (learn P1, write P2–P3, build P4, post P5, now: schedule pins waiting for room).

First read [../core/rules.md](../core/rules.md) and [../core/platforms/facebook.md](../core/platforms/facebook.md). The money-safety, repost-cap and warm-up rules there bind every post.

## Modes (one task or four)

The work hands off through files in `yeez-work/`, so it runs as one task or as four scheduled tasks in this order, each starting after the previous one has had time to finish (see [../core/tasks.md](../core/tasks.md)):

| Prompt | Does | Needs | Leaves |
|---|---|---|---|
| `/yeez:social learn` | steps 0–1 | connected accounts | `yeez-work/social/<CODE>-learn.md` per account |
| `/yeez:social write` | steps 2–3 | today's learn notes (if missing or older than a day, do step 1 first) | `yeez-work/queue/<today>/<CODE>.json`, items `written` |
| `/yeez:social build` | step 4 | today's queue files (if none, do write first) | rendered media, items `built` |
| `/yeez:social post` | step 5 | built items (if none, do build first) | scheduled posts, recorded with `record_social_posts` |

| `/yeez:social now` | step 5 again | today's queue | stories and Instagram items posted at their times, waiting pins scheduled |
| `/yeez:social pinterest` | pinterest.md P1–P5 | a Pinterest business account in the app's browser | pins scheduled on Pinterest |

`/yeez:social` with no mode does learn through post. Every mode only picks up items in the state it needs, so running one twice never posts anything twice.

**Which day.** For learn, write, build and post, `<today>` below means the **posting day**: the brief's `today` when the run starts before noon local time, otherwise the day after, so an evening run builds tomorrow. For `now`, it is always the brief's `today`.

**Stories and Instagram can't be scheduled ahead.** Facebook feed posts are scheduled the moment `post` runs; stories (Facebook and Instagram) and every Instagram post wait in the queue until their time is under 30 minutes away. So when the buyer has stories or Instagram accounts, setup also creates a **social now** task that runs `/yeez:social now` at :10 past every hour of the posting window (06:10–21:10 in the account's timezone). It posts whatever is due and stops.

## 0. Ready?

0. **Can this app post?** Posting runs Yeez's scripts on the buyer's computer (or the app's own computer) and calls Facebook directly. If you can't run commands here, or `app_guide` said `social: false` for this app (ChatGPT, grok.com), stop: tell the buyer once that Facebook and Instagram posting runs from a computer app (Claude, Claude Code, Codex, Cursor, Grok Build, Kimi Code or Claw, Hermes or OpenClaw; their yeez.ai account page shows how to install it), and carry on with the rest of the run.
1. Call `list_social_accounts`. If nothing is connected, call `connect_meta`, give the buyer the link (it walks them through their own Meta app, about 15 minutes), and continue when they say it's done.
   **No skills folder here?** (You got these instructions from the `get_skill` tool.) Get the scripts first: `curl -fsSL https://yeez.ai/install.sh | sh -s ./yeez-skills`, then use `./yeez-skills/yeez-social` as "this skill's folder" below.
2. Make sure the render script can run: `python3 -c "import PIL"`. If that fails, `pip install pillow` (add `--break-system-packages` if pip asks for it).
3. **The keys file.** Posting uses `yeez-work/yeez-keys.json` (the buyer's own Facebook and Instagram keys). If it's missing, or an account isn't in it: call `get_social_keys_link` and save the file straight into the folder with `python3 <this skill's folder>/scripts/yeez_post.py --fetch-keys "<link>" --work yeez-work`. Never print the file or paste its contents into the chat. If that command can't reach the internet, the AI app needs network access turned on (Claude: Settings → Capabilities; Codex: network access for the sandbox; other apps: their sandbox or permissions settings; it's in the setup video); the buyer can also download the file from the Facebook connect page and drop it in the folder.
4. **Reels** need the account's `settings.footage_folder` (the buyer's shared Google Drive folder) and ffmpeg (`ffmpeg -version`; if missing: `apt-get install -y ffmpeg`, or `pip install imageio-ffmpeg` and put its binary on PATH). List the folders once: `python3 <this skill's folder>/scripts/yeez_footage.py --folder "<footage_folder>" --list`. Its folder names are the moods you can use for `reel_mood`. No footage folder, no music, or no ffmpeg: write the reel slots as news_image cards and tell the buyer once what's missing.

## 1. Learn, per account

Call `get_social_brief` for the account. Keep its `brand`, `logo_url`, `timezone` and `today`.

**Warm-up.** If `warmup` is set, this Page is new: plan only 2 original posts a day (news_image, text_image or gradient), with no links, no link posts, no calls to action and no keyword asks, and skip the rest of the Page's grid. If `warmup` isn't set but the Page has under 100 `followers` and fewer than 15 `recent_posts`, it's new too: call `save_social_settings` with `warmup_until` 7 days from today (keep its `per_day`) and treat it as warm-up. Tell the buyer once, in the report, why the Page is posting less this week.

Save what you learn in `yeez-work/social/<CODE>-learn.md` (date it): the winners' shared traits, the losers', and what to test today.

From `recent_posts`, rank by shares, then comments, then reactions. Note what the top quarter share: topic, the person named, the number, the ending type, the format. Note what the bottom quarter share. Write today more like the winners. Keep one or two posts that test something new.

The first time you see an account, if its name has no "verified" status and the buyer hasn't been told, tell them once: "Getting this Page verified (Meta Verified) helps it get trusted and shown. The cards never fake a badge."

## 2. Plan the day

- **Slots:** from [grids.json](grids.json). Use `settings.grid` if the account has one; otherwise `core` for a Facebook Page posting 8+ a day, `starter` for fewer, `instagram` for Instagram. If `settings.mix` is set, it overrides the counts. Add the account's offset (grids.json `offset_rule`).
- **Topics:** today's scheduled articles in `articles_to_share` first, strongest first, then the other strong stories from today's headline research (`get_headlines` for the buyer's sites). Spread the day across topics; never the same topic twice in a row on one Page. Several Pages can share a story, but each gets its own wording.
- **Repost cap.** Keep `yeez-work/social/concepts.csv` (`page,concept,first_date,last_date,times`): one row per concept (the same story, angle, on-image line or mechanism) per Page. Before planning an item, look up the concept on that Page: 3 times already = it's retired there, unless it's genuinely new news (a new number or event makes it a new concept). Each copy is worded fresh; never the same overlay or text on two Pages (plain black-background text posts may repeat word for word, still within the cap). Add or bump the row when you write the item.
- **Calls to action:** about half the feed posts, only where an offer or keyword fits (format-rules.md → Calls to action).
- Instagram: news_image, text_image, story, reel and image_reel (no gradient, no link posts). Captions end with where to find the full story (links aren't clickable) and 3–5 hashtags.

## 3. Write the queue

Work in a folder named `yeez-work` (create it next to where you run commands).

1. Write `yeez-work/brands.json`: a list with one entry per account, built from each brief's `brand` plus `logo_url`. Use each brief's `brand.code` exactly as given: yeez.ai keeps every account's code different, and the code names that account's queue file. To change a code, save it with `save_social_settings` (`brand.code`); never edit it only in the files.
   `[{"code": "<brand.code>", "name": "<brand.name>", "c1": "...", "c2": "...", "c3": "...", "icon": "...", "fonts": <brand.fonts, if set>, "logo_url": "<logo_url>"}]`

   **Card fonts.** When the buyer asks for a font on their cards (for example "use Gaegu Bold for the red line above the title"), save it on the account with `save_social_settings` `brand.fonts`: `script_font` is the short script line above the title (the kicker), `title_font` the headline, `small_font` the site label, `display_font` big numbers, `serif_font` serif titles. Write it as `"Family:weight"`, e.g. `"Gaegu:700"`. Any Google Fonts family works (it's fetched once into `yeez-work/fonts/google`). For their own font file, they put the .ttf/.otf in `yeez-work/fonts` and you use its family name. An empty string goes back to the default.
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
      "design": {"template": "center_box", "title": "...", "kicker": "...", "photos": ["..."]},
      "text": "... (text_image, gradient, story)",
      "image_brief": {"format": "T", "subject": "person: <Full Name> official portrait", "must": "1-3 words the photo shows (no person)", "query": "4-7 concrete words", "image_url": "<own-site photo from find_site_images, optional>"},
      "reel_format": "R | P (reels)", "reel_mood": "<a footage folder name> (reel R)", "source_item": "<a card's id> (image_reel)",
      "cta": {"mode": "KEYWORD | LINK | none", "keyword": "WORD", "pill": "the thing we send", "first_comment": "One sentence: https://yeez.ai/r/..."},
      "status": "written"
    }
  ]
}
```

Set `audience` to `older` when the buyer's audience is mostly 55+; the photo search then skips young-adult and crypto stock.

`design` (optional, news_image and text_image): renders the card in one of the pin designs instead (format-rules.md → Designed cards), at 1080x1350 for the feed. Use it for recipes, products, roundups and how-tos, where the buyer's own photo is the point; the same article's pin and Facebook card can share a design and photo.

3. Run the final check from [../core/platforms/facebook.md](../core/platforms/facebook.md) on every item (accurate and current, no banned money wording, no attack on a group, no private person, this Page's own version within the cap). Rewrite or drop anything that misses.
4. Check every item against format-rules.md before rendering: word counts (overlay 20–45, story ≤25, text_image ≤45, gradient ≤130 characters, reel R 6–10 lines and 35–80 words, reel P 20–45 words), the ending, no emoji, every number in `source_urls`. Fix misses; never shrink text to make it fit.

## 4. Render

From the folder that contains `yeez-work`, run the script that sits next to this file (one command per account if a run takes long):

```
python3 <this skill's folder>/scripts/yeez_build.py --date <today> --work yeez-work [--page CODE]
```

With more than one Page, hand the rendering to `yeez-renderer` helpers, one per Page (reels as their own job), following [../core/helpers.md](../core/helpers.md): call `get_model_plan` once, name the plan's `render` model on every hand-off, never more than `max_helpers_at_once` at the same time. Give each the date, the work folder, the Page code, this script's full path and whether it's the reels job. When they're done, you check the images below. With one Page, or if this app can't start helpers, run the commands yourself.

A reel takes about a minute to render (it downloads only the clips it needs from the buyer's Drive folder); run reels with `--type reel,image_reel --page CODE` in their own command if a command would run long. It finds a licensed photo for each card (Wikimedia Commons and Openverse; Pexels, Unsplash, Pixabay or Freepik too if the buyer added keys to `yeez-work/image-keys.json`), renders each card, and writes the media path and the photo credit back into the queue file. Then **look at every rendered image** in `yeez-work/queue/<today>/media/`:
- the photo must show what the card is about (the named person, the actual thing), with no text, logos or watermarks fighting the headline;
- nothing cut off;
- for reels, pull one frame (`ffmpeg -ss 4 -i <reel>.mp4 -frames:v 1 frame.png`) and check the lines are readable and the footage fits the story.

If the script prints **FONT PROBLEMS**, the cards were built with a stand-in font. Put that line first in your report to the buyer, with the fix it names.

**PHOTO CHECK.** When the script isn't sure a photo shows the `must` thing, or found none and used the brand background, it says so under PHOTO CHECK and marks the card; the post script holds marked cards. Look at each one:
- Right: set `"photo_ok": true` on the item.
- Wrong: run `python3 <this skill's folder>/scripts/yeez_build.py --date <today> --work yeez-work --flag <ITEM> --reason "<what's wrong>"`. That blocks the photo for good and sets the card to be rebuilt. Improve the brief (a sharper `must`, a better `query`, or the buyer's own photo through `find_site_images`), then run the build again. Two tries, then take `image_brief` off the card so it uses the brand background, or drop the item.
Do the same for any bad photo you spot yourself, marked or not.

**When the buyer says a photo is bad** (now or on a later day):
1. Fix that card: run `--flag <ITEM> --reason "<their words>"`, give it a better brief, rebuild and post it again. If it was only scheduled on Facebook, the post script swaps it (deletes the scheduled one, schedules the new card). If it's already live, say it can't be swapped automatically and they can delete it on the Page.
2. Learn from it, a little. Work out what they want from photos like that one, and save it on the same flag as one short `--lesson` ("recall cards show the recalled product itself, not store shelves"). Add `--when "<topic words>"` so it applies to that kind of card, and `--avoid "<what they objected to>"` when they named something to keep out. It stays on that Page unless they say every Page (`--all-pages`).
3. Keep the adjustment small: one lesson per complaint, about that kind of card. Don't turn photos off, don't change other kinds of cards, and don't rewrite the rest of the day's briefs.

Before writing image briefs for a Page, read its lessons (`python3 <this skill's folder>/scripts/yeez_build.py --lessons --page CODE --work yeez-work`) and follow them. They sit in `yeez-work/photo-feedback.json`, and the build also applies their `avoid` words by itself.

## 5. Post

```
python3 <this skill's folder>/scripts/yeez_post.py --date <today> --work yeez-work [--page CODE]
```

It posts every built item straight to the account in its queue file, with the keys file:
- Facebook news image and text image cards, gradient posts, link posts and reels are **scheduled** at their `time` with Meta's own scheduler (anything due in under 15 minutes moves to 20 minutes out).
- Stories, and everything on Instagram, are **published** when their time is under 30 minutes away; earlier than that they stay `built` and the script says they're waiting (the social now task posts them). Instagram reels wait for Instagram to finish processing, up to about 4 minutes.

To preview first, add `--dry-run`: it lists what would post and changes nothing (no posts, no file edits), so there's nothing to record afterwards.

Then call `record_social_posts` with the list the script saved in `yeez-work/queue/<today>/_to_record.json`. That puts the posts in the buyer's queue and dashboard, and any LINK post's `first_comment` is added by yeez.ai the moment Facebook says the post is live.

If an item failed, read its `error` in the queue file, fix it once (shorten, re-render, or re-fetch the keys) and run the post script again: it only posts items still marked `built`. Otherwise set it to `"held"` with the reason.

## Report

Per account: how many of each type were scheduled or posted, with local times; anything held and why (photo checks first: what you looked at and what you changed); that if a photo looks wrong they can just tell you which card and why; and that the buyer can review everything with `list_social_queue`, on the Page, or in Meta Business Suite before it goes live.
