"""Vertical (1080x1920) covers for Shorts, same look as thumbnails style C."""
import pathlib
from PIL import Image, ImageDraw, ImageFilter
from videoengine.settings import SERIES
from videoengine.thumbnails import font, fit, draw_lines, BLACK

W, H = 1080, 1920


def cover(hook, hi, num, out):
    im = Image.new("RGB", (W, H))
    px = im.load()
    for y in range(H):
        t = y / H
        c = (int(70 + 10 * t), int(30 + 60 * t), int(140 + 90 * t))
        for x in range(W):
            px[x, y] = c
    d = ImageDraw.Draw(im)
    f = font(BLACK, 760)
    bb = d.textbbox((0, 0), num, font=f)
    d.text((W - 70 - bb[2], H - 90 - bb[3]), num, font=f, fill=None,
           stroke_width=8, stroke_fill=(150, 130, 235))
    lines = hook.split("|")
    fnt = fit(d, lines, BLACK, W - 140, 230)
    y = 520
    glow = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    draw_lines(ImageDraw.Draw(glow), lines, None, 70, y, fnt, (0, 255, 200, 255), (0, 0, 0), (0, 0, 0), shadow=False)
    g = glow.filter(ImageFilter.GaussianBlur(16))
    im.paste(g, (0, 0), g)
    d = ImageDraw.Draw(im)
    draw_lines(d, lines, hi, 70, y, fnt, (255, 255, 255), (20, 10, 60), (0, 255, 200), shadow=False)
    tf = font(BLACK, 46)
    tag = f"DAY {num} · FULL LESSON LINKED"
    tw = d.textlength(tag, font=tf)
    d.rounded_rectangle([70, 290, 70 + tw + 50, 290 + 46 + 36], 18, fill=(255, 255, 255))
    d.text((95, 305), tag, font=tf, fill=(60, 30, 140))
    d.text((70, 180), SERIES.upper(), font=font(BLACK, 48), fill=(255, 255, 255))
    im.save(out, quality=90)


if __name__ == "__main__":
    out = pathlib.Path.cwd() / "output" / "covers"
    out.mkdir(parents=True, exist_ok=True)
    cover("MCP vs|FUNCTION|Calling", "FUNCTION", "4", out / "example_cover.jpg")
    print("ok", out)
