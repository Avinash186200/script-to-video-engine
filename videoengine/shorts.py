"""Shorts engine.

Vertical (1080x1920) kinetic-caption Shorts: white background, a bold black headline that
stays for the beat, a small animated visual in the middle (so the screen is never blank),
and a word-by-word karaoke caption underneath (current word highlighted yellow) driven by
edge-tts word-boundary timing so the highlight is frame-accurate to the narration.

Each beat is rendered as ONE continuous frame-by-frame sequence -> ONE ffmpeg encode, timed
off each word's start time (not its raw spoken duration), so the video track always covers
the full audio exactly -- no truncated words, no join-point stutter between words.

A short is a Python file defining META (dict) and BEATS (list of dicts).
Each beat: {"headline": "<short on-screen statement, stays for the beat>",
            "say": "<narration text, also captioned word-by-word>",
            "visual": {...} }  # optional, see VISUALS below

    python -m videoengine.shorts examples/short_example.py            # build one short
    python -m videoengine.shorts --all                                # build every short in ./shorts
    python -m videoengine.shorts --all --force                        # rebuild everything
    python -m videoengine.shorts examples/short_example.py --check    # validate + still frames, no audio

Output goes to output/shorts/<short_id>/ : video.mp4, captions.srt, youtube.txt
"""
from __future__ import annotations

import argparse
import asyncio
import importlib.util
import json
import math
import shutil
import subprocess
from pathlib import Path

import edge_tts
from PIL import Image, ImageDraw, ImageFont

ROOT = Path.cwd()
SCRIPTS = ROOT / "shorts"
OUT = ROOT / "output" / "shorts"
W, H, FPS = 1080, 1920, 30
from videoengine.settings import SERIES, VOICE, banned_words, load_font

BG = (250, 250, 250)
INK = (20, 20, 22)
DIM = (140, 140, 148)
HILITE = (255, 209, 0)
ACCENT = (45, 110, 255)
GREEN = (60, 180, 110)

WORDS_PER_LINE = 4
POP_SEC = 0.12          # word pop-in length
MID_Y = (560, 1260)     # vertical band reserved for the middle visual
CAPTION_Y = H - 560


def font(size, bold=True):
    return load_font("bold" if bold else "regular", size)


def ease(t):
    return 1 - (1 - t) ** 3


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


def text_block(d, xy, text, size, width, color=INK, bold=True, gap=1.18, align="center"):
    x, y = xy
    fnt = font(size, bold)
    lines = wrap(d, text, fnt, width)
    for line in lines:
        lw = d.textlength(line, font=fnt)
        lx = x + (width - lw) / 2 if align == "center" else x
        d.text((lx, y), line, font=fnt, fill=color)
        y += int(size * gap)
    return y


def frame_base(kicker=None):
    im = Image.new("RGB", (W, H), BG)
    d = ImageDraw.Draw(im)
    d.rectangle([0, 0, W, 10], fill=ACCENT)
    d.text((W / 2, H - 46), SERIES, font=font(24), fill=DIM, anchor="mm")
    if kicker:
        d.text((W / 2, 70), str(kicker).upper(), font=font(26), fill=ACCENT, anchor="mm")
    return im, d


def paint_headline(d, headline):
    if not headline:
        return
    size = 72 if len(headline) < 40 else (60 if len(headline) < 70 else 50)
    text_block(d, (90, 230), headline, size, W - 180, INK, True, gap=1.18)


def paint_caption(d, words, hi_idx, pop_t=1.0):
    size = 68
    gap_px = 22
    while size > 40 and (sum(d.textlength(w.upper(), font=font(size, True)) for w in words)
                         + gap_px * (len(words) - 1) + 40) > W - 120:
        size -= 4
    fnt = font(size, True)
    widths = [d.textlength(w.upper(), font=fnt) for w in words]
    total = sum(widths) + gap_px * (len(words) - 1)
    x = (W - total) / 2
    y = CAPTION_Y
    for i, w_ in enumerate(words):
        wtxt = w_.upper()
        ww = widths[i]
        if i == hi_idx:
            pad = 18
            scale = 0.82 + 0.18 * ease(pop_t)
            bw, bh = (ww + pad * 2) * scale, (size + pad * 1.1) * scale
            cx, cy = x + ww / 2, y + size / 2
            d.rounded_rectangle([cx - bw / 2, cy - bh / 2, cx + bw / 2, cy + bh / 2], 18,
                                 fill=HILITE, outline=INK, width=4)
            d.text((cx, cy), wtxt, font=fnt, fill=INK, anchor="mm")
        else:
            d.text((x + ww / 2, y + size / 2), wtxt, font=fnt, fill=(255, 255, 255),
                   anchor="mm", stroke_width=7, stroke_fill=INK)
        x += ww + gap_px


