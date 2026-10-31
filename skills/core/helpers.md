# Helpers: handing work to other models inside a task

A Yeez task runs on the model the buyer set for it (the **task model**). Headlines, Articles and Social build hand their heavy, repeatable jobs to **helpers**: separate agents, each on the model Yeez names for that job. The task model stays in charge: it splits the work, briefs each helper, reviews what comes back, and makes every decision that changes the buyer's site (scoring, holding, scheduling, posting).

## The rules

1. **Get the plan first.** Call `get_model_plan` once at the start of the task (pass this app's id). It names each helper job's agent, its `model` (and `model_id` in Claude), and `max_helpers_at_once`.
2. **Name the model on every hand-off.** When you start a helper, pass the plan's model for that job explicitly (in Claude, the `model` parameter of the Agent tool with `model_id`). Never rely on the helper's own default.
3. **Never more than `max_helpers_at_once` running at the same time** (3). Start the next one only when one finishes.
4. **Use the Yeez helper agents when this app has them** (`yeez-gatherer`, `yeez-writer`, `yeez-checker`, `yeez-renderer`; in Claude they may show as `yeez:yeez-writer`). If they aren't listed, start a general helper and give it the matching instructions from [helpers/](helpers/) word for word, plus the assignment.
5. **Brief each helper completely.** A helper starts with nothing: give it the site, the job, and everything from the brief it needs (voice notes, story-type guide, the buyer's rules, tonight's openings so far). Ask for the result in the shape its instructions give.
6. **Helpers never change anything the buyer sees.** They don't schedule, post, hold, score or save settings. You do, after you've read what they returned.
7. **No helpers in this app?** (ChatGPT and other chat apps, or a run where starting one fails twice.) Do the helper's steps yourself, in order, exactly as its instructions say. Same result, one model.
8. **Unattended:** helpers never ask the buyer anything either. Anything the buyer needs to know goes in your summary.
