"""Slide-lesson engine: a Python script of narrated steps -> a 1080p video with captions and chapters.

A lesson is a Python file that defines META (dict) and STEPS (list of dicts).
Each step = one narration line ("say") + one slide state ("t" = template + its fields).
Build-ups are written as consecutive steps whose slide shows one more item each time.

    python -m videoengine.slides examples/lesson_example.py            # build one lesson
    python -m videoengine.slides examples/lesson_example.py --check    # validate + one still per step, no audio
    python -m videoengine.slides --all --dir lessons/                  # build every lesson in a folder

Outputs go to output/<lesson_id>/ : video.mp4, captions.srt, youtube.txt (title, description with
chapters, tags).
"""
from __future__ import annotations

import argparse
import asyncio
import importlib.util
import json
import shutil
import subprocess
import sys
from pathlib import Path

import edge_tts
from PIL import Image, ImageDraw, ImageFont

ROOT = Path.cwd()
EPISODES = ROOT / "lessons"
OUTPUT = ROOT / "output"
W, H, FPS = 1920, 1080, 30
from videoengine.settings import SERIES, REPO_URL, VOICE, load_font, banned_words

BG = (16, 22, 38)
PANEL = (27, 36, 60)
PANEL2 = (40, 52, 84)
FG = (236, 240, 248)
DIM = (150, 160, 185)
ACCENT = (86, 182, 255)
GOLD = (255, 196, 87)
GREEN = (98, 211, 140)
RED = (255, 120, 120)
COLORS = {"accent": ACCENT, "gold": GOLD, "green": GREEN, "red": RED, "panel": PANEL}


def font(size, bold=False, mono=False):
    kind = ("mono_bold" if bold else "mono") if mono else ("bold" if bold else "regular")
    return load_font(kind, size)


def ease(t):
    return 1 - (1 - t) ** 3


def mix(c, t):
    """Fade colour c in from the background as t goes 0 -> 1."""
    return tuple(int(BG[k] + (c[k] - BG[k]) * t) for k in range(3))


def wrap(d, text, fnt, width):
    out = []
    for para in str(text).split("\n"):
        words, cur = para.split(), ""
        for w_ in words:
            trial = (cur + " " + w_).strip()
            if d.textlength(trial, font=fnt) <= width:
                cur = trial
            else:
                if cur:
                    out.append(cur)
                cur = w_
        out.append(cur)
    return out


def text_block(d, xy, text, size, width, color=FG, bold=False, mono=False, gap=1.32):
    x, y = xy
    fnt = font(size, bold, mono)
    for line in wrap(d, text, fnt, width):
        d.text((x, y), line, font=fnt, fill=color)
        y += int(size * gap)
    return y


class Ctx:
    def __init__(self, meta):
        self.meta = meta
        self.tag = meta.get("tag") or f"Day {meta['day']} · Part {meta['part']}"


def frame(ctx, kicker=None, title=None):
    im = Image.new("RGB", (W, H), BG)
    d = ImageDraw.Draw(im)
    d.rectangle([0, 0, W, 8], fill=ACCENT)
    d.text((80, H - 60), f"{SERIES}  ·  {ctx.tag}", font=font(26), fill=DIM)
    if kicker:
        d.text((120, 92), str(kicker).upper(), font=font(30, True), fill=ACCENT)
    if title:
        fs = 64 if d.textlength(title, font=font(64, True)) < 1680 else 52
        d.text((120, 136), title, font=font(fs, True), fill=FG)
    return im, d


# ------------------------------------------------------------------ templates
# Every template: fn(ctx, s, t) -> Image ; s = step's "t" dict, t = animation progress 0..1

def T_title(ctx, s, t):
    im, d = frame(ctx)
    d.text((120, 290), s.get("over", ""), font=font(70), fill=DIM)
    y = text_block(d, (120, 380), s["title"], 96, 1650, FG, True, gap=1.15)
    d.rectangle([120, y + 20, 120 + int(700 * ease(t)), y + 28], fill=ACCENT)
    if s.get("subtitle"):
        d.text((120, y + 60), s["subtitle"], font=font(44), fill=mix(DIM, ease(t)))
    d.text((120, y + 150), f"{SERIES}  ·  {ctx.tag}", font=font(36, True), fill=ACCENT)
    if s.get("tip"):
        d.rounded_rectangle([1350, 860, 1800, 960], 16, outline=GOLD, width=3)
        d.text((1385, 885), s["tip"], font=font(38, True), fill=GOLD)
    return im


