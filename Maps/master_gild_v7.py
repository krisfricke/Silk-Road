# master_gild.py - RECIPE v7 (Kris 7/17): the v6 desert scheme BAKED INTO MASTER STRIPS 2-4,
# so every future cut inherits it. Same polygons, gold, relief-preserving recolor, ribbon and
# dry salt pans as Maps/rebake_urgench_post.py v6. Seasonal April re-wet stays chart-side.
import json, math, random
import numpy as np, cv2
from PIL import Image
Image.MAX_IMAGE_PIXELS = None

GOLD = np.array((238,223,163), np.float32)
RIPAR = np.array((150,165,105), np.float32)
KYZYLKUM = [(59.8,43.8),(61.5,44.3),(63.5,44.3),(65.5,43.6),(66.8,42.6),(67.5,41.7),(66.5,40.9),(64.6,40.3),(63.0,40.5),(61.7,41.6),(60.3,42.5)]
KARAKUM  = [(52.5,41.2),(56.0,41.6),(58.5,41.5),(60.5,41.0),(61.5,40.0),(60.5,38.8),(57.5,37.8),(54.0,37.8),(52.3,39.0)]
USTYURT  = [(52.6,48.3),(56.5,47.9),(59.5,47.4),(61.8,46.2),(61.4,43.9),(59.9,43.2),(58.9,42.5),(57.0,42.3),(55.2,42.6),(53.4,43.2),(52.4,44.5),(52.3,46.5)]
ZAUNGUZ  = [(52.2,44.6),(55.6,44.3),(57.3,43.3),(57.6,42.2),(57.0,41.4),(54.5,41.3),(52.6,41.8),(52.2,43.5)]
MANGYSH  = [(50.7,44.7),(53.5,44.6),(54.3,43.8),(53.3,43.0),(51.6,43.2),(50.5,43.9)]
OASIS_N  = [(58.3,44.4),(59.6,44.4),(60.4,43.0),(60.8,42.3),(60.7,41.75),(59.6,41.7),(58.6,41.75),(57.8,41.8),(57.5,42.6),(57.9,43.4)]
AMU_BB   = (58.6, 62.7, 38.9, 42.8)
DRYBOXES = [(54.55,55.50,45.05,46.55),(62.95,63.45,40.98,41.40),(65.75,67.65,40.55,41.35)]
PPD = 147.0; W0 = 8.0; N0 = 52.0; STEP = 14.375

def wat(a):
    return (a[:,:,2].astype(int) > a[:,:,0] + 15) & (a[:,:,2] > 120)

