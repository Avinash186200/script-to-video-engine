"""Render every example in --check mode (no TTS, no network) and sanity-check the stills."""
import importlib
import subprocess
import sys
from pathlib import Path

from PIL import Image

ROOT = Path(__file__).resolve().parents[1]


def run(*args):
    subprocess.run([sys.executable, "-m", *args], cwd=ROOT, check=True)


def test_lesson_check_renders_one_still_per_step():
    run("videoengine.slides", "examples/lesson_example.py", "--check")
    stills = sorted((ROOT / "output" / "_check" / "lesson_example").glob("*.png"))
    assert len(stills) == 6
    assert Image.open(stills[0]).size == (1920, 1080)


def test_short_check_renders_vertical_stills():
    run("videoengine.shorts", "examples/short_example.py", "--check")
    stills = sorted((ROOT / "output" / "shorts" / "_check" / "short_example").glob("*.png"))
    assert len(stills) == 4
    assert Image.open(stills[0]).size == (1080, 1920)


def test_banned_words_block_a_script(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    (tmp_path / "banned_words.txt").write_text("retrieve\n", encoding="utf-8")
    slides = importlib.import_module("videoengine.slides")
    meta, steps = slides.load(ROOT / "examples" / "lesson_example.py")
    try:
        slides.validate(meta, steps)
    except SystemExit as e:
        assert "banned" in str(e)
    else:
        raise AssertionError("banned word was not caught")



def test_banned_words_block_a_short(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    (tmp_path / "banned_words.txt").write_text("function calling\n", encoding="utf-8")
    shorts = importlib.import_module("videoengine.shorts")
    meta, beats = shorts.load(ROOT / "examples" / "short_example.py")
    try:
        shorts.validate(meta, beats)
    except SystemExit as e:
        assert "banned" in str(e)
    else:
        raise AssertionError("banned word was not caught")

def test_covers_and_thumbnails():
    run("videoengine.covers")
    run("videoengine.thumbnails")
    assert Image.open(ROOT / "output" / "covers" / "example_cover.jpg").size == (1080, 1920)
    assert Image.open(ROOT / "output" / "thumbnails" / "C_d1.jpg").size == (1280, 720)
