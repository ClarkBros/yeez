---
name: setup
description: First-time Yeez setup. Connects the buyer's sites, gets the basics from their yeez.ai form, learns from their sites and real numbers (with the learn skill), and connects (WordPress, Ghost, Shopify, Wix, Webflow, HubSpot, Joomla, Framer or Blogger). Use when the user installs Yeez, types /yeez:setup, says "set up Yeez" or "continue setup", or when Yeez has no saved setup yet.
---

# Yeez setup

Read [../core/rules.md](../core/rules.md) first: who Yeez is and the rules it never breaks.

You are setting up Yeez for a publisher. Be warm, brief and plain-spoken. Ask one question at a time. Never use jargon the user didn't use first.

## 1. Check the connection

Call the Yeez tool `whoami`.

- **It works and `ok` is true:** greet them by email and say their license is active.
- **The tool isn't available, or asks to sign in:** Yeez isn't connected yet. Their account page, https://yeez.ai/account, has the exact steps for their app (Claude, Claude Code, Codex, ChatGPT, Cursor, Grok, Kimi, Hermes or OpenClaw). Point them there, then stop until they say it's done. Apps that ask for a key use a sign-in key they make on that page; never ask them to paste it into the chat. No account yet: they create it from the link after paying, or at https://yeez.ai/account.
- **`ok` is false:** read them the `error` and point them to https://yeez.ai/account or alex@clarkbrosmedia.com.

## 2. Resume where they left off

Call `setup_status`. Skip any section already in `sections_saved` unless they want to change it. If everything is saved and every site is connected, jump to step 5.

