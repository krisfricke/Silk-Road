# gen_gulf_exhibit.py -- the Gulf routes exhibition map (Kris's Twitter exhibit).
# Rebuilt + SAVED PERMANENTLY 8/03 after the v6 one-off died with /tmp (Ozymandias rule:
# exhibit recipes live in files, not in shell history). Reads routes_master.json geometry
# live, so route restructures (e.g. Basra|Shiraz replacing Baghdad|Shiraz) flow through
# automatically -- just update LAND_LEGS/HALTS below if the CAST changes.
# Usage: python3 _gulf_stage.py 0 ; python3 _gulf_stage.py 1 ; python3 gen_gulf_exhibit.py  (cwd = Maps/)
import json, math, re
import numpy as np
from PIL import Image, ImageDraw, ImageFont

src = open('gen_setout_1271.py').read()
ns = {}
exec(src[:src.index('def slug(')], ns)
gebco_relief = ns['gebco_relief']; GEO = ns['GEO']; LL = ns['LL']
def geom(a, b):
    k = '|'.join(sorted([a, b]))
    if k in GEO: return GEO[k]
    raise KeyError(k)

W, E, S0, N = 35.2, 64.0, 25.0, 37.8
OW = 2000
OH = int(OW * (N - S0) / ((E - W) * math.cos(math.radians((S0 + N) / 2))))
print('frame', OW, OH)

# BAKE NOTE: a full-frame gebco_relief here takes >45s (the shell call cap) - bake the two
# lon-halves first via _gulf_stage.py 0 / 1 (separate calls), which this picks up and stitches.
import os
if os.path.exists('_gulf_bg_0.npy') and os.path.exists('_gulf_bg_1.npy'):
    im = Image.fromarray(np.hstack([np.load('_gulf_bg_0.npy'), np.load('_gulf_bg_1.npy')]))
else:
    bg = gebco_relief(W, E, S0, N, OW, OH)
    im = bg if isinstance(bg, Image.Image) else Image.fromarray(np.asarray(bg, np.uint8))
im = im.convert('RGB')
d = ImageDraw.Draw(im)

def px(lon, lat):
    return ((lon - W) / (E - W) * OW, (N - lat) / (N - S0) * OH)

INK = (58, 42, 30)
ROAD = (118, 52, 26)
SEA = (52, 86, 112)
PARCH = (239, 226, 194)

def dashline(pts, color, width, on, off):
    # arc-length dasher (MAP_NOTES doctrine: dash in px space along the polyline, no masks)
    P = [px(*p) for p in pts]
    segs = []
    for i in range(1, len(P)):
        x0, y0 = P[i-1]; x1, y1 = P[i]
        L = math.hypot(x1-x0, y1-y0)
        if L > 0: segs.append((x0, y0, x1, y1, L))
    t = 0.0
    for x0, y0, x1, y1, L in segs:
        a = 0.0
        while a < L:
            ph = (t + a) % (on + off)
            if ph < on:
                b = min(L, a + (on - ph))
                f0, f1 = a / L, b / L
                d.line([x0+(x1-x0)*f0, y0+(y1-y0)*f0, x0+(x1-x0)*f1, y0+(y1-y0)*f1],
                       fill=color, width=width)
                a = b
            else:
                a = min(L, a + (on + off - ph))
        t += L

F_T = ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSerif-Bold.ttf', 46)
F_S = ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSerif-Italic.ttf', 26)
F_C = ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSerif-Bold.ttf', 30)
F_H = ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSerif-Italic.ttf', 22)

def st(xy, txt, f, fill):
    x, y = xy
    for dx in (-2, 0, 2):
        for dy in (-2, 0, 2):
            if dx or dy: d.text((x+dx, y+dy), txt, font=f, fill=PARCH)
    d.text((x, y), txt, font=f, fill=fill)

LAND_LEGS = ['Aleppo|Baghdad', 'Baghdad|Damascus', 'Aleppo|Damascus', 'Baghdad|Basra',
             'Basra|Shiraz', 'Hormuz|Shiraz', 'Shiraz|Yazd', 'Kerman|Yazd',
             'Hormuz|Kerman', 'Herat|Kerman', 'Varamin|Yazd']
SEA_LEGS = ['Basra|Kish', 'Hormuz|Kish']

CH = json.load(open('setout_charts_1271.json'))
def sea_geom(k):
    if k in GEO: return GEO[k]
    c = CH['so_hormuz']
    return ns['px2ll'](c['sealegs'][k], c['geo'], c['vbw'], c['vbh'])

ns['marsh_hatch'](im, (W,E,S0,N))   # al-Bata'ih + Hawizeh tussocks, under the routes

for k in SEA_LEGS:
    dashline(sea_geom(k), SEA, 4, 12, 9)
for k in LAND_LEGS:
    a, b = k.split('|')
    dashline(geom(a, b), ROAD, 4, 16, 10)

HALTS = {'Wasit': (46.3, 32.2), 'Ahwaz': (48.68, 31.33), 'Arrajan': (50.25, 30.65),
         'Lar': (54.34, 27.68), 'Abarkuh': (53.28, 31.13), 'Kashan': (51.44, 33.98),
         "Na'in": (53.08, 32.86), 'Palmyra': (38.27, 34.55), 'Homs': (36.72, 34.73),
         'Hama': (36.75, 35.13), 'the Lut rim': (59.88, 30.88)}
for nm, llh in HALTS.items():
    x, y = px(*llh)
    if x < -20 or x > OW+20 or y < -20 or y > OH+20: continue
    d.ellipse([x-5, y-5, x+5, y+5], fill=PARCH, outline=(90, 60, 30), width=2)
    st((x+9, y-30), nm, F_H, (92, 64, 40))

CITY_LBL = {'Aleppo': (14, -44), 'Damascus': (14, -44), 'Baghdad': (14, -44),
            'Basra': (14, 10), 'Shiraz': (14, -44), 'Hormuz': (14, 12),
            'Kish': (-72, 14), 'Yazd': (14, -44), 'Kerman': (14, -44),
            'Varamin': (14, -44), 'Herat': (-100, -44)}
for nm, (dx, dy) in CITY_LBL.items():
    x, y = px(*LL[nm])
    if x < -20 or x > OW+20 or y < -20 or y > OH+20: continue
    d.ellipse([x-9, y-9, x+9, y+9], fill=(192, 36, 26), outline=PARCH, width=3)
    st((x+dx, y+dy), nm, F_C, INK)

st((36, 26), 'The Gulf & the Fars Road — 1271', F_T, INK)
st((40, OH - 58), "Baghdad · Wasit · Basra · Ahwaz · Arrajan · Shiraz — the road-books' way east; the marshes allow no shorter", F_S, (92, 64, 40))

im.save('gulf_routes_1271.jpg', quality=88)
print('gulf exhibit rebuilt (Basra|Shiraz edition)', OW, OH)
