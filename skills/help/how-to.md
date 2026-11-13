# How do I…

Generated from index.json and articles/ (scripts/build-help.py); edit those, not this file. The same answers are at https://yeez.ai/help.

Answer with the steps for the buyer's app, one short list, and do the part you can do for them. `{{model_table}}` and `{{if_limit}}` mean: call `get_model_plan` (with this app's id) and give the buyer that part of it.

## Getting started

### Where do I start?

Start at [Get started](https://yeez.ai/start). It walks you through installing Yeez, connecting your sites, your basics, your numbers and turning on the scheduled tasks, and ticks each step off as you go. Your dashboard shows your plan and today's runs once it's running.

### Set up Pinterest

Yeez makes your pins and schedules them in your own Pinterest account, through your AI app's browser. There's nothing to connect and no keys.

What you need:
- A Pinterest **business** account (free). Your AI app checks this and shows you the switch if you're on a personal account; your pins and followers stay.
- Your AI app's browser signed in to Pinterest (in the Claude app, that's Claude in Chrome).

Then tell your AI app: `Set up Pinterest for Yeez`

It reads your boards, picks your colours from your site and your existing pins, and shows you three sample pins in different designs. Pick the look you like. From then on, the social tasks make new pins from your articles every day, each article getting a fresh design every couple of weeks, and schedule them with Pinterest's own scheduler.

Every week it checks your Pinterest analytics and the top pins for your topics, and makes more of what gets clicks.

### Change how my pins and cards look

Your pins (and recipe or product cards on Facebook and Instagram) use a set of designs: a boxed title over your photo, a title band between two photos, a big title at the top, a recipe card, a four-photo roundup collage and a numbered roundup grid.

To change the look, just tell your AI app what you want, for example:

`Make my pins use our dark green and yellow`

`Use a bigger number on roundup pins`

`Stop using the recipe card design`

It saves the change for your site, rebuilds a sample so you can see it, and every pin after that follows it.

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

### Have Yeez find stories on certain sites

Tell your AI app which sites to look at first, for one of your sites:

`Yeez rule for lovelygardenroots.com: look for stories on bhg.com/gardening and hgtv.com/outdoors/gardens first`

It's saved to that site, and every Headlines run searches those sites first. Yeez writes its own article from each story and credits where it came from. It never copies another site's text.

#### Want lighter or different kinds of stories?

Try them as tests first instead of giving them fixed daily slots:

`Yeez rule for parentdiaries.com: test parenting tips and fun, lighter stories, and keep the kinds that get views`

About a quarter of each day's picks are tests. Learn grades every test against your site's views and gives more room to the kinds that win, so you get more variety without your views dropping.

