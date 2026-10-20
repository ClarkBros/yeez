#!/usr/bin/env python3
"""
reel_parse.py — turn the nightly `Reels - <date>.md` spec files into a render manifest.

Reads every page's reel spec for a working date, extracts the machine-renderable
fields (format, on-screen text, caption, model id, slug), resolves Format S model
IDs to their source screenshot filename via the Daily-Prep ingest ledger, and
writes a single JSON manifest that reel_render.py consumes.

This script READS ONLY. It never edits a spec file, never touches Drive, never
publishes. Per CLAUDE.md §0 the render pipeline is render-only.

Usage:
    python3 reel_parse.py --date 2026-08-15 [--brain /path/to/MediaCo-Brain]
                          [--out manifest.json] [--pages CLW,NEN]
"""

import argparse
import json
import os
import re
import sys
from datetime import date, datetime, timedelta

# ---------------------------------------------------------------- constants

# Model-ID families used across the political/news corpus (rebrand spec).
MODEL_ID_RE = re.compile(r"\b((?:V-IMG-P|V-IMG|BBG-P|BBG|TI-P|TI)\s*\d+)\b")

REEL_HEADING_RE = re.compile(
    r"^###\s+(?P<page>.+?)\s+Reel\s+(?P<num>\d+)\s*[—-]\s*(?P<slug>.+?)\s*"
    r"(?:\((?:Format\s+)?(?P<fmt>[A-Z])\))?\s*$"
)

FIELD_RE = re.compile(r"^\*\*(?P<name>[^*]+?):?\*\*\s*(?P<rest>.*)$")

# A real field label carries a colon immediately before the closing "**"
# ("**AI video prompt:** ..."). Tested on the raw line, because FIELD_RE's
# optional ":?" swallows the colon, and a label may carry inline content after
# it — so "endswith(':**')" is NOT a valid test.
LABEL_COLON_RE = re.compile(r"^\*\*[^*]+:\*\*")

# One on-screen row. Format N numbers them ("1. ..."); Format A used dash
# bullets ("- (white) ..."). Both mean the same thing: one row, one box.
NUMBERED_RE = re.compile(r"^\s*(?:(\d+)[.)]|[-*•])\s+(.*\S)\s*$")

# Fields that terminate the on-screen-text block.
ONSCREEN_TERMINATORS = (
    "length", "caption", "clones", "clones / source", "variation note",
    "format extras", "tag", "§7 note", "model id", "concept",
)

# Canonical field names. The specs decorate these headers freely — e.g.
# "**On-screen text (Title Case) — silent text-on-b-roll, 20-40s, hook in 3s:**"
# — so we match on the leading words and throw the decoration away. Longest
# prefix wins so "caption" never swallows a longer key.
CANONICAL_FIELDS = (
    "on-screen text", "on screen text", "model id", "concept", "length",
    "caption", "clones / source", "clones", "variation note", "format extras",
    "tag",
)

# Page-name → short code, from _Brain/Data/account-page-map.md conventions.
PAGE_CODES = {
    "The Retirement Wire": "TRW",
    "The Daily Overview": "TDO",
    "The Cost of Living Wire": "CLW",
    "The Money Overview": "TMO",
    "The Financial Wire": "TFW",
    "Morning Overview": "MO",
    "Overview Today": "OT",
    "Nest Egg Nation": "NEN",
    "The Golden Years": "GY",
    "Ask Retirement": "AR",
    "Beyond the Paycheck": "BTP",
    "Runway to Retirement": "RR",
}

# Retirement roster (2026-09-24, _Shared/Prompts/SRC/_data/fb-pages.yaml): site folder AND live FB name -> code.
PAGE_CODES.update({
    "The Cost of Living Wire": "CLW", "Patriot Summit News": "CLW",
    "Nest Egg Nation": "NEN", "Liberty Front Daily": "NEN",
    "Morning Overview": "MO", "The Red Wave": "MO",
    "Runway to Retirement": "RR",
    "Off the Clock": "OTC",
    "Retirement Real Talk": "RRT",
})

