"""Batch thumbnails from a hooks file, plus contact sheets to review them at a glance.

    python -m videoengine.hooks examples/hooks.example.csv --out output/thumbs --style C

Hooks file (CSV with a header): ``id,hook,highlight,visual,tag``. ``hook`` uses ``|`` for line breaks,
``highlight`` is the word drawn in the accent colour (it must appear in the hook), ``visual`` is one of
bars | nodes | warn | chat, ``tag`` is the small label (for example ``DAY 3 · PART 1``).
"""
from __future__ import annotations

import argparse
import csv
from pathlib import Path

VISUALS = {"bars", "nodes", "warn", "chat"}
FIELDS = ("id", "hook", "highlight", "visual", "tag")


def check_hook(hook: str, highlight: str, visual: str) -> list[str]:
    problems = []
    if not hook.strip():
        problems.append("empty hook")
    if highlight not in hook:
        problems.append(f"highlight '{highlight}' not in hook")
    if visual not in VISUALS:
        problems.append(f"visual '{visual}' not one of {sorted(VISUALS)}")
    lines = hook.split("|")
    if len(lines) > 3:
        problems.append("more than 3 lines")
    if len(hook.replace("|", " ").split()) > 6:
        problems.append("more than 6 words (thumbnails read best at 2-5)")
    return problems


def read_hooks(path: str | Path) -> list[dict]:
    with open(path, encoding="utf-8", newline="") as f:
        rows = list(csv.DictReader(f))
    missing = [c for c in FIELDS if rows and c not in rows[0]]
    if missing:
        raise SystemExit(f"hooks file is missing columns: {missing}")
    return rows


def validate(rows: list[dict]) -> list[str]:
    out, seen = [], set()
    for r in rows:
        if r["id"] in seen:
            out.append(f"{r['id']}: duplicate id")
        seen.add(r["id"])
        out += [f"{r['id']}: {p}" for p in check_hook(r["hook"], r["highlight"], r["visual"])]
    return out


def pages(n: int, per_page: int = 12) -> list[range]:
    """Index ranges for contact sheets of per_page thumbnails each."""
    return [range(k, min(k + per_page, n)) for k in range(0, n, per_page)]


def contact_sheet(files: list[Path], out: Path, cols: int = 4, tile=(320, 180), pad=10):
    from PIL import Image
    rows = (len(files) + cols - 1) // cols
    sheet = Image.new("RGB", (cols * (tile[0] + pad) + pad, rows * (tile[1] + pad) + pad), (15, 15, 15))
    for i, f in enumerate(files):
        sheet.paste(Image.open(f).resize(tile), (pad + (i % cols) * (tile[0] + pad), pad + (i // cols) * (tile[1] + pad)))
    sheet.save(out, quality=88)


def main(argv=None):
    ap = argparse.ArgumentParser(description="Batch thumbnails from a hooks CSV")
    ap.add_argument("hooks")
    ap.add_argument("--out", default="output/thumbs")
    ap.add_argument("--style", default="C", choices=["A", "B", "C"])
    a = ap.parse_args(argv)
    from videoengine.thumbnails import STYLES
    rows = read_hooks(a.hooks)
    problems = validate(rows)
    if problems:
        raise SystemExit("hook problems:\n  " + "\n  ".join(problems))
    out = Path(a.out)
    out.mkdir(parents=True, exist_ok=True)
    files = []
    for r in rows:
        f = out / f"{r['id']}.jpg"
        STYLES[a.style](r["hook"], r["highlight"], r["tag"], r["visual"], f)
        files.append(f)
    for n, idx in enumerate(pages(len(files)), 1):
        contact_sheet([files[i] for i in idx], out / f"_SHEET_{n}.jpg")
    print("ok", len(files), "thumbnails in", out)


if __name__ == "__main__":
    main()
