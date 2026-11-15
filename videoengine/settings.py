"""Settings shared by every engine. Override with environment variables."""
from __future__ import annotations

import os
from pathlib import Path

from PIL import ImageFont

SERIES = os.environ.get("VE_SERIES", "My Course")
REPO_URL = os.environ.get("VE_REPO_URL", "https://github.com/your-name/your-course")
VOICE = os.environ.get("VE_VOICE", "en-IN-PrabhatNeural")   # any edge-tts voice, e.g. en-US-GuyNeural
FONT_DIR = os.environ.get("VE_FONT_DIR", "")

# (regular, bold, black, mono, mono-bold) per platform; the first set whose bold file exists wins.
_CANDIDATES = [
    ("C:/Windows/Fonts/", "segoeui.ttf", "segoeuib.ttf", "seguibl.ttf", "consola.ttf", "consolab.ttf"),
    ("/usr/share/fonts/truetype/dejavu/", "DejaVuSans.ttf", "DejaVuSans-Bold.ttf", "DejaVuSans-Bold.ttf",
     "DejaVuSansMono.ttf", "DejaVuSansMono-Bold.ttf"),
    ("/System/Library/Fonts/Supplemental/", "Arial.ttf", "Arial Bold.ttf", "Arial Black.ttf",
     "Courier New.ttf", "Courier New Bold.ttf"),
]


def _font_set():
    if FONT_DIR:
        d = FONT_DIR.rstrip("/\\") + "/"
        names = [os.environ.get(k, v) for k, v in (("VE_FONT", "regular.ttf"), ("VE_FONT_BOLD", "bold.ttf"),
                                                   ("VE_FONT_BLACK", "black.ttf"), ("VE_FONT_MONO", "mono.ttf"),
                                                   ("VE_FONT_MONO_BOLD", "mono-bold.ttf"))]
        return [d + n for n in names]
    for d, *names in _CANDIDATES:
        if Path(d + names[1]).exists():
            return [d + n for n in names]
    return [None] * 5


_FILES = _font_set()
_cache: dict = {}


def font_file(kind: str) -> str | None:
    """kind: regular | bold | black | mono | mono_bold"""
    return _FILES[["regular", "bold", "black", "mono", "mono_bold"].index(kind)]


def load_font(kind: str, size: int):
    key = (kind, size)
    if key not in _cache:
        path = font_file(kind)
        _cache[key] = ImageFont.truetype(path, size) if path else ImageFont.load_default(size)
    return _cache[key]


def banned_words() -> list[str]:
    """Words that must never appear in a script (company or employer names, say). One per line in
    banned_words.txt next to this package or in the working directory. The file is gitignored."""
    for p in (Path.cwd() / "banned_words.txt", Path(__file__).resolve().parents[1] / "banned_words.txt"):
        if p.exists():
            return [w.strip().lower() for w in p.read_text(encoding="utf-8").splitlines() if w.strip() and not w.startswith("#")]
    return []