# Monetized Tier-1 pages (fb-pages.yaml `monetized: true`).
TIER1 = {"CLW", "NEN"}


# ---------------------------------------------------------------- helpers

def strip_md(text):
    """Remove the inline markdown emphasis the specs use, keep the words."""
    text = re.sub(r"\*\*(.+?)\*\*", r"\1", text)
    text = re.sub(r"\*(.+?)\*", r"\1", text)
    text = re.sub(r"`(.+?)`", r"\1", text)
    return text.strip()


def normalize_model_id(raw):
    """'V-IMG-P  62' -> 'V-IMG-P 62' so ledger lookups match."""
    return re.sub(r"\s+", " ", raw.strip()).upper()


def working_day(now=None):
    """CLAUDE.md working-day rule: before 05:00 local, the working day is yesterday."""
    now = now or datetime.now()
    d = now.date()
    if now.hour < 5:
        d = d - timedelta(days=1)
    return d.isoformat()


# ---------------------------------------------------------------- ledger

def load_screenshot_ledger(brain):
    """
    Parse _Shared/Daily-Prep/ingested-screenshots.md into {MODEL_ID: {...}}.

    Rows look like:
      | 2026-08-15 | News-Image | news/Screenshot ... .png | V-IMG-P 62 | summary |

    A model ID can legitimately appear more than once (re-screenshots of the
    same post). We keep the FIRST clean row and record the duplicates, because
    later rows are often tagged '(duplicate file)' or '(recapture)'.
    """
    path = os.path.join(brain, "_Shared", "Daily-Prep", "ingested-screenshots.md")
    ledger = {}
    if not os.path.exists(path):
        return ledger, path

    with open(path, encoding="utf-8") as fh:
        for line in fh:
            if not line.lstrip().startswith("|"):
                continue
            cells = [c.strip() for c in line.strip().strip("|").split("|")]
            if len(cells) < 4:
                continue
            row_date, row_type, row_path, row_id = cells[0], cells[1], cells[2], cells[3]
            if row_date.lower().startswith("date") or set(row_date) <= set("-: "):
                continue  # header / separator

            m = MODEL_ID_RE.search(row_id)
            if not m:
                continue  # EXCLUDED rows carry no ID by design
            mid = normalize_model_id(m.group(1))

            # Skip rows explicitly marked as a duplicate/recapture of an existing ID.
            noisy = re.search(r"duplicate|recapture", row_id, re.I)

            entry = {
                "model_id": mid,
                "ingested_date": row_date,
                "type": row_type,
                "drive_path": strip_md(row_path),
                "basename": os.path.basename(strip_md(row_path)),
                "summary": cells[4] if len(cells) > 4 else "",
            }
            if mid not in ledger:
                ledger[mid] = entry
            elif not noisy:
                # A cleaner later row for the same ID; keep the earliest but note it.
                ledger[mid].setdefault("also_seen", []).append(entry["drive_path"])

    return ledger, path


# ---------------------------------------------------------------- spec parsing

def split_reel_blocks(lines):
    """Yield (heading_match, block_lines) for each '### ... Reel N ...' section."""
    blocks, current, heading = [], [], None
    for line in lines:
        m = REEL_HEADING_RE.match(line.rstrip())
        if m:
            if heading is not None:
                blocks.append((heading, current))
            heading, current = m, []
            continue
        if line.startswith("## ") and heading is not None:
            # 'Craft Notes' etc. closes the last reel block.
            blocks.append((heading, current))
            heading, current = None, []
            continue
        if heading is not None:
            current.append(line)
    if heading is not None:
        blocks.append((heading, current))
    return blocks


