Each Yeez task runs on its own model, set once in the task's settings. The tasks that decide what gets published get the strongest model. The routine ones get a lighter model. Inside Headlines, Articles and Social build, Yeez hands the heavy work to lighter models by itself (see [How Yeez splits work across models](helpers)), so you only set the task model.

{{model_table}}

## Set it in Claude

1. Click **Scheduled** in the sidebar and open the task.
2. Click the pencil icon to **Edit**.
3. In the bar under the instructions box, open the model menu and pick the model from the table.
4. Save. The next run uses it.

Or tell Claude: `Set each of my Yeez tasks to the model Yeez recommends.` If it can't change a model itself, it gives you the list to set by hand.

## Codex and other apps

Open the automation or scheduled task, pick the model in its settings if the app offers one, and save. Where the table says the strongest model, pick the app's top model with high reasoning. Where it says the everyday model, pick its standard model. If the app doesn't let you choose, it runs on the app's default model and Yeez still works.

## Check which model a run used

Open the task, click a run in **History**, and look at the model that session ran on. If it isn't the one you picked, set it again and save.