# ------------------------------------------------------------------ mid-screen visuals
def _pulse(t, period=1.6, lo=0.92, hi=1.04):
    return lo + (hi - lo) * (0.5 + 0.5 * math.sin(2 * math.pi * t / period))


def visual_default(d, v, t, kicker):
    """Ambient filler so the middle band is never blank: a soft breathing ring."""
    cx, cy = W / 2, (MID_Y[0] + MID_Y[1]) / 2
    r = 150 * _pulse(t)
    d.ellipse([cx - r, cy - r, cx + r, cy + r], outline=ACCENT, width=10)
    r2 = 90 * _pulse(t, period=1.6, lo=1.0, hi=0.9)
    d.ellipse([cx - r2, cy - r2, cx + r2, cy + r2], fill=(232, 240, 255))
    letter = (kicker or "AI")[0:1].upper() or "A"
    d.text((cx, cy), letter, font=font(90, True), fill=ACCENT, anchor="mm")


def visual_icon_thermometer(d, v, t, kicker):
    cx, cy = W / 2, (MID_Y[0] + MID_Y[1]) / 2
    top, bot = cy - 220, cy + 160
    bw = 46
    d.rounded_rectangle([cx - bw / 2, top, cx + bw / 2, bot], bw / 2, outline=INK, width=8, fill=(255, 255, 255))
    bulb_r = 70
    d.ellipse([cx - bulb_r, bot - 40, cx + bulb_r, bot + bulb_r * 2 - 40], outline=INK, width=8, fill=(255, 255, 255))
    level = v.get("level", 0.5)
    level = max(0.05, min(1.0, level * min(1.0, t / 0.9)))
    fill_top = min(bot - (bot - top - bw / 2) * level, bot - 31)
    d.rounded_rectangle([cx - bw / 2 + 10, fill_top, cx + bw / 2 - 10, bot - 30], (bw - 20) / 2, fill=HILITE)
    d.ellipse([cx - bulb_r + 10, bot - 30, cx + bulb_r - 10, bot + bulb_r * 2 - 50], fill=HILITE)
    for i in range(5):
        yy = top + 30 + i * (bot - top - 60) / 4
        d.line([cx + bw / 2 + 6, yy, cx + bw / 2 + 28, yy], fill=INK, width=5)


def visual_gauge(d, v, t, kicker):
    cx, cy = W / 2, (MID_Y[0] + MID_Y[1]) / 2
    x0, x1 = cx - 320, cx + 320
    d.rounded_rectangle([x0, cy - 24, x1, cy + 24], 24, fill=(230, 230, 234))
    frac = max(0.0, min(1.0, v.get("value", 0.5))) * min(1.0, t / 0.9)
    fx = x0 + (x1 - x0) * frac
    d.rounded_rectangle([x0, cy - 24, max(fx, x0 + 10), cy + 24], 24, fill=ACCENT)
    kr = 30
    d.ellipse([fx - kr, cy - kr, fx + kr, cy + kr], fill=HILITE, outline=INK, width=5)
    d.text((x0, cy - 90), v.get("lo", "LOW"), font=font(34, True), fill=DIM, anchor="lm")
    d.text((x1, cy - 90), v.get("hi", "HIGH"), font=font(34, True), fill=DIM, anchor="rm")
    if v.get("label"):
        d.text((cx, cy + 100), v["label"], font=font(40, True), fill=INK, anchor="mm")


def visual_versus(d, v, t, kicker):
    cx, cy = W / 2, (MID_Y[0] + MID_Y[1]) / 2
    bw, bh, gap = 330, 220, 60
    scale = 0.85 + 0.15 * ease(min(1.0, t / 0.6))
    for side, (label, sub) in ((-1, (v.get("left", ""), v.get("left_sub", ""))),
                                (1, (v.get("right", ""), v.get("right_sub", "")))):
        x = cx + side * (bw / 2 + gap / 2)
        bw_s, bh_s = bw * scale, bh * scale
        c = ACCENT if side < 0 else GREEN
        d.rounded_rectangle([x - bw_s / 2, cy - bh_s / 2, x + bw_s / 2, cy + bh_s / 2], 24, fill=c)
        text_block(d, (x - bw_s / 2 + 20, cy - 40), label, 40, bw_s - 40, (255, 255, 255), True, align="center")
        if sub:
            d.text((x, cy + 50), sub, font=font(24, False), fill=(255, 255, 255), anchor="mm")
    d.ellipse([cx - 44, cy - 44, cx + 44, cy + 44], fill=INK)
    d.text((cx, cy), "VS", font=font(30, True), fill=(255, 255, 255), anchor="mm")


