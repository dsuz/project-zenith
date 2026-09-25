# 魔法使いのプロトタイプ用スプライトシートを生成する
# 使い方: pip install pillow && python3 Tools/Sprites/wizard.py Assets/Sprite/Characters/Wizard.png preview.png [日本語フォント.ttf]
from PIL import Image, ImageDraw, ImageFilter, ImageFont
import sys

S = 4          # supersampling
F = 100        # frame size (px) = 1 unit at PPU 100
OL = (28, 24, 48, 255)

ROBE, ROBE_D = (74, 91, 214, 255), (52, 64, 168, 255)
HAT, HAT_L = (91, 63, 168, 255), (122, 92, 209, 255)
BAND, STAR = (232, 193, 74, 255), (255, 226, 110, 255)
SKIN = (242, 194, 155, 255)
BOOT = (107, 66, 38, 255)
WOOD = (138, 90, 43, 255)
ORB = (111, 243, 255, 255)
HAIR = (200, 200, 210, 255)

def canvas():
    return Image.new("RGBA", (F * S, F * S), (0, 0, 0, 0))

def ell(d, cx, cy, rx, ry, fill, w=1.2, ol=OL):
    d.ellipse([(cx - rx) * S, (cy - ry) * S, (cx + rx) * S, (cy + ry) * S],
              fill=fill, outline=ol, width=int(w * S) if ol else 0)

def line(d, p, q, width, fill, ol=True):
    pts = [(p[0] * S, p[1] * S), (q[0] * S, q[1] * S)]
    if ol:
        d.line(pts, fill=OL, width=int((width + 2.4) * S))
        for c in (p, q):
            r = (width + 2.4) / 2
            d.ellipse([(c[0] - r) * S, (c[1] - r) * S, (c[0] + r) * S, (c[1] + r) * S], fill=OL)
    d.line(pts, fill=fill, width=int(width * S))
    for c in (p, q):
        r = width / 2
        d.ellipse([(c[0] - r) * S, (c[1] - r) * S, (c[0] + r) * S, (c[1] + r) * S], fill=fill)

def star(d, cx, cy, r, fill):
    import math
    pts = []
    for i in range(10):
        a = -math.pi / 2 + i * math.pi / 5
        rr = r if i % 2 == 0 else r * 0.45
        pts.append(((cx + rr * math.cos(a)) * S, (cy + rr * math.sin(a)) * S))
    d.polygon(pts, fill=fill, outline=OL, width=int(0.6 * S))

def orb(img, cx, cy, r=5.5):
    glow = canvas()
    gd = ImageDraw.Draw(glow)
    ell(gd, cx, cy, r * 1.8, r * 1.8, (111, 243, 255, 90), ol=None)
    glow = glow.filter(ImageFilter.GaussianBlur(2 * S))
    img.alpha_composite(glow)
    d = ImageDraw.Draw(img)
    ell(d, cx, cy, r, r, ORB)
    ell(d, cx - r * 0.35, cy - r * 0.35, r * 0.35, r * 0.35, (255, 255, 255, 230), ol=None)

def hat(d, cx=50, cy=50):
    ell(d, cx, cy, 21, 21, HAT)                  # brim
    ell(d, cx, cy, 13, 13, BAND, w=1.0)          # band
    ell(d, cx, cy, 11, 11, HAT_L)                # crown
    ell(d, cx - 3, cy - 3, 5, 5, (150, 122, 230, 255), ol=None)  # highlight near tip
    star(d, cx, cy, 5, STAR)

