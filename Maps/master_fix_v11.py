# master_fix_v11.py (Kris 7/17): the SOURCE-DATA repairs.
# (1) KURA/ARAXES from the underlying data: master_detail.py drew all rivers from
#     ne_10m_rivers_lake_centerlines.geojson but clipped riv&(dd>0) - the Caspian Depression
#     lies below 0m, so every river's lower reach was beheaded ("depression clip disease",
#     found at last). Repair: restore the lowland window from pregild, re-green (v10 recipe,
#     Kris-approved), then re-rasterize the SAME geojson lines at the same ppd and widths with
#     the sea-clip removed (clip only at actual drawn water). Color matched by sampling the
#     existing thread. Perfect join + width by construction. My v9/v10 hand courses: erased.
# (2) GULF TIP: the v3.1.54 sor-drying box dried everything east of 54.55E including the
#     CONNECTED TIP OF THE CASPIAN ITSELF -> ruler-straight shoreline. Repair: from the
#     prevolga backup, re-wet exactly the water component connected to the open sea; the
#     detached inland lakes stay dry as Kris directed.
import json
import numpy as np, cv2
from PIL import Image, ImageDraw
Image.MAX_IMAGE_PIXELS = None

PPD = 147.0; W0 = 8.0; N0 = 52.0; STEP = 14.375
LOWGREEN = np.array((146,155,96), np.float32)
BK = '/sessions/jolly-charming-gates/mnt/outputs/work/strip_backups_pregild/strip_%02d.png'
PV = '/sessions/jolly-charming-gates/mnt/outputs/work/strip_backups_prevolga/strip_%02d.png'

def wat(a):
    return (a[:,:,2].astype(int) > a[:,:,0] + 15) & (a[:,:,2] > 120)

# ============ (1) strip 2: Kura/Araxes from Natural Earth, clip disease cured ============
si = 2; sw = W0 + si*STEP
fn = 'Maps/master1271/strip_%02d.png' % si
a = np.array(Image.open(fn).convert('RGB'))
b = np.array(Image.open(BK % si).convert('RGB'))
def P2i(lon, lat):
    return (int((lon-sw)*PPD), int((N0-lat)*PPD))
WW, EE, SS, NN = 46.30, 49.70, 38.80, 41.60
x0,y0 = P2i(WW,NN); x1,y1 = P2i(EE,SS)
a[y0:y1,x0:x1] = b[y0:y1,x0:x1]                    # erase hand rivers + green
# --- sample the true river color from the restored existing thread near the old terminus ---
tx,ty = P2i(47.10,40.60)
disc = a[ty-25:ty+25, tx-25:tx+25]
dw = wat(disc)
assert dw.sum() > 4, 'no thread pixels found to sample'
rivcol = np.median(disc[dw].reshape(-1,3), axis=0).astype(np.float32)
print('sampled river color:', rivcol.astype(int))
# --- re-green the lowland (v10 recipe, canonical, relief-shaded, class-feathered) ---
LOWLAND = [(46.9,41.35),(48.2,41.20),(49.1,40.85),(49.5,40.30),(49.3,39.35),(48.6,38.95),(47.6,39.25),(46.8,39.85),(46.6,40.60)]
H, W = a.shape[:2]
mask = np.zeros((H,W), np.uint8)
cv2.fillPoly(mask, [np.array([P2i(lo,la) for lo,la in LOWLAND], np.int32)], 1)
m = cv2.GaussianBlur(mask.astype(np.float32),(0,0),12)
g = cv2.cvtColor(a, cv2.COLOR_RGB2GRAY).astype(np.float32)
m[wat(a)] = 0
m[(g>232)&(np.abs(a[:,:,0].astype(int)-a[:,:,2])<14)] = 0
grad = cv2.boxFilter(np.abs(cv2.Sobel(g,cv2.CV_32F,1,0))+np.abs(cv2.Sobel(g,cv2.CV_32F,0,1)),-1,(9,9))
m[grad>90] = 0
Lref = cv2.GaussianBlur(g,(0,0),36)+1e-3
shade = np.clip(g/Lref, 0.6, 1.4)
af = a.astype(np.float32)
for c in range(3):
    af[:,:,c] = af[:,:,c]*(1-0.93*m) + np.clip(LOWGREEN[c]*shade,0,255)*0.93*m