def T_section(ctx, s, t):
    im, d = frame(ctx)
    d.text((120, 380), str(s.get("kicker", "Section")).upper(), font=font(40, True), fill=ACCENT)
    text_block(d, (120, 450), s["title"], 88, 1650, mix(FG, ease(t)), True, gap=1.15)
    if s.get("subtitle"):
        d.text((120, 680), s["subtitle"], font=font(42), fill=DIM)
    return im


def _bullets(d, items, x, y, size, width, t, hi=None, new_last=True):
    fnt = font(size)
    for i, it in enumerate(items):
        last = new_last and i == len(items) - 1
        col = GOLD if hi is not None and i == hi else FG
        col = mix(col, ease(t)) if last else col
        dot = mix(ACCENT, ease(t)) if last else ACCENT
        d.ellipse([x, y + size * 0.45, x + 16, y + size * 0.45 + 16], fill=dot)
        for line in wrap(d, it, fnt, width):
            d.text((x + 40, y), line, font=fnt, fill=col)
            y += int(size * 1.33)
        y += int(size * 0.5)
    return y


def T_bullets(ctx, s, t):
    im, d = frame(ctx, s.get("kicker"), s.get("title"))
    items = s["items"]
    size = s.get("size") or (44 if len(items) <= 4 else 38)
    y = _bullets(d, items, 140, 290, size, 1600, t, s.get("hi"), s.get("animate_last", True))
    if s.get("note"):
        text_block(d, (140, max(y + 20, 860)), s["note"], 38, 1640, GREEN, True)
    return im


def T_twocol(ctx, s, t):
    im, d = frame(ctx, s.get("kicker"), s.get("title"))
    for k, side in enumerate(("left", "right")):
        if side not in s:
            continue
        col = s[side]
        x = 140 + k * 860
        d.rounded_rectangle([x, 290, x + 800, 820], 22, fill=PANEL)
        c = COLORS.get(col.get("color", "accent" if k == 0 else "gold"), ACCENT)
        d.text((x + 40, 320), col["head"], font=font(48, True), fill=c)
        _bullets(d, col.get("items", []), x + 40, 410, col.get("size", 34), 700, t if k == len([z for z in ("left", "right") if z in s]) - 1 else 1)
    if s.get("note"):
        text_block(d, (140, 860), s["note"], 38, 1640, GREEN, True)
    return im


