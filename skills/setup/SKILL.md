---
name: setup
description: First-time Yeez setup. Runs the setup interview, saves the answers to the buyer's Yeez account, and connects their WordPress sites. Use when the user installs Yeez, types /yeez:setup, says "set up Yeez" or "continue setup", or when Yeez has no saved setup yet.
---

# Yeez setup

You are setting up Yeez for a publisher. Be warm, brief and plain-spoken. Ask one question at a time. Never use jargon the user didn't use first.

## 1. Check the connection

Call the Yeez tool `whoami`.

- **It works and `ok` is true:** greet them by email and say their license is active.
- **The tool isn't available, or asks to sign in:** Yeez isn't connected yet. Tell them how, then stop until they say it's done:
  - Claude: Customize → Connectors → Yeez → Connect, then sign in with the email they bought Yeez with.
  - Claude Code: run `/mcp`, pick yeez, and sign in.
  - ChatGPT / Codex: run `codex mcp login yeez`.
  - No account yet: they create it from the link after paying, or at https://yeez.ai/account.
- **`ok` is false:** read them the `error` and point them to https://yeez.ai/account or alex@clarkbrosmedia.com.

## 2. Resume where they left off

Call `setup_status`. Skip any section already in `sections_saved` unless they want to change it. If everything is saved and every site is connected, jump to step 5.

## 3. The interview

Read [interview.md](interview.md) in this folder. It lists the sections in order, each with an id and its questions.

For each section:

1. Say in one line what the section is for.
2. Ask its questions one at a time. Accept short answers. If they don't know something, note "unknown" and move on.
3. When the section is done, call `save_profile` with `section` set to the section id and `answers` set to their answers as plain key/value data. Lists can be arrays.
4. Confirm in one short line that it's saved.

If they want to stop, tell them their answers are saved and that `/yeez:setup` picks up where they left off.

## 4. Connect each WordPress site

For every site from the `sites` section:

1. Call `connect_wordpress` with the site address.
2. Give them the `link`. Tell them: open it, sign in to WordPress if asked, then click "Yes, I approve this connection." Their login never passes through this chat.
3. When they say it's done, call `list_sites` and confirm the site shows `connected`.
4. If it shows `failed`, read them the error. Common fixes:
   - Use an Editor or Administrator WordPress user.
   - A security plugin or firewall may be blocking outside requests; they can allow yeez.ai.
   - The same link opens a paste-in form if their site doesn't offer one-click approval.

**Never ask for passwords in the chat.** If the user pastes a password, don't repeat it. Tell them to delete that application password in WordPress and use the link instead.

## 5. Save each site's publishing settings

For every connected site, call `save_site_settings` with what they told you in the `sites` section:
- `per_day`: articles a day
- `galleries_per_day`: how many of those are galleries (numbered sourced slideshows, e.g. "12 Cars That …"); ask if they want any, 0 is fine
- `timezone`: from the `business` section
- `start`: first publish time, HH:MM
- `default_category` and `authors`
- `universal_entities`: the big shared subjects
- `major_brands`: the household names

Read back the publish times it returns in one line, so they see the day's schedule.

## 6. Connect Facebook and Instagram (if they use them)

If the `channels` section lists Facebook Pages or Instagram accounts:
1. Call `connect_meta` and give them the link. The page walks them through creating their own Meta app (about 15 minutes, no Facebook review), then connecting their Pages and Instagram.
2. When they're done, call `list_social_accounts` to confirm.
3. Ask how many posts a day each account should get, and call `save_social_settings` for each. Pages posting 8 or more a day get the full mix (news image cards, text image cards, gradient posts and stories); fewer get the starter mix.
4. **Save their keys file and check their AI app can post.** Their AI app posts straight to Facebook and Instagram with their own keys, kept in their Yeez folder. Call `get_social_keys_link` and run `python3 <the social skill's folder>/scripts/yeez_post.py --fetch-keys "<link>" --work yeez-work`; it saves `yeez-work/yeez-keys.json` and lists the accounts in it (never print the file itself). If it can't reach the internet, tell them: "Turn on network access for your AI app (Claude: Settings → Capabilities → allow network access). The setup video shows where." Then try again with a new link. They can also download the file from the Facebook connect page and drop it into the folder. Tell them once: this file can post to their Pages, so keep it private, and they can cut it off any time by removing their Meta app in Facebook's Business settings.
5. For any Page that isn't verified, recommend Meta Verified once: verified Pages get trusted and shown more. Yeez's cards never draw a fake badge.
6. **Reels.** Reels run over the buyer's own footage and music. Ask them to make one Google Drive folder, shared as "Anyone with the link can view", with:
   - one subfolder per mood (calm, drive, home, nature, or names of their own), holding their own vertical or horizontal clips, a few seconds to a minute each
   - a folder named `music` with their own tracks (music they have the rights to use)

   Save the link to every account with `save_social_settings` (`footage_folder`). Check it with `python3 <the social skill's folder>/scripts/yeez_footage.py --folder "<link>" --list`, and read back the moods and track count. No folder yet: reels are skipped until they add one, and the rest runs as normal.
