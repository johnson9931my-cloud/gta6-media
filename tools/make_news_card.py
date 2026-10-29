#!/usr/bin/env python3
"""News-style "breaking news" cards for Threads (1080x1350, 4:5).

Two templates, both drawn on top of an official Rockstar screenshot:

  shock  - tilted two-colour sticker at the top (e.g. "ШОК / КОНТЕНТ!"),
           corner badge, glitch stripes, hazard tape, red "СРОЧНЫЕ НОВОСТИ" bar,
           big tag above the bar (e.g. "GTA 6: ДАТА?") and a LIVE pill.
  tv     - TV lower third: "ПРЯМОЙ ЭФИР / LIVE" pill, red strip with a GTA 6
           block and a kicker, a big white plate with the headline and a ticker.

Example:
  python3 tools/make_news_card.py --style shock --bg content-photo/Vice_City_03.jpg \
      --out out.jpg --top1 "ШОК" --top2 "КОНТЕНТ!" --tag "GTA 6: ЦЕНА?" \
      --bar "СРОЧНЫЕ НОВОСТИ" --badge "19.11"
"""
import argparse
import os
import random

from PIL import Image, ImageDraw, ImageEnhance, ImageFilter, ImageFont

W, H = 1080, 1350
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FONTS = os.path.join(ROOT, "fonts")

RED = (226, 18, 32)
RED_DARK = (150, 6, 16)
YELLOW = (255, 196, 0)
NAVY = (14, 26, 64)
WHITE = (255, 255, 255)
BLACK = (12, 12, 14)


def font(name, size):
    return ImageFont.truetype(os.path.join(FONTS, name), size)


def fit_font(draw, text, name, max_w, start, min_size=20):
    size = start
    while size > min_size:
        f = font(name, size)
        if draw.textlength(text, font=f) <= max_w:
            return f
        size -= 2
    return font(name, min_size)


def load_bg(path, focus):
    img = Image.open(path).convert("RGB")
    scale = max(W / img.width, H / img.height)
    img = img.resize((round(img.width * scale), round(img.height * scale)), Image.LANCZOS)
    x = int((img.width - W) * focus)
    y = (img.height - H) // 2
    img = img.crop((x, y, x + W, y + H))
    img = ImageEnhance.Color(img).enhance(1.25)
    img = ImageEnhance.Contrast(img).enhance(1.1)
    img = img.filter(ImageFilter.UnsharpMask(radius=2, percent=60, threshold=2))
    return img


def vignette(img, strength=150):
    mask = Image.new("L", (W, H), 0)
    d = ImageDraw.Draw(mask)
    for i in range(60):
        a = int(strength * (1 - i / 60) ** 2)
        d.rectangle([i * 4, i * 4, W - i * 4, H - i * 4], outline=a, width=4)
    dark = Image.new("RGB", (W, H), (0, 0, 0))
    return Image.composite(dark, img, mask.filter(ImageFilter.GaussianBlur(30)))


def gradient(img, top=True, bottom=True, h_top=380, h_bot=520):
    over = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(over)
    if top:
        for y in range(h_top):
            d.line([(0, y), (W, y)], fill=(0, 0, 0, int(150 * (1 - y / h_top))))
    if bottom:
        for y in range(h_bot):
            d.line([(0, H - y), (W, H - y)], fill=(0, 0, 0, int(200 * (1 - y / h_bot))))
    return Image.alpha_composite(img.convert("RGBA"), over)


