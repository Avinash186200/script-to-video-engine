"""Lesson pages: one Markdown page per lesson script, plus an index, for the course repository.

    python -m videoengine.lessons --lessons lessons/ --renders output/ --out site/lessons --config channel.json

Each page has the video link, clickable chapters (read from output/<id>/youtube.txt when it exists), the slide
content and the full narration, and previous/next links. Video ids, playlist links and the repo URL come from the
channel config, never from code. A lesson without a video id gets a page without the watch link.
"""
from __future__ import annotations

import argparse
import importlib.util
import re
from pathlib import Path

from videoengine.config import load_config, video_url
from videoengine.settings import banned_words


def load(path):
    spec = importlib.util.spec_from_file_location(path.stem, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod.META, mod.STEPS


def parse_chapters(youtube_txt: str):
    """[(timestamp, seconds, name)] from the 'Chapters:' block the slide engine writes."""
    m = re.search(r"Chapters:\n(.*?)(\n\n|$)", youtube_txt, re.S)
    out = []
    for line in (m.group(1).splitlines() if m else []):
        ts, _, name = line.partition(" ")
        parts = [int(p) for p in ts.split(":")]
        secs = parts[-1] + 60 * parts[-2] + (3600 * parts[-3] if len(parts) == 3 else 0)
        out.append((ts, secs, name))
    return out


def md_escape_cell(s):
    return str(s).replace("|", "\\|").replace("\n", " ")


def render_slide(s):
    """Markdown for one slide state (the final state of a build-up)."""
    tpl = s["tpl"]
    L = []
    head = s.get("title")
    if tpl in ("title", "roadmap", "end"):
        return ""
    if tpl == "section":
        return f"## {s['title']}\n"
    if head:
        L.append(f"**{head}**\n")
    if tpl in ("bullets", "recap"):
        L += [f"- {i}" for i in s["items"]]
    elif tpl == "steps":
        L += [f"{n}. {i}" for n, i in enumerate(s["items"], 1)]
    elif tpl == "twocol":
        for side in ("left", "right"):
            if side in s:
                L.append(f"- **{s[side]['head']}**")
                L += [f"  - {i}" for i in s[side].get("items", [])]
    elif tpl == "table":
        L.append("| " + " | ".join(md_escape_cell(h) for h in s["headers"]) + " |")
        L.append("|" + "---|" * len(s["headers"]))
        L += ["| " + " | ".join(md_escape_cell(c) for c in row) + " |" for row in s["rows"]]
    elif tpl == "code":
        if s.get("file"):
            L.append(f"`{s['file']}`")
        L.append("```python\n" + s["code"].strip("\n") + "\n```")
    elif tpl == "flow":
        L.append(" → ".join(f"**{b[0]}**" + (f" ({b[1]})" if len(b) > 1 and b[1] else "") for b in s["boxes"]))
    elif tpl == "bars":
        if s.get("prompt"):
            L.append(f"> {s['prompt']}")
        fmt = s.get("fmt", "{:.2f}")
        L += [f"- {lab}: {fmt.format(v)}" for lab, v in s["items"]]
    elif tpl == "chat":
        for role, txt in s["messages"]:
            L.append(f"> **{role.capitalize()}:** {txt}")
            L.append(">")
        if L and L[-1] == ">":
            L.pop()
    elif tpl == "tokens":
        if s.get("text"):
            L.append(f"> {s['text']}")
        L.append(" ".join(f"`{t}`" for t in s["tokens"]))
    elif tpl == "callout":
        L.append(f"> **{s['text']}**")
        if s.get("sub"):
            L.append(f"> {s['sub']}")
    elif tpl == "quiz":
        L = ["**Quick check:** " + s["q"]]
        L += [f"- {o}" for o in s.get("options", [])]
        if s.get("answer"):
            L.append(f"\n<details><summary>Answer</summary>\n\n{s['answer']}\n\n</details>")
    for k in ("note", "note2"):
        if s.get(k):
            L.append(f"\n*{s[k]}*")
    return "\n".join(L) + "\n"


def slide_key(s):
    return (s["tpl"], s.get("title"), s.get("kicker"))


def lesson_label(meta):
    day, part = meta.get("day"), meta.get("part")
    if isinstance(day, int):
        return f"Day {day}, Part {part}"
    return f"{day}, Part {part}" if day else meta["id"]


def build_lesson(meta, steps, vid, prev_next, chapters, cfg):
    eid = meta["id"]
    title = meta["yt_title"].split(" | ")[0]
    links = []
    if vid:
        links.append(f"**Watch:** [youtu.be/{vid}]({video_url(vid)})")
    if meta.get("code"):
        links.append(f"**Code:** [`{meta['code']}/`](../{meta['code']}/)")
    if cfg.get("main_playlist_url"):
        links.append(f"**Full course playlist:** [in order]({cfg['main_playlist_url']})")
    out = [f"# {lesson_label(meta)}: {title}\n"]
    if links:
        out.append(" · ".join(links) + "\n")
    desc = meta["description"].strip()
    learn = re.search(r"You will learn:\n(.*?)(\n\n|$)", desc, re.S)
    out.append(desc.split("\n\n")[0] + "\n")
    if learn:
        out.append("## What you will learn\n\n" + learn.group(1).strip() + "\n")
    if chapters and vid:
        out.append("## Chapters\n")
        out += [f"- [{ts}](https://youtu.be/{vid}?t={secs}) {name}" for ts, secs, name in chapters]
        out.append("")
    out.append("## Lesson notes\n\nSlide content and the full narration, in order.\n")
    for i, st in enumerate(steps):
        s = st["t"]
        nxt = steps[i + 1]["t"] if i + 1 < len(steps) else None
        last_of_build = nxt is None or slide_key(nxt) != slide_key(s)
        if s["tpl"] == "section":
            out.append(render_slide(s))
        out.append(st["say"] + "\n")
        if last_of_build and s["tpl"] != "section":
            block = render_slide(s)
            if block.strip():
                out.append(block)
    prev_l, next_l = prev_next
    nav = []
    if prev_l:
        nav.append(f"← [{prev_l[1]}]({prev_l[0]}.md)")
    nav.append("[All lessons](README.md)")
    if next_l:
        nav.append(f"[{next_l[1]}]({next_l[0]}.md) →")
    out.append("---\n\n" + " · ".join(nav) + "\n")
    return title, "\n".join(out)


def check_banned(text, banned):
    low = text.lower()
    return [w for w in banned if w in low]


def build_all(lesson_dir, renders, out_dir, cfg):
    paths = sorted(Path(lesson_dir).glob("*.py"))
    loaded = [load(p) for p in paths]
    metas = [(m["id"], lesson_label(m)) for m, _ in loaded]
    eps = cfg.get("episodes", {})
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    banned = banned_words()
    rows = []
    for n, (meta, steps) in enumerate(loaded):
        eid = meta["id"]
        vid = eps.get(eid, {}).get("video_id")
        yt = Path(renders) / eid / "youtube.txt"
        chapters = parse_chapters(yt.read_text(encoding="utf-8")) if yt.exists() else []
        prev_l = metas[n - 1] if n > 0 else None
        next_l = metas[n + 1] if n + 1 < len(metas) else None
        title, text = build_lesson(meta, steps, vid, (prev_l, next_l), chapters, cfg)
        bad = check_banned(text, banned)
        if bad:
            raise SystemExit(f"{eid}: banned words {bad}")
        (out_dir / f"{eid}.md").write_text(text, encoding="utf-8")
        rows.append((lesson_label(meta), title, vid, eid))
    idx = ["# Lessons\n", "Every lesson in order, with the video, chapters, slide content and narration.\n"]
    if cfg.get("main_playlist_url"):
        idx.append(f"Playlist: [{cfg.get('series', 'the course')}, in order]({cfg['main_playlist_url']}).\n")
    idx += ["| Lesson | Title | Video |", "|---|---|---|"]
    idx += [f"| {lab} | [{t}]({e}.md) | " + (f"[watch]({video_url(v)})" if v else "-") + " |" for lab, t, v, e in rows]
    shorts = [(sid, s) for sid, s in cfg.get("shorts", {}).items() if s.get("title") and s.get("short_id")]
    if shorts:
        idx += ["", "## Shorts\n", "| Short | Full lesson |", "|---|---|"]
        idx += [f"| [{s['title']}](https://youtube.com/shorts/{s['short_id']}) | "
                f"[{s.get('episode', '-')}]({s.get('episode', '')}.md) |" for _, s in shorts]
    (out_dir / "README.md").write_text("\n".join(idx) + "\n", encoding="utf-8")
    return rows


def main(argv=None):
    ap = argparse.ArgumentParser(description="Build Markdown lesson pages from lesson scripts")
    ap.add_argument("--lessons", default="lessons")
    ap.add_argument("--renders", default="output")
    ap.add_argument("--out", default="site/lessons")
    ap.add_argument("--config")
    a = ap.parse_args(argv)
    rows = build_all(a.lessons, a.renders, a.out, load_config(a.config))
    print("wrote", len(rows), "lessons + index to", a.out)


if __name__ == "__main__":
    main()
