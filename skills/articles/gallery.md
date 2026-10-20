# Galleries (sourced slideshows)

A gallery is a numbered swipe-through: "12 Cars That …". These are the Clark Bros network's own gallery rules (Morning Overview). Use them for the site's `galleries_per_day` slots (from `get_site_brief` settings); the rest of the day is articles.

## Pick the gallery
- **Headline:** starts with the item count, and the number equals the items. 8–14 items, 12 is the target. Every specific in the headline (a year, a place, a record) must be carried by the gallery's own items.
- **Evergreen first.** Lists that stay true for months: vehicles, aircraft, animals, landmarks, inventions, places, products. The site's niche decides the subject; whatever readers of this site recognize on sight.
- **Every item is mainstream and recognizable** and has a real photo of exactly that thing. Skip items that only exist as drawings, very old events with no photos, things too small or far away to photograph (minor moons, deep-sea species), or anything you can't show.
- Score gallery headlines with `score_headlines` like any other (put the count in `facts`).

## Sources
- One deep source page per item (the page about that exact thing, not a home page or search page).
- At least 3 different websites; no single page for more than 40% of items; Wikipedia for at most 60%; at least one primary or institutional source (an agency, a museum, the maker).
- Never Google Books, placeholder or search-result links.

## Photos (the "depiction" rule)
- Each slide shows **exactly the named thing**: the actual model, the actual animal, the actual place. No stand-ins, no "a similar car".
- Search `find_images` with `source: "commons"` and the exact name (the Wikipedia article title works best). Use `openverse` only if Commons has nothing.
- No repeated photo. The **cover** is a separate, different photo that never appears in the slides.
- Credit format: `Creator - License/Source`, e.g. `Jane Doe - CC BY-SA 4.0/Wikimedia Commons`.

## Writing
- **Intro:** 3 sentences, 45–70 words. The last sentence names the count in words ("Here are twelve …").
- **Each item:** `subject` is the exact named thing; `kicker` is a short hook ("the fastest of its decade"). Two paragraphs, plain text:
  - 8 items: 90–125 words per item; 9–10 items: 80–120; 11–14 items: 70–110.
  - The first paragraph contains **exactly one link**, to that item's own `source_url`: `<a href="SOURCE_URL">the agency</a>`. No other links, no bold, no lists, no headings.
- Same voice and facts rules as articles: sourced, current, third person, no hype.

## Schedule
Call `schedule_gallery` with `title`, `intro`, `items` (subject, kicker, p1_html, p2_html, source_url, image_url, image_credit, image_alt), `cover`, the `headline_id` and an `excerpt`. It re-checks everything, uploads every photo, builds the post (real blocks on WordPress, clean HTML elsewhere) with a credit under each photo, sets the cover as the featured image and schedules it in the next slot. If it lists problems, fix them and call it again.