def visual_loop(d, v, t, kicker):
    cx, cy = W / 2, (MID_Y[0] + MID_Y[1]) / 2
    items = v.get("items", [])
    n = max(len(items), 1)
    radius = 230
    active = int(t * 1.4) % n
    pts = [(cx + radius * math.cos(-math.pi / 2 + 2 * math.pi * i / n),
            cy + radius * math.sin(-math.pi / 2 + 2 * math.pi * i / n)) for i in range(n)]
    # connectors first, so the nodes sit on top of them
    for i in range(n):
        (x0, y0), (x1, y1) = pts[i], pts[(i + 1) % n]
        d.line([x0, y0, x1, y1], fill=DIM, width=6)
        # small arrowhead just outside the next node, pointing at it
        ang = math.atan2(y1 - y0, x1 - x0)
        tipx, tipy = x1 - 100 * math.cos(ang), y1 - 100 * math.sin(ang)
        wing = 22
        d.polygon([(tipx, tipy),
                   (tipx - wing * math.cos(ang - 0.5), tipy - wing * math.sin(ang - 0.5)),
                   (tipx - wing * math.cos(ang + 0.5), tipy - wing * math.sin(ang + 0.5))], fill=DIM)
    for i, label in enumerate(items):
        x, y = pts[i]
        on = i == active
        r = 95 if on else 80
        d.ellipse([x - r, y - r, x + r, y + r], fill=HILITE if on else (235, 235, 240), outline=INK, width=5)
        fs = 28
        while fs > 16 and d.textlength(label, font=font(fs, True)) > r * 2 - 24:
            fs -= 2
        d.text((x, y), label, font=font(fs, True), fill=INK, anchor="mm")


def visual_bignum(d, v, t, kicker):
    cx, cy = W / 2, (MID_Y[0] + MID_Y[1]) / 2
    scale = 0.8 + 0.2 * ease(min(1.0, t / 0.5))
    num = v.get("num", "?")
    base = 190
    while base > 60 and d.textlength(num, font=font(base, True)) > W - 160:
        base -= 10
    size = int(base * scale)
    d.text((cx, cy - 40), num, font=font(size, True), fill=ACCENT, anchor="mm")
    if v.get("label"):
        d.text((cx, cy + 140), v["label"], font=font(36, True), fill=INK, anchor="mm")


VISUALS = {
    "thermometer": visual_icon_thermometer,
    "gauge": visual_gauge,
    "versus": visual_versus,
    "loop": visual_loop,
    "bignum": visual_bignum,
}


def paint_visual(d, beat_visual, t, kicker):
    if not beat_visual:
        visual_default(d, {}, t, kicker)
        return
    fn = VISUALS.get(beat_visual.get("type"))
    (fn or visual_default)(d, beat_visual, t, kicker)


# ------------------------------------------------------------------ TTS + word timing
async def synth_words(text, mp3_path):
    for attempt in range(5):
        try:
            c = edge_tts.Communicate(text, VOICE, rate="+14%", pitch="+20Hz", boundary="WordBoundary")
            words = []
            with open(mp3_path, "wb") as f:
                async for chunk in c.stream():
                    if chunk["type"] == "audio":
                        f.write(chunk["data"])
                    elif chunk["type"] == "WordBoundary":
                        words.append({"text": chunk["text"], "start": chunk["offset"] / 1e7})
            if not words:
                raise RuntimeError("no WordBoundary events returned")
            return words
        except Exception:
            if attempt == 4:
                raise
            await asyncio.sleep(3 * (attempt + 1))


def duration(path):
    out = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "json", str(path)],
                          capture_output=True, text=True, check=True).stdout
    return float(json.loads(out)["format"]["duration"])


def ff(*args):
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", *args], check=True)


def ts(sec):
    ms = int(round(sec * 1000))
    h, ms = divmod(ms, 3600000)
    m, ms = divmod(ms, 60000)
    s, ms = divmod(ms, 1000)
    return f"{h:02}:{m:02}:{s:02},{ms:03}"


