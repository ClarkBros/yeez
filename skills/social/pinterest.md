# Pinterest

Pins are built on the buyer's computer with `scripts/pin_build.py` and posted through the buyer's own Pinterest account in the app's browser (Claude in Chrome in Claude; the app's own browser tool elsewhere), using Pinterest's own scheduler. Nothing goes through yeez.ai and no image is hosted anywhere: the browser uploads the file from the buyer's computer.

Pinterest steps run inside the social modes: learn (P1), write (P2–P3), build (P4), post (P5). `/yeez:social pinterest` runs P1–P5 on their own.

## P0. Ready? (first time, then whenever something is missing)

1. **A browser this app can drive**, signed in to the buyer's Pinterest. If the app has no browser tool, tell the buyer once that Pinterest posting needs one (Claude in Chrome in the Claude app) and skip Pinterest.
2. **A business account.** Open `https://www.pinterest.com/settings/` (account management). Scheduling needs a Pinterest business account (it's free). If it's personal, show the buyer the "Convert to business account" option and ask them to confirm before you click it; they keep their pins and followers.
3. **`yeez-work/social/pinterest.json`.** Create it once and keep it current:

```json
{
  "profile": "https://www.pinterest.com/<username>/",
  "site": "https://<their site>",
  "timezone": "<IANA timezone>",
  "per_day": 5,
  "brand": {"accent": "#1E4D47", "accent_2": "#F2C230", "ink": "#22201C", "paper": "#FFF9EF", "site_label": "<site domain>"},
  "style": {},
  "templates": ["center_box", "split_band", "top_title", "recipe_card", "roundup_collage", "roundup_grid"],
  "boards": [{"name": "Easy Weeknight Dinners", "covers": "quick dinners, one-pan, 30-minute meals"}]
}
```

   - `per_day`: 3–5 new pins a day for an account under about 1,000 followers or under 3 months of pinning, 5–10 for an established one. New pins (fresh designs) are what bring site traffic on Pinterest; saves of old pins don't.
   - `brand`: take the colours from the site's logo and the buyer's existing pins (open their profile's Created tab and look). `site_label` is the bare domain. The buyer changes the look by saying so ("make my pins darker", "use the yellow band"): change `brand` or `style` here and rebuild.
   - `boards`: read them from the profile. Board names should be what people search ("Easy Weeknight Dinners", not "Recipes 2"). If the site has whole topics with no board, list the boards you'd add and create them only after the buyer agrees.

## P1. Learn (weekly, and the first time)

1. Open Pinterest Analytics (`https://analytics.pinterest.com/`) for the last 30 days, sorted by outbound clicks, then saves. Note which pins won: template, on-image words, kicker, photo type, board, topic. Note the losers.
2. Search Pinterest for the site's 3–5 main topics (`https://www.pinterest.com/search/pins/?q=<topic>`). Look at the top 20 pins for each: layout (boxed title, band, top title, collage, numbered grid, card), fonts (bold condensed, serif, script accents), colours, how many words, whether there's a number. These are the proven looks to match or beat.
3. Write `yeez-work/social/pinterest-learn.md` (dated): winners' shared traits, losers', what to test this week, and any template or `style` change (for example a darker band or a bigger number on roundups). Change `templates` order so winners come first.

## P2. Plan the day's pins

- **Count:** `per_day`.
- **What to pin, in order:** today's new articles; then older articles that already get Pinterest clicks; then the rest of the archive, oldest-pinned first. Read `yeez-work/social/pins.csv` (`date,url,template,title,pin_url`) so each URL gets a **different design** every time (a different template, photo, crop or on-image words) and no URL gets a new pin more than once every 2 weeks, up to 5 designs per URL.
- **Template by content:**
  - roundups and "N ideas" lists: `roundup_collage` or `roundup_grid`, with the number;
  - one recipe or how-to: `center_box`, `split_band`, `top_title` or `recipe_card` (the card needs a few key items and facts like time and servings);
  - news: `top_title` or `center_box`.
  Spread templates across the day; follow pinterest-learn.md's order.
- **Boards:** the board whose `covers` fits the article best; spread the day across boards.

## P3. Write the pins

Write `yeez-work/pins/<today>/pins.json`:

```json
{
  "brand": {"...": "from pinterest.json"},
  "style": {"center_box": {}},
  "pins": [
    {"id": "<MMDD>-01", "template": "center_box",
     "title": "on-image words, 2-6 words", "kicker": "2-4 words (optional)",
     "photos": ["https://<site>/wp-content/uploads/...jpg"], "focus": [0.5, 0.5],
     "number": "25 (roundups)", "labels": ["roundup_grid item names"],
     "facts": ["30 min", "Serves 6"], "items": ["recipe_card key ingredients"],
     "pin_title": "Keyword-first title, under 100 characters",
     "description": "2-3 sentences, about 200-250 characters (under 500): what it is, who it's for, the main search words",
     "alt": "What the photo shows",
     "link": "https://<site>/<article>/",
     "board": "<board name>",
     "time": "<today>T12:30:00<offset>",
     "status": "written"}
  ]
}
```

- **Photos:** only the buyer's own photos from the article (featured image and in-article photos). Never AI images, stock photos, or other sites' photos, including other bloggers' photos that appear in a roundup post (the buyer has permission to use those in the post, not on pins). A roundup pin uses the buyer's own recipes' photos from that roundup.
- **On-image words** are short (2–6 words, the dish or the list); the pin title carries the full search phrase. Lead `pin_title` with the main search term (people search "chicken and dumplings", not "my favorite comfort food").
- **No clickbait, no prices unless they're the point, no emoji on the image.** Every fact (time, servings, ingredients) comes from the article.
- **Times:** spread through the account's day (about 7:00–22:00), at least an hour apart.

## P4. Build and check

```
python3 <this skill's folder>/scripts/pin_build.py --pins yeez-work/pins/<today>/pins.json --out yeez-work/pins/<today>
```

If it prints **FONT PROBLEMS**, the pins were built with a stand-in font: put that first in the report, with the fix it names. Fonts for pins go in the pins file's `brand` (`title_font`, `script_font`, ...) as `"Family:weight"`; any Google Fonts family or a font file in `yeez-work/fonts` works.

Then **look at every pin** (open each image):
- the food or subject is clearly visible and not covered by text; if a band or box hides it, change `focus` (0–1 for left-right, top-bottom) or the template's `style` (for example `box_y`) for that pin;
- the words are readable at phone size, nothing is cut off, the number and title match the article;
- two pins of the same URL never look alike.

Fix and rebuild one pin with `--only <id>`. Two tries, then drop the pin. Set `status` to `built`.

## P5. Post

For each built pin, in time order, in the browser:
1. Open `https://www.pinterest.com/pin-creation-tool/`.
2. Upload the image file (`yeez-work/pins/<today>/<id>.jpg`) with the browser's file upload.
3. Fill in the title (`pin_title`), description, link, board, and alt text (under "More options").
4. Choose **Publish at a later date** and set the day and time from `time` (the account's timezone). Then publish.
5. Note the pin's link, set `status` to `scheduled`, and add a row to `pins.csv`.

Pinterest only holds a limited number of scheduled pins at once (10 when last checked). Before you start, open the profile's scheduled pins and count; schedule only up to the limit and leave the rest `built`. The social now task schedules them as earlier ones go live.

If the page looks different from these steps, read it and find the same fields; never guess. If Pinterest shows an error or a captcha, stop Pinterest for today and tell the buyer.

## Report

Pins scheduled (with times and boards), pins waiting for room in the schedule, anything dropped and why, and what pinterest-learn.md says to test next.
