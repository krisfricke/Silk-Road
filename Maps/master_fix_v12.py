# master_fix_v12.py (Kris 7/17): Volga + Ural get the v11 treatment — hand-drawn lower courses
# ERASED (diff vs the prevolga backup finds exactly my painted pixels), then the TRUE courses
# re-rasterized from ne_10m_rivers_lake_centerlines.geojson at original widths, sea-clip removed.
# The AKHTUBA is not in Natural Earth (no distributaries) — it is laid on its real course at
# <=0.2-degree spacing (branch near Volzhsky, Akhtubinsk, through the game's Sarai dot at
# 47.47E,47.18N ~ Selitrennoye, rejoining the delta), 1px — narrower than the 2px Volga, as in
# life. Emba/Terek/Sulak: NOT in the source data and never on the master — nothing is invented.
# Strip-3 exclusion boxes protect the dried sors, the healed gulf and the seam from the erase.
import json, math, random
import numpy as np, cv2
from PIL import Image, ImageDraw
Image.MAX_IMAGE_PIXELS = None

PPD = 147.0; W0 = 8.0; N0 = 52.0; STEP = 14.375
PV = '/sessions/jolly-charming-gates/mnt/outputs/work/strip_backups_prevolga/strip_%02d.png'
RIV = json.load(open('Maps/ne_10m_rivers_lake_centerlines.geojson'))['features']

def wat(a):
    return (a[:,:,2].astype(int) > a[:,:,0] + 15) & (a[:,:,2] > 120)

def ne_mask(shape, sw, WW, EE, SS, NN):
    H, W = shape
    im = Image.new('L', (W,H), 0); dr = ImageDraw.Draw(im)
    for f in RIV:
        pr = f['properties']; gj = f['geometry']
        if gj is None: continue
        wdt = 1 + int(max(0, (6-(pr.get('scalerank') or 6)))//2)
        coords = gj['coordinates'] if gj['type']=='MultiLineString' else [gj['coordinates']]
        for line in coords:
            xs=[c[0] for c in line]; ys=[c[1] for c in line]
            if max(xs)<WW-0.3 or min(xs)>EE+0.3 or max(ys)<SS-0.3 or min(ys)>NN+0.3: continue
            dr.line([((x-sw)*PPD,(N0-y)*PPD) for x,y in line], fill=255, width=wdt)
    return np.array(im) > 0

def repair(si, WW, EE, SS, NN, excl_boxes=(), extra_draw=None):
    sw = W0 + si*STEP
    fn = 'Maps/master1271/strip_%02d.png' % si
    a = np.array(Image.open(fn).convert('RGB'))
    v = np.array(Image.open(PV % si).convert('RGB'))
    H, W = a.shape[:2]
    def Pi(lon, lat):
        return (int((lon-sw)*PPD), int((N0-lat)*PPD))
    x0,y0 = Pi(WW,NN); x1,y1 = Pi(EE,SS)
    x0,y0 = max(0,x0),max(0,y0); x1,y1 = min(W,x1),min(H,y1)
    win = np.zeros((H,W), bool); win[y0:y1,x0:x1] = True
    for (bw,be,bs,bn) in excl_boxes:
        ex0,ey0 = Pi(bw,bn); ex1,ey1 = Pi(be,bs)
        win[max(0,ey0):min(H,ey1), max(0,ex0):min(W,ex1)] = False
    # erase MY paint: water now that was not water before
    mine = wat(a) & ~wat(v) & win
    mine = cv2.dilate(mine.astype(np.uint8), np.ones((5,5),np.uint8)).astype(bool) & win
    a[mine] = v[mine]
    print('strip %d: erased %d px of hand-drawn water (+halo)' % (si, int(mine.sum())))
    # sample true river color from a surviving thread in the window
    thr = wat(v) & win
    ys, xs = np.nonzero(thr)
    assert len(xs) > 30, 'no thread to sample on strip %d' % si
    med = np.median(a[thr].reshape(-1,3), axis=0).astype(np.float32)
    # draw the data's rivers, clipped only at real drawn water (the sea), inside the window
    riv = ne_mask((H,W), sw, WW, EE, SS, NN) & win & ~wat(a)
    rng = np.random.default_rng(5+si)
    a[riv] = np.clip(med[None,:] + rng.normal(0,1.2,(int(riv.sum()),3)), 0, 255).astype(np.uint8)
    print('strip %d: %d px re-laid from Natural Earth' % (si, int(riv.sum())))
    if extra_draw:
        im = Image.new('L', (W,H), 0); dr = ImageDraw.Draw(im)
        for course, wdt in extra_draw:
            pts=[]
            random.seed(47)
            for i in range(len(course)-1):
                (lo1,la1),(lo2,la2)=course[i],course[i+1]
                seg=math.hypot(lo2-lo1,la2-la1); n=max(3,int(seg/0.03)); dx,dy=(lo2-lo1)/seg,(la2-la1)/seg
                for t in range(n):
                    f2=t/n; wob=math.sin(f2*math.pi*2+i*1.7)*0.006*random.uniform(0.4,1.0)
                    pts.append((lo1+(lo2-lo1)*f2-dy*wob, la1+(la2-la1)*f2+dx*wob))
            pts.append(course[-1])
            dr.line([((x-sw)*PPD,(N0-y)*PPD) for x,y in pts], fill=255, width=wdt)
        em = (np.array(im)>0) & win & ~wat(a)
        a[em] = np.clip(med[None,:] + rng.normal(0,1.2,(int(em.sum()),3)), 0, 255).astype(np.uint8)
        print('strip %d: distributary laid, %d px' % (si, int(em.sum())))
    Image.fromarray(a).save(fn)

# the real Akhtuba: branch near Volzhsky -> Akhtubinsk -> the game's Sarai (Selitrennoye) -> delta
AKHTUBA = [(44.74,48.80),(45.00,48.72),(45.30,48.62),(45.65,48.48),(45.95,48.38),(46.19,48.29),
           (46.45,48.15),(46.68,48.00),(46.90,47.82),(47.10,47.60),(47.30,47.38),(47.47,47.18),
           (47.65,47.02),(47.85,46.86),(48.05,46.72)]

# strip 2: the Volga window (bend to delta) — nothing else lives here
repair(2, 44.0, 49.70, 45.4, 49.9, extra_draw=[(AKHTUBA,1)])
# strip 3: the Ural window; protect the dried sors + healed gulf + seam country
repair(3, 49.6, 55.60, 46.0, 52.0, excl_boxes=[(54.30,55.70,44.80,46.80)])
print('MASTER FIX v12 DONE')
