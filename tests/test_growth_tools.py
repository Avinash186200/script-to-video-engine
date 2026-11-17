"""Pure-function tests for the growth, upload and batch tools. No rendering, no network."""
import ast
import json
from pathlib import Path

import pytest

from videoengine import ab_thumbs, batch_shorts, growth, hooks, lessons, upload_prep
from videoengine.config import load_config

ROOT = Path(__file__).resolve().parents[1]

CFG = {
    "repo_url": "https://github.com/your-name/your-course",
    "main_playlist_url": "https://www.youtube.com/playlist?list=PL_EXAMPLE",
    "episodes": {
        "day01_p1": {"video_id": "VID1", "label": "Day 1, Part 1", "code": "day01", "question": "Why?"},
        "day01_p2": {"video_id": "VID2", "label": "Day 1, Part 2", "code": "day01"},
    },
    "shorts": {"s01_tokens": {"episode": "day01_p2"}, "s02_old_name": {"video_id": "VIDX", "label": "Bonus"}},
    "default_related": {"video_id": "VIDD", "label": "the full course"},
    "pinned_comment": {"template": "Q:\n{question}\n\nCode: {code_url}\nNext: {next_url}"},
}


# ------------------------------------------------------------------ config
def test_config_defaults_file_and_env(tmp_path, monkeypatch):
    monkeypatch.delenv("VE_CONFIG", raising=False)
    monkeypatch.chdir(tmp_path)
    assert load_config()["episodes"] == {}
    (tmp_path / "c.json").write_text(json.dumps({"series": "From file"}), encoding="utf-8")
    monkeypatch.setenv("VE_REPO_URL", "https://example.org/repo")
    cfg = load_config(tmp_path / "c.json")
    assert cfg["series"] == "From file" and cfg["repo_url"] == "https://example.org/repo"


def test_example_config_parses():
    cfg = load_config(ROOT / "channel.example.json")
    assert "day01_p1" in cfg["episodes"]


# ------------------------------------------------------------------ upload prep lookup
@pytest.mark.parametrize("meta,expected", [
    ({"id": "s01_tokens"}, "VID2"),                                   # config by exact id -> episode
    ({"id": "s02_renamed"}, "VIDX"),                                  # config by number prefix
    ({"id": "s09_x", "source_episode": "day01_p1"}, "VID1"),          # source_episode is an episode id
    ({"id": "s09_x", "related_video": {"video_id": "META"}}, "META"),  # explicit in the script wins
    ({"id": "s77_unknown"}, "VIDD"),                                  # fallback
])
def test_related_lookup_order(meta, expected):
    assert upload_prep.related_for(meta, CFG)["video_id"] == expected


def test_related_none_without_fallback():
    cfg = dict(CFG, default_related=None)
    assert upload_prep.related_for({"id": "s77_unknown"}, cfg) is None


def test_description_and_checks():
    meta = {"id": "s01", "yt_title": "T", "description": "Body text.\n\n#AI #LLM", "tags": ["a"]}
    d = upload_prep.build_description(meta, {"video_id": "VID2", "label": "Day 1, Part 2"}, CFG)
    assert d.startswith("Body text.")
    assert "Full episode (Day 1, Part 2): https://youtu.be/VID2" in d
    assert d.endswith("#AI #LLM #Shorts")
    assert upload_prep.check_metadata(meta, d) == []
    assert upload_prep.check_metadata(dict(meta, yt_title="x" * 101), "<b>")
    no_tags = upload_prep.build_description({"description": "Only body."}, None, {})
    assert no_tags == "Only body.\n\n#Shorts"


def test_example_shorts_have_valid_metadata():
    files = sorted((ROOT / "examples" / "shorts").glob("s*.py"))
    assert len(files) == 5
    for f in files:
        meta = upload_prep.load_meta(f)
        assert upload_prep.check_metadata(meta, upload_prep.build_description(meta, None, {})) == []


# ------------------------------------------------------------------ batch shorts
SPEC = json.loads((ROOT / "examples" / "shorts_batch.example.json").read_text(encoding="utf-8"))


def test_batch_spec_valid_and_renders_python():
    assert batch_shorts.validate_spec(SPEC) == []
    s = batch_shorts.merged(SPEC["shorts"][0], SPEC["defaults"])
    src = batch_shorts.render_script(s)
    tree = ast.parse(src)
    ns: dict = {}
    exec(compile(tree, "gen", "exec"), ns)
    assert ns["META"]["id"] == "s90_cache_threshold" and ns["META"]["outro"] is False
    assert ns["META"]["description"].endswith("#AIEngineering #AIInterview")
    assert len(ns["BEATS"]) == 3 and ns["BEATS"][0]["visual"]["type"] == "bignum"


