"""Growth tooling: title experiments, A/B scoring and pinned comments. Pure Python, no API calls.

    python -m videoengine.growth titles examples/title_experiments.example.csv --out output/growth
    python -m videoengine.growth ab --a 4000 120 --b 4100 165
    python -m videoengine.growth pinned --config channel.json --out output/growth

``titles`` checks each proposed title and writes a change log that keeps the old title for rollback and a
review date. ``ab`` compares two click-through rates with a two-proportion z-test. ``pinned`` writes one pinned
comment per episode (quick-check question, code, lesson notes, next episode) from the channel config.
Uploading or editing on YouTube stays a human step.
"""
from __future__ import annotations

import argparse
import csv
import datetime as dt
import json
import math
from pathlib import Path

from videoengine.config import load_config, video_url

MAX_TITLE = 100
MOBILE_CUTOFF = 60  # characters a phone shows before truncating, roughly
REVIEW_DAYS = 14


# ------------------------------------------------------------------ titles
def check_title(title: str, banned: list[str] | None = None) -> list[str]:
    problems = []
    if not title.strip():
        problems.append("empty")
    if len(title) > MAX_TITLE:
        problems.append(f"{len(title)} characters (max {MAX_TITLE})")
    if "<" in title or ">" in title:
        problems.append("contains < or >")
    if title.isupper():
        problems.append("all caps")
    low = title.lower()
    problems += [f"banned word: {w}" for w in (banned or []) if w in low]
    return problems


def front_loaded(title: str, keyword: str) -> bool:
    """True if the keyword sits in the part a phone shows before truncating."""
    return keyword.lower() in title[:MOBILE_CUTOFF].lower()


def review_date(start: str, days: int = REVIEW_DAYS) -> str:
    return (dt.date.fromisoformat(start) + dt.timedelta(days=days)).isoformat()


def _cell(s: str) -> str:
    return s.replace("|", "\\|")


def title_log(rows: list[dict], banned: list[str] | None = None) -> tuple[str, list[str]]:
    """Markdown change log (old title kept for rollback) and a list of problems."""
    problems = []
    out = ["| Video | Old title | New title | Keyword up front | Review on |", "|---|---|---|---|---|"]
    for r in rows:
        for p in check_title(r["new_title"], banned):
            problems.append(f"{r['video_id']}: {p}")
        kw = r.get("keyword", "")
        up = ("yes" if front_loaded(r["new_title"], kw) else "no") if kw else "-"
        out.append(f"| {r['video_id']} | {_cell(r['old_title'])} | {_cell(r['new_title'])} | {up} | "
                   f"{review_date(r['start_date'])} |")
    return "\n".join(out) + "\n", problems


# ------------------------------------------------------------------ A/B
def ctr_test(imp_a: int, clicks_a: int, imp_b: int, clicks_b: int, min_impressions: int = 1000,
             alpha: float = 0.05) -> dict:
    """Two-proportion z-test on click-through rate. Verdict is 'A', 'B', 'no difference' or 'not enough data'."""
    if min(imp_a, imp_b) <= 0 or clicks_a > imp_a or clicks_b > imp_b or min(clicks_a, clicks_b) < 0:
        raise ValueError("impressions must be positive and clicks between 0 and impressions")
    pa, pb = clicks_a / imp_a, clicks_b / imp_b
    pooled = (clicks_a + clicks_b) / (imp_a + imp_b)
    se = math.sqrt(pooled * (1 - pooled) * (1 / imp_a + 1 / imp_b))
    z = (pb - pa) / se if se > 0 else 0.0
    p = math.erfc(abs(z) / math.sqrt(2))
    if min(imp_a, imp_b) < min_impressions:
        verdict = "not enough data"
    elif p >= alpha:
        verdict = "no difference"
    else:
        verdict = "B" if pb > pa else "A"
    return {"ctr_a": pa, "ctr_b": pb, "lift": (pb - pa) / pa if pa else math.inf, "z": z, "p": p, "verdict": verdict}


