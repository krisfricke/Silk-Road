# rebake_1271_fields.py -- re-slice the 8 era-1271 departure charts from the master WITH the
# farmland quilt (Talas; design per MAP_NOTES 'FARMLAND LAYER DESIGN', Kris 07-04):
# settlements [(name,lon,lat,radius_km)] -> steppe762-style polygonal quilt (jittered voronoi-ish
# cells, 2-3 earth tones + green), clipped by DEM (lowland near the town, no sea, no steep relief),
# feathered. Master stays era-neutral; this script supplies the 1271 towns.
import numpy as np, json, math, glob, re, sys
from PIL import Image
import tifffile
sys.path.insert(0,'.')
from slice_master import slice_master

# ---------------- DEM sampler (GEBCO tiles from outputs/work) ----------------
TILES=[]
for f in glob.glob('/sessions/jolly-charming-gates/mnt/outputs/work/geb3/*.tif')+glob.glob('/sessions/jolly-charming-gates/mnt/outputs/work/geb6/*.tif')+[x for x in glob.glob('/sessions/jolly-charming-gates/mnt/outputs/work/geb/*.tif') if 'w24.246' not in x and 'w28.475' not in x]:
    b=f.split('/')[-1].split('_')
    n=float(b[2][1:]); s=float(b[3][1:]); w=float(b[4][1:]); e=float(b[5][1:])
    TILES.append([f,w,e,s,n,None])
def dem_at(lon,lat):
    for t in TILES:
        f,w,e,s,n,arr=t
        if w<=lon<=e and s<=lat<=n:
            if arr is None: t[5]=tifffile.imread(f).astype(np.float32); arr=t[5]
            h,wd=arr.shape
            c=min(wd-1,max(0,int((lon-w)/(e-w)*wd))); r=min(h-1,max(0,int((n-lat)/(n-s)*h)))
            win=arr[max(0,r-6):r+7,max(0,c-6):c+7]
            return float(arr[r,c]), float(win.max()-win.min())
    return 300.0,0.0

# ---------------- settlements (1271) ----------------
LL=eval(re.search(r'LL=\{.*?\}',open('route_1271.py').read(),re.S).group(0)[3:])
HUB={'Venice','Ragusa','Candia','Constantinople','Caffa','Tana','Sarai','Ayas','Acre','Sivas','Tabriz',
 'Kerman','Hormuz','Urgench','Almaliq','Herat','Alexandria','Trebizond','Bukhara','Samarkand','Kashgar',
 'Khotan','Turfan','Khanbaliq','Xanadu','Kinsay','Zaiton','Zhangye','Lanzhou',"Chang'an",'Yangzhou','Baghdad','Nishapur'}
SKIP={'Venice','Hormuz','Mangyshlak'}   # lagoon / bare salt rock: no field quilt
MEGA={'Khanbaliq':62,'Kinsay':62,'Kenjanfu':55,'Constantinople':55,'Tabriz':52,'Samarkand':48,'Zaiton':46,'Yangzhou':48,'Baghdad':45}
SETTLE=[]
for n,(lo,la) in LL.items():
    if n in SKIP: continue
    r=MEGA.get(n, 42 if n in HUB else 26)
    SETTLE.append((n,lo,la,r))