def parse_fields(block_lines):
    """
    Walk a reel block and collect '**Field:** value' entries, supporting values
    that continue across following lines (captions are often multi-paragraph).
    """
    fields, order = {}, []
    current = None
    for raw in block_lines:
        line = raw.rstrip("\n")
        m = FIELD_RE.match(line.strip())
        if m:
            name = m.group("name").strip().lower().rstrip(":").strip()
            # Drop decoration wherever it sits, then map onto a canonical key.
            stripped = re.sub(r"\s*[(—–-]\s.*$", "", name).strip()
            stripped = re.sub(r"\s*\(.*?\)", "", stripped).strip()
            base = None
            for key in sorted(CANONICAL_FIELDS, key=len, reverse=True):
                if stripped.startswith(key) or name.startswith(key):
                    base = "on-screen text" if key == "on screen text" else key
                    break
            # A bold line is a FIELD LABEL only if it names a canonical field or
            # ends with a colon ("**§7 note:**"). A fully-bold line with no
            # trailing colon is body copy — specs use them as on-screen kickers
            # ("**BUILD THEM HERE. HIRE HERE.**"). Treating those as labels
            # silently truncated the field at the kicker, and dropped the block
            # entirely when the bold line came first. This is the same defect
            # that gutted 31 of 33 text-image cards on 2026-08-17.
            # Trailing-colon (not canonical-only, as in textimage_parse.py)
            # because reel specs carry real non-canonical labels like "§7 note".
            if base is None and not LABEL_COLON_RE.match(line.strip()):
                if current is not None:
                    fields[current].append(line)
                continue
            base = base or stripped or name
            current = base
            fields.setdefault(base, [])
            order.append(base)
            rest = m.group("rest").strip()
            if rest:
                fields[base].append(rest)
            continue
        if current is not None:
            fields[current].append(line)
    return {k: "\n".join(v).strip() for k, v in fields.items()}


def extract_onscreen(fields):
    """
    Return (mode, cards) for the on-screen text.

    mode 'sequence' -> numbered cards revealed one at a time (Format N)
    mode 'single'   -> one held field (Format B, and the card text for S)
    """
    raw = fields.get("on-screen text", "")
    if not raw:
        return "none", []

    lines = [l for l in raw.splitlines()]
    cards, saw_numbered = [], False
    for line in lines:
        s = line.strip()
        if not s:
            continue
        # Stop if we ran into an adjacent field that failed to split.
        low = s.lower().lstrip("*").rstrip(":*").strip()
        if any(low.startswith(t) for t in ONSCREEN_TERMINATORS):
            break
        nm = NUMBERED_RE.match(s)
        cards.append(strip_md(nm.group(2)) if nm else strip_md(s))
        if nm:
            saw_numbered = True

    cards = [c for c in cards if c]
    if not cards:
        return "none", []
    if saw_numbered and len(cards) > 1:
        return "sequence", cards
    return "single", [" ".join(cards)]


# Format A (retired 2026-08-09) tagged every on-screen line with the colour of
# its box: "1. (white) The Apartment Rent Number Isn't The Real Number."
# That is the writer's own styling decision, so honour it wherever it appears
# instead of inventing a pattern downstream.
STYLE_TAG_RE = re.compile(r"^\((white|black|red)\)\s*", re.I)


def split_style_tags(cards):
    """
    ([text...], [style-or-None...]) — strips a leading (white)/(black)/(red)
    tag off each card and returns the styles alongside the cleaned text.
    """
    texts, styles = [], []
    for card in cards:
        m = STYLE_TAG_RE.match(card)
        if m:
            styles.append(m.group(1).lower())
            texts.append(STYLE_TAG_RE.sub("", card).strip())
        else:
            styles.append(None)
            texts.append(card)
    return texts, styles


