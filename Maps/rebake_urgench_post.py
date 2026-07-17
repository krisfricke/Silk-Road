# rebake_urgench_post.py - RECIPE v6 (Kris 7/17): post-passes for so_urgench after generator rebake.
# GOLD (238,223,163) sampled from in-use khwarezm dune sea @60.5E,39.6N.
# Dune seas 0.80 + stipple; clay/stony desert 0.55 no stipple (climate_biome P<150mm floor).
# v3: Khwarezm oasis (Kris's N polygon) EXCLUDED - wears standard steppe; Amu corridor excluded
# with a faint riparian green ribbon along the drawn river; trans-Amu gap + Mangyshlak added as
# desert; Karakum extended west; Kyzylkum extended toward the Bukhara road.
# v4 (Kris): deserts CONNECT across the Amu (corridor 13px, ribbon 9px both banks); ZAUNGUZ
# (trans-Unguz Karakum) joins Ustyurt to Karakum; OASIS = the delta-Khwarezm wedge (west bound
# ~Pulzhay 58.4E, south ~Sarygamysh 41.8N); the sor-lake at 63.19E,41.18N is a salt flat, wet
# only in the _spring seasonal (April fill).
# v5 (Kris: 'reapply to the base relief so it looks natural'): the wash is now a RELIEF-PRESERVING
# recolor - per-pixel luminance ratio against a sigma-25 local mean carries every ridge, contour
# and blur into the gold instead of skipping around them (old grad>40 exclusion removed; only
# hard rock grad>90, water, green and snow are spared). The Amu corridor exclusion is GONE -
# the deserts truly meet at the banks and the green ribbon is painted over the top after.
# v6 (Kris): OASIS southern bound corrected to Sarygamysh latitude (~41.75N) - my v4/v5 wedge
# dangled to 40.7N and smothered the Amu crossing; below Khwarezm the river runs through open
# desert with only the tugai ribbon. AND lake AYDAR (66.9E,40.95N) is a 1271 ANACHRONISM -
# modern Aydarkul formed 1969 from Chardara overflow; dried to salt flat, wet only in _spring
# (the Syr's exceptional flood years). TODO: migrate Aydar into anachronize() at the source.
import json, re, random
import numpy as np, cv2
from PIL import Image

GOLD = np.array((238,223,163), np.float32)
RIPAR = np.array((150,165,105), np.float32)
KYZYLKUM = [(59.8,43.8),(61.5,44.3),(63.5,44.3),(65.5,43.6),(66.8,42.6),(67.5,41.7),(66.5,40.9),(64.6,40.3),(63.0,40.5),(61.7,41.6),(60.3,42.5)]
KARAKUM  = [(52.5,41.2),(56.0,41.6),(58.5,41.5),(60.5,41.0),(61.5,40.0),(60.5,38.8),(57.5,37.8),(54.0,37.8),(52.3,39.0)]
USTYURT  = [(52.6,48.3),(56.5,47.9),(59.5,47.4),(61.8,46.2),(61.4,43.9),(59.9,43.2),(58.9,42.5),(57.0,42.3),(55.2,42.6),(53.4,43.2),(52.4,44.5),(52.3,46.5)]
ZAUNGUZ  = [(52.2,44.6),(55.6,44.3),(57.3,43.3),(57.6,42.2),(57.0,41.4),(54.5,41.3),(52.6,41.8),(52.2,43.5)]  # trans-Unguz Karakum: Ustyurt joins the Karakum
MANGYSH  = [(50.7,44.7),(53.5,44.6),(54.3,43.8),(53.3,43.0),(51.6,43.2),(50.5,43.9)]
OASIS_N  = [(58.3,44.4),(59.6,44.4),(60.4,43.0),(60.8,42.3),(60.7,41.75),(59.6,41.7),(58.6,41.75),(57.8,41.8),(57.5,42.6),(57.9,43.4)]  # delta-Khwarezm wedge; SOUTH BOUND = Sarygamysh lat 41.75 (Kris) - below it the desert owns both banks
AMU_BB   = (58.6, 62.7, 38.9, 42.8)
LAKES = (54.55, 55.50, 45.05, 46.55)
SORLAKE = (62.95, 63.45, 40.98, 41.40)   # dry salt flat; wet only in spring (Kris: fill it every April)
AYDAR   = (65.75, 67.65, 40.55, 41.35)   # dry in 1271 (Aydarkul is a 1969 artifact); wet only in spring

