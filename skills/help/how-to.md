# How do I…

Quick answers to the small things buyers ask. Give the steps for their app, one short list, and offer to do the part you can do for them.

## Scheduled tasks

Claude (the desktop app):
- **See your tasks:** click **Scheduled** in the sidebar.
- **Change a task's time or days:** Scheduled → click the task → **Edit** (pencil icon) → change the schedule → save. Daily picks one time; Weekly picks a day and a time.
- **Change a task's instructions:** same Edit form, the instructions box. A Yeez task's instructions are only its command (for example `/yeez:headlines`). Nothing else goes there; rules go to Yeez (see "Give Yeez a rule" below).
- **Delete a task:** Scheduled → click the task → **Delete** on its page.
- **Pause a task without deleting it:** on the task's page, switch **Status** from Active to Paused.
- **Run a task now:** on the task's page, click **Run now**.
- **See what a run did, or why it didn't run:** on the task's page, the **History** list. Click a run to open what it did. Hover a skipped run to see why.
- **Keep runs from being missed while you're away:** Settings → This computer → System → turn on **Keep computer awake**. Closing a laptop lid still puts it to sleep.
- **Missed runs:** tasks run only while the computer is awake and the app is open. When it wakes, a task that missed its time runs once to catch up.
- **Let a task run without stopping for approvals:** click **Run now** once after creating it, and pick "always allow" for each prompt. Later runs reuse those approvals.

You can also ask Claude: "Change my Yeez Learn task to 2:30 PM", "Pause my Yeez Search task", "Show me my Yeez tasks". To check and fix every task's time and instructions at once, say **"Fix my Yeez tasks"**.

Other apps (Codex automations, Cursor Automations, cron): open the automation or task in the app, edit its schedule or prompt there, and save. If unsure, ask the app "Show me my Yeez tasks and let me change their times".

## Your sites and articles

- **Change how many articles a day:** tell your AI app "Set parentdiaries.com to 15 articles a day". Yeez saves it (`save_site_settings`, `per_day`) and the next run follows it.
- **Change publish times:** "Publish on parentdiaries.com from 8 AM to 8 PM" (`start`, `end`).
- **See what's scheduled:** `/yeez:scheduled`. Each post has an edit link to change or unschedule it in your site's editor.
- **Run everything now:** `/yeez:run`.
- **Give Yeez a rule for a site:** tell your AI app "Yeez rule for parentdiaries.com: never cover celebrity gossip". It's saved to that site in Yeez (`buyer_rules`) and every run follows it. Yeez already sticks to named, reported sources, never uses Reddit or forums, and never writes clickbait, so those don't need saving.
- **Change a site's mix or voice:** `/yeez:learn` for that site, then tell it what to change before you confirm.

## Numbers and logins

- **Learn asks you to log in:** log in to NewsBreak (or the dashboard it names) in your AI app's browser, then tell it "done". You stay logged in after that.
- **Pull your numbers now:** `/yeez:learn daily`.

## Search articles (Google)

- **Who gets them:** nobody has to turn them on. Once Search Console is connected, Yeez checks each site every Monday and writes a few search articles a week only on sites Google already trusts (it indexes nearly all the site's new articles and already ranks it for real searches). The Articles task writes them; there's no separate task. To see where a site stands, ask "Does my site get Yeez search articles?" (`get_search_ideas` gives the reasons).
- **Turn them off anyway:** "Turn off Yeez search articles for parentdiaries.com" (`search_per_week` 0).
- **Approve one:** on your yeez.ai dashboard, by telling your AI app, or in WordPress under Posts → Pending.

## Newsletter

- **Change send days:** tell your AI app "My newsletter now sends Tuesday and Friday". Then say "Fix my Yeez tasks" so the Newsletter task runs the night before each send day.

## Anything else

Your dashboard: https://yeez.ai/dashboard. Billing, refunds and anything Yeez can't do: alex@clarkbrosmedia.com.