def T_table(ctx, s, t):
    im, d = frame(ctx, s.get("kicker"), s.get("title"))
    heads, rows = s["headers"], s["rows"]
    n = len(heads)
    widths = s.get("widths") or [1640 // n] * n
    size = s.get("size", 34 if len(rows) <= 5 else 30)
    x0, y = 140, 290
    xs = [x0]
    for w_ in widths[:-1]:
        xs.append(xs[-1] + w_)
    for j, h in enumerate(heads):
        d.text((xs[j] + 20, y), h, font=font(size + 2, True), fill=[ACCENT, GOLD, GREEN, DIM][j % 4])
    y += int(size * 1.7)
    for i, row in enumerate(rows):
        lines = [wrap(d, c, font(size), widths[j] - 40) for j, c in enumerate(row)]
        hgt = max(len(l) for l in lines) * int(size * 1.3) + 26
        last = i == len(rows) - 1 and s.get("animate_last", True)
        d.rounded_rectangle([x0, y, x0 + sum(widths), y + hgt], 12, fill=mix(PANEL, ease(t)) if last else PANEL)
        for j, ls in enumerate(lines):
            for k, line in enumerate(ls):
                d.text((xs[j] + 20, y + 13 + k * int(size * 1.3)), line, font=font(size, j == 0), fill=mix(FG, ease(t)) if last else FG)
        y += hgt + 12
    if s.get("note"):
        text_block(d, (140, max(y + 20, 880)), s["note"], 36, 1640, GREEN, True)
    return im


def T_code(ctx, s, t):
    im, d = frame(ctx, s.get("kicker"), s.get("title"))
    lines = s["code"].strip("\n").split("\n")
    size = s.get("size") or (34 if len(lines) <= 14 else 28 if len(lines) <= 18 else 24)
    hl = set(s.get("hl", []))
    top = 280
    d.rounded_rectangle([120, top, 1800, top + 40 + len(lines) * int(size * 1.4) + 30], 18, fill=(10, 14, 26))
    if s.get("file"):
        d.text((150, top + 12), s["file"], font=font(26, True, True), fill=DIM)
    y = top + 52
    for i, line in enumerate(lines, start=1):
        if i in hl:
            d.rectangle([124, y - 4, 1796, y + int(size * 1.3)], fill=mix((50, 62, 30), ease(t)))
        d.text((150, y), line, font=font(size, False, True), fill=GOLD if i in hl else FG)
        y += int(size * 1.4)
    if s.get("note"):
        text_block(d, (140, min(y + 40, 900)), s["note"], 36, 1640, GREEN, True)
    return im


def T_flow(ctx, s, t):
    im, d = frame(ctx, s.get("kicker"), s.get("title"))
    boxes = s["boxes"]
    n = len(boxes)
    gap = 60
    bw = min(400, (1680 - (n - 1) * gap) // max(n, 1))
    x = 120 + (1680 - (n * bw + (n - 1) * gap)) // 2
    y0 = s.get("y", 330)
    for k, b in enumerate(boxes):
        head, sub = b[0], (b[1] if len(b) > 1 else "")
        c = COLORS.get(b[2] if len(b) > 2 else "panel", PANEL)
        last = k == n - 1 and s.get("animate_last", True)
        fill = mix(c, ease(t)) if last else c
        d.rounded_rectangle([x, y0, x + bw, y0 + 250], 20, fill=fill)
        tc = BG if c != PANEL else FG
        tc = mix(tc, ease(t)) if last else tc
        yy = text_block(d, (x + 25, y0 + 25), head, 38 if bw > 300 else 32, bw - 50, tc, True, gap=1.15)
        text_block(d, (x + 25, yy + 10), sub, 28 if bw > 300 else 24, bw - 50, tc)
        if k < n - 1:
            d.text((x + bw + 8, y0 + 95), "→", font=font(48, True), fill=DIM)
        x += bw + gap
    if s.get("note"):
        text_block(d, (140, y0 + 330), s["note"], 46, 1640, GREEN, True)
    if s.get("note2"):
        text_block(d, (140, y0 + 430), s["note2"], 36, 1640, FG)
    return im


def T_bars(ctx, s, t):
    im, d = frame(ctx, s.get("kicker"), s.get("title"))
    y = 290
    if s.get("prompt"):
        d.rounded_rectangle([140, y, 1500, y + 100], 18, fill=PANEL)
        d.text((175, y + 25), s["prompt"], font=font(44), fill=FG)
        y += 150
    items = s["items"]
    vmax = max(v for _, v in items) or 1
    tt = ease(t) if s.get("animate", True) else 1
    for k, (lab, v) in enumerate(items):
        d.text((160, y), str(lab), font=font(40, True), fill=FG)
        bw = int(1000 * (v / vmax) * tt)
        d.rounded_rectangle([520, y + 6, 520 + max(bw, 4), y + 50], 10, fill=GOLD if k == 0 else ACCENT)
        fmt = s.get("fmt", "{:.2f}")
        d.text((540 + max(bw, 4), y + 2), fmt.format(v * tt), font=font(36), fill=FG)
        y += 80
    if s.get("note"):
        text_block(d, (140, y + 30), s["note"], 38, 1640, GREEN, True)
    return im


def T_chat(ctx, s, t):
    im, d = frame(ctx, s.get("kicker"), s.get("title"))
    d.rounded_rectangle([300, 270, 1620, 960], 24, fill=PANEL)
    y = 300
    msgs = s["messages"]
    for k, (role, txt) in enumerate(msgs):
        last = k == len(msgs) - 1
        mono = role == "tool"
        fnt = font(30, False, mono)
        lines = wrap(d, txt, fnt, 760)
        hgt = len(lines) * 42 + 30
        if role == "user":
            x, c, tc = 760, ACCENT, BG
        elif role == "tool":
            x, c, tc = 360, (60, 52, 20), GOLD
        else:
            x, c, tc = 360, PANEL2, FG
        if last:
            c, tc = mix(c, ease(t)), mix(tc, ease(t))
        d.rounded_rectangle([x, y, x + 820, y + hgt], 18, fill=c)
        label = {"user": "User", "assistant": "Assistant", "tool": "Tool"}.get(role, role)
        for j, line in enumerate(lines):
            d.text((x + 24, y + 15 + j * 42), line, font=fnt, fill=tc)
        d.text((x + 830 if role != "user" else x - 120, y + 10), label, font=font(24, True), fill=DIM)
        y += hgt + 22
    return im


def T_tokens(ctx, s, t):
    im, d = frame(ctx, s.get("kicker"), s.get("title"))
    if s.get("text"):
        text_block(d, (140, 290), s["text"], 42, 1640, DIM)
    x, y = 140, s.get("y", 470)
    toks = s["tokens"]
    hf = s.get("hl_from", len(toks))
    for k, tk in enumerate(toks):
        fnt = font(44, True, True)
        w_ = d.textlength(tk, font=fnt) + 46
        if x + w_ > 1800:
            x, y = 140, y + 110
        new = k >= hf
        c = GOLD if new else PANEL
        if k == len(toks) - 1 and new:
            c = mix(c, ease(t))
        d.rounded_rectangle([x, y, x + w_, y + 86], 14, fill=c)
        d.text((x + 23, y + 16), tk, font=fnt, fill=BG if new else FG)
        x += w_ + 16
    if s.get("note"):
        text_block(d, (140, 880), s["note"], 38, 1640, GREEN, True)
    return im


def T_callout(ctx, s, t):
    im, d = frame(ctx, s.get("kicker"), s.get("title"))
    c = COLORS.get(s.get("color", "gold"), GOLD)
    d.rounded_rectangle([140, 330, 1780, 760], 26, outline=mix(c, ease(t)), width=5)
    y = text_block(d, (200, 390), s["text"], s.get("size", 58), 1520, mix(c, ease(t)), True, gap=1.2)
    if s.get("sub"):
        text_block(d, (200, y + 25), s["sub"], 38, 1520, FG)
    return im


def T_steps(ctx, s, t):
    """Numbered process, items appear one by one (numbers carry meaning: order)."""
    im, d = frame(ctx, s.get("kicker"), s.get("title"))
    y = 290
    items = s["items"]
    size = s.get("size", 40 if len(items) <= 5 else 34)
    for i, it in enumerate(items):
        last = i == len(items) - 1
        c = mix(ACCENT, ease(t)) if last else ACCENT
        tc = mix(FG, ease(t)) if last else FG
        d.ellipse([140, y, 140 + size + 22, y + size + 22], fill=c)
        num = str(i + 1)
        d.text((140 + (size + 22 - d.textlength(num, font=font(size - 4, True))) / 2, y + 6), num, font=font(size - 4, True), fill=BG)
        y = text_block(d, (140 + size + 50, y + 4), it, size, 1500, tc) + int(size * 0.45)
    if s.get("note"):
        text_block(d, (140, max(y + 20, 880)), s["note"], 36, 1640, GREEN, True)
    return im


def T_roadmap(ctx, s, t):
    im, d = frame(ctx, "The roadmap", s.get("title", "Where we are in the series"))
    days = ["How language models work", "Prompts, structured output, safety", "AI agents: models that use tools",
            "MCP: plugging tools into any AI", "RAG: answers from your documents", "Testing and monitoring AI",
            "Fine-tuning and validating models", "Taking it to production", "System design and interviews", "Mock interviews"]
    cur = s.get("day", ctx.meta["day"])
    for k, name in enumerate(days):
        col, row = k // 5, k % 5
        x, y = 140 + col * 840, 290 + row * 125
        on = k + 1 == cur
        done = k + 1 < cur
        d.rounded_rectangle([x, y, x + 780, y + 100], 16, fill=ACCENT if on else PANEL)
        d.text((x + 25, y + 22), f"Day {k + 1}", font=font(36, True), fill=BG if on else (GREEN if done else GOLD))
        d.text((x + 180, y + 26), name, font=font(32, on), fill=BG if on else FG)
    return im


def T_quiz(ctx, s, t):
    im, d = frame(ctx, "Quick check", s.get("title", "Pause and answer"))
    y = text_block(d, (140, 300), s["q"], 50, 1640, FG, True)
    if s.get("options"):
        y = _bullets(d, s["options"], 160, y + 40, 40, 1500, 1, new_last=False)
    if s.get("answer"):
        d.rounded_rectangle([140, max(y + 20, 700), 1780, max(y + 20, 700) + 180], 18, outline=mix(GREEN, ease(t)), width=4)
        text_block(d, (180, max(y + 20, 700) + 30), "Answer: " + s["answer"], 38, 1560, mix(GREEN, ease(t)), True)
    return im


def T_recap(ctx, s, t):
    im, d = frame(ctx, "Recap", s.get("title", "What you learned"))
    y = _bullets(d, s["items"], 140, 280, s.get("size", 38), 1600, 1, new_last=False)
    if s.get("next"):
        d.text((140, max(y + 30, 900)), "Next: " + s["next"], font=font(40, True), fill=mix(ACCENT, ease(t)))
    return im


def T_end(ctx, s, t):
    im, d = frame(ctx)
    d.text((120, 300), "Thanks for watching", font=font(90, True), fill=FG)
    lines = s.get("lines", ["Code for this video: link in the description",
                            "Subscribe for the next episode", SERIES])
    y = 460
    for k, l in enumerate(lines):
        d.text((120, y), l, font=font(46, k == len(lines) - 1), fill=ACCENT if k == len(lines) - 1 else DIM)
        y += 80
    return im


TEMPLATES = {k[2:]: v for k, v in globals().items() if k.startswith("T_")}


# ------------------------------------------------------------------ build
def ff(*args):
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", *args], check=True)


def duration(path):
    out = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "json", str(path)],
                         capture_output=True, text=True, check=True).stdout
    return float(json.loads(out)["format"]["duration"])


