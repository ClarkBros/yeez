# Giving your AI app a browser

Yeez pulls NewsBreak (and, when your app can, MSN and Yahoo exports) through a browser your AI app controls. You log in to each dashboard once yourself; the AI app never sees or types your passwords.

## Claude desktop app (Cowork)

Cowork comes with a built-in browser (Pro, Max, Team and Enterprise plans).
- It opens in the side panel the first time Yeez needs it. Log in to NewsBreak there once; Claude keeps the login on that computer.
- To use your own Chrome and the logins you already have instead: install **Claude in Chrome** (https://claude.com/chrome), sign in with the same Claude account, then in the Claude app go to **Settings → Cowork → Preferred browser** and pick Chrome.
- Team and Enterprise: if you don't see the browser, ask your admin to turn it on.

## Claude Code

Install **Claude in Chrome** (https://claude.com/chrome) and sign in with the same Claude account. Start Claude Code with `claude --chrome`, or type `/chrome` in a session to connect it.

## ChatGPT desktop app (Codex)

- **Built-in browser:** in a Codex chat, open it from the toolbar or press Cmd+Shift+B (Mac) / Ctrl+Shift+B (Windows). Log in to NewsBreak there once. Approve access when it asks.
- **Your own Chrome:** install the **Codex Chrome extension** from the Chrome Web Store and sign in with your ChatGPT account. Codex can then use the tabs and logins you already have.

## Grok Build

Turn on the **Browser Use** plugin in Grok Build, then ask Grok to open NewsBreak. Log in yourself in the browser it opens.

## Apps without a browser (ChatGPT in the browser, grok.com)

Use the one-click **Yeez · NewsBreak** bookmark button on https://yeez.ai/data: drag it to your bookmarks bar, open your NewsBreak dashboard while logged in, click it. Upload MSN, Yahoo and other exports on the same page.

## If something goes wrong

- **"Not logged in to NewsBreak":** open https://mp.newsbreak.com/home/content/post in the browser your AI app uses (not a different one), log in, and try again.
- **The pull runs but saves 0:** you're logged in to a NewsBreak account with no articles, or a different account than the site. Switch accounts and run it again.
- **The app says it can't run JavaScript:** use the bookmark button on https://yeez.ai/data instead.
