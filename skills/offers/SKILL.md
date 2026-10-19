---
name: offers
description: Manages the buyer's offers (affiliate offers, their own products, sponsors, newsletter recommendations), their tracked links, and the earnings report. Use when the user types /yeez:offers, adds or changes an offer, logs earnings, or asks what's earning.
---

# Yeez offers and earnings

## Add or change an offer

Ask for these, then call `save_offer`:
- **Name and link.** Their affiliate link, or their product page.
- **Kind:** affiliate, product, sponsor, or recommendation (another newsletter they're paid to recommend).
- **Topics:** the words or phrases a story must mention for this offer to fit. Be specific. Five to fifteen is typical.
- **A short call to action, and a one-sentence plain description.**
- **Claims:** anything the offer's terms say they must or must not claim.
- **Where it may appear:** articles, social, newsletter, DMs.

Call `list_offers` to show what's saved.

## How Yeez uses them

Yeez places an offer only where it fits the story. That means at most one per article, post or issue, through `match_offers`, which also gives a tracked yeez.ai link. Tracked links count clicks by offer, channel and placement. Links in comment-to-DM messages should be tracked too (`make_tracked_link`).

## Earnings

- **Log money as it comes in.** Call `record_earnings` with the amount, the date, and the offer or source (for example "NewsBreak", "AdSense", or an offer name). Weekly, from each dashboard, is enough.
- **See what's working.** Call `earnings_report` (default: the last 30 days). Show:
  - clicks and earnings by offer, with earnings per click
  - clicks by channel
  - the top placements
  - total earnings

  Then point out, in two lines at most, which offer earns the most per click and which gets clicks but no recorded earnings.