def process_strip(si):
    sw = W0 + si*STEP
    fn = 'Maps/master1271/strip_%02d.png' % si
    a = np.array(Image.open(fn).convert('RGB'))
    H, W = a.shape[:2]
    def P(lon, lat):
        return (int((lon-sw)*PPD), int((N0-lat)*PPD))
    ex = np.zeros((H, W), np.uint8)
    cv2.fillPoly(ex, [np.array([P(lo,la) for lo,la in OASIS_N], np.int32)], 1)
    x0,y0 = P(AMU_BB[0],AMU_BB[3]); x1,y1 = P(AMU_BB[1],AMU_BB[2])
    bb = np.zeros((H, W), np.uint8)
    bb[max(0,y0):min(H,y1), max(0,x0):min(W,x1)] = 1
    amu = (wat(a).astype(np.uint8) & bb)
    g = cv2.cvtColor(a, cv2.COLOR_RGB2GRAY).astype(np.float32)
    grad = cv2.boxFilter(np.abs(cv2.Sobel(g,cv2.CV_32F,1,0))+np.abs(cv2.Sobel(g,cv2.CV_32F,0,1)), -1, (9,9))
    Lref = cv2.GaussianBlur(g, (0,0), 36) + 1e-3
    shade = np.clip(g / Lref, 0.55, 1.45)
    for polys, alpha, stipple in (([KYZYLKUM,KARAKUM], 0.80, True), ([USTYURT,ZAUNGUZ,MANGYSH], 0.55, False)):
        mask = np.zeros((H, W), np.uint8)
        for poly in polys:
            cv2.fillPoly(mask, [np.array([P(lo,la) for lo,la in poly], np.int32)], 1)
        mask[ex > 0] = 0
        m = cv2.GaussianBlur(mask.astype(np.float32), (0,0), 15)
        m[grad > 90] = 0
        m[wat(a)] = 0
        m[(a[:,:,1].astype(int) - a[:,:,0]) > 6] = 0
        m[(g > 232) & (np.abs(a[:,:,0].astype(int)-a[:,:,2]) < 14)] = 0
        af = a.astype(np.float32)
        for c in range(3):
            gsh = np.clip(GOLD[c]*shade, 0, 255)
            af[:,:,c] = af[:,:,c]*(1-alpha*m) + gsh*alpha*m
        a = np.clip(af, 0, 255).astype(np.uint8)
        if stipple:
            rng = random.Random(11+si)
            ys, xs = np.where(m > 0.6)
            if len(xs):
                for _ in range(max(30, len(xs)//1400)):
                    i = rng.randrange(len(xs)); x, y = int(xs[i]), int(ys[i])
                    b = a[y, x].astype(int)
                    cv2.circle(a, (x, y), 1, tuple(int(v) for v in np.clip(b-22,0,255)), -1)
                    cv2.circle(a, (x+3, y+1), 1, tuple(int(v) for v in np.clip(b+18,0,255)), -1)
    # ribbon
    rib = cv2.dilate(amu, np.ones((13,13),np.uint8)).astype(np.float32)
    rib = cv2.GaussianBlur(rib, (0,0), 4)
    rib[wat(a)] = 0
    af = a.astype(np.float32)
    for c in range(3):
        af[:,:,c] = af[:,:,c]*(1-0.30*rib) + RIPAR[c]*0.30*rib
    a = np.clip(af, 0, 255).astype(np.uint8)
    # dry the salt pans
    for (bw, be, bs, bn) in DRYBOXES:
        x0,y0 = P(bw,bn); x1,y1 = P(be,bs)
        x0,y0,x1,y1 = max(0,x0),max(0,y0),min(W,x1),min(H,y1)
        if x1<=x0 or y1<=y0: continue
        reg = a[y0:y1,x0:x1]
        mk = wat(reg).astype(np.uint8)
        if mk.sum() < 8: continue
        tone = reg[~mk.astype(bool)].reshape(-1,3).mean(0)
        pale = np.clip(tone*1.07+8,0,255); pale = pale*0.97+pale.mean()*0.03
        mm = cv2.GaussianBlur(cv2.dilate(mk,np.ones((3,3),np.uint8)).astype(np.float32),(0,0),2)[...,None].clip(0,1)
        a[y0:y1,x0:x1] = np.clip(reg.astype(np.float32)*(1-mm)+pale[None,None,:]*mm,0,255).astype(np.uint8)
    Image.fromarray(a).save(fn)
    print('strip', si, 'gilded at source')

# ---- 0. fix the Samarkand-road stickiness in canonical geometry ----
rm = json.load(open('Maps/routes_master.json'))
A = rm['legs']['Andijan|Samarkand']; C = rm['legs']['Chach|Samarkand']
def near_idx(pts, lon, lat):
    return min(range(len(pts)), key=lambda i:(pts[i][0]-lon)**2+(pts[i][1]-lat)**2)
# orient both starting at Samarkand
if (A[0][0]-66.97)**2+(A[0][1]-39.65)**2 > (A[-1][0]-66.97)**2+(A[-1][1]-39.65)**2: A = A[::-1]
if (C[0][0]-66.97)**2+(C[0][1]-39.65)**2 > (C[-1][0]-66.97)**2+(C[-1][1]-39.65)**2: C = C[::-1]
iA = near_idx(A, 67.85, 40.12)   # Jizzakh: the two roads part here
jC = near_idx(C, 67.85, 40.12)
rm['legs']['Chach|Samarkand'] = [list(p) for p in (A[:iA+1] + C[jC+1:])]
json.dump(rm, open('Maps/routes_master.json','w'))
print('Chach road now shares the Samarkand-Jizzakh trunk with the Fergana road (%d+%d pts)' % (iA+1, len(C)-jC-1))

for si in (2, 3, 4):
    process_strip(si)
print('MASTER GILDED')
