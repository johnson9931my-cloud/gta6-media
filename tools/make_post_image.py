#!/usr/bin/env python3
"""Make a branded 4:5 post image for @jonny_gta6.

Usage:
  make_post_image.py --bg screenshots/Vice_City_10.jpg --out posts/2026-10-28_holivar.jpg \
      --badge "ХОЛИВАР ДНЯ" --line1 "ПК" --mid "или" --line2 "КОНСОЛЬ?" [--focus 0.5] [--credit "кадр: Rockstar Games"]
  make_post_image.py --stat --out posts/x.jpg --badge "ЦИФРА ДНЯ" --line1 "25 ДНЕЙ" --line2 "до релиза GTA 6" --credit "Источник: Rockstar"

--focus: horizontal crop center 0..1 (0 = left edge, 1 = right edge) to keep faces in frame.
--stat without --bg draws a brand-colour background (for infographics / numbers).
"""
import argparse, os
from PIL import Image, ImageDraw, ImageFont, ImageEnhance

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BOLD = os.path.join(ROOT, "fonts", "DejaVuSansCondensed-Bold.ttf")
W, H = 1080, 1350
PINK = (255, 46, 140); NAVY = (20, 4, 40); YEL = (255, 214, 64); WHITE = (255, 255, 255)

def fit(t, maxw, start):
    s = start
    while s > 20 and ImageFont.truetype(BOLD, s).getlength(t) > maxw:
        s -= 2
    return ImageFont.truetype(BOLD, s)

def main():
    p = argparse.ArgumentParser()
    p.add_argument("--bg"); p.add_argument("--out", required=True)
    p.add_argument("--badge", default=""); p.add_argument("--line1", default="")
    p.add_argument("--mid", default=""); p.add_argument("--line2", default="")
    p.add_argument("--credit", default="кадр: Rockstar Games")
    p.add_argument("--focus", type=float, default=0.5)
    p.add_argument("--stat", action="store_true")
    a = p.parse_args()

    if a.bg:
        src = Image.open(os.path.join(ROOT, a.bg) if not os.path.isabs(a.bg) else a.bg).convert("RGB")
        s = max(W / src.width, H / src.height)
        im = src.resize((int(src.width * s) + 1, int(src.height * s) + 1), Image.LANCZOS)
        x = int((im.width - W) * min(max(a.focus, 0), 1))
        im = im.crop((x, 0, x + W, H))
        im = ImageEnhance.Color(im).enhance(1.2); im = ImageEnhance.Contrast(im).enhance(1.08)
    else:
        im = Image.new("RGB", (W, H), NAVY)
        d0 = ImageDraw.Draw(im)
        for y in range(H):
            t = y / H
            d0.line([(0, y), (W, y)], fill=(int(214 * (1 - t) + 20 * t), int(36 * (1 - t) + 4 * t), int(140 * (1 - t) + 40 * t)))

    ov = Image.new("RGBA", (W, H), (0, 0, 0, 0)); d = ImageDraw.Draw(ov)
    for y in range(H):
        al = 0
        if y < 360: al = int(190 * (1 - y / 360))
        if y > H - 640: al = max(al, int(235 * ((y - (H - 640)) / 640)))
        d.line([(0, y), (W, y)], fill=NAVY + (al,))
    im = Image.alpha_composite(im.convert("RGBA"), ov)
    d = ImageDraw.Draw(im)

    def center(t, f, y, fill):
        if not t: return
        w = d.textlength(t, font=f)
        d.text(((W - w) / 2, y), t, font=f, fill=fill, stroke_width=6, stroke_fill=NAVY)

    if a.badge:
        f = ImageFont.truetype(BOLD, 46); w = d.textlength(a.badge, font=f)
        d.rounded_rectangle([(W - w) / 2 - 30, 58, (W + w) / 2 + 30, 136], radius=18, fill=PINK)
        d.text(((W - w) / 2, 70), a.badge, font=f, fill=WHITE)

    big = 200 if not a.stat else 170
    center(a.line1, fit(a.line1, 960, big), H - 575, WHITE)
    if a.mid:
        center(a.mid, fit(a.mid, 900, 80), H - 375, YEL)
        center(a.line2, fit(a.line2, 960, big), H - 285, WHITE)
    else:
        center(a.line2, fit(a.line2, 960, 90), H - 330, YEL)

    foot = "@jonny_gta6" + ("  ·  " + a.credit if a.credit else "")
    f2 = fit(foot, 1000, 34); w2 = d.textlength(foot, font=f2)
    d.text(((W - w2) / 2, H - 64), foot, font=f2, fill=(232, 222, 242))

    os.makedirs(os.path.dirname(os.path.abspath(a.out)), exist_ok=True)
    im.convert("RGB").save(a.out, quality=88, optimize=True, progressive=True)
    print(a.out)

if __name__ == "__main__":
    main()
