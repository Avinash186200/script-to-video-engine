"""Write a batch of Short scripts from one JSON spec, then (optionally) render their covers.

    python -m videoengine.batch_shorts examples/shorts_batch.example.json --out shorts/
    python -m videoengine.batch_shorts examples/shorts_batch.example.json --covers output/covers

Spec format (see ``examples/shorts_batch.example.json``)::

    {"defaults": {"kicker": "...", "source_episode": "...", "hashtags": "#AI", "footer": "...",
                  "related_video": {"video_id": "...", "label": "..."}},
     "shorts": [{"id": "s60_x", "title": "... #Shorts", "body": "...", "tags": [...],
                 "cover": ["Hook|LINES", "LINES", "42"],
                 "beats": [["headline", "narration", {"type": "bignum", ...}], ...]}]}

Run it once, then edit the generated scripts by hand. Existing scripts are not overwritten without --force.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

MAX_TITLE = 100


def merged(short: dict, defaults: dict) -> dict:
    out = dict(defaults)
    out.update(short)
    return out


def validate_spec(spec: dict) -> list[str]:
    problems, seen = [], set()
    for s in spec.get("shorts", []):
        s = merged(s, spec.get("defaults", {}))
        sid = s.get("id", "?")
        if sid in seen:
            problems.append(f"{sid}: duplicate id")
        seen.add(sid)
        for k in ("id", "title", "body", "beats"):
            if not s.get(k):
                problems.append(f"{sid}: missing {k}")
        if len(s.get("title", "")) > MAX_TITLE:
            problems.append(f"{sid}: title longer than {MAX_TITLE}")
        for b in s.get("beats", []):
            if len(b) != 3 or not isinstance(b[2], dict) or "type" not in b[2]:
                problems.append(f"{sid}: each beat is [headline, say, visual-with-type]")
                break
        cov = s.get("cover")
        if cov and cov[1] not in cov[0]:
            problems.append(f"{sid}: cover highlight '{cov[1]}' is not in the hook")
    return problems


def description(s: dict) -> str:
    parts = [s["body"].strip()]
    if s.get("footer"):
        parts.append(s["footer"].strip())
    if s.get("hashtags"):
        parts.append(s["hashtags"].strip())
    return "\n\n".join(parts)


def render_script(s: dict) -> str:
    """Python source for one Short script (META + BEATS), the format videoengine.shorts reads."""
    meta = {"id": s["id"], "kicker": s.get("kicker", ""), "outro": s.get("outro", False), "yt_title": s["title"],
            "description": description(s), "source_episode": s.get("source_episode", ""), "tags": s.get("tags", [])}
    if s.get("related_video"):
        meta["related_video"] = s["related_video"]
    out = ["META = {"]
    out += [f"    {json.dumps(k)}: {_py(v)}," for k, v in meta.items()]
    out += ["}", "", "BEATS = ["]
    for h, say, vis in s["beats"]:
        out.append(f'    {{"headline": {json.dumps(h)},\n     "say": {json.dumps(say)},\n     "visual": {_py(vis)}}},')
    out.append("]")
    return "\n".join(out) + "\n"


def _py(v):
    """JSON literal as Python (true/false/null differ)."""
    if isinstance(v, bool):
        return "True" if v else "False"
    if v is None:
        return "None"
    if isinstance(v, dict):
        return "{" + ", ".join(f"{json.dumps(k)}: {_py(x)}" for k, x in v.items()) + "}"
    if isinstance(v, list):
        return "[" + ", ".join(_py(x) for x in v) + "]"
    return json.dumps(v)


def word_count(s: dict) -> int:
    return sum(len(b[1].split()) for b in s["beats"])


def main(argv=None):
    ap = argparse.ArgumentParser(description="Write Short scripts from a JSON spec")
    ap.add_argument("spec")
    ap.add_argument("--out", default="shorts")
    ap.add_argument("--force", action="store_true")
    ap.add_argument("--covers", help="also render a vertical cover per Short into this folder")
    a = ap.parse_args(argv)
    spec = json.loads(Path(a.spec).read_text(encoding="utf-8"))
    problems = validate_spec(spec)
    if problems:
        raise SystemExit("spec problems:\n  " + "\n  ".join(problems))
    out = Path(a.out)
    out.mkdir(parents=True, exist_ok=True)
    for raw in spec["shorts"]:
        s = merged(raw, spec.get("defaults", {}))
        path = out / f"{s['id']}.py"
        if path.exists() and not a.force:
            print("exists, skipped:", path)
        else:
            path.write_text(render_script(s), encoding="utf-8")
            print(s["id"], word_count(s), "words,", len(s["title"]), "char title")
        if a.covers and s.get("cover"):
            from videoengine.covers import cover
            Path(a.covers).mkdir(parents=True, exist_ok=True)
            hook, hi, num = s["cover"]
            cover(hook, hi, num, Path(a.covers) / f"{s['id']}.jpg")


if __name__ == "__main__":
    main()