async def _tts(text, path):
    for attempt in range(4):
        try:
            await edge_tts.Communicate(text, VOICE, rate="-4%").save(str(path))
            return
        except Exception:
            if attempt == 3:
                raise
            await asyncio.sleep(3 * (attempt + 1))


def ts(sec, srt=False):
    ms = int(round(sec * 1000))
    h, ms = divmod(ms, 3600000)
    m, ms = divmod(ms, 60000)
    s, ms = divmod(ms, 1000)
    return f"{h:02}:{m:02}:{s:02},{ms:03}" if srt else (f"{h}:{m:02}:{s:02}" if h else f"{m}:{s:02}")


def load(path):
    spec = importlib.util.spec_from_file_location(path.stem, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod.META, mod.STEPS


def validate(meta, steps):
    text = json.dumps([meta, steps]).lower()
    bad = [m for m in banned_words() if m in text]
    if bad:
        raise SystemExit(f"{meta.get('id')}: banned words {bad}")
    for i, st in enumerate(steps):
        tpl = st["t"].get("tpl")
        if tpl not in TEMPLATES:
            raise SystemExit(f"{meta['id']} step {i}: unknown template {tpl!r}")
        if not st.get("say", "").strip():
            raise SystemExit(f"{meta['id']} step {i}: empty narration")


def build(path, force=False):
    meta, steps = load(path)
    validate(meta, steps)
    out = OUTPUT / meta["id"]
    if (out / "video.mp4").exists() and not force:
        print("skip (built):", meta["id"])
        return
    work = out / "_work"
    if work.exists():
        shutil.rmtree(work)
    work.mkdir(parents=True)
    ctx = Ctx(meta)
    ANIM, PAD = 0.6, 0.45
    segs, srt, chapters, clock = [], [], [], 0.0
    for n, st in enumerate(steps):
        s = st["t"]
        if st.get("chapter_name") or (s["tpl"] in ("section", "roadmap") and st.get("chapter", True)):
            chapters.append((clock, st.get("chapter_name") or s.get("title") or "Intro"))
        mp3 = work / f"{n:03}.mp3"
        asyncio.run(_tts(st["say"], mp3))
        dur = duration(mp3) + PAD
        fdir = work / f"f{n:03}"
        fdir.mkdir()
        paint = TEMPLATES[s["tpl"]]
        k = int(ANIM * FPS)
        for fi in range(k):
            paint(ctx, s, (fi + 1) / k).save(fdir / f"{fi:04}.png")
        paint(ctx, s, 1.0).save(fdir / "hold.png")
        seg = work / f"{n:03}.mp4"
        ff("-framerate", str(FPS), "-i", str(fdir / "%04d.png"),
           "-loop", "1", "-framerate", str(FPS), "-t", f"{max(dur - ANIM, 0.1):.3f}", "-i", str(fdir / "hold.png"),
           "-i", str(mp3),
           "-filter_complex", "[0:v][1:v]concat=n=2:v=1:a=0,format=yuv420p[v];[2:a]apad[a]",
           "-map", "[v]", "-map", "[a]", "-t", f"{dur:.3f}",
           "-c:v", "libx264", "-preset", "medium", "-crf", "20", "-r", str(FPS),
           "-c:a", "aac", "-b:a", "160k", "-ar", "48000", "-ac", "2", str(seg))
        shutil.rmtree(fdir)
        segs.append(seg)
        srt.append(f"{len(srt) + 1}\n{ts(clock, True)} --> {ts(clock + dur - PAD, True)}\n{st['say']}\n")
        clock += dur
    lst = work / "list.txt"
    lst.write_text("".join(f"file '{p.as_posix()}'\n" for p in segs), encoding="utf-8")
    ff("-f", "concat", "-safe", "0", "-i", str(lst), "-c", "copy", "-movflags", "+faststart", str(out / "video.mp4"))
    (out / "captions.srt").write_text("\n".join(srt), encoding="utf-8")
    if not chapters or chapters[0][0] > 0:
        chapters.insert(0, (0.0, "Intro"))
    chap = "\n".join(f"{ts(c)} {name}" for c, name in chapters)
    yt = (f"TITLE:\n{meta['yt_title']}\n\nDESCRIPTION:\n{meta['description'].strip()}\n\n"
          f"Code: {REPO_URL}/tree/main/{meta.get('code', '')}\n\nChapters:\n{chap}\n\n"
          f"Series: {SERIES} | {meta.get('tag') or 'Day %s, Part %s' % (meta['day'], meta['part'])}\n\nTAGS:\n{', '.join(meta.get('tags', []))}\n")
    (out / "youtube.txt").write_text(yt, encoding="utf-8")
    shutil.rmtree(work)
    print(f"built {meta['id']}: {clock / 60:.1f} min, {len(steps)} steps")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("episode", nargs="?")
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--force", action="store_true")
    ap.add_argument("--check", action="store_true", help="validate specs and render one still per step, no audio")
    ap.add_argument("--dir", help="folder of lesson scripts for --all (default ./lessons)")
    a = ap.parse_args()
    paths = sorted((Path(a.dir) if a.dir else EPISODES).glob("*.py")) if a.all else [Path(a.episode).resolve()]
    for p in paths:
        if a.check:
            meta, steps = load(p)
            validate(meta, steps)
            cdir = OUTPUT / "_check" / meta["id"]
            cdir.mkdir(parents=True, exist_ok=True)
            ctx = Ctx(meta)
            for n, st in enumerate(steps):
                TEMPLATES[st["t"]["tpl"]](ctx, st["t"], 1.0).save(cdir / f"{n:03}.png")
            words = sum(len(st["say"].split()) for st in steps)
            print(f"ok {meta['id']}: {len(steps)} steps, ~{words / 140:.1f} min narration")
        else:
            build(p, a.force)


if __name__ == "__main__":
    main()