def wat(a):
    return (a[:,:,2].astype(int) > a[:,:,0] + 15) & (a[:,:,2] > 120)

def build_excl(a, P):
    H, W = a.shape[:2]
    ex = np.zeros((H, W), np.uint8)
    cv2.fillPoly(ex, [np.array([P(lo,la) for lo,la in OASIS_N], np.int32)], 1)
    x0,y0 = P(AMU_BB[0],AMU_BB[3]); x1,y1 = P(AMU_BB[1],AMU_BB[2])
    bb = np.zeros((H, W), np.uint8)
    bb[max(0,y0):min(H,y1), max(0,x0):min(W,x1)] = 1
    amu = (wat(a).astype(np.uint8) & bb)
    # v5: no corridor exclusion - the deserts meet at the banks; the ribbon overlays after
    return ex, amu

def desert_wash(a, P, polys, alpha, stipple, excl, seed=11):
    H, W = a.shape[:2]
    mask = np.zeros((H, W), np.uint8)
    for poly in polys:
        cv2.fillPoly(mask, [np.array([P(lo,la) for lo,la in poly], np.int32)], 1)
    mask[excl > 0] = 0
    m = cv2.GaussianBlur(mask.astype(np.float32), (0,0), 10)
    g = cv2.cvtColor(a, cv2.COLOR_RGB2GRAY).astype(np.float32)
    grad = cv2.boxFilter(np.abs(cv2.Sobel(g,cv2.CV_32F,1,0))+np.abs(cv2.Sobel(g,cv2.CV_32F,0,1)), -1, (7,7))
    m[grad > 90] = 0                                   # only hard rock is spared; contours get gilded WITH their shading
    m[wat(a)] = 0
    m[(a[:,:,1].astype(int) - a[:,:,0]) > 6] = 0
    m[(g > 232) & (np.abs(a[:,:,0].astype(int)-a[:,:,2]) < 14)] = 0   # snowcaps stay white
    Lref = cv2.GaussianBlur(g, (0,0), 25) + 1e-3
    shade = np.clip(g / Lref, 0.55, 1.45)              # the relief itself, as a shading field
    af = a.astype(np.float32)
    for c in range(3):
        gsh = np.clip(GOLD[c] * shade, 0, 255)
        af[:,:,c] = af[:,:,c]*(1-alpha*m) + gsh*alpha*m
    out = np.clip(af, 0, 255).astype(np.uint8)
    if stipple:
        rng = random.Random(seed)
        ys, xs = np.where(m > 0.6)
        if len(xs):
            for _ in range(max(30, len(xs)//900)):
                i = rng.randrange(len(xs)); x, y = int(xs[i]), int(ys[i])
                b = out[y, x].astype(int)
                cv2.circle(out, (x, y), 1, tuple(int(v) for v in np.clip(b-22,0,255)), -1)
                cv2.circle(out, (x+2, y+1), 1, tuple(int(v) for v in np.clip(b+18,0,255)), -1)
    return out

def river_ribbon(a, amu):
    rib = cv2.dilate(amu, np.ones((9,9),np.uint8)).astype(np.float32)
    rib = cv2.GaussianBlur(rib, (0,0), 3)
    rib[wat(a)] = 0
    af = a.astype(np.float32)
    for c in range(3):
        af[:,:,c] = af[:,:,c]*(1-0.30*rib) + RIPAR[c]*0.30*rib
    return np.clip(af, 0, 255).astype(np.uint8)

def dry_lakes(a, P):
    x0,y0 = P(LAKES[0],LAKES[3]); x1,y1 = P(LAKES[1],LAKES[2])
    x0,y0,x1,y1 = int(max(0,x0)),int(max(0,y0)),int(min(a.shape[1],x1)),int(min(a.shape[0],y1))
    if x1<=x0 or y1<=y0: return a
    reg = a[y0:y1,x0:x1]
    mk = wat(reg).astype(np.uint8)
    if mk.sum() < 8: return a
    tone = reg[~mk.astype(bool)].reshape(-1,3).mean(0)
    pale = np.clip(tone*1.07+8,0,255); pale = pale*0.97+pale.mean()*0.03
    mm = cv2.GaussianBlur(cv2.dilate(mk,np.ones((3,3),np.uint8)).astype(np.float32),(0,0),1.5)[...,None].clip(0,1)
    a[y0:y1,x0:x1] = np.clip(reg.astype(np.float32)*(1-mm)+pale[None,None,:]*mm,0,255).astype(np.uint8)
    return a

ch = json.load(open('Maps/setout_charts_1271.json'))
e = ch['so_urgench']; g = e['geo']; W, H = e['vbw'], e['vbh']
def P(lon, lat):
    return (int((lon-g[0])/(g[1]-g[0])*W), int((g[3]-lat)/(g[3]-g[2])*H))
for suf in ['','_spring','_summer','_autumn','_winter']:
    fn = 'Maps/so1271_urgench%s.jpg' % suf
    a = np.array(Image.open(fn).convert('RGB'))
    excl, amu = build_excl(a, P)
    a = desert_wash(a, P, [KYZYLKUM, KARAKUM], 0.80, True, excl)
    a = desert_wash(a, P, [USTYURT, ZAUNGUZ, MANGYSH], 0.55, False, excl)
    a = river_ribbon(a, amu)
    a = dry_lakes(a, P)
    if suf != '_spring':
        _sv = LAKES
        for _box in (SORLAKE, AYDAR):
            globals()['LAKES'] = _box
            a = dry_lakes(a, P)
        globals()['LAKES'] = _sv
    Image.fromarray(a).save(fn, quality=90)
    print(fn, 'post-passed v3')

rm = json.load(open('Maps/routes_master.json'))['legs']
def resample(pts, n=44):
    p = np.array(pts, float)
    if len(p) <= n: return p
    dd = np.r_[0, np.cumsum(np.hypot(np.diff(p[:,0]), np.diff(p[:,1])))]
    t = np.linspace(0, dd[-1], n)
    return np.c_[np.interp(t,dd,p[:,0]), np.interp(t,dd,p[:,1])]
def PF(lon, lat):
    return ((lon-g[0])/(g[1]-g[0])*W, (g[3]-lat)/(g[3]-g[2])*H)
for nm, lo, la in (('Chach',69.28,41.31),('Baku',49.87,40.37)):
    if nm not in e['cities']:
        x,y = PF(lo,la)
        e['cities'][nm] = {'x':round(x),'y':round(y),'r':6,'ldx':(-58 if x>W*0.8 else 12),'ldy':-10,'faint':True}
for key in ('Chach|Samarkand','Andijan|Samarkand'):
    if key not in e['legs']:
        pts = resample(rm[key])
        e['legs'][key] = ' '.join('%.1f,%.1f' % PF(lon,lat) for lon,lat in pts)
json.dump(ch, open('Maps/setout_charts_1271.json','w'))

s2 = open('index.html', encoding='utf-8').read()
i = s2.find('"so_urgench":')
d=0;q=None;k=s2.find('{',i); j=k
while True:
    c=s2[j]
    if q:
        if c=='\\': j+=1
        elif c==q: q=None
    elif c in '"\'': q=c
    elif c=='{': d+=1
    elif c=='}':
        d-=1
        if d==0: break
    j+=1
end=j+1
if s2[end]==',': end+=1
s2 = s2[:i]+'"so_urgench":'+json.dumps(e,ensure_ascii=False)+','+s2[end:]
oldv = "const VERSION='3.1.55'; const BUILD='0716.2305';"
assert s2.count(oldv)==1
s2 = s2.replace(oldv, "const VERSION='3.1.56'; const BUILD='0716.2330';")
open('index.html','w',encoding='utf-8').write(s2)
print('entry swapped, v3.1.56')
