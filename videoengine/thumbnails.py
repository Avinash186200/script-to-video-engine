"""Thumbnail v2: short hook, one highlighted word, a simple visual. Three styles."""
from PIL import Image, ImageDraw, ImageFont, ImageFilter

from videoengine.settings import load_font, SERIES

W, H = 1280, 720
BLACK = "black"
BOLD = "bold"


def font(kind, size):
    return load_font(kind, size)


def fit(d, lines, path, max_w, start):
    s = start
    while s > 40 and max(d.textlength(l, font=font(path, s)) for l in lines) > max_w:
        s -= 4
    return font(path, s)


def draw_lines(d, lines, hi, x, y, fnt, fg, hi_fg, hi_bg, gap=1.05, shadow=True):
    """Draw hook lines; the word `hi` gets a coloured box."""
    for line in lines:
        cx = x
        for i, w in enumerate(line.split(" ")):
            word = w + (" " if i < len(line.split(" ")) - 1 else "")
            ww = d.textlength(w, font=fnt)
            if hi and w.strip("?!.,").upper() == hi.strip("?!.,").upper():
                pad = 14
                d.rounded_rectangle([cx - pad, y + fnt.size * 0.12, cx + ww + pad, y + fnt.size * 1.12], 14, fill=hi_bg)
                d.text((cx, y), w, font=fnt, fill=hi_fg)
            else:
                if shadow:
                    d.text((cx + 5, y + 5), w, font=fnt, fill=(0, 0, 0))
                d.text((cx, y), w, font=fnt, fill=fg)
            cx += d.textlength(word, font=fnt)
        y += int(fnt.size * gap)
    return y


def tag(d, text, x, y, bg, fg, size=34):
    f = font(BLACK, size)
    w = d.textlength(text, font=f)
    d.rounded_rectangle([x, y, x + w + 44, y + size + 30], 14, fill=bg)
    d.text((x + 22, y + 10), text, font=f, fill=fg)


