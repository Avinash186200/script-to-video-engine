"""Channel configuration for the growth and upload tools.

Nothing channel-specific lives in code. Values come from a JSON file (``VE_CONFIG`` or ``./channel.json``),
and a few can be overridden by environment variables. See ``channel.example.json``.
"""
from __future__ import annotations

import json
import os
from pathlib import Path

DEFAULTS: dict = {
    "series": "My Course",
    "repo_url": "https://github.com/your-name/your-course",
    "main_playlist_url": "",
    "shorts_playlist_url": "",
    "episodes": {},          # episode id -> {"video_id": "...", "label": "Day 1, Part 2", "code": "folder"}
    "shorts": {},            # short id -> {"episode": "<episode id>"} or {"video_id": "...", "label": "..."}
    "default_related": None,  # {"video_id": "...", "label": "..."} used when nothing else matches
    "pinned_comment": {
        "template": "Quick check before you go:\n{question}\nAnswer in the comments.\n\nCode: {code_url}\nLesson notes: {notes_url}\nNext episode: {next_url}",
    },
}

ENV = {"series": "VE_SERIES", "repo_url": "VE_REPO_URL", "main_playlist_url": "VE_MAIN_PLAYLIST_URL",
       "shorts_playlist_url": "VE_SHORTS_PLAYLIST_URL"}


def load_config(path: str | os.PathLike | None = None) -> dict:
    """Defaults, then the JSON file (if any), then environment overrides."""
    cfg = json.loads(json.dumps(DEFAULTS))
    p = Path(path or os.environ.get("VE_CONFIG", "") or (Path.cwd() / "channel.json"))
    if p.is_file():
        cfg.update(json.loads(p.read_text(encoding="utf-8")))
    for key, var in ENV.items():
        if os.environ.get(var):
            cfg[key] = os.environ[var]
    return cfg


def video_url(video_id: str | None) -> str:
    return f"https://youtu.be/{video_id}" if video_id else ""