CAPTION_MAX_W = W - 120
_measure = ImageDraw.Draw(Image.new("RGB", (10, 10)))


def _line_width(texts):
    fnt = font(68, True)
    # +40 leaves room for the highlight pill's padding on whichever word is active
    return sum(_measure.textlength(t.upper(), font=fnt) for t in texts) + 22 * (len(texts) - 1) + 40


def group_words(words, n=WORDS_PER_LINE):
    """Greedy grouping by measured width (max n words) so a caption line never runs off-screen."""
    lines, cur = [], []
    for w_ in words:
        trial = cur + [w_]
        if cur and (len(trial) > n or _line_width([x["text"] for x in trial]) > CAPTION_MAX_W):
            lines.append(cur)
            cur = [w_]
        else:
            cur = trial
    if cur:
        lines.append(cur)
    return lines


# ------------------------------------------------------------------ build one beat (single continuous encode)
def build_beat(kicker, headline, visual, words, beat_dur, mp3_path, work, idx_prefix):
    """One PNG per video frame for the full beat (timed off word START times, so the video
    always covers the whole audio), one ffmpeg encode, muxed with the beat's mp3."""
    lines = group_words(words)
    # (line_idx, word_idx_in_line, global_word_idx, start, end) for every word
    flat = []
    gi = 0
    for li, line in enumerate(lines):
        for wi in range(len(line)):
            flat.append([li, wi, gi])
            gi += 1
    starts = [w["start"] for w in words]
    ends = starts[1:] + [beat_dur]

    fdir = work / idx_prefix
    fdir.mkdir(parents=True)
    n_frames = max(1, math.ceil(beat_dur * FPS))
    cur = 0
    for fi in range(n_frames):
        t = fi / FPS
        while cur + 1 < len(starts) and t >= starts[cur + 1]:
            cur += 1
        li, wi, _ = flat[cur]
        pop_t = max(0.0, min(1.0, (t - starts[cur]) / POP_SEC)) if cur < len(starts) else 1.0
        im, d = frame_base(kicker)
        paint_headline(d, headline)
        paint_visual(d, visual, t, kicker)
        paint_caption(d, [w["text"] for w in lines[li]], wi, pop_t)
        im.save(fdir / f"{fi:05}.png")

    seg = work / f"{idx_prefix}.mp4"
    ff("-framerate", str(FPS), "-i", str(fdir / "%05d.png"), "-i", str(mp3_path),
       "-c:v", "libx264", "-pix_fmt", "yuv420p", "-preset", "medium", "-crf", "20", "-r", str(FPS),
       "-c:a", "aac", "-b:a", "160k", "-ar", "48000", "-ac", "2",
       "-shortest", "-movflags", "+faststart", str(seg))
    shutil.rmtree(fdir)
    return seg


def build_outro(meta, work):
    """Standardised outro card: generated by the engine, not hand-authored per script."""
    say = meta.get("outro_say") or (
        f"Thanks for watching! Full breakdown in {meta.get('source_episode', 'the full episode')}. "
        f"Subscribe for the next one."
    )
    mp3 = work / "outro.mp3"
    words = asyncio.run(synth_words(say, mp3))
    beat_dur = duration(mp3)
    fdir = work / "outro_frames"
    fdir.mkdir(parents=True)
    n_frames = max(1, math.ceil(beat_dur * FPS))
    for fi in range(n_frames):
        t = fi / FPS
        im, d = frame_base(meta.get("kicker", ""))
        cx, cy = W / 2, H / 2 - 120
        scale = 0.85 + 0.15 * ease(min(1.0, t / 0.5))
        d.text((cx, cy - 140), "Thanks for watching!", font=font(int(66 * scale), True), fill=INK, anchor="mm")
        text_block(d, (90, cy), f"Full breakdown: {meta.get('source_episode', '')}", 42, W - 180, ACCENT, True)
        d.text((cx, cy + 220), "Subscribe for the next one \u2192", font=font(40, True), fill=GREEN, anchor="mm")
        d.text((cx, cy + 300), SERIES, font=font(30, True), fill=DIM, anchor="mm")
        im.save(fdir / f"{fi:05}.png")
    seg = work / "outro.mp4"
    ff("-framerate", str(FPS), "-i", str(fdir / "%05d.png"), "-i", str(mp3),
       "-c:v", "libx264", "-pix_fmt", "yuv420p", "-preset", "medium", "-crf", "20", "-r", str(FPS),
       "-c:a", "aac", "-b:a", "160k", "-ar", "48000", "-ac", "2",
       "-shortest", "-movflags", "+faststart", str(seg))
    shutil.rmtree(fdir)
    return seg, say, beat_dur


