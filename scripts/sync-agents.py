#!/usr/bin/env python3
"""Copies the Yeez helper instructions (skills/core/helpers/*.md, the one source) into agents/,
where Claude loads them as plugin agents. Run after editing a helper; commit both."""
import pathlib, shutil
root = pathlib.Path(__file__).resolve().parent.parent
src, dst = root / "skills/core/helpers", root / "agents"
dst.mkdir(exist_ok=True)
for f in sorted(src.glob("*.md")):
    shutil.copyfile(f, dst / f.name)
    print("synced", f.name)
