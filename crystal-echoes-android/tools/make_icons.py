"""Draws the app icon and splash screens into resources/android/res (run once; output is committed)."""
from PIL import Image, ImageDraw, ImageFilter
import pathlib
OUT = pathlib.Path(__file__).resolve().parent.parent / 'resources' / 'android' / 'res'
BG = (13, 19, 21); CRY = (212, 195, 255); GLOW = (155, 124, 240); AMBER = (240, 163, 58); COBALT = (90, 162, 255)

def crystal(size, bg=True, scale=1.0, round_mask=False):
    S = size * 4  # supersample
    img = Image.new('RGBA', (S, S), BG + (255,) if bg else (0, 0, 0, 0))
    cx, cy = S / 2, S / 2
    h = S * 0.30 * scale; w = h * 0.66
    def diamond(dx=0, dy=0, k=1.0):
        return [(cx + dx, cy - h * k + dy), (cx + w * k + dx, cy + dy), (cx + dx, cy + h * k + dy), (cx - w * k + dx, cy + dy)]
    # echoes: two faded outlines trailing to the left, in the two player colours
    d = ImageDraw.Draw(img)
    lw = max(2, int(S * 0.018))
    d.polygon(diamond(-w * 1.05, 0, 0.82), outline=AMBER + (150,), width=lw)
    d.polygon(diamond(w * 1.05, 0, 0.82), outline=COBALT + (150,), width=lw)
    # glow
    glow = Image.new('RGBA', (S, S), (0, 0, 0, 0))
    ImageDraw.Draw(glow).polygon(diamond(k=1.12), fill=GLOW + (200,))
    glow = glow.filter(ImageFilter.GaussianBlur(S * 0.05))
    img = Image.alpha_composite(img, glow)
    d = ImageDraw.Draw(img)
    d.polygon(diamond(), fill=CRY + (255,))
    facet = Image.new('RGBA', (S, S), (0, 0, 0, 0))
    ImageDraw.Draw(facet).polygon([(cx, cy - h), (cx + w * 0.45, cy), (cx, cy + h)], fill=(255, 255, 255, 150))
    img = Image.alpha_composite(img, facet)
    img = img.resize((size, size), Image.LANCZOS)
    if round_mask:
        m = Image.new('L', (size * 4, size * 4), 0); ImageDraw.Draw(m).ellipse((0, 0, size * 4 - 1, size * 4 - 1), fill=255)
        img.putalpha(m.resize((size, size), Image.LANCZOS))
    return img

dens = {'mdpi': 48, 'hdpi': 72, 'xhdpi': 96, 'xxhdpi': 144, 'xxxhdpi': 192}
for k, px in dens.items():
    f = OUT / f'mipmap-{k}'; f.mkdir(parents=True, exist_ok=True)
    crystal(px).save(f / 'ic_launcher.png')
    crystal(px, round_mask=True).save(f / 'ic_launcher_round.png')
    crystal(int(px * 2.25), bg=False, scale=0.62).save(f / 'ic_launcher_foreground.png')  # adaptive: keep art in the safe zone

splash = {'drawable': (480, 320)}
for o, sizes in (('land', [(800, 480, 'hdpi'), (480, 320, 'mdpi'), (1280, 720, 'xhdpi'), (1600, 960, 'xxhdpi'), (1920, 1280, 'xxxhdpi')]),
                 ('port', [(480, 800, 'hdpi'), (320, 480, 'mdpi'), (720, 1280, 'xhdpi'), (960, 1600, 'xxhdpi'), (1280, 1920, 'xxxhdpi')])):
    for w, h, k in sizes: splash[f'drawable-{o}-{k}'] = (w, h)
for folder, (w, h) in splash.items():
    img = Image.new('RGBA', (w, h), BG + (255,))
    c = crystal(int(min(w, h) * 0.5), bg=False)
    img.alpha_composite(c, ((w - c.width) // 2, (h - c.height) // 2))
    f = OUT / folder; f.mkdir(parents=True, exist_ok=True)
    img.convert('RGB').save(f / 'splash.png')
print('icons written to', OUT)
