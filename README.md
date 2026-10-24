# Yeez by Clark Bros Media

The system behind a 40M-view-a-month publishing network, as a plugin for your AI app: Claude, Claude Code, Codex, ChatGPT, Cursor, Grok, Kimi, Hermes and OpenClaw. It publishes to WordPress, Ghost, Shopify, Wix, Webflow, HubSpot, Joomla, Framer and Blogger.

**You need a Yeez license.** Get one at https://clarkbrosmedia.com/yeez/ — your account page, https://yeez.ai/account, has the exact install steps for your app.

## Install

**Claude (desktop app or claude.ai):** Customize → Plugins → Add marketplace → `ClarkBros/yeez` → install Yeez → turn on *Sync automatically*. Then run `/yeez:setup`.

**Claude Code:**
```
/plugin marketplace add ClarkBros/yeez
/plugin install yeez@clarkbros
```

**Codex:**
```
codex plugin marketplace add ClarkBros/yeez
codex mcp login yeez
```

**Cursor, Kimi Code, Hermes, OpenClaw and other agents that read skill folders:**
```
curl -fsSL https://yeez.ai/install.sh | sh            # ~/.agents/skills
curl -fsSL https://yeez.ai/install.sh | sh -s hermes  # ~/.hermes/skills
curl -fsSL https://yeez.ai/install.sh | sh -s openclaw
```
then connect the app to `https://yeez.ai/api/mcp` (your account page shows the config, with a sign-in key if the app asks for one).

**Any agent:** tell it *"Install Yeez by following https://yeez.ai/install.md"*.

**ChatGPT and grok.com:** add `https://yeez.ai/api/mcp` as a custom app/connector. Everything runs there except Facebook and Instagram posting, which needs one of the computer apps above.

## Commands

| Command | What it does | Status |
|---|---|---|
| `/yeez:setup` | Connects your sites, learns them from your own numbers, and turns on the scheduled tasks | Available |
| `/yeez:learn` | Pulls your NewsBreak, MSN, Yahoo and other numbers into your own Yeez folder and works out what gets views on each site | Available |
| `/yeez:run` | The whole chain in one go: learn, headlines, articles, search, social, newsletter (and the Monday review) | Available |
| `/yeez:headlines` | Finds today's stories and ranks the headlines | Available |
| `/yeez:articles` | Writes, checks and schedules today's articles and galleries (sourced slideshows) | Available |
| `/yeez:scheduled` | What's queued to publish, with edit links | Available |
| `/yeez:help` | What Yeez can do and where your setup stands | Available |
| `/yeez:social` | (`learn`, `write`, `build`, `post`, `now`) Writes, renders and posts news image cards, text image cards, gradient posts, stories and reels (over your own footage and music) for Facebook and Instagram, learning from each account's winners | Available |
| `/yeez:dm` | Comment-to-DM: a keyword comment gets a private message with your link | Available |
| `/yeez:newsletter` | Builds the issue from the day's best story; creates the beehiiv draft or a copy-ready page | Available |
| `/yeez:offers` | Offers, tracked links and the earnings report | Available |
| `/yeez:search` | Search lane: up to 5 articles a week built for Google, approved by you before they go live, plus Search Console results | Available |
| `/yeez:review` | The weekly review: winners, losers, next week's headline rules, and the 90-day earn-back tracker | Available |

Yeez's rules, the platform rules (NewsBreak, MSN, Yahoo, SmartNews, Google, Facebook and more) and how the scheduled tasks fit together are in `skills/core/`.

Your dashboard: https://yeez.ai/dashboard

Support: alex@clarkbrosmedia.com