To change how much of each kind of story a site runs, see [Change a site's story mix or voice](https://yeez.ai/help/site-mix-voice).

### A site got no articles, or fewer than its daily count

A site got no articles, or fewer than its daily count.

- **Fill it now:** tell your AI app `Fill today's Yeez articles for lovelygardenroots.com` (with your site). It picks headlines for the missing slots and writes them. Leave out the site to fill every site.
- **See why:** open Scheduled, then the Headlines and Articles tasks, and look at **History**. A skipped run means the computer was asleep or the app was closed (see [missed-runs](https://yeez.ai/help/missed-runs)). A run that finished short says why at the top of its report: too few true stories found, or stories held at the fact check.
- **Nothing to fix in the tasks:** the Articles task works through every site. If the Headlines task didn't run, it picks the headlines itself, and it tops up any site that's short before it finishes.

### The stories drift off-topic

The stories drift away from what your site covers.

Give Yeez a rule for that site: `Yeez rule for lovelygardenroots.com: every story is about gardening` (with your site and what it covers). It's saved to the site and the next Headlines run follows it.

Before you set how many of each kind of story to run, check your weekly review. It shows which kinds of stories get views on your site and flags any of your rules that put slots into kinds that don't.

### Can Yeez tick my SimpleFeed / NewsBreak boxes?

Yes. If your site uses a feed plugin like SimpleFeed or NewsBreak Feed for WordPress, Yeez ticks its boxes (NewsBreak, MSN Article, MSN Gallery, Yahoo and the rest) on every post it schedules, so you don't tick them by hand.

You choose which boxes in setup. To change them later, tell your AI app:

`Yeez, show the feed boxes on example.com`

then, for example:

`Yeez, tick NewsBreak and MSN Article on example.com`

Article boxes go on articles and gallery boxes (MSN Gallery, Yahoo Slideshows, AOL Slideshows) on galleries.

#### Why Yeez needs a small helper on your site

WordPress doesn't let outside tools change a feed plugin's boxes on their own. Yeez opens them one of two ways:

- If your site has the free **Code Snippets** plugin, Yeez adds a snippet called "Yeez: let Yeez tick your feed boxes" by itself. Leave it on.
- Otherwise, install the **Yeez WordPress plugin**: download https://yeez.ai/downloads/yeez-wp.zip, then WordPress → Plugins → Add New → Upload Plugin → Install Now → Activate. If you already have it, choose "replace" so you get the newest version.

Posts you scheduled before this was set up keep whatever boxes they had.

## Views, Learn and your numbers

### How do I use Yeez to get more views and money?

Yeez writes and publishes for you every day, and Learn fine-tunes your headlines as your numbers come in. The bigger moves are yours: what kinds of stories you run, how many a day, how headlines are written, what each post should earn. Yeez does the digging for you. You just ask it the right things in your AI app. This is how the Yeez team works its own sites, step by step, with what to type at each step.

You can type any of these in the Claude desktop app (or your AI app) where Yeez is installed, any time. The weekly review runs them for you every Monday, but asking yourself is how you get the most out of it.

#### 1. Set your goal: views or money

Pick one number per site and a date. If what you really want is income, make it money, because your money may come from more than one place: the platform's revenue share, site ads, your newsletter and its sponsors, affiliate offers, your own products.

Type:
- `/yeez:review set my goals`
- or: `My goal for parentdiaries.com is $3,000 a month by February. Work out the views and posts it takes.`

For money goals, give Yeez your income, in as much detail as you have. The more data, the better the money math. Don't just type totals; drop in the full statements and exports:
- NewsBreak's monthly PDF statement, MSN's earnings statement, Yahoo or SmartNews reports
- your ad network's report (by day and by page if it offers one)
- affiliate exports (clicks, sales and commissions by link or page)
- newsletter sponsor and paid recommendation payouts, and product sales

Then type: `Here are my October statements. Log everything in them.` Yeez keeps the originals in your Yeez folder and pulls out every number: totals by source, your RPM on each platform month to month and, when a statement lists earnings per article, exactly what each post made. That's what tells you which kinds of stories really pay.

Yeez works out what one view pays you on each platform, turns the goal into views per day and money per post, and tells you straight if your site has never done it before. A good first goal is one your site has already hit, like your best month.

#### 2. See where you really stand

One good day or one bad week tells you almost nothing. Ask for the full picture:
- `/yeez:review`
- `How did each of my sites do month by month this year? Where am I against my goal?`
- `Why did views drop in October? Look at everything that changed around then.`

Yeez compares each post with others published the same month on the same platform, so one good or bad month can't fake a pattern. "Lift" is that comparison: 1.0 is average for its month, 2.0 is twice the views. The current month always looks low because its posts haven't had time to collect views.

#### 3. Find what each slot is worth

Every post you publish takes a slot, and some slots are worth far more than others. That's the biggest lever you have.
- `Which kinds of stories on my garden site earn the most per post, counting views and anything else they bring in? Which get the most slots?`
- `Which of my story types get lots of slots but earn the least?`
- `Show me every post this month over 20,000 views. What do they have in common?`
- `Which story types are wearing out, and which are rising?`

Yeez ranks your story types by money per post: platform pay plus affiliate clicks and earnings, and newsletter signups where it can track them. Moving even a few slots a day from a weak type to a strong one adds up fast.

#### 4. Check what's actually moving your numbers

- `Which headline shapes win on my site? Length, opening with a person, a number, a quote?`
- `Read my 5 best and 5 worst posts from the last month. How do they open, and what's different?`
- `Did my views per post drop in the weeks I published more?`
- `Did NewsBreak make all my posts live? Is anything being flagged?`
- `Which of my old big hits could run again with today's facts?`
- `Look at my whole setup like an outsider. What could be holding my sites back that I haven't thought of?`

Ask for the numbers behind every answer and how many posts they rest on. Under about 15 posts is a hunch, not a pattern.

#### 5. Question your own rules

Every rule you've saved controls part of your day, and a rule that's costing you is usually the fastest fix there is.
- `List every rule on my sites and tell me what my numbers say about each one.`
- `Is my one-tip-a-day rule helping or hurting Parent Diaries?`

#### 6. Pick one change and test it

- `What are the 3 changes most likely to get me to my goal? Show the math for each.`
- `Let's test option 2.`
- `I want to try 15 posts a day on Parent Diaries. What do my numbers say?`

Yeez applies the change, logs it as a test, and checks it after 7 days (a whole-site change like the daily count or the mix) or 14 days (a headline or story-type test). Then:
- **Grow** it if it clearly beat the rest.
- **Hold** it another week if it's too close to call.
- **End** it if it lost. That's a result too.

Change one thing at a time. Change two and you'll never know which one worked.

- `How is my test doing?`
- `End the test and put things back.`

#### 7. Keep going

Every Monday the review opens with how your running test did, then gives you the next options. Reply in that same chat to dig in, or type `/yeez:review` any time. The full review is also saved in your Yeez folder (`yeez-work/reviews/`) so you can look back.

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

### A newsletter for each site

Each site has its own newsletter. A site's articles show only its own newsletter's signup line, and each newsletter's issues are built from that site's own stories. A site with no newsletter gets no signup line.

Set one up for a site by telling your AI app:

`Set up the newsletter for lovelygardenroots.com`

It asks for the newsletter's name, platform, signup page, send days and send time, and saves it to that site. Do the same for each site that has a newsletter. If two sites share one newsletter, set it up on both.

Change one the same way: `Change the newsletter for parentdiaries.com: the signup page is now …`

The Newsletter task builds the next issue for every site whose newsletter sends the next day. If your send days change, see [Change newsletter send days](https://yeez.ai/help/newsletter-days).

### Change newsletter send days

Tell your AI app the site and the new days, for example: `The parentdiaries.com newsletter now sends Tuesday and Friday`. Then say `Fix my Yeez tasks`, so the Newsletter task runs the night before each send day.

## Billing and the guarantee

### Billing, refunds and the guarantee

Payments, licenses, refunds and the 90-day guarantee terms: email [alex@clarkbrosmedia.com](mailto:alex@clarkbrosmedia.com). The guarantee terms are on the Terms page, under Guarantee.

## Anything else

Search every answer at https://yeez.ai/help. Your dashboard: https://yeez.ai/dashboard. Billing, refunds and anything Yeez can't do: alex@clarkbrosmedia.com.