def shadow_layer(layer, offset=(10, 12), blur=10, alpha=170):
    a = layer.split()[3].point(lambda v: v * alpha // 255)
    sh = Image.new("RGBA", layer.size, (0, 0, 0, 0))
    sh.putalpha(a)
    sh = sh.filter(ImageFilter.GaussianBlur(blur))
    out = Image.new("RGBA", layer.size, (0, 0, 0, 0))
    out.alpha_composite(sh, offset)
    out.alpha_composite(layer)
    return out


def grunge(layer, seed=7, amount=260):
    """Knock small specks out of white text for a worn print look."""
    rnd = random.Random(seed)
    d = ImageDraw.Draw(layer)
    for _ in range(amount):
        x, y = rnd.randrange(layer.width), rnd.randrange(layer.height)
        r = rnd.choice([1, 1, 1, 2])
        px = layer.getpixel((x, y))
        if px[3] and px[0] > 200 and px[1] > 200 and px[2] > 200:
            d.ellipse([x - r, y - r, x + r, y + r], fill=(228, 228, 228, 255))
    return layer


def sticker(top1, top2):
    """Red box with white text over a yellow box with black text, tilted."""
    tmp = ImageDraw.Draw(Image.new("RGB", (10, 10)))
    f1 = fit_font(tmp, top1, "Montserrat-Black.ttf", 640, 190)
    f2 = fit_font(tmp, top2, "Montserrat-Black.ttf", 700, 150)
    b1 = tmp.textbbox((0, 0), top1, font=f1)
    b2 = tmp.textbbox((0, 0), top2, font=f2)
    w1, h1 = b1[2] - b1[0], b1[3] - b1[1]
    w2, h2 = b2[2] - b2[0], b2[3] - b2[1]
    pad = 34
    lw = max(w1 + 2 * pad + 60, w2 + 2 * pad) + 40
    lh = h1 + h2 + 4 * pad + 30
    layer = Image.new("RGBA", (lw, lh), (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)
    r1 = [0, 0, w1 + 2 * pad + 60, h1 + 2 * pad]
    d.rectangle(r1, fill=RED)
    d.text((pad + 30 - b1[0], pad - b1[1]), top1, font=f1, fill=WHITE)
    y2 = r1[3] - 6
    r2 = [20, y2, 20 + w2 + 2 * pad, y2 + h2 + 2 * pad]
    d.rectangle(r2, fill=YELLOW)
    d.text((20 + pad - b2[0], y2 + pad - b2[1]), top2, font=f2, fill=BLACK)
    layer = grunge(layer)
    layer = layer.rotate(4, resample=Image.BICUBIC, expand=True)
    return shadow_layer(layer)


def outlined_text(d, xy, text, f, fill, stroke, sw, anchor="la"):
    d.text(xy, text, font=f, fill=fill, stroke_width=sw, stroke_fill=stroke, anchor=anchor)


def gradient_text(text, f, colors, stroke=(40, 10, 60), sw=6):
    tmp = ImageDraw.Draw(Image.new("RGB", (10, 10)))
    b = tmp.textbbox((0, 0), text, font=f, stroke_width=sw)
    w, h = b[2] - b[0] + 20, b[3] - b[1] + 20
    mask = Image.new("L", (w, h), 0)
    ImageDraw.Draw(mask).text((10 - b[0], 10 - b[1]), text, font=f, fill=255)
    grad = Image.new("RGBA", (w, h))
    gd = ImageDraw.Draw(grad)
    for y in range(h):
        t = y / max(1, h - 1)
        c = tuple(int(colors[0][i] + (colors[1][i] - colors[0][i]) * t) for i in range(3))
        gd.line([(0, y), (w, y)], fill=c + (255,))
    out = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    ImageDraw.Draw(out).text((10 - b[0], 10 - b[1]), text, font=f, fill=stroke + (255,),
                             stroke_width=sw, stroke_fill=stroke + (255,))
    fill = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    fill.paste(grad, (0, 0), mask)
    out.alpha_composite(fill)
    return shadow_layer(out, offset=(6, 8), blur=8)


def hazard(d, x0, y0, x1, y1, step=34):
    d.rectangle([x0, y0, x1, y1], fill=YELLOW)
    hgt = y1 - y0
    x = x0 - hgt
    while x < x1:
        d.polygon([(x, y1), (x + hgt, y0), (x + hgt + step / 2, y0), (x + step / 2, y1)], fill=BLACK)
        x += step


def glitch(img, seed=3, n=26):
    rnd = random.Random(seed)
    d = ImageDraw.Draw(img)
    palette = [(255, 40, 60, 210), (40, 230, 255, 210), (255, 220, 40, 210), (120, 255, 120, 190),
               (255, 255, 255, 200)]
    for _ in range(n):
        y = rnd.choice([rnd.randrange(80, 300), rnd.randrange(H - 520, H - 40)])
        x = rnd.choice([rnd.randrange(0, 160), rnd.randrange(W - 240, W - 20)])
        w = rnd.randrange(20, 120)
        d.rectangle([x, y, x + w, y + rnd.choice([3, 4, 6])], fill=rnd.choice(palette))
    # subtle scanlines
    over = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    od = ImageDraw.Draw(over)
    for y in range(0, H, 4):
        od.line([(0, y), (W, y)], fill=(0, 0, 0, 18))
    img.alpha_composite(over)


def pill(d, x, y, text, f, bg=RED, fg=WHITE, dot=True, anchor_right=False):
    tw = d.textlength(text, font=f)
    pw = tw + (64 if dot else 40)
    ph = f.size + 26
    if anchor_right:
        x = x - pw
    d.rounded_rectangle([x, y, x + pw, y + ph], radius=12, fill=bg)
    tx = x + 20
    if dot:
        d.ellipse([x + 18, y + ph / 2 - 8, x + 34, y + ph / 2 + 8], fill=fg)
        tx = x + 44
    d.text((tx, y + ph / 2), text, font=f, fill=fg, anchor="lm")
    return pw, ph


def style_shock(img, a):
    img = gradient(img, h_top=420, h_bot=560)
    st = sticker(a.top1, a.top2)
    img.alpha_composite(st, (18, 40))
    d = ImageDraw.Draw(img)
    if a.badge:
        fb = font("Montserrat-Black.ttf", 46)
        tw = d.textlength(a.badge, font=fb)
        d.rounded_rectangle([W - 52 - tw - 40, 44, W - 52, 44 + 92], radius=16, fill=RED_DARK)
        d.text((W - 52 - tw - 20, 90), a.badge, font=fb, fill=WHITE, anchor="lm")
    glitch(img, seed=len(a.top1 + a.tag))
    d = ImageDraw.Draw(img)
    # bottom block
    bar_y = H - 170
    hazard(d, 0, bar_y - 34, 430, bar_y - 6)
    hazard(d, W - 330, bar_y + 112, W, bar_y + 140)
    d.rectangle([0, bar_y, W, bar_y + 110], fill=RED)
    d.rectangle([0, bar_y + 96, W, bar_y + 110], fill=RED_DARK)
    fbar = fit_font(d, a.bar, "Montserrat-Black.ttf", W - 120, 76)
    d.text((W // 2, bar_y + 50), a.bar, font=fbar, fill=WHITE, anchor="mm")
    # LIVE pill right above the bar
    pill(d, W - 30, bar_y - 86, "LIVE", font("Montserrat-Black.ttf", 40), anchor_right=True)
    # big tag
    ft = fit_font(d, a.tag, "Oswald-Bold.ttf", W - 100, 130)
    tag = gradient_text(a.tag, ft, [(255, 255, 255), (190, 225, 255)])
    img.alpha_composite(tag, (W - tag.width - 30, bar_y - 100 - tag.height))
    return img


def style_tv(img, a):
    img = gradient(img, h_top=220, h_bot=640)
    d = ImageDraw.Draw(img)
    fp = font("Montserrat-ExtraBold.ttf", 34)
    pill(d, 40, 40, a.live, fp)
    base = H - 470
    pill(d, 40, base, a.live, fp)
    # red strip with GTA 6 block + kicker
    ry = base + 84
    d.rectangle([40, ry, W - 120, ry + 96], fill=RED)
    fg = font("RussoOne-Regular.ttf", 70)
    outlined_text(d, (70, ry + 48), "GTA 6", fg, WHITE, BLACK, 6, anchor="lm")
    gx = 70 + d.textlength("GTA 6", font=fg) + 40
    fk = fit_font(d, a.kicker, "Montserrat-ExtraBold.ttf", W - 160 - gx, 52)
    d.text((gx, ry + 48), a.kicker, font=fk, fill=WHITE, anchor="lm")
    # white plate with headline
    py = ry + 96
    d.rectangle([40, py, W - 40, py + 200], fill=WHITE)
    fh = fit_font(d, a.headline, "Montserrat-Black.ttf", W - 140, 140)
    d.text((70, py + 100), a.headline, font=fh, fill=NAVY, anchor="lm")
    if a.sub:
        fs = font("Montserrat-ExtraBold.ttf", 38)
        d.text((W - 70, py + 190), a.sub, font=fs, fill=NAVY, anchor="rb")
    # ticker
    ty = py + 200
    d.rectangle([40, ty, W - 40, ty + 64], fill=NAVY)
    ftk = font("Montserrat-ExtraBold.ttf", 32)
    tick = f"{a.ticker}   •   {a.ticker}   •   {a.ticker}"
    d.text((60, ty + 32), tick, font=ftk, fill=WHITE, anchor="lm")
    d.rectangle([W - 40, ty, W, ty + 64], fill=(0, 0, 0, 0))
    return img


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--style", choices=["shock", "tv"], default="shock")
    p.add_argument("--bg", required=True)
    p.add_argument("--out", required=True)
    p.add_argument("--focus", type=float, default=0.5)
    # shock
    p.add_argument("--top1", default="ШОК")
    p.add_argument("--top2", default="КОНТЕНТ!")
    p.add_argument("--tag", default="GTA 6")
    p.add_argument("--bar", default="СРОЧНЫЕ НОВОСТИ")
    p.add_argument("--badge", default="")
    # tv
    p.add_argument("--live", default="ПРЯМОЙ ЭФИР / LIVE")
    p.add_argument("--kicker", default="НОВЫЕ ПОДРОБНОСТИ")
    p.add_argument("--headline", default="НОВОСТЬ ДНЯ!")
    p.add_argument("--sub", default="")
    p.add_argument("--ticker", default="ВСЁ О GTA 6 ДО РЕЛИЗА")
    p.add_argument("--credit", default="кадр: Rockstar Games")
    a = p.parse_args()

    img = vignette(load_bg(a.bg, a.focus)).convert("RGBA")
    img = style_shock(img, a) if a.style == "shock" else style_tv(img, a)
    d = ImageDraw.Draw(img)
    fc = font("Montserrat-ExtraBold.ttf", 22)
    if a.style == "shock":
        xy, anc = (24, H - 12), "ld"
    else:
        xy, anc = (W - 24, H - 12), "rd"
    d.text(xy, f"@jonny_gta6 · {a.credit}", font=fc, fill=(255, 255, 255, 230),
           anchor=anc, stroke_width=2, stroke_fill=(0, 0, 0))
    img.convert("RGB").save(a.out, "JPEG", quality=90)
    print("OK", a.out)


if __name__ == "__main__":
    main()
