"""Prepare rendered Shorts for upload: copy video + captions and write one metadata file per Short.

    python -m videoengine.upload_prep                       # ./shorts scripts, ./output/shorts renders -> ./upload/shorts
    python -m videoengine.upload_prep --scripts examples/shorts --out upload/shorts --config channel.json

Which long video a Short links to is data, not code. ``related_for`` tries, in order:

1. ``META["related_video"]`` in the Short script ({"video_id": ..., "label": ...});
2. the config ``shorts`` map, by exact Short id, then by its number prefix (``s07`` matches ``s07_mcp``);
   an entry is either {"video_id", "label"} or {"episode": "<episode id>"} looked up in ``episodes``;
3. ``META["source_episode"]`` when it is an episode id in the config;
4. ``default_related`` from the config;
5. nothing: the description is written without an episode link and the Short is reported.
"""
from __future__ import annotations

import argparse
import importlib.util
import re
import shutil
from pathlib import Path

from videoengine.config import load_config, video_url

MAX_TITLE = 100


def load_meta(path: Path) -> dict:
    spec = importlib.util.spec_from_file_location(path.stem, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod.META


def _resolve(entry: dict | None, cfg: dict) -> dict | None:
    if not entry:
        return None
    if entry.get("video_id"):
        return {"video_id": entry["video_id"], "label": entry.get("label", "")}
    ep = cfg.get("episodes", {}).get(entry.get("episode", ""))
    if ep and ep.get("video_id"):
        return {"video_id": ep["video_id"], "label": ep.get("label", entry.get("episode", ""))}
    return None


def related_for(meta: dict, cfg: dict) -> dict | None:
    """The long video a Short points to, or None. See the module docstring for the order."""
    sid = meta["id"]
    found = _resolve(meta.get("related_video"), cfg)
    if found:
        return found
    shorts = cfg.get("shorts", {})
    found = _resolve(shorts.get(sid), cfg)
    if found:
        return found
    m = re.match(r"(s\d+)", sid)
    if m:
        for key, entry in shorts.items():
            if re.match(r"(s\d+)", key) and re.match(r"(s\d+)", key).group(1) == m.group(1):
                found = _resolve(entry, cfg)
                if found:
                    return found
    found = _resolve({"episode": meta.get("source_episode", "")}, cfg)
    if found:
        return found
    return _resolve(cfg.get("default_related"), cfg)


def build_description(meta: dict, related: dict | None, cfg: dict) -> str:
    """Body, then the episode and playlist links, then the hashtags plus #Shorts."""
    body, sep, hashtags = meta["description"].strip().rpartition("\n\n")
    if not sep or not hashtags.lstrip().startswith("#"):
        body, hashtags = meta["description"].strip(), ""
    lines = [body, ""]
    if related:
        label = f" ({related['label']})" if related.get("label") else ""
        lines.append(f"Full episode{label}: {video_url(related['video_id'])}")
    if cfg.get("main_playlist_url"):
        lines.append(f"Complete course, in order: {cfg['main_playlist_url']}")
    if lines[-1]:
        lines.append("")
    lines.append(f"{hashtags} #Shorts".strip())
    return "\n".join(lines)


def check_metadata(meta: dict, desc: str) -> list[str]:
    """YouTube rejects angle brackets in descriptions; titles are capped at 100 characters."""
    problems = []
    if "<" in desc or ">" in desc:
        problems.append("description contains < or >")
    if len(meta["yt_title"]) > MAX_TITLE:
        problems.append(f"title is {len(meta['yt_title'])} characters (max {MAX_TITLE})")
    return problems


def metadata_text(meta: dict, desc: str, related: dict | None) -> str:
    text = f"TITLE:\n{meta['yt_title']}\n\nDESCRIPTION:\n{desc}\n\nTAGS:\n{', '.join(meta.get('tags', []))}\n"
    if related:
        text += f"\nRELATED_VIDEO: {related['video_id']}\n"
    return text


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--scripts", default="shorts")
    ap.add_argument("--renders", default="output/shorts")
    ap.add_argument("--out", default="upload/shorts")
    ap.add_argument("--config")
    a = ap.parse_args(argv)
    cfg = load_config(a.config)
    out = Path(a.out)
    out.mkdir(parents=True, exist_ok=True)
    failed = False
    for script in sorted(Path(a.scripts).glob("s*.py")):
        meta = load_meta(script)
        sid = meta["id"]
        src = Path(a.renders) / sid
        if not (src / "video.mp4").exists():
            print("NOT RENDERED:", sid)
            continue
        related = related_for(meta, cfg)
        desc = build_description(meta, related, cfg)
        problems = check_metadata(meta, desc)
        if problems:
            print("SKIPPED:", sid, "; ".join(problems))
            failed = True
            continue
        shutil.copy2(src / "video.mp4", out / f"{sid}.mp4")
        if (src / "captions.srt").exists():
            shutil.copy2(src / "captions.srt", out / f"{sid}.srt")
        (out / f"{sid}.txt").write_text(metadata_text(meta, desc, related), encoding="utf-8")
        print("ready:", sid, "" if related else "(no related video found)")
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
