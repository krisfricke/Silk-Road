# master_fix_v10.py (Kris 7/17): three defect repairs, each done by full-recipe redo, never patch.
# (1) strip 3: melt the hard vertical water seam at 54.55E (a rectangular-window restore's edge).
# (2) strip 4: the Aydar box restored whole from pre-gild, RE-GILDED by the standard class recipe
#     within the window, then the lake shape flat-salted - erases the v8 rectangle artifacts.
# (3) strip 2: the Kura-Araxes lowland restored whole, re-greened, and the rivers drawn DENSE
#     from real courses CONNECTED to their detected upstream termini (Kura 47.30,40.47; Araxes
#     46.90,39.17) - the Suyab lesson obeyed this time.
import numpy as np, cv2, math, random
from PIL import Image, ImageDraw, ImageFilter
Image.MAX_IMAGE_PIXELS = None

GOLD = np.array((238,223,163), np.float32)
SALT = np.array((233,229,213), np.float32)
LOWGREEN = np.array((146,155,96), np.float32)
RIVER = (78,128,170)
PPD = 147.0; W0 = 8.0; N0 = 52.0; STEP = 14.375
BK = '/sessions/jolly-charming-gates/mnt/outputs/work/strip_backups_pregild/strip_%02d.png'

def wat(a):
    return (a[:,:,2].astype(int) > a[:,:,0] + 15) & (a[:,:,2] > 120)

# ---------- (1) strip 3 seam melt ----------
si = 3; sw = W0 + si*STEP
fn = 'Maps/master1271/strip_%02d.png' % si
a = np.array(Image.open(fn).convert('RGB'))
def P3(lon, lat):
    return (int((lon-sw)*PPD), int((N0-lat)*PPD))
for edge_lon in (54.55, 55.50):
    x, _ = P3(edge_lon, 46.0)
    y0 = P3(edge_lon, 46.60)[1]; y1 = P3(edge_lon, 45.00)[1]
    band = a[y0:y1, x-16:x+16].astype(np.float32)
    sm = cv2.GaussianBlur(band, (0, 0), sigmaX=7, sigmaY=0)
    w = np.abs(np.arange(-16, 16))[None, :, None].astype(np.float32)
    alpha = np.clip(1.0 - w/14.0, 0, 1)
    a[y0:y1, x-16:x+16] = np.clip(band*(1-alpha) + sm*alpha, 0, 255).astype(np.uint8)
Image.fromarray(a).save(fn)
print('strip 3: seams melted at 54.55/55.50')

# ---------- (2) strip 4 Aydar window: full-recipe redo ----------
si = 4; sw = W0 + si*STEP
fn = 'Maps/master1271/strip_%02d.png' % si
a = np.array(Image.open(fn).convert('RGB'))
b = np.array(Image.open(BK % si).convert('RGB'))
def P4(lon, lat):
    return (int((lon-sw)*PPD), int((N0-lat)*PPD))
KYZYLKUM = [(59.8,43.8),(61.5,44.3),(63.5,44.3),(65.5,43.6),(66.8,42.6),(67.5,41.7),(66.5,40.9),(64.6,40.3),(63.0,40.5),(61.7,41.6),(60.3,42.5)]
x0,y0 = P4(65.60,41.50); x1,y1 = P4(67.80,40.40)
x0,y0 = max(0,x0),max(0,y0); x1,y1 = min(a.shape[1],x1),min(a.shape[0],y1)
win = b[y0:y1,x0:x1].copy()                      # clean pre-gild ground truth
lake = wat(win).astype(np.uint8)                 # the true lake shape
# re-gild the window with the standard class recipe (poly mask ∩ window)
H2, W2 = win.shape[:2]
pm = np.zeros(a.shape[:2], np.uint8)
cv2.fillPoly(pm, [np.array([P4(lo,la) for lo,la in KYZYLKUM], np.int32)], 1)
m = cv2.GaussianBlur(pm.astype(np.float32), (0,0), 15)[y0:y1,x0:x1]
g = cv2.cvtColor(win, cv2.COLOR_RGB2GRAY).astype(np.float32)
m[wat(win)] = 0
m[(win[:,:,1].astype(int)-win[:,:,0]) > 6] = 0
Lref = cv2.GaussianBlur(g, (0,0), 36) + 1e-3
shade = np.clip(g/Lref, 0.55, 1.45)
wf = win.astype(np.float32)
for c in range(3):
    wf[:,:,c] = wf[:,:,c]*(1-0.93*m) + np.clip(GOLD[c]*shade,0,255)*0.93*m