**Which AI app is this?** If you know (you're Claude, Codex, Cursor, Grok, Kimi, Hermes, OpenClaw, ChatGPT…), call `app_guide` with its id and keep the answer: it says whether this app can post to Facebook and Instagram, and how the daily run is scheduled here (step 9). If it says `social: false`, tell the buyer once, early: everything but Facebook/Instagram posting runs here; for social posting they also install Yeez in a computer app (the account page lists them).

## 3. Order

Setup runs in the same order as the buyer's Get started page (https://yeez.ai/start): connect sites → the basics → their numbers → learn and confirm → Facebook and Instagram → search → newsletter and offers → earn-back baseline → daily run. Do step 4 (sites) first, then come back to the basics.

## 3b. The basics

Call `get_profile`. The basics come from a short form on https://yeez.ai/start#basics, all buttons and dropdowns: business name, how the sites make money (each choice is saved with what that income rewards), articles a day now and wanted per site, which syndication partners they're approved on or applying to, Facebook and Instagram, newsletter platform, goals, and optional house style and offers. Their timezone comes from their browser.

- **`business`, `sites`, `channels` and `goals` are saved:** use them. Don't re-ask any of it.
- **Not saved yet:** send them to https://yeez.ai/start#basics: "Takes about two minutes, all clicks." Wait for "done", then `get_profile` again.
- **They'd rather answer here:** ask the questions in [interview.md](interview.md), offering the choices listed there as options to pick from, and save each section with `save_profile`.

Never ask what Yeez can work out itself: what a site is about, who reads it, its categories, authors, big subjects, brands, best articles, voice or what's working. The **learn** skill finds those in step 5b and the buyer confirms them.

## 4. Connect each site

The basics list the sites Yeez publishes to. Work out what each is built with yourself before asking: WordPress answers at `https://<site>/wp-json/`, Ghost at `/ghost/api/`, Shopify at `/products.json`; Wix, Webflow, HubSpot, Joomla, Framer and Blogger name themselves in the page source. Ask only if you can't tell (what do they log in to when they edit the site?). (Squarespace, Substack, Medium and Weebly can't be published to from outside. Tell them plainly: Yeez's articles need to live on a site built with one of the platforms above, for example a news section on a subdomain like news.theirsite.com; then connect that.)

For every site:

1. Call `connect_site` with the site address and its `platform`.
2. Give them the `link` and read them `what_they_need` (and `needs_first`, if any) in plain words:
   - **WordPress:** open the link, sign in to WordPress if asked, then click "Yes, I approve this connection."
   - **Other platforms:** they make a key in their platform (the page shows where) and paste it into the page, never into this chat.
3. Tell them any `differences` once (for example, Webflow and Framer publish when the daily run happens, because they can't schedule ahead).
4. When they say it's done, call `list_sites` and confirm the site shows `connected`.
5. If it shows `failed`, read them the error. Common fixes:
   - WordPress: use an Editor or Administrator user; a security plugin or firewall may be blocking outside requests (allow yeez.ai); the same link opens a paste-in form if their site doesn't offer one-click approval.
   - Other platforms: the key is missing a permission the page lists, or they copied the wrong key. Make a new one and paste again.

**Never ask for passwords or keys in the chat.** If the user pastes one, don't repeat it. Tell them to delete it in their platform, make a new one, and use the link instead.

## 5. Save each site's publishing settings

For every connected site, call `save_site_settings` with:
- `per_day`: `articles_per_day_wanted` for that site from the basics
- `timezone`: from `business.timezone` in the basics
- `platforms`: the platforms this site is approved on, from `channels.syndication` in the basics
- `newsbreak_feed` (WordPress sites on NewsBreak only): open `https://<site>/feed/newsbreak`. If it answers with an RSS feed, the site uses the NewsBreak Feed for WordPress plugin: set `true`, so every post Yeez schedules carries the plugin's "send to NewsBreak" flag. If it's a 404, set `false` (NewsBreak reads the normal feed).
- `galleries_per_day`: don't ask. 0 unless the site is on MSN and already publishes numbered galleries (titles like "12 Cars That …" among its posts); then keep its current share. Never on NewsBreak-only sites. In 5b's confirm message, mention once that galleries pay on MSN if the site is on MSN and has none.
- `start`: leave the default for now; step 5b sets it from the site's best publish hours

Read back the publish times it returns in one line, so they see the day's schedule.

## 5a. Their numbers

Yeez learns from every article's real views. Follow the **learn** skill's steps 1–3 (setup mode) for every platform the basics list as approved: NewsBreak is pulled straight from their dashboard through the browser ([../learn/browser.md](../learn/browser.md) has how to turn the browser on in each app); MSN, Yahoo, SmartNews and analytics come as exports. If their sites aren't on any platform yet, skip to 5b.

## 5b. Learn and confirm

Follow the **learn** skill's steps 4–6 (setup mode) for each site: read the site, work out what wins, and show the buyer one "Here's what we found" message per site to confirm or fix. It saves categories, authors, default category, big subjects, brands, voice and the best articles with `save_site_profile`. Then call `save_site_settings` again with `start` set from the best publish hours.

## 6. Connect Facebook and Instagram (if they use them)

If the `channels` section lists Facebook Pages or Instagram accounts:
1. Call `connect_meta` and give them the link. The page walks them through creating their own Meta app (about 15 minutes, no Facebook review), then connecting their Pages and Instagram.
2. When they're done, call `list_social_accounts` to confirm.
3. Don't ask how many posts a day: for each account, call `get_social_brief` and match what it already posts per day (from `recent_posts`), at least 3, then call `save_social_settings`. Pages posting 8 or more a day get the full mix (news image cards, text image cards, gradient posts and stories); fewer get the starter mix. A new Page (under 100 followers and fewer than 15 posts) gets `warmup_until` a week out instead ([../core/platforms/facebook.md](../core/platforms/facebook.md)); tell the buyer in one line why it starts slow.
4. **Save their keys file and check their AI app can post.** Their AI app posts straight to Facebook and Instagram with their own keys, kept in their Yeez folder. Call `get_social_keys_link` and run `python3 <the social skill's folder>/scripts/yeez_post.py --fetch-keys "<link>" --work yeez-work`; it saves `yeez-work/yeez-keys.json` and lists the accounts in it (never print the file itself). If it can't reach the internet, tell them: "Turn on network access for your AI app (Claude: Settings → Capabilities → allow network access). The setup video shows where." Then try again with a new link. They can also download the file from the Facebook connect page and drop it into the folder. Tell them once: this file can post to their Pages, so keep it private, and they can cut it off any time by removing their Meta app in Facebook's Business settings.
5. For any Page that isn't verified, recommend Meta Verified once: verified Pages get trusted and shown more. Yeez's cards never draw a fake badge.
6. **Reels.** Reels run over the buyer's own footage and music. Ask them to make one Google Drive folder, shared as "Anyone with the link can view", with:
   - one subfolder per mood (calm, drive, home, nature, or names of their own), holding their own vertical or horizontal clips, a few seconds to a minute each
   - a folder named `music` with their own tracks (music they have the rights to use)

   Save the link to every account with `save_social_settings` (`footage_folder`). Check it with `python3 <the social skill's folder>/scripts/yeez_footage.py --folder "<link>" --list`, and read back the moods and track count. No folder yet: reels are skipped until they add one, and the rest runs as normal.
7. If they want comment-to-DM, follow the **dm** skill.

## 6b. Search setup (for each site)

1. **WordPress sites: install the Yeez WordPress plugin.** (Other platforms skip this; their own search settings are used.) It lets Yeez set each article's search title and description in their SEO plugin, marks articles as news articles for Google, keeps a Google News sitemap and tells Bing about new posts. Give them the download link `https://yeez.ai/downloads/yeez-wp.zip` and the steps: WordPress → Plugins → Add New → Upload Plugin → choose the file → Install Now → Activate.
2. Call `site_seo_status` and go through its `fixes` one at a time:
   - **Trust pages** Google News looks for (about, contact, editorial policy, corrections): write each from what the buyer tells you (who runs the site, how to reach them, how articles are sourced, checked and published with AI assistance and their review, how corrections are handled) and publish with `publish_site_page`. If the platform can't make pages from outside (Wix, Webflow, Framer), it gives you back the text: hand it to the buyer to paste into a new page. Never invent people, credentials or addresses.
   - **Author bios**: each real writer adds 2–3 sentences to their author profile in the site's editor (WordPress: Users → Profile → Biographical Info). Never invent writers.
   - **Search Console**: they open their site in search.google.com/search-console (add it as a Domain property if it isn't there), then Settings → Users and permissions → Add user → the email `site_seo_status` gives → Restricted. Check with `search_console_status`.
3. **Search lane:** tell them Yeez writes up to 5 articles a week built for Google, and they approve each before it goes live (yeez.ai dashboard or chat; on WordPress also from Posts → Pending). Save a different weekly number with `save_site_settings` (`search_per_week`) if they want one; 0 turns it off.

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

## 9. Turn on the scheduled tasks

Yeez runs as a chain of scheduled tasks, each with one job, with enough time between them for each to finish. [../core/tasks.md](../core/tasks.md) has every task, its prompt, what it needs and the timing rules. Don't ask the buyer to design this; work it out and set it up.

1. **Work out the times** from tasks.md's timing rules, using the total articles a day across all sites, the number of Pages, whether there are stories or Instagram accounts, the newsletter's send days, and the earliest first publish time across the sites (start the chain the evening before). Use the buyer's timezone.
2. **Create the tasks**, using what `app_guide` said for this app (`daily_how`):
   - **Apps that can hold several scheduled tasks** (Claude's scheduled tasks, Claude Code, Codex automations, Cursor Automations, Hermes or OpenClaw cron): create one task per row of tasks.md, named `Yeez 1 · Learn`, `Yeez 2 · Headlines`, `Yeez 3 · Articles`, `Yeez 3b · Search`, `Yeez 4a · Social learn` and so on, each with exactly its prompt from tasks.md (`/yeez:learn daily`, `/yeez:headlines`, `/yeez:articles`, `/yeez:search`, `/yeez:social learn`, `/yeez:social write`, `/yeez:social build`, `/yeez:social post`, `/yeez:social now`, `/yeez:newsletter`, `/yeez:review`). Where slash commands don't work, use the words instead ("Run Yeez learn in daily mode", "Run Yeez headlines"). Skip social tasks with no Pages connected and the newsletter task with no newsletter. The newsletter task runs only on the days before send days; the review task only on Mondays; social now hourly at :10 through the posting window.
   - **Apps that can hold only one** (ChatGPT or Grok scheduled tasks, Kimi Claw cron): one daily task with `/yeez:run` (or "Run Yeez"), which does the whole chain in order.
   - If `daily` is `computer-on`, tell them the tasks only run while their computer is on and the app is open. If it's `manual`, they start it each evening by saying "Run Yeez".
3. **Show the schedule** in a short list (task, time, what it does in a few words). Mention they can run everything now with `/yeez:run`, and see what's queued with `/yeez:scheduled`.

Never create duplicates: if Yeez tasks already exist (a re-run of setup), update their times instead of adding new ones.

## 10. Finish

Summarize what's saved and which sites are connected, in a short list. Then tell them:

- They can change any answer by running `/yeez:setup` again.
- Their account page is https://yeez.ai/account.
- Articles schedule automatically; they can review or change anything before it publishes with `/yeez:scheduled` or in their site's editor.
- Every day the run makes news image cards, text image cards, gradient posts, stories and reels for each Page. Facebook posts are scheduled ahead; Instagram posts and stories go out at their times through the social now task; comment-to-DM starts in test mode until they turn it on.
- The newsletter issue is built in the daily run before each send day; offers are placed only where they fit, with tracked links.
- Every Monday the run does a weekly review: it finds what won, updates next week's headline rules, and updates the 90-day earn-back tracker. Their dashboard is https://yeez.ai/dashboard.