def visual(d, kind, box, col, bg):
    """Simple icon-like visuals drawn with shapes."""
    x0, y0, x1, y1 = box
    cx, cy = (x0 + x1) // 2, (y0 + y1) // 2
    if kind == "chat":
        d.rounded_rectangle([x0, y0 + 20, x1 - 60, y0 + 150], 30, fill=col)
        d.rounded_rectangle([x0 + 60, y0 + 190, x1, y0 + 330], 30, fill=(255, 255, 255))
        for i in range(3):
            d.ellipse([x0 + 50 + i * 60, y0 + 70, x0 + 80 + i * 60, y0 + 100], fill=bg)
    elif kind == "bars":
        vals = [0.9, 0.35, 0.2, 0.1]
        bw = (x1 - x0) // 5
        for i, v in enumerate(vals):
            h = int((y1 - y0 - 40) * v)
            d.rounded_rectangle([x0 + i * (bw + 18), y1 - h, x0 + i * (bw + 18) + bw, y1], 10,
                                fill=col if i == 0 else (255, 255, 255))
    elif kind == "nodes":
        pts = [(x0 + 40, cy), (cx, y0 + 40), (cx, y1 - 40), (x1 - 40, cy)]
        for a in pts:
            for b in pts:
                d.line([a, b], fill=(255, 255, 255), width=6)
        for i, (px, py) in enumerate(pts):
            r = 46
            d.ellipse([px - r, py - r, px + r, py + r], fill=col if i == 3 else (255, 255, 255))
    elif kind == "warn":
        d.polygon([(cx, y0), (x1, y1), (x0, y1)], fill=col)
        f = font(BLACK, (y1 - y0) // 2)
        d.text((cx - d.textlength("!", font=f) / 2, y0 + (y1 - y0) * 0.33), "!", font=f, fill=bg)


def style_a(hook, hi, day, kind, out):
    """Dark navy, giant white hook, yellow highlight box, accent visual on the right."""
    BG = (13, 18, 33)
    im = Image.new("RGB", (W, H), BG)
    d = ImageDraw.Draw(im)
    d.ellipse([760, -120, 1480, 600], fill=(26, 40, 78))
    visual(d, kind, (850, 170, 1220, 540), (86, 182, 255), BG)
    lines = hook.split("|")
    fnt = fit(d, lines, BLACK, 760, 150)
    y = (H - len(lines) * fnt.size * 1.05) / 2 + 10
    draw_lines(d, lines, hi, 60, y, fnt, (255, 255, 255), (13, 18, 33), (255, 210, 60))
    tag(d, day, 60, 40, (86, 182, 255), BG)
    d.text((60, H - 70), SERIES.upper(), font=font(BLACK, 30), fill=(255, 210, 60))
    im.save(out, quality=92)


def style_b(hook, hi, day, kind, out):
    """Bright yellow background, heavy black text, red highlight. High contrast in a dark feed."""
    BG = (255, 214, 10)
    im = Image.new("RGB", (W, H), BG)
    d = ImageDraw.Draw(im)
    d.rounded_rectangle([820, 120, 1240, 600], 40, fill=(20, 20, 20))
    visual(d, kind, (870, 170, 1190, 550), (255, 60, 60), (20, 20, 20))
    lines = hook.split("|")
    fnt = fit(d, lines, BLACK, 720, 150)
    y = (H - len(lines) * fnt.size * 1.05) / 2 + 10
    draw_lines(d, lines, hi, 60, y, fnt, (15, 15, 15), (255, 255, 255), (230, 40, 40), shadow=False)
    tag(d, day, 60, 40, (15, 15, 15), BG)
    d.text((60, H - 70), SERIES.upper(), font=font(BLACK, 30), fill=(15, 15, 15))
    im.save(out, quality=92)


def style_c(hook, hi, day, kind, out):
    """Gradient purple-to-blue, glow text, big outlined number for the day."""
    im = Image.new("RGB", (W, H))
    px = im.load()
    for x in range(W):
        t = x / W
        c = (int(70 + 10 * t), int(30 + 60 * t), int(140 + 90 * t))
        for y in range(H):
            px[x, y] = c
    d = ImageDraw.Draw(im)
    num = day.split()[1] if len(day.split()) > 1 else ""
    f = font(BLACK, 620 if len(num) < 2 else 430)
    nx = W - 40 - d.textlength(num, font=f)
    d.text((max(nx, 860) if len(num) < 2 else nx, -150 if len(num) < 2 else -60), num, font=f, fill=None, stroke_width=6, stroke_fill=(150, 130, 235))
    glow = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    gd = ImageDraw.Draw(glow)
    lines = hook.split("|")
    fnt = fit(d, lines, BLACK, 760 if len(num) < 2 else 700, 150)
    y = (H - len(lines) * fnt.size * 1.05) / 2 + 10
    draw_lines(gd, lines, None, 60, y, fnt, (0, 255, 200, 255), (0, 0, 0), (0, 0, 0), shadow=False)
    im.paste(glow.filter(ImageFilter.GaussianBlur(14)), (0, 0), glow.filter(ImageFilter.GaussianBlur(14)))
    d = ImageDraw.Draw(im)
    draw_lines(d, lines, hi, 60, y, fnt, (255, 255, 255), (20, 10, 60), (0, 255, 200), shadow=False)
    tag(d, day, 60, 40, (255, 255, 255), (60, 30, 140))
    d.text((60, H - 70), SERIES.upper(), font=font(BLACK, 30), fill=(255, 255, 255))
    im.save(out, quality=92)


STYLES = {"A": style_a, "B": style_b, "C": style_c}

if __name__ == "__main__":
    import pathlib
    out = pathlib.Path.cwd() / "output" / "thumbnails"
    out.mkdir(parents=True, exist_ok=True)
    demos = [("LLMs Are|Just CLASSIFIERS", "CLASSIFIERS", "DAY 1", "bars", "d1"),
             ("What Is an|AI AGENT?", "AGENT?", "DAY 3", "nodes", "d3"),
             ("Why Model|Results LIE", "LIE", "DAY 7", "warn", "d7")]
    for s, fn in STYLES.items():
        for hook, hi, day, kind, name in demos:
            fn(hook, hi, day, kind, out / f"{s}_{name}.jpg")
    print("ok", out)