a = np.clip(af,0,255).astype(np.uint8)
# --- rasterize the SAME geojson lines, original widths, inside the window, no dd clip ---
RIV = json.load(open('Maps/ne_10m_rivers_lake_centerlines.geojson'))['features']
rivim = Image.new('L', (W,H), 0); dr = ImageDraw.Draw(rivim)
def px(lo, la):
    return ((lo-sw)*PPD, (N0-la)*PPD)
for f in RIV:
    pr = f['properties']; gj = f['geometry']
    if gj is None: continue
    wdt = 1 + int(max(0, (6-(pr.get('scalerank') or 6)))//2)   # master_detail.py's exact width rule
    coords = gj['coordinates'] if gj['type']=='MultiLineString' else [gj['coordinates']]
    for line in coords:
        xs=[c[0] for c in line]; ys=[c[1] for c in line]
        if max(xs)<WW-0.3 or min(xs)>EE+0.3 or max(ys)<SS-0.3 or min(ys)>NN+0.3: continue
        dr.line([px(x,y) for x,y in line], fill=255, width=wdt)
riv = (np.array(rivim) > 0)
win = np.zeros((H,W), bool); win[y0:y1,x0:x1] = True
riv &= win
riv &= ~wat(a)                                     # stop at the drawn Caspian, nowhere else
a = np.where(riv[:,:,None], (rivcol[None,None,:]*1.0).astype(np.uint8), a)  # rivcol already sampled post-*0.97
nz = np.random.default_rng(3)
noise = nz.normal(0,1.2,(H,1))
a[riv] = np.clip(a[riv].astype(np.float32) + nz.normal(0,1.2,(int(riv.sum()),3)), 0, 255).astype(np.uint8)
Image.fromarray(a).save(fn)
print('strip 2: rivers re-laid from Natural Earth (%d px), clip disease cured in the window' % int(riv.sum()))

# ============ (2) strip 3: gulf tip re-wetted from the prevolga render ============
si = 3; sw = W0 + si*STEP
fn = 'Maps/master1271/strip_%02d.png' % si
a = np.array(Image.open(fn).convert('RGB'))
v = np.array(Image.open(PV % si).convert('RGB'))
def P3i(lon, lat):
    return (int((lon-sw)*PPD), int((N0-lat)*PPD))
gx0,gy0 = P3i(54.30,46.80); gx1,gy1 = P3i(55.70,44.80)
cw = wat(a[gy0:gy1,gx0:gx1]).astype(np.uint8)      # current water (open sea reaches in from the west edge)
vw = wat(v[gy0:gy1,gx0:gx1]).astype(np.uint8)      # the original render's water
n, lab = cv2.connectedComponents(vw, connectivity=8)
keep = np.zeros_like(vw)
for k in range(1, n):
    comp = (lab==k)
    if (comp & (cw>0)).sum() > 20:                 # touches today's sea -> it IS the sea
        keep |= comp.astype(np.uint8)
rewet = (keep>0) & (cw==0)
print('gulf: %d sea-connected water px to restore; detached lakes stay dry' % int(rewet.sum()))
if rewet.sum():
    mm = cv2.GaussianBlur(cv2.dilate(rewet.astype(np.uint8),np.ones((3,3),np.uint8)).astype(np.float32),(0,0),1.2)[...,None].clip(0,1)
    mm = np.where(rewet[...,None], 1.0, mm*0.999)
    reg = a[gy0:gy1,gx0:gx1].astype(np.float32)
    a[gy0:gy1,gx0:gx1] = np.clip(reg*(1-mm) + v[gy0:gy1,gx0:gx1].astype(np.float32)*mm, 0, 255).astype(np.uint8)
    Image.fromarray(a).save(fn)
    print('strip 3: gulf tip restored to its true shape')
print('MASTER FIX v11 DONE')