def load(path):
    spec = importlib.util.spec_from_file_location(path.stem, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod.META, mod.BEATS


def validate(meta, beats):
    text = json.dumps([meta, beats]).lower()
    bad = [m for m in banned_words() if m in text]
    if bad:
        raise SystemExit(f"{meta.get('id')}: banned words {bad}")
    for i, b in enumerate(beats):
        if not b.get("say", "").strip():
            raise SystemExit(f"{meta.get('id')}: beat {i} has empty 'say'")


def build(path, force=False):
    meta, beats = load(path)
    validate(meta, beats)
    out = OUT / meta["id"]
    if (out / "video.mp4").exists() and not force:
        print("skip (built):", meta["id"])
        return
    work = out / "_work"
    if work.exists():
        shutil.rmtree(work)
    work.mkdir(parents=True)

    beat_videos, srt, clock = [], [], 0.0
    for n, b in enumerate(beats):
        mp3 = work / f"{n:03}.mp3"
        words = asyncio.run(synth_words(b["say"], mp3))
        if not words:
            raise SystemExit(f"{meta['id']} beat {n}: no word-boundary data returned")
        beat_dur = duration(mp3)
        kicker = meta.get("kicker", meta.get("topic", ""))
        beat_mp4 = build_beat(kicker, b.get("headline", ""), b.get("visual"), words, beat_dur, mp3, work, f"b{n:03}")
        beat_videos.append(beat_mp4)
        srt.append(f"{len(srt) + 1}\n{ts(clock)} --> {ts(clock + beat_dur)}\n{b['say']}\n")
        clock += beat_dur

    if meta.get("outro", True):  # fast Shorts set "outro": False: the outro card is the biggest swipe-away point
        outro_seg, outro_say, outro_dur = build_outro(meta, work)
        beat_videos.append(outro_seg)
        srt.append(f"{len(srt) + 1}\n{ts(clock)} --> {ts(clock + outro_dur)}\n{outro_say}\n")
        clock += outro_dur

    lst = work / "final_list.txt"
    lst.write_text("".join(f"file '{p.as_posix()}'\n" for p in beat_videos), encoding="utf-8")
    ff("-f", "concat", "-safe", "0", "-i", str(lst), "-c", "copy", "-movflags", "+faststart", str(out / "video.mp4"))
    (out / "captions.srt").write_text("\n".join(srt), encoding="utf-8")

    yt = (f"TITLE:\n{meta['yt_title']}\n\nDESCRIPTION:\n{meta['description'].strip()}\n\n"
          f"Full episode: {meta.get('source_episode', '')}\n"
          f"Series: {SERIES}\n\nTAGS:\n{', '.join(meta.get('tags', []))}\n")
    (out / "youtube.txt").write_text(yt, encoding="utf-8")
    shutil.rmtree(work)
    print(f"built {meta['id']}: {clock:.1f}s, {len(beats)} beats" + (" + outro" if meta.get("outro", True) else ""))


def check(path):
    meta, beats = load(path)
    validate(meta, beats)
    cdir = OUT / "_check" / meta["id"]
    cdir.mkdir(parents=True, exist_ok=True)
    for n, b in enumerate(beats):
        im, d = frame_base(meta.get("kicker", meta.get("topic", "")))
        paint_headline(d, b.get("headline", ""))
        paint_visual(d, b.get("visual"), 1.0, meta.get("kicker", ""))
        first_line = group_words([{"text": x} for x in b["say"].split()])[0]
        paint_caption(d, [x["text"] for x in first_line], min(1, len(first_line) - 1), 1.0)
        im.save(cdir / f"{n:03}.png")
    words = sum(len(b["say"].split()) for b in beats)
    print(f"ok {meta['id']}: {len(beats)} beats, ~{words / 2.3:.0f}s narration estimate (stills in {cdir})")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("short", nargs="?")
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--force", action="store_true")
    ap.add_argument("--check", action="store_true")
    a = ap.parse_args()
    paths = sorted(SCRIPTS.glob("s*.py")) if a.all else [Path(a.short).resolve()]
    for p in paths:
        if a.check:
            check(p)
        else:
            build(p, a.force)


if __name__ == "__main__":
    main()
