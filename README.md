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
| `/yeez:setup` | The setup interview, and connecting your WordPress sites | Available |
| `/yeez:help` | What Yeez can do and where your setup stands | Available |
| `/yeez:headlines`, `/yeez:articles`, `/yeez:social`, `/yeez:dm`, `/yeez:newsletter`, `/yeez:offers`, `/yeez:review` | The daily and weekly runs | Arriving in updates |

Support: alex@clarkbrosmedia.com
