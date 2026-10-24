---
name: dm
description: Sets up and manages comment-to-DM on Facebook and Instagram. When someone comments a keyword on a post, Yeez messages them a link and replies publicly. Use when the user types /yeez:dm, or asks to add, change, test or turn on comment keywords.
---

# Yeez comment-to-DM

Read [../core/rules.md](../core/rules.md) first: who Yeez is and the rules it never breaks.

## How it works

The buyer picks a keyword per offer, for example GUIDE. When someone comments just that keyword on their Page or Instagram, Yeez sends them a private message with a button to the link, then replies under the comment. A comment fires only when it's the keyword alone or with a word or two, so normal conversation never triggers it. Each comment gets one message, ever.

## Steps

1. Call `list_social_accounts`. If Meta isn't connected, call `connect_meta`, give them the link, and wait.
2. Call `list_dm_flows` to show the current keywords and mode.
3. **Add or change a keyword:** ask for these, then call `save_dm_flow`:
   - the offer (what they're sending and the link). If it's one of their saved offers (`list_offers`), use `make_tracked_link` with channel `dm` so clicks are counted.
   - the keyword: one short, memorable word
   - the message: friendly, one or two sentences; `{name}` becomes the commenter's first name
   - the button text: two or three words
   - an optional public reply, such as "Sent you a message, {name}."
4. **Test it.** Call `test_dm_keyword` with a few sample comments: the keyword alone, the keyword with "please", and a normal sentence that contains the word. Only the first two should match.
5. **Turn it on safely.** New accounts start in `shadow`, a test mode that logs who would get a message without sending anything.
   - Ask the buyer to comment the keyword from a personal account on one of their posts. Then call `dm_activity` to confirm it was seen.
   - When it shows up, call `set_dm_mode` with `live`.
   - If nothing shows up, the Meta app is probably still in Development mode. Tell them to switch it to Live in the Meta developer dashboard.
6. **Check on it any time** with `dm_activity`, and pause with `set_dm_mode` set to `off`.

Posts that ask for a keyword should read as an offer, not bait. At most one a day per account.
