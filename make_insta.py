"""Generate today's CraveSave Instagram deal graphic (1080x1350)."""
from PIL import Image, ImageDraw, ImageFont

W, H = 1080, 1350
GF = "/usr/share/fonts/truetype/google-fonts/"
DV = "/usr/share/fonts/truetype/dejavu/"

def F(path, size): return ImageFont.truetype(path, size)
poppins_b  = lambda s: F(GF+"Poppins-Bold.ttf", s)
poppins_m  = lambda s: F(GF+"Poppins-Medium.ttf", s)
poppins_l  = lambda s: F(GF+"Poppins-Light.ttf", s)
mono       = lambda s: F(DV+"DejaVuSansMono.ttf", s)
mono_b     = lambda s: F(DV+"DejaVuSansMono-Bold.ttf", s)

# palette
INK   = (26, 31, 28)
CREAM = (246, 241, 227)
MUTE  = (120, 120, 110)
SAVE  = (10, 135, 84)      # money green
RED   = (214, 64, 44)      # discount stamp
NOON  = (243, 211, 0)      # noon yellow

# today's deals (corrected prices)
DEALS = [
    ("Samsung Galaxy S25 Ultra", 5099, 2799, 45),
    ("PS5 Console (New) +ADCB AED250", 2300, 1850, 20),
    ("WHOOP 5.0 + 12-mo Membership", 1379, 1049, 24),
    ("Echo Dot (5th Gen)", 229, 149, 35),
    ("WaterWipes 720 Wipes (12 packs)", 220, 180, 18),
]
TOTAL_SAVED = sum(o - n for _, o, n, _ in DEALS)   # 3200

img = Image.new("RGB", (W, H))
d = ImageDraw.Draw(img)

# vertical gradient background (deep teal-green)
top, bot = (7, 59, 44), (2, 22, 16)
for y in range(H):
    t = y / H
    d.line([(0, y), (W, y)],
           fill=tuple(int(top[i] + (bot[i]-top[i])*t) for i in range(3)))

def spaced(draw, xy, text, font, fill, sp):
    x, y = xy
    for ch in text:
        draw.text((x, y), ch, font=font, fill=fill)
        x += draw.textlength(ch, font=font) + sp
    return x

def perforate(draw, x0, x1, y, up=True):
    step = 26
    x = x0
    while x < x1:
        cx = x + step/2
        draw.ellipse([cx-13, y-13, cx+13, y+13],
                     fill=(7, 59, 44) if up else (3, 25, 18))
        x += step

# ── receipt card ──
CX0, CX1, CY0, CY1 = 60, 1020, 78, 1272
d.rounded_rectangle([CX0, CY0, CX1, CY1], radius=8, fill=CREAM)
perforate(d, CX0, CX1, CY0)          # top perforation
perforate(d, CX0, CX1, CY1, up=False)
PAD = 58
ix0, ix1 = CX0 + PAD, CX1 - PAD

# header
spaced(d, (ix0, 132), "CRAVESAVE  ·  ABU DHABI", mono_b(24), INK, 2)
d.text((ix0, 168), "TODAY'S DEALS", font=poppins_b(82), fill=INK)
d.text((ix0, 270), "SAT 28 JUN 2026   —   AMAZON.AE", font=mono(24), fill=MUTE)

def dashed(y):
    x = ix0
    while x < ix1:
        d.line([(x, y), (min(x+14, ix1), y)], fill=(190, 184, 168), width=3)
        x += 26

dashed(322)

# line items
ry = 348
ROW = 120
for title, old, new, pct in DEALS:
    d.text((ix0, ry), title, font=poppins_m(31), fill=INK)
    # prices
    py = ry + 50
    oldtxt = f"AED {old:,}"
    d.text((ix0, py), oldtxt, font=mono(30), fill=MUTE)
    ow = d.textlength(oldtxt, font=mono(30))
    d.line([(ix0, py+18), (ix0+ow, py+18)], fill=RED, width=3)   # strikethrough
    newtxt = f"  ➜  AED {new:,}"
    d.text((ix0+ow, py), newtxt, font=mono_b(30), fill=SAVE)
    # red % badge (right aligned)
    bt = f"-{pct}%"
    bw = d.textlength(bt, font=poppins_b(38)) + 36
    d.rounded_rectangle([ix1-bw, ry+8, ix1, ry+70], radius=10, fill=RED)
    d.text((ix1-bw+18, ry+12), bt, font=poppins_b(38), fill=CREAM)
    ry += ROW
    if title != DEALS[-1][0]:
        dashed(ry-22)

# total saved (hero)
dashed(ry-4)
d.text((ix0, ry+10), "YOU SAVE UP TO", font=mono_b(28), fill=INK)
d.text((ix0, ry+42), f"AED {TOTAL_SAVED:,}", font=poppins_b(78), fill=SAVE)

# noon coupon stub
sy = ry + 144
d.rounded_rectangle([ix0, sy, ix1, sy+72], radius=10, fill=NOON)
d.text((ix0+24, sy+16), "NOON  +10% OFF", font=poppins_b(34), fill=INK)
code = "CODE  ZOQJN"
cw = d.textlength(code, font=mono_b(34))
d.text((ix1-cw-24, sy+18), code, font=mono_b(34), fill=INK)

# footer
fy = sy + 86
d.text((ix0, fy), "@cravesave.ad   ·   Link in bio", font=poppins_m(27), fill=INK)
d.text((ix0, fy+36),
       "Affiliate links · As an Amazon Associate I earn from qualifying purchases.",
       font=poppins_l(18), fill=MUTE)

img.save("insta_deals.png")
print("saved insta_deals.png  total saved:", TOTAL_SAVED)