def parse_spec_file(path, page_dir):
    """Parse one `Reels - <date>.md` into a list of reel dicts."""
    with open(path, encoding="utf-8") as fh:
        lines = fh.readlines()

    # Headers vary ("Working date: **2026-08-15**" vs "Working Date 2026-08-10"),
    # so match loosely and fall back to the date in the filename.
    header = "".join(lines[:8])
    pub = re.search(r"publish(?:\s+date)?:?\s*\**\s*(\d{4}-\d{2}-\d{2})", header, re.I)
    work = re.search(r"working\s+date:?\s*\**\s*(\d{4}-\d{2}-\d{2})", header, re.I)
    fname_date = re.search(r"(\d{4}-\d{2}-\d{2})", os.path.basename(path))
    working_date = (work.group(1) if work
                    else fname_date.group(1) if fname_date else None)

    reels = []
    for heading, block in split_reel_blocks(lines):
        fields = parse_fields(block)

        fmt = heading.group("fmt")
        if not fmt:
            tag = fields.get("tag", "")
            fm = re.search(r"Format:\s*([A-Z])", tag)
            fmt = fm.group(1) if fm else None
        if not fmt:
            fm = re.search(r"Format used:?\s*\**\s*([A-Z])", header)
            fmt = fm.group(1) if fm else "B"

        model_raw = fields.get("model id", "")
        model_ids = [normalize_model_id(x) for x in MODEL_ID_RE.findall(model_raw)]

        mode, cards = extract_onscreen(fields)
        cards, card_styles = split_style_tags(cards)

        page_name = os.path.basename(page_dir)
        code = PAGE_CODES.get(page_name, heading.group("page").strip())

        reels.append({
            "page": page_name,
            "page_code": code,
            "tier1": code in TIER1,
            "reel_number": int(heading.group("num")),
            "slug": strip_md(heading.group("slug")),
            "format": fmt,
            "model_ids": model_ids,
            "primary_model_id": model_ids[0] if model_ids else None,
            "concept": strip_md(fields.get("concept", "")),
            "onscreen_mode": mode,
            "onscreen_cards": cards,
            "onscreen_styles": card_styles,
            "length_note": strip_md(fields.get("length", "")),
            "caption": strip_md(fields.get("caption", "")),
            "variation_note": strip_md(fields.get("variation note", "")),
            "spec_file": path,
            "working_date": working_date,
            "publish_date": pub.group(1) if pub else None,
        })
    return reels


# ---------------------------------------------------------------- assembly

def resolve_assets(reel, ledger, assets_dir):
    """
    Attach source-image info.

    No format REQUIRES the still any more. Since 2026-08-16 (Alex) every format —
    S included — renders as the spec's on-screen text over b-roll, so a still is
    at most an optional background and a miss is never fatal. Format S used to be
    special-cased here as "missing", which made the parser print a blocked count
    for reels the renderer went on to build perfectly.
    """
    info = {"source_image": None, "source_status": "not_required",
            "drive_path": None, "resolved_via": None}

    mid = reel["primary_model_id"]
    if mid:
        info["source_status"] = "optional_missing"
    else:
        return info

    entry = ledger.get(mid)
    if not entry:
        info["source_status"] = "optional_missing"
        return info

    info["drive_path"] = entry["drive_path"]
    info["resolved_via"] = "ingested-screenshots.md"

    # Look for the file in the local assets drop folder (Drive auth deferred).
    candidate = os.path.join(assets_dir, entry["basename"])
    if os.path.exists(candidate):
        info["source_image"] = candidate
        info["source_status"] = "ok"
        return info

    # Also accept a nested copy that mirrors the Drive folder layout.
    nested = os.path.join(assets_dir, entry["drive_path"])
    if os.path.exists(nested):
        info["source_image"] = nested
        info["source_status"] = "ok"
    return info


