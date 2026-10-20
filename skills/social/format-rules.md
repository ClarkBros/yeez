# Yeez social format rules

These are the Clark Bros Media network's own rules for its Facebook Pages, learned from thousands of posts and from the top Pages in its niche. They apply to every buyer. Wherever they say "the reader", use the buyer's audience from setup (`get_site_brief` → audience).

## Every post
- **Touch the reader's money or life.** A check, a bill, a price, a benefit, a tax, savings, their home, their health costs, or whatever the buyer's niche is about. A post that costs or pays the reader nothing doesn't run.
- **Fourth-grade words.** Short sentences, one idea each. "Costs more", not "incurs additional expense". Only official names may be hard words.
- **No emoji, ever.** At most one ALL-CAPS word per post (RAISE, CUT, NEVER).
- **Exact and sourced.** Every number comes from the source you read. Bills and proposals are labeled as such. Never invent a quote. Never claim a crime nobody was charged with.
- **No money promises** ("you'll get $X", "you qualify"), no countdowns, no made-up urgency, no prices in a call to action. A real deadline may appear when the reader needs it to act.
- **Name the person who acted.** When a person made the decision (an official, a judge, a CEO), name them, and put their photo on the card. Back them when the move helps the reader, push back when it costs them. Facts only; no insults about looks, family or identity.
- Stay out of election horse races, culture fights and immigration.

## Endings: every feed post takes a side or asks a question
Posts that end on a plain fact get almost nothing. Rotate these six; never the same one twice in a row on a Page, and none more than 40% of a Page's day:

| Ending | Example |
|---|---|
| Yes or No | Should Social Security be taxed at all after you paid in for 40 years? Yes or No |
| Verdict | Paying tax on money you already paid tax on is just wrong! |
| This or that | Raise the retirement age, or cut every check? |
| Raise your hand | Raise your hand if your premium ate your whole raise. |
| Do you back it | The governor wants to cap property taxes for seniors. Do you back her? |
| Your own number | How much of your last raise actually reached your pocket? |

Never end on a sourced fact, a date, an instruction or "Learn more". The ending must be answerable in one word, a name or a number.

**Keyword posts end on the keyword, not a yes/no.** On posts with a comment-to-DM keyword, readers who are asked a yes/no answer "Yes" and skip the keyword. Shape: the stake → the facts (who, the number, the date) → the catch ("it isn't automatic") → ONE personal question the keyword answers ("Want the checklist for your state?") → `Comment WORD and we'll send you [the thing].`

## news_image — photo post card
- `overlay`: 20–45 words, one paragraph, sentence case: who did what, the number, then the ending. Lead with the number that hits the reader.
- `image_brief`: `format: "T"`.
  - One person: `subject: "person: <Full Name> official portrait"`.
  - Two people: also `subject2: "person: <Full Name> official portrait"` (the photos run side by side).
  - No person: `query` is 4–7 concrete words for a real moment (the document, the store, a person like the reader). Always keep `query` filled as a fallback.
- `caption`: 60–110 words. Hook (the stake) → 2–3 short sentences of facts with the number, who decided it and the source named in words → one line on who it hits → the question again (or, on keyword posts, why people miss it + what we send + `Comment WORD.`).

| Weak | Strong |
|---|---|
| Every drug plan makes you cross a deductible before it pays. For 2027 that can be $700. The floor rose with the roof. | Medicare drug plans can now make you pay up to $700 before they pay a cent, and the yearly cap rises to $2,400. Is that fair to people on a fixed check? |

## text_image — white text card
- `text`: a **bold** title plus up to 4 bullets (`- ` lines) or 1–4 short paragraphs, 45 words at most. Two exact numbers or one clear rule, then the stake. The last line is the ending.
- The card never carries the keyword, a link or a product name; the call to action lives in the caption's last line.
- `caption` complements the card (source, date, who it hits); it doesn't repeat it.

## gradient — short text on Facebook's colour background (Facebook only)
- `text` ≤130 characters in all, CTA included (Facebook drops the background above that). No caption.
- At least 2 of every 3 are questions. Keep the question itself under about 100 characters.
- With a keyword: the question, then `Comment WORD and we'll send you [8 words at most].`

## story
- `text`: 25 words or fewer, a glance. `cta: {mode: "KEYWORD", keyword, pill}` where `pill` is the thing we send in 6 words or fewer ("your state's property-tax breaks"). The button reads "Reply WORD for <pill>".
- Optional `image_brief` adds a photo band. `image_brief.format` "brand" (white) or "gradient"; leave it out and they alternate.

## link — the article itself (Facebook only)
- Share today's articles from `articles_to_share` as plain link posts only when the Page has no photo slot left; a photo post with the link in the first comment does better.

## Calls to action
- About half of a Page's feed posts carry one, and only when one of the buyer's offers (`list_offers`) or a comment-to-DM keyword (`list_dm_flows`) fits the post's own topic. Never force one.
- **Keyword:** only a keyword that exists in `list_dm_flows`, typed exactly.
- **Link:** put it in `first_comment`, never in the caption: one short sentence, then the tracked link from `make_tracked_link` (channel `social`, ref = the item id). Nothing after the link.

## reel — on-screen text over the buyer's own footage (Facebook and Instagram)
Set `reel_format` on every reel.
- **R, "read it on screen" (about 70% of reels).** `text` is the whole message, one line per row: 6–10 lines, 35–80 words in all, each line 3–8 words (about 30 characters at most). Sentence case, plain words, no hashtags or emoji. The renderer shows every line at once, white type on dark boxes, over the footage for 12 seconds (`duration_s` 10–15 if needed). Two voices that work:
  - **First person**, someone like the reader talking: "I paid into Social Security for 44 years. / Every paycheck. No choice. / … / Has this happened to you?"
  - **A number list:** "What a drug plan can take before it pays: / 2026: $615 / 2027: $700 / Is that fair?"
  The LAST line is the ending (a question or a verdict). Set `reel_mood` to one of the buyer's footage folder names (from the footage list). Never use a luxury-looking folder on a cut, a scam, a bill or any hardship story.
- **P, "named person" (about 30%, when a person acted).** `text` is 20–45 words in one paragraph, the same rules as a news image card, ending on the side-taking question. `image_brief.subject` is `"person: <Full Name> official portrait"`. The card sits on top and the person's photo below with a slow push-in, 9 seconds.
- **Caption:** one or two plain sentences with the source or date, then the question again. A call to action only when an offer fits.

## image_reel — a card held still over music
`source_item` is the id of one of today's built news image or text image cards, usually the strongest one. The card is held still (no motion, no new text) over the buyer's music for 10 seconds. Caption like a news image's.