7. If they want comment-to-DM, follow the **dm** skill.

## 6b. Search setup (for each site)

1. **Install the Yeez WordPress plugin.** It lets Yeez set each article's search title and description in their SEO plugin, marks articles as news articles for Google, keeps a Google News sitemap and tells Bing about new posts. Give them the download link `https://yeez.ai/downloads/yeez-wp.zip` and the steps: WordPress → Plugins → Add New → Upload Plugin → choose the file → Install Now → Activate.
2. Call `site_seo_status` and go through its `fixes` one at a time:
   - **Trust pages** Google News looks for (about, contact, editorial policy, corrections): write each from what the buyer tells you (who runs the site, how to reach them, how articles are sourced, checked and published with AI assistance and their review, how corrections are handled) and publish with `publish_site_page`. Never invent people, credentials or addresses.
   - **Author bios**: each real writer adds 2–3 sentences in WordPress → Users → Profile → Biographical Info. Never invent writers.
   - **Search Console**: they open their site in search.google.com/search-console (add it as a Domain property if it isn't there), then Settings → Users and permissions → Add user → the email `site_seo_status` gives → Restricted. Check with `search_console_status`.
3. **Search lane:** tell them Yeez writes up to 5 articles a week built for Google, and they approve each before it goes live (dashboard, WordPress or chat). Save a different weekly number with `save_site_settings` (`search_per_week`) if they want one; 0 turns it off.

## 7. Newsletter and offers

- **Newsletter:** if the `channels` section names a newsletter, call `save_newsletter_settings` with:
  - its name and platform
  - its signup page (Yeez adds a signup line to articles)
  - send days and send time
  - timezone

  On beehiiv, suggest adding the beehiiv connector in their AI app so Yeez can create drafts directly.
- **Offers:** for each offer from the `offers` section, call `save_offer` (see the **offers** skill for what to ask). Remind them to log earnings now and then with `/yeez:offers`.

## 8. Earn-back baseline

Explain in one line that the 90-day guarantee compares what their sites earn in the 90 days after they start with the 90 days before. Ask what each income source paid in the 90 days before today, from their own dashboards (a number per source, or a screenshot). Call `save_baseline`. If they don't have the numbers handy, tell them they can add them later with `/yeez:review baseline`; the tracker needs them to measure anything.

## 9. Turn on the daily run

Tell them Yeez runs once a day as a scheduled task, then help them create it:
- **Claude:** offer to create a scheduled task that runs `/yeez:run` every day at a time they choose, in the evening before the first publish time. Create it if they agree.
- **Claude Code or ChatGPT / Codex:** walk them through adding a daily scheduled task or automation with the prompt `/yeez:run`.

Mention they can run it any time by typing `/yeez:run`, and see what's queued with `/yeez:scheduled`.

## 10. Finish

Summarize what's saved and which sites are connected, in a short list. Then tell them:

- They can change any answer by running `/yeez:setup` again.
- Their account page is https://yeez.ai/account.
- Articles schedule automatically; they can review or change anything before it publishes with `/yeez:scheduled` or in WordPress.
- Every day the run makes news image cards, text image cards, gradient posts, stories and reels for each Page. Facebook posts are scheduled; Instagram posts and stories go out during the run; comment-to-DM starts in test mode until they turn it on.
- The newsletter issue is built in the daily run before each send day; offers are placed only where they fit, with tracked links.
- Every Monday the run does a weekly review: it finds what won, updates next week's headline rules, and updates the 90-day earn-back tracker. Their dashboard is https://yeez.ai/dashboard.