def main():
    ap = argparse.ArgumentParser(description="Parse reel specs into a render manifest.")
    ap.add_argument("--date", default=None,
                    help="Working date (YYYY-MM-DD). Defaults to the working day.")
    ap.add_argument("--brain", default=os.environ.get("MEDIACO_BRAIN", "."),
                    help="Path to the MediaCo-Brain root.")
    ap.add_argument("--assets", default=None,
                    help="Local folder holding source screenshots + music.")
    ap.add_argument("--out", default=None, help="Manifest output path.")
    ap.add_argument("--pages", default=None,
                    help="Comma-separated page codes to limit the run (e.g. CLW,NEN).")
    args = ap.parse_args()

    brain = os.path.abspath(args.brain)
    wdate = args.date or working_day()
    assets_dir = args.assets or os.path.join(brain, "_Brain", "Data", "reel-render", "assets")
    only = {p.strip().upper() for p in args.pages.split(",")} if args.pages else None

    sites_dir = os.path.join(brain, "Sites")
    if not os.path.isdir(sites_dir):
        sys.exit(f"ERROR: no Sites/ directory under {brain}")

    ledger, ledger_path = load_screenshot_ledger(brain)

    reels, missing_specs = [], []
    for page_name in sorted(os.listdir(sites_dir)):
        page_dir = os.path.join(sites_dir, page_name)
        spec = os.path.join(page_dir, "07-Facebook", "Posts", "Reels",
                            f"Reels - {wdate}.md")
        if not os.path.exists(spec):
            if os.path.isdir(os.path.join(page_dir, "07-Facebook", "Posts", "Reels")):
                missing_specs.append(page_name)
            continue
        for reel in parse_spec_file(spec, page_dir):
            if only and reel["page_code"].upper() not in only:
                continue
            reel["assets"] = resolve_assets(reel, ledger, assets_dir)
            reels.append(reel)

    # Tier-1 monetized pages render first (CLAUDE.md §5 monetized-first).
    reels.sort(key=lambda r: (not r["tier1"], r["page_code"], r["reel_number"]))

    manifest = {
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "working_date": wdate,
        "brain": brain,
        "assets_dir": assets_dir,
        "ledger_path": ledger_path,
        "ledger_entries": len(ledger),
        "pages_without_spec": missing_specs,
        "counts": {
            "total": len(reels),
            "by_format": {f: sum(1 for r in reels if r["format"] == f)
                          for f in sorted({r["format"] for r in reels})},
            "tier1": sum(1 for r in reels if r["tier1"]),
            "source_ok": sum(1 for r in reels if r["assets"]["source_status"] == "ok"),
        },
        "reels": reels,
    }

    out = args.out or os.path.join(brain, "_Brain", "Data", "reel-render",
                                   f"manifest-{wdate}.json")
    os.makedirs(os.path.dirname(out), exist_ok=True)
    with open(out, "w", encoding="utf-8") as fh:
        json.dump(manifest, fh, indent=2, ensure_ascii=False)

    c = manifest["counts"]
    print(f"working date : {wdate}")
    print(f"reels parsed : {c['total']}  ({', '.join(f'{k}={v}' for k, v in c['by_format'].items()) or 'none'})")
    print(f"tier-1 reels : {c['tier1']}")
    print(f"ledger IDs   : {len(ledger)}")
    print(f"source ok    : {c['source_ok']} (optional background stills; no format needs one)")
    if missing_specs:
        print(f"no spec for  : {', '.join(missing_specs)}")
    print(f"manifest     : {out}")

    # Zero reels is a STOP condition, not a quiet success (task file 32, Hard
    # rules: "If ZERO reels parse, STOP — fb-reels-daily has not run, and
    # rendering nothing is not success"). On 2026-08-30 this printed
    # "reels parsed : 0", exited 0, and the night was lost without anyone
    # noticing until 2026-09-02. A non-zero exit makes the failure loud so the
    # caller cannot walk past it. Reversible: delete these three lines.
    if c["total"] == 0:
        print("\nSTOP: zero reels parsed. fb-reels-daily has not written tonight's "
              "specs yet — rendering nothing is not success. Re-run this task "
              "after the specs exist.", file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main() or 0)
