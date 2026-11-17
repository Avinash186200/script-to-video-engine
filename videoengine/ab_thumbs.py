"""Thumbnail A/B: render challenger variants next to the live thumbnail on one comparison sheet.

    python -m videoengine.ab_thumbs examples/ab_thumbs.example.json --out output/ab_thumbs

Jobs file (JSON list)::

    [{"id": "day01_p2", "tag": "DAY 1", "live": "output/thumbs/day01_p2.jpg",
      "variants": {"B": {"style": "A", "hook": "Why Your AI|Bill Is HIGH", "highlight": "HIGH", "visual": "bars"},
                   "C": {"style": "B", "hook": "Tokens|= MONEY", "highlight": "MONEY", "visual": "bars"}}}]

``live`` is optional. Each row of the sheet is one video: live (if given), then each variant. Run the test with
YouTube's built-in thumbnail test or by swapping manually, then score it with ``videoengine.growth ab``.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

from videoengine.hooks import check_hook


def validate_jobs(jobs: list[dict]) -> list[str]:
    out = []
    for j in jobs:
        if not j.get("variants"):
            out.append(f"{j.get('id', '?')}: no variants")
        for name, v in j.get("variants", {}).items():
            if v.get("style", "C") not in ("A", "B", "C"):
                out.append(f"{j['id']}/{name}: unknown style {v.get('style')}")
            out += [f"{j['id']}/{name}: {p}" for p in check_hook(v["hook"], v["highlight"], v["visual"])]
    return out


def sheet_grid(jobs: list[dict]) -> tuple[int, int]:
    """(rows, columns) of the comparison sheet."""
    cols = max((len(j["variants"]) + (1 if j.get("live") else 0) for j in jobs), default=0)
    return len(jobs), cols


def main(argv=None):
    ap = argparse.ArgumentParser(description="Render thumbnail A/B variants and a comparison sheet")
    ap.add_argument("jobs")
    ap.add_argument("--out", default="output/ab_thumbs")
    a = ap.parse_args(argv)
    from PIL import Image
    from videoengine.thumbnails import STYLES
    jobs = json.loads(Path(a.jobs).read_text(encoding="utf-8"))
    problems = validate_jobs(jobs)
    if problems:
        raise SystemExit("job problems:\n  " + "\n  ".join(problems))
    out = Path(a.out)
    out.mkdir(parents=True, exist_ok=True)
    rows, cols = sheet_grid(jobs)
    sheet = Image.new("RGB", (cols * 420 + 20, rows * 245 + 20), (15, 15, 15))
    for r, j in enumerate(jobs):
        tiles = [Path(j["live"])] if j.get("live") and Path(j["live"]).exists() else []
        for name, v in j["variants"].items():
            f = out / f"{j['id']}_{name}.jpg"
            STYLES[v.get("style", "C")](v["hook"], v["highlight"], j.get("tag", ""), v["visual"], f)
            tiles.append(f)
        for i, p in enumerate(tiles):
            sheet.paste(Image.open(p).resize((400, 225)), (10 + i * 420, 10 + r * 245))
    sheet.save(out / "_SHEET.jpg", quality=88)
    print("ok", out)


if __name__ == "__main__":
    main()