win = np.clip(wf,0,255).astype(np.uint8)
rng = random.Random(15)
ys, xs = np.where(m > 0.6)
if len(xs):
    for _ in range(max(20, len(xs)//1400)):
        i = rng.randrange(len(xs)); x, y = int(xs[i]), int(ys[i])
        bb = win[y, x].astype(int)
        cv2.circle(win, (x, y), 1, tuple(int(v) for v in np.clip(bb-22,0,255)), -1)
        cv2.circle(win, (x+3, y+1), 1, tuple(int(v) for v in np.clip(bb+18,0,255)), -1)
# flat-canon salt over the lake shape, feather only the rim
rng2 = np.random.default_rng(7)
flat = SALT[None,None,:] + rng2.normal(0,3,win.shape).astype(np.float32)
core = cv2.erode(lake, np.ones((3,3),np.uint8))
edgef = cv2.GaussianBlur(cv2.dilate(lake,np.ones((3,3),np.uint8)).astype(np.float32),(0,0),2).clip(0,1)
f = np.where(core[...,None]>0, 1.0, edgef[...,None])
win = np.clip(win.astype(np.float32)*(1-f) + flat*f, 0, 255).astype(np.uint8)
# feather the window boundary into its surroundings (no box edges, ever again)
outer = a[y0:y1,x0:x1].astype(np.float32)
bx = np.ones((H2,W2), np.float32)
bx[:10,:] *= np.linspace(0,1,10)[:,None]; bx[-10:,:] *= np.linspace(1,0,10)[:,None]
bx[:,:10] *= np.linspace(0,1,10)[None,:]; bx[:,-10:] *= np.linspace(1,0,10)[None,:]
a[y0:y1,x0:x1] = np.clip(outer*(1-bx[...,None]) + win.astype(np.float32)*bx[...,None], 0, 255).astype(np.uint8)
Image.fromarray(a).save(fn)
print('strip 4: Aydar window fully re-reciped, rectangle erased')

# ---------- (3) strip 2 lowland: restore, re-green, real rivers ----------
si = 2; sw = W0 + si*STEP
fn = 'Maps/master1271/strip_%02d.png' % si
a = np.array(Image.open(fn).convert('RGB'))
b = np.array(Image.open(BK % si).convert('RGB'))
def P2i(lon, lat):
    return (int((lon-sw)*PPD), int((N0-lat)*PPD))
def P2f(lon, lat):
    return ((lon-sw)*PPD, (N0-lat)*PPD)
x0,y0 = P2i(46.30,41.60); x1,y1 = P2i(49.70,38.80)
a[y0:y1,x0:x1] = b[y0:y1,x0:x1]                  # wipe my straight rivers + old green
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
# rivers: dense real courses, CONNECTED to the detected termini
KURA = [(47.30,40.47),(47.45,40.36),(47.62,40.28),(47.80,40.18),(48.00,40.10),(48.20,40.04),(48.43,39.98),(48.62,39.92),(48.80,39.85),(48.95,39.72),(48.98,39.60),(49.10,39.48),(49.25,39.40),(49.33,39.37)]
ARAX = [(46.90,39.17),(47.05,39.25),(47.20,39.35),(47.38,39.47),(47.58,39.60),(47.80,39.73),(48.05,39.84),(48.25,39.92),(48.43,39.98)]
random.seed(43)
def meander(ps, amp=0.009):
    out=[]
    for i in range(len(ps)-1):
        (x,y),(u,v)=ps[i],ps[i+1]
        seg=math.hypot(u-x,v-y); n=max(3,int(seg/0.035)); dx,dy=(u-x)/seg,(v-y)/seg
        for t in range(n):
            f2=t/n; w2=math.sin(f2*math.pi*2+i*1.9)*amp*random.uniform(0.35,1.0)
            out.append((x+(u-x)*f2-dy*w2, y+(v-y)*f2+dx*w2))
    out.append(ps[-1]); return out
im = Image.fromarray(a)
ov = Image.new('RGBA', im.size, (0,0,0,0)); dr = ImageDraw.Draw(ov)
for course in (KURA, ARAX):
    pts = [P2f(lon,lat) for lon,lat in meander(course)]
    cut = len(pts)
    for i,(x,y) in enumerate(pts):
        if i>len(pts)*2//3 and 0<=int(x)<W and 0<=int(y)<H:
            r,g2,b2 = a[int(y),int(x)]
            if int(b2)>int(r)+15 and b2>120: cut=i+3; break
    dr.line(pts[:cut], fill=RIVER+(255,), width=2, joint='curve')
ov = ov.filter(ImageFilter.GaussianBlur(0.4))
im2 = im.convert('RGBA'); im2.alpha_composite(ov)
Image.fromarray(np.array(im2.convert('RGB'))).save(fn)
print('strip 2: lowland re-reciped, Kura+Araxes on true courses, connected')
print('MASTER FIX v10 DONE')
