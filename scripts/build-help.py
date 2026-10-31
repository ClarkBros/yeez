#!/usr/bin/env python3
"""Builds skills/help/how-to.md (what the AI app reads in one go) from the help center's one source:
skills/help/index.json + skills/help/articles/*.md. yeez.ai/help reads the same files. Run after editing an answer."""
import json, pathlib, re
root = pathlib.Path(__file__).resolve().parent.parent / "skills/help"
idx = json.loads((root / "index.json").read_text())
out = ["# How do I…", "", "Generated from index.json and articles/ (scripts/build-help.py); edit those, not this file. The same answers are at https://yeez.ai/help.",
       "", "Answer with the steps for the buyer's app, one short list, and do the part you can do for them. `{{model_table}}` and `{{if_limit}}` mean: call `get_model_plan` (with this app's id) and give the buyer that part of it.", ""]
for t in idx["topics"]:
    arts = [a for a in idx["articles"] if a["topic"] == t["id"]]
    if not arts: continue
    out += [f"## {t['name']}", ""]
    for a in arts:
        body = (root / "articles" / f"{a['slug']}.md").read_text().strip()
        body = re.sub(r"\]\(([a-z0-9-]+)\)", r"](https://yeez.ai/help/\1)", body)
        body = body.replace("](/start)", "](https://yeez.ai/start)")
        body = re.sub(r"^## ", "#### ", body, flags=re.M)
        out += [f"### {a['title']}", "", body, ""]
out += ["## Anything else", "", "Search every answer at https://yeez.ai/help. Your dashboard: https://yeez.ai/dashboard. Billing, refunds and anything Yeez can't do: alex@clarkbrosmedia.com.", ""]
(root / "how-to.md").write_text("\n".join(out))
print("how-to.md:", len(idx["articles"]), "answers")
