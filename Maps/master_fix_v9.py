# master_fix_v9.py - RECIPE v9 (Kris 7/17, the flat-canon rule):
# (1) SALT PANS repainted correctly: 100% canonical salt over the water shape, feather ONLY the
#     edge (2px), light paper noise - no shading multiplier (the old one inherited the dead
#     lake's darkness = Kris's "darker grey"), no box artifacts.
# (2) KURA + ARAXES extended through the Kura-Araxes lowland to the Caspian (same clipping
#     disease as the Volga/Ural); the lowland itself recolored to canonical LOWLAND GREEN
#     (Mugan/Shirvan steppe - Kris: "this one is generally green").
import numpy as np, cv2, math, random
from PIL import Image, ImageDraw, ImageFilter
Image.MAX_IMAGE_PIXELS = None

SALT = np.array((233,229,213), np.float32)
LOWGREEN = np.array((146,155,96), np.float32)
RIVER = (78,128,170)
PPD = 147.0; W0 = 8.0; N0 = 52.0; STEP = 14.375
DRYBOXES = [(3,(54.55,55.50,45.05,46.55)), (3,(62.95,63.45,40.98,41.40)), (4,(65.75,67.65,40.55,41.35))]
KURA_EXT = [(46.8,41.05),(47.4,40.95),(47.9,40.80),(48.4,40.55),(48.8,40.25),(49.05,39.90),(49.20,39.60),(49.33,39.38)]
ARAX_EXT = [(45.3,39.55),(46.0,39.45),(46.7,39.45),(47.3,39.60),(47.9,39.80),(48.48,40.01)]
LOWLAND = [(46.9,41.35),(48.2,41.20),(49.1,40.85),(49.5,40.30),(49.3,39.35),(48.6,38.95),(47.6,39.25),(46.8,39.85),(46.6,40.60)]

def wat(a):
    return (a[:,:,2].astype(int) > a[:,:,0] + 15) & (a[:,:,2] > 120)

# ---- 1. salt pans, done right ----
rng = np.random.default_rng(7)
for si, (bw, be, bs, bn) in DRYBOXES:
    sw = W0 + si*STEP
    fn = 'Maps/master1271/strip_%02d.png' % si
    bfn = '/sessions/jolly-charming-gates/mnt/outputs/work/strip_backups_pregild/strip_%02d.png' % si
    a = np.array(Image.open(fn).convert('RGB'))
    b = np.array(Image.open(bfn).convert('RGB'))
    def P(lon, lat):
        return (int((lon-sw)*PPD), int((N0-lat)*PPD))
    x0,y0 = P(bw,bn); x1,y1 = P(be,bs)
    x0,y0 = max(0,x0),max(0,y0); x1,y1 = min(a.shape[1],x1),min(a.shape[0],y1)
    if x1<=x0 or y1<=y0: continue
    lake = wat(b[y0:y1,x0:x1]).astype(np.uint8)          # the ORIGINAL water shape
    if lake.sum() < 8:
        print('strip',si,'box',bw,'- no lake in backup'); continue
    reg = a[y0:y1,x0:x1].astype(np.float32)
    flat = SALT[None,None,:] + rng.normal(0, 3, reg.shape).astype(np.float32)
    core = cv2.erode(lake, np.ones((3,3),np.uint8)).astype(np.float32)
    edge = cv2.GaussianBlur(cv2.dilate(lake,np.ones((3,3),np.uint8)).astype(np.float32),(0,0),2).clip(0,1)
    f = np.maximum(core, edge*0.999)[...,None].clip(0,1)   # 100% core, feather only the rim
    f = np.where(core[...,None]>0, 1.0, edge[...,None])
    reg = reg*(1-f) + flat*f
    a[y0:y1,x0:x1] = np.clip(reg,0,255).astype(np.uint8)
    Image.fromarray(a).save(fn)
    print('strip',si,'salt pan repainted flat at',bw,'-',be)

# ---- 2. Kura/Araxes + lowland green on strip 2 ----
si = 2; sw = W0 + si*STEP
fn = 'Maps/master1271/strip_%02d.png' % si
im = Image.open(fn).convert('RGB')
a = np.array(im)
H, W = a.shape[:2]
def P2f(lon, lat):
    return ((lon-sw)*PPD, (N0-lat)*PPD)
random.seed(1271)
def meander(ps, amp=0.012):
    out=[]
    for i in range(len(ps)-1):
        (x,y),(u,v)=ps[i],ps[i+1]
        seg=math.hypot(u-x,v-y); n=max(2,int(seg/0.05)); dx,dy=(u-x)/seg,(v-y)/seg
        for t in range(n):
            f2=t/n; w2=math.sin(f2*math.pi*2+i*1.7)*amp*random.uniform(0.4,1.0)
            out.append((x+(u-x)*f2-dy*w2, y+(v-y)*f2+dx*w2))
    out.append(ps[-1]); return out
ov = Image.new('RGBA',(W,H),(0,0,0,0)); dr = ImageDraw.Draw(ov)
for course in (KURA_EXT, ARAX_EXT):
    pts = [P2f(lon,lat) for lon,lat in meander(course)]
    cut = len(pts)
    for i,(x,y) in enumerate(pts):
        if i>len(pts)//2 and 0<=int(x)<W and 0<=int(y)<H:
            r,g2,b2 = a[int(y),int(x)]
            if int(b2)>int(r)+15 and b2>120: cut=i+3; break
    dr.line(pts[:cut], fill=RIVER+(255,), width=2, joint='curve')
ov = ov.filter(ImageFilter.GaussianBlur(0.4))
im2 = im.convert('RGBA'); im2.alpha_composite(ov)
a = np.array(im2.convert('RGB'))
# lowland green: canonical colour x relief shading, near-opaque, class boundary feather only
mask = np.zeros((H,W), np.uint8)
cv2.fillPoly(mask, [np.array([(int(P2f(lo,la)[0]),int(P2f(lo,la)[1])) for lo,la in LOWLAND], np.int32)], 1)
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
    gsh = np.clip(LOWGREEN[c]*shade, 0, 255)
    af[:,:,c] = af[:,:,c]*(1-0.93*m) + gsh*0.93*m
a = np.clip(af,0,255).astype(np.uint8)
Image.fromarray(a).save(fn)
print('strip 2: Kura+Araxes to the sea, lowland greened')
print('MASTER FIX v9 DONE')