def upright(feet, swing):
    """feet: 'even' | 'right' | 'left'. Character faces up (+Y in Unity)."""
    base = canvas()
    d = ImageDraw.Draw(base)
    ell(d, 50, 54, 30, 26, (0, 0, 0, 55), ol=None)   # shadow

    front, back = 27, 73
    if feet == "even":
        lf, rf = 33, 33
    elif feet == "right":
        lf, rf = back, front
    else:
        lf, rf = front, back
    ell(d, 41, lf, 6, 9, BOOT)
    ell(d, 59, rf, 6, 9, BOOT)

    # upper body on its own layer so it can twist with the stride
    body = canvas()
    b = ImageDraw.Draw(body)
    ell(b, 50, 53, 24, 20, ROBE_D)          # robe skirt
    ell(b, 50, 51, 27, 15, ROBE)            # shoulders

    # left arm (always relaxed)
    ell(b, 25, 51, 8, 8, ROBE)
    ell(b, 25, 45, 4.5, 4.5, SKIN)

    if swing:
        # right arm thrust forward, staff pointing ahead
        line(b, (70, 50), (68, 28), 12, ROBE)
        ell(b, 68, 26, 5, 5, SKIN)
        line(b, (69, 40), (64, 15), 3.6, WOOD)
    else:
        ell(b, 75, 51, 8, 8, ROBE)
        ell(b, 75, 45, 4.5, 4.5, SKIN)
        line(b, (75, 49), (79, 40), 3.6, WOOD)  # staff held upright, seen from above

    hat(b)
    if swing:
        ell(b, 68, 26, 5, 5, SKIN)            # hand stays above brim
        orb(body, 64, 14)
    else:
        orb(body, 79, 39)

    twist = {"even": 0, "right": -7, "left": 7}[feet]
    if twist:
        body = body.rotate(twist, resample=Image.BICUBIC, center=(50 * S, 52 * S))
    base.alpha_composite(body)
    return base

def fallen():
    img = canvas()
    d = ImageDraw.Draw(img)
    ell(d, 50, 60, 22, 34, (0, 0, 0, 55), ol=None)
    # staff dropped on the ground
    line(d, (32, 94), (16, 71), 3.6, WOOD)
    ell(d, 44, 88, 6, 8, BOOT)
    ell(d, 57, 90, 6, 8, BOOT)
    # sprawled arms
    line(d, (38, 46), (22, 30), 11, ROBE)
    line(d, (62, 46), (78, 32), 11, ROBE)
    ell(d, 21, 28, 4.5, 4.5, SKIN)
    ell(d, 79, 30, 4.5, 4.5, SKIN)
    ell(d, 50, 62, 18, 27, ROBE_D)          # body lying face down
    ell(d, 50, 48, 21, 13, ROBE)            # shoulders
    ell(d, 50, 30, 10, 10, HAIR)            # bare head (hat fell off)
    ell(d, 50, 27, 5, 4, (225, 225, 235, 255), ol=None)
    orb(img, 16, 70)
    # hat lying on its side
    hd = ImageDraw.Draw(img)
    ell(hd, 83, 80, 14, 9, HAT)
    hd.polygon([(76 * S, 78 * S), (90 * S, 78 * S), (97 * S, 62 * S)], fill=HAT_L, outline=OL, width=int(1.2 * S))
    line(hd, (76, 78), (90, 78), 2, BAND, ol=False)
    return img

frames = [
    upright("even", False), upright("even", True),
    upright("right", False), upright("right", True),
    upright("left", False), upright("left", True),
    fallen(),
]
frames = [f.resize((F, F), Image.LANCZOS) for f in frames]

sheet = Image.new("RGBA", (F * len(frames), F), (0, 0, 0, 0))
for i, f in enumerate(frames):
    sheet.paste(f, (i * F, 0))
sheet.save(sys.argv[1])

# labelled preview on a checker background
labels = ["0 立/杖立", "1 立/振る", "2 右足前/杖立", "3 右足前/振る", "4 左足前/杖立", "5 左足前/振る", "6 倒れ"]
Z = 3
pv = Image.new("RGBA", (F * Z * 7, F * Z + 40), (245, 245, 245, 255))
pd = ImageDraw.Draw(pv)
for i in range(7):
    for y in range(0, F * Z, 30):
        for x in range(0, F * Z, 30):
            if (x // 30 + y // 30) % 2:
                pd.rectangle([i * F * Z + x, y, i * F * Z + x + 29, y + 29], fill=(225, 225, 225, 255))
pv.alpha_composite(sheet.resize((F * Z * 7, F * Z), Image.LANCZOS))
try:
    font = ImageFont.truetype(sys.argv[3], 22)
except Exception:
    font = ImageFont.load_default()
for i, t in enumerate(labels):
    pd.text((i * F * Z + 10, F * Z + 8), t, fill=(30, 30, 30, 255), font=font)
    if i:
        pd.line([(i * F * Z, 0), (i * F * Z, F * Z + 40)], fill=(180, 180, 180, 255), width=2)
pv.save(sys.argv[2])
