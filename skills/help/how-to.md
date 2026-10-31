# How do I…

Generated from index.json and articles/ (scripts/build-help.py); edit those, not this file. The same answers are at https://yeez.ai/help.

Answer with the steps for the buyer's app, one short list, and do the part you can do for them. `{{model_table}}` and `{{if_limit}}` mean: call `get_model_plan` (with this app's id) and give the buyer that part of it.

## Getting started

### Where do I start?

Start at [Get started](https://yeez.ai/start). It walks you through installing Yeez, connecting your sites, your basics, your numbers and turning on the scheduled tasks, and ticks each step off as you go. Your dashboard shows your plan and today's runs once it's running.

## Scheduled tasks

### See your Yeez tasks

In Claude, click **Scheduled** in the sidebar. Every Yeez task is named `Yeez 1 · Learn`, `Yeez 2 · Headlines` and so on.

Or ask your AI app: `Show me my Yeez tasks`.

### Change a task's time or days

In Claude: **Scheduled** → click the task → **Edit** (pencil icon) → change the schedule → save. Daily picks one time; Weekly picks a day and a time.

Or tell Claude: `Change my Yeez Learn task to 2:30 PM`.

Keep the order: Learn in the afternoon, then Headlines, Articles, Social and Newsletter in the evening, each with time to finish before the next starts. To have Yeez work the times out again, say `Fix my Yeez tasks`.

### A task didn't run

Scheduled tasks run only while your computer is awake and the app is open.

- **Why it didn't run:** open the task and look at **History**. Hover a skipped run to see why: the computer was asleep, the previous run was still going, or other tasks were already running.
- **Stop it happening:** in Claude, Settings → This computer → System → turn on **Keep computer awake**. Closing a laptop lid still puts it to sleep.
- **What happens after:** when the computer wakes, a task that missed its time runs once to catch up. Nothing else to do.

### Stop a task asking for approval every run

Click **Run now** once after the task is created, and pick "always allow" at each prompt. Later runs reuse those approvals and don't stop to ask.

### Check and fix every task at once

Tell your AI app: `Fix my Yeez tasks`.

It checks every task's time and instructions against your plan, fixes what's off, pauses tasks you don't need, creates any that are missing, and gives you the list of models to set.

### What goes in a task's instructions

A Yeez task's instructions are only its command, for example `/yeez:headlines`. Nothing else goes there. Yeez updates reach you through the plugin and your yeez.ai account, so anything written into a task would freeze an old version.

Your own rules go to Yeez instead: [Give Yeez a rule for a site](https://yeez.ai/help/site-rule).

### Pause or delete a task

- **Pause without deleting:** in Claude, open the task and switch **Status** from Active to Paused.
- **Delete:** open the task and click **Delete** on its page.

Or tell Claude: `Pause my Yeez Social now task`.

### Run a task now

Open the task in Claude and click **Run now**.

To run the whole chain at once, type `/yeez:run` in your AI app.

### Tasks in Codex, Cursor and other apps

In Codex automations, Cursor Automations or cron, open the automation, edit its schedule or prompt, and save. If you're not sure where, ask the app: `Show me my Yeez tasks and let me change their times`.

Apps that hold only one scheduled task (ChatGPT, Grok) run everything in one daily task with `/yeez:run`.

## AI models and usage limits

### Which AI model should each scheduled task use?

Each Yeez task runs on its own model, set once in the task's settings. The tasks that decide what gets published get the strongest model. The routine ones get a lighter model. Inside Headlines, Articles and Social build, Yeez hands the heavy work to lighter models by itself (see [How Yeez splits work across models](https://yeez.ai/help/helpers)), so you only set the task model.

{{model_table}}

#### Set it in Claude

1. Click **Scheduled** in the sidebar and open the task.
2. Click the pencil icon to **Edit**.
3. In the bar under the instructions box, open the model menu and pick the model from the table.
4. Save. The next run uses it.

Or tell Claude: `Set each of my Yeez tasks to the model Yeez recommends.` If it can't change a model itself, it gives you the list to set by hand.

#### Codex and other apps

Open the automation or scheduled task, pick the model in its settings if the app offers one, and save. Where the table says the strongest model, pick the app's top model with high reasoning. Where it says the everyday model, pick its standard model. If the app doesn't let you choose, it runs on the app's default model and Yeez still works.

#### Check which model a run used

Open the task, click a run in **History**, and look at the model that session ran on. If it isn't the one you picked, set it again and save.

### Hitting your plan's usage limit

If a run stops because you hit your plan's limit:

{{if_limit}}

### How Yeez splits work across models

A Yeez task works like an editor with a small team. The task's own model is the editor: it picks the stories, decides what's good enough, and schedules everything. For the heavy, repeatable jobs it starts helpers, each on the model Yeez names for that job:

- **Headlines:** helpers search for stories and record every fact with its source. The task writes and ranks the headlines.
- **Articles:** one helper writes each article and runs Yeez's check on it. A second helper reads the finished article cold against its sources. The task reads it last, then schedules it.
- **Social build:** helpers render each Page's cards and reels. The task looks at every image.

No more than 3 helpers run at once, so your plan's usage doesn't burn in one burst. Helpers never publish, post or change anything on your site; the task does that after reading their work. In apps that can't start helpers (ChatGPT in the browser, for example), the task does every step itself.

## Sites and articles

### Change how many articles a day

Tell your AI app: `Set parentdiaries.com to 15 articles a day` (with your site). Yeez saves it and the next run follows it.

Raise it in steps, and only while views hold up.

### Change publish times

Tell your AI app: `Publish on parentdiaries.com from 8 AM to 8 PM` (with your site). Yeez spreads the day's articles across that window from the next run.

### See and change what's scheduled

Type `/yeez:scheduled` in your AI app. Each article has an edit link, so you can change or unschedule it in your site's editor before it publishes. Your dashboard lists them too.

### Give Yeez a rule for a site

Tell your AI app: `Yeez rule for parentdiaries.com: never cover celebrity gossip`. It's saved to that site and every run follows it.

Yeez already sticks to named, reported sources, never uses Reddit or forums, and never writes clickbait, so those don't need saving.

### Change a site's story mix or voice

Type `/yeez:learn` for that site, then tell it what to change before you confirm: more of one kind of story, less of another, or how the writing should sound.

## Learn and your numbers

### Learn asks me to log in

Learn pulls your numbers from NewsBreak and your other dashboards in your AI app's browser. When a login expires, log in there again, then tell it `done`. You stay logged in after that.

Learn runs in the early afternoon, when you're usually at the computer, so it can ask.

### Pull your numbers now

Type `/yeez:learn daily` in your AI app.

## Google search

### Search articles: who gets them, turning them off, approving

Nobody has to turn them on. Once Search Console is connected, Yeez checks each site every Monday and writes a few search articles a week only on sites Google already trusts: it indexes nearly all the site's new articles and already ranks it for real searches. The Articles task writes them; there's no separate task.

- **Where a site stands:** ask `Does my site get Yeez search articles?`
- **Turn them off anyway:** `Turn off Yeez search articles for parentdiaries.com`.
- **Approve one:** on your dashboard, by telling your AI app, or in WordPress under Posts → Pending.

## Newsletter

### Change newsletter send days

Tell your AI app: `My newsletter now sends Tuesday and Friday`. Then say `Fix my Yeez tasks`, so the Newsletter task runs the night before each send day.

## Billing and the guarantee

### Billing, refunds and the guarantee

Payments, licenses, refunds and the 90-day guarantee terms: email [alex@clarkbrosmedia.com](mailto:alex@clarkbrosmedia.com). The guarantee terms are on the Terms page, under Guarantee.

## Anything else

Search every answer at https://yeez.ai/help. Your dashboard: https://yeez.ai/dashboard. Billing, refunds and anything Yeez can't do: alex@clarkbrosmedia.com.