def test_batch_spec_problems():
    bad = {"shorts": [{"id": "a", "title": "x" * 101, "body": "b", "beats": [["h", "s"]], "cover": ["Hi|THERE", "NOPE", "1"]},
                      {"id": "a", "title": "t", "body": "b", "beats": []}]}
    probs = " ".join(batch_shorts.validate_spec(bad))
    for frag in ("title longer", "each beat", "cover highlight", "duplicate id", "missing beats"):
        assert frag in probs


# ------------------------------------------------------------------ hooks + A/B jobs
def test_check_hook():
    assert hooks.check_hook("What Is|RAG?", "RAG?", "bars") == []
    assert len(hooks.check_hook("What Is|RAG?", "LLM", "stars")) == 2
    assert hooks.pages(25, 12) == [range(0, 12), range(12, 24), range(24, 25)]


def test_example_hooks_and_ab_jobs_valid():
    assert hooks.validate(hooks.read_hooks(ROOT / "examples" / "hooks.example.csv")) == []
    jobs = json.loads((ROOT / "examples" / "ab_thumbs.example.json").read_text(encoding="utf-8"))
    assert ab_thumbs.validate_jobs(jobs) == []
    assert ab_thumbs.sheet_grid(jobs) == (2, 2)
    assert ab_thumbs.sheet_grid([dict(jobs[0], live="x.jpg")]) == (1, 3)


# ------------------------------------------------------------------ growth
def test_title_checks():
    assert growth.check_title("RAG Explained Simply | Day 5") == []
    assert growth.check_title("SHOUTING TITLE") == ["all caps"]
    assert "banned word: acme" in growth.check_title("Acme secrets", ["acme"])
    assert growth.front_loaded("LLM Tokens Explained", "tokens")
    assert not growth.front_loaded("x" * 70 + " tokens", "tokens")
    assert growth.review_date("2026-11-12") == "2026-11-26"


def test_title_log_escapes_and_keeps_old_title():
    rows = [{"video_id": "V", "old_title": "Old | A", "new_title": "New title", "keyword": "new", "start_date": "2026-01-01"}]
    md, probs = growth.title_log(rows)
    assert "Old \\| A" in md and "| yes |" in md and "2026-01-15" in md and probs == []


def test_ctr_test_verdicts():
    r = growth.ctr_test(5000, 150, 5000, 230)
    assert r["verdict"] == "B" and r["p"] < 0.05 and r["lift"] == pytest.approx(230 / 150 - 1)
    assert growth.ctr_test(5000, 150, 5000, 152)["verdict"] == "no difference"
    assert growth.ctr_test(200, 5, 200, 20)["verdict"] == "not enough data"
    with pytest.raises(ValueError):
        growth.ctr_test(10, 11, 10, 1)


def test_pinned_comments_drop_missing_lines():
    items = growth.all_pinned(CFG)
    first, last = items[0]["text"], items[1]["text"]
    assert "Why?" in first and "Next: https://youtu.be/VID2" in first
    assert "/tree/main/day01" in first
    assert "{question}" not in last and "Next: https://www.youtube.com/playlist?list=PL_EXAMPLE" in last


# ------------------------------------------------------------------ lessons
def test_parse_chapters_and_render_slide():
    txt = "Title\n\nChapters:\n0:00 Intro\n1:05 Part two\n1:02:03 End\n\nTags: a"
    assert lessons.parse_chapters(txt) == [("0:00", 0, "Intro"), ("1:05", 65, "Part two"), ("1:02:03", 3723, "End")]
    assert lessons.render_slide({"tpl": "bullets", "title": "T", "items": ["a", "b"]}) == "**T**\n\n- a\n- b\n"
    assert lessons.render_slide({"tpl": "title", "title": "x"}) == ""
    assert "\\|" in lessons.md_escape_cell("a|b")


def test_build_all_from_example_lessons(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    cfg = dict(CFG, episodes={"lesson_example": {"video_id": "VIDL"}})
    src = tmp_path / "lessons"
    src.mkdir()
    for f in (ROOT / "examples" / "lesson_example.py", ROOT / "examples" / "lessons" / "arch_evolution.py"):
        (src / f.name).write_text(f.read_text(encoding="utf-8"), encoding="utf-8")
    rows = lessons.build_all(src, tmp_path / "renders", tmp_path / "site", cfg)
    assert [r[3] for r in rows] == ["arch_evolution", "lesson_example"]
    page = (tmp_path / "site" / "lesson_example.md").read_text(encoding="utf-8")
    assert "https://youtu.be/VIDL" in page and "[All lessons](README.md)" in page
    arch = (tmp_path / "site" / "arch_evolution.md").read_text(encoding="utf-8")
    assert arch.startswith("# Special, Part 1:") and "Watch:" not in arch
    assert "| - |" in (tmp_path / "site" / "README.md").read_text(encoding="utf-8")