# ---------------- the quilt ----------------
PAL=[(196,176,102),(178,158,88),(206,188,118),(160,158,86)]   # crop golds and straw, steppe762-style (Kris)   # greens + straw earth tones
def add_fields(img,geo,settle,seed=7):
    W,E,S,N=geo
    h,w=img.shape[:2]
    ppx=w/(E-W)                     # px per deg lon
    ppy=h/(N-S)
    rng=np.random.default_rng(seed)
    overlay=np.zeros((h,w,3),np.float32); alpha=np.zeros((h,w),np.float32)
    for name,lo,la,rkm in settle:
        if not(W-0.5<lo<E+0.5 and S-0.5<la<N+0.5): continue
        e0,_=dem_at(lo,la)
        rdeg=rkm/(111.0*math.cos(math.radians(la)))
        rpx=rdeg*ppx
        cx=(lo-W)*ppx; cy=(N-la)*ppy
        cell=max(5,int(rpx/5))
        n_cells=int((2*rpx/cell))+2
        for iy in range(-n_cells//2-1,n_cells//2+2):
            for ix in range(-n_cells//2-1,n_cells//2+2):
                px=cx+ix*cell+rng.uniform(-cell*.4,cell*.4)
                py=cy+iy*cell+rng.uniform(-cell*.4,cell*.4)
                d=math.hypot(px-cx,py-cy)
                if d>rpx*(0.75+rng.uniform(0,0.5)): continue
                if rng.uniform()<0.25: continue           # gaps in the quilt
                lon=W+px/ppx; lat=N-py/ppy
                ev,rel=dem_at(lon,lat)
                # sea test by RASTER COLOR (GEBCO<=0 also means Turfan-style depressions - not sea!)
                pxi=int(min(w-1,max(0,px))); pyi=int(min(h-1,max(0,py)))
                bb,gg,rr2=int(img[pyi,pxi,2]),int(img[pyi,pxi,1]),int(img[pyi,pxi,0])
                if bb>rr2+12 and bb>gg+4: continue
                if ev>e0+260 or rel>180: continue  # hill / rough ground
                col=PAL[rng.integers(0,len(PAL))]
                x0=int(max(0,px-cell*.55)); x1=int(min(w,px+cell*.55))
                y0=int(max(0,py-cell*.55)); y1=int(min(h,py+cell*.55))
                if x1<=x0 or y1<=y0: continue
                a=0.55*(1.0-0.45*d/max(rpx,1))
                overlay[y0:y1,x0:x1]=col
                alpha[y0:y1,x0:x1]=np.maximum(alpha[y0:y1,x0:x1],a)
    # feather
    import cv2
    alpha=cv2.GaussianBlur(alpha,(0,0),1.6)
    out=img.astype(np.float32)
    out=out*(1-alpha[...,None])+overlay*alpha[...,None]
    return out.astype(np.uint8)

CHARTS=[
 ('adriatic1271.png', (11,29.5,34,46.5), 1980,1338),
 ('pontic1271.png',   (27,56,39,52),     1980,888),
 ('khwarezm1271.png', (45,72,37,49.5),   1980,917),
 ('bactria1271.png',  (58,78,32,41),     1980,891),
 ('yuaneast1271.png', (95.5,122.5,24,45.5),1980,1577),
 ('anatolia1271.png', (26,43,32,43),     1980,1281),
 ('persia1271.png',   (42,63,25,40),     1980,1414),
 ('tarim1271.png',    (74,96,34,45),     1980,990),
]
if __name__=='__main__':
    for fn,geo,OW,OH in CHARTS:
        W,E,S,N=geo
        slice_master(W,E,S,N,OW,OH,'_tmp_slice.png')
        img=np.array(Image.open('_tmp_slice.png').convert('RGB'))
        img=relief_boost(img,geo,OW,OH)
        img=add_fields(img,geo,SETTLE)
        Image.fromarray(img).save(fn)
        print('rebaked',fn)

def relief_boost(img,geo,OW,OH,dem_grid_fn=None):
    """slice-time contrast + snow (Kris: 1271 charts read flatter than 762; Taurus should look like mountains)"""
    import numpy as np, cv2, math
    W,E,S,N=geo
    d=_dem_for_rect(W,E,S,N,OW,OH)
    gy,gx=np.gradient(d,(N-S)/OH*111000.0,(E-W)/OW*111000.0*math.cos(math.radians((S+N)/2)))
    az=math.radians(315); alt=math.radians(45)
    slope=np.arctan(np.hypot(gx,gy)*3.0); aspect=np.arctan2(-gx,gy)
    hs=np.clip(np.sin(alt)*np.cos(slope)+math.cos(alt)*np.sin(slope)*np.cos(az-aspect),0.0,1.2)
    boost=np.clip(0.72+0.55*hs,0.62,1.22)
    out=img.astype(np.float32)
    land=(d>0)
    out[land]*=boost[land][...,None]
    # snowcaps: seasonal-summer line, high where the sun is strong, lower on the great ranges
    lat=np.linspace(N,S,OH)[:,None].repeat(OW,1)
    snowline=np.where(lat>=32.0, np.clip(3800.0-(lat-32.0)*120.0,2400,4300), 4900.0)   # Taurus/Pontic/Tian Shan cap properly; south of 32 only the Himalaya-class crests whiten
    dpk=cv2.dilate(d,np.ones((5,5),np.float32))   # crest-widen so caps read at chart scale
    sn=np.clip((dpk-snowline)/300.0,0,1)*land
    sn=cv2.GaussianBlur(sn.astype(np.float32),(0,0),1.2)
    out=out*(1-sn[...,None])+np.array([246,248,250],np.float32)[None,None,:]*(sn[...,None]*(0.55+0.45*hs[...,None]))
    return np.clip(out,0,255).astype(np.uint8)
def _dem_for_rect(W,E,S,N,OW,OH):
    import numpy as np, tifffile, cv2
    d=np.full((OH,OW),np.nan,np.float32)
    for f,tw,te,ts,tn,_ in TILES:
        ow,oe=max(W,tw),min(E,te); os_,on=max(S,ts),min(N,tn)
        if ow>=oe or os_>=on: continue
        a=tifffile.imread(f).astype(np.float32); h,w2=a.shape
        rx=(te-tw)/w2; ry=(tn-ts)/h
        c0=int((ow-tw)/rx); c1=int((oe-tw)/rx); r0=int((tn-on)/ry); r1=int((tn-os_)/ry)
        gx0=int((ow-W)/(E-W)*OW); gx1=int((oe-W)/(E-W)*OW); gy0=int((N-on)/(N-S)*OH); gy1=int((N-os_)/(N-S)*OH)
        if gx1<=gx0 or gy1<=gy0: continue
        sub=cv2.resize(a[r0:r1,c0:c1],(gx1-gx0,gy1-gy0),interpolation=cv2.INTER_AREA)
        tgt=d[gy0:gy1,gx0:gx1]; m=np.isnan(tgt); tgt[m]=sub[m]
    return np.nan_to_num(d,nan=300.0)