# ------------------------------------------------------------------ pinned comments
def pinned_comment(ep_id: str, order: list[str], cfg: dict) -> str:
    """Fill the pinned-comment template for one episode. Lines whose fields are missing are dropped."""
    eps = cfg.get("episodes", {})
    ep = eps[ep_id]
    repo = cfg.get("repo_url", "").rstrip("/")
    i = order.index(ep_id)
    nxt = eps[order[i + 1]].get("video_id") if i + 1 < len(order) else None
    fields = {
        "question": ep.get("question", ""),
        "code_url": f"{repo}/tree/main/{ep['code']}" if repo and ep.get("code") else "",
        "notes_url": f"{repo}/blob/main/lessons/{ep_id}.md" if repo else "",
        "next_url": video_url(nxt) if nxt else (cfg.get("main_playlist_url") or ""),
    }
    lines = []
    for line in cfg["pinned_comment"]["template"].split("\n"):
        keys = [k for k in fields if "{" + k + "}" in line]
        if keys and not all(fields[k] for k in keys):
            continue
        lines.append(line.format(**fields))
    text = "\n".join(lines).strip()
    while "\n\n\n" in text:
        text = text.replace("\n\n\n", "\n\n")
    return text


def all_pinned(cfg: dict) -> list[dict]:
    order = list(cfg.get("episodes", {}))
    return [{"ep": e, "video_id": cfg["episodes"][e].get("video_id"), "text": pinned_comment(e, order, cfg)}
            for e in order]


# ------------------------------------------------------------------ CLI
def main(argv=None):
    ap = argparse.ArgumentParser(description="Title experiments, A/B scoring and pinned comments")
    sub = ap.add_subparsers(dest="cmd", required=True)
    t = sub.add_parser("titles")
    t.add_argument("csv")
    t.add_argument("--out", default="output/growth")
    b = sub.add_parser("ab")
    b.add_argument("--a", nargs=2, type=int, required=True, metavar=("IMPRESSIONS", "CLICKS"))
    b.add_argument("--b", nargs=2, type=int, required=True, metavar=("IMPRESSIONS", "CLICKS"))
    b.add_argument("--min-impressions", type=int, default=1000)
    p = sub.add_parser("pinned")
    p.add_argument("--config")
    p.add_argument("--out", default="output/growth")
    a = ap.parse_args(argv)

    if a.cmd == "titles":
        from videoengine.settings import banned_words
        with open(a.csv, encoding="utf-8", newline="") as f:
            rows = list(csv.DictReader(f))
        md, problems = title_log(rows, banned_words())
        Path(a.out).mkdir(parents=True, exist_ok=True)
        (Path(a.out) / "title_changes.md").write_text("# Title changes (old titles kept for rollback)\n\n" + md,
                                                       encoding="utf-8")
        print(md)
        if problems:
            print("problems:\n  " + "\n  ".join(problems))
            return 1
    elif a.cmd == "ab":
        r = ctr_test(*a.a, *a.b, min_impressions=a.min_impressions)
        print(f"CTR A {r['ctr_a']:.2%}  B {r['ctr_b']:.2%}  lift {r['lift']:+.1%}  z {r['z']:.2f}  p {r['p']:.4f}  "
              f"-> {r['verdict']}")
    elif a.cmd == "pinned":
        items = all_pinned(load_config(a.config))
        out = Path(a.out)
        out.mkdir(parents=True, exist_ok=True)
        (out / "pinned_comments.json").write_text(json.dumps(items, indent=1, ensure_ascii=False), encoding="utf-8")
        (out / "pinned_comments_paste.txt").write_text(
            "\n\n".join(f"===== {i['ep']} ({i['video_id']}) =====\n{i['text']}" for i in items) + "\n",
            encoding="utf-8")
        print("wrote", len(items), "pinned comments to", out)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
