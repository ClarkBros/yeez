# Yeez by Clark Bros Media

The system behind a 40M-view-a-month publishing network, as a plugin for Claude and ChatGPT / Codex.

**You need a Yeez license.** Get one at https://clarkbrosmedia.com/yeez/ — your account and install steps live at https://yeez.ai/account.

## Install

**Claude (desktop app or claude.ai):** Customize → Plugins → Add marketplace → `ClarkBros/yeez` → install Yeez → turn on *Sync automatically*. Then run `/yeez:setup`.

**Claude Code:**
```
/plugin marketplace add ClarkBros/yeez
/plugin install yeez@clarkbros
```

**ChatGPT / Codex:**
```
codex plugin marketplace add ClarkBros/yeez
codex mcp login yeez
```

## Commands

| Command | What it does | Status |
|---|---|---|
| `/yeez:setup` | The setup interview, connecting WordPress, and turning on the daily run | Available |
| `/yeez:run` | Today's headlines and articles for every site, end to end | Available |
| `/yeez:headlines` | Finds today's stories and ranks the headlines | Available |
| `/yeez:articles` | Writes, checks and schedules today's articles and galleries (sourced slideshows) | Available |
| `/yeez:scheduled` | What's queued to publish, with edit links | Available |
| `/yeez:help` | What Yeez can do and where your setup stands | Available |
| `/yeez:social` | Writes, renders and posts news image cards, text image cards, gradient posts and stories for Facebook and Instagram, learning from each account's winners | Available |
| `/yeez:dm` | Comment-to-DM: a keyword comment gets a private message with your link | Available |
| `/yeez:newsletter` | Builds the issue from the day's best story; creates the beehiiv draft or a copy-ready page | Available |
| `/yeez:offers` | Offers, tracked links and the earnings report | Available |
| `/yeez:review` | The weekly review: winners, losers, next week's headline rules, and the 90-day earn-back tracker | Available |

Your dashboard: https://yeez.ai/dashboard

Support: alex@clarkbrosmedia.com
