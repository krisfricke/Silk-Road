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
for f in glob.glob('/sessions/jolly-charming-gates/mnt/outputs/work/geb3/*.tif')+glob.glob('/sessions/jolly-charming-gates/mnt/outputs/work/geb6/*.tif')+glob.glob('work/geb_amber/*.tif')+[x for x in glob.glob('/sessions/jolly-charming-gates/mnt/outputs/work/geb/*.tif') if 'w24.246' not in x and 'w28.475' not in x]:
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
LL.update({'Chach':(69.28,41.31)})   # QUILT v3.1b: the Stone City farms too (Kris) - route_1271's LL never listed it
HUB={'Venice','Ragusa','Candia','Constantinople','Caffa','Tana','Sarai','Ayas','Acre','Sivas','Tabriz',
 'Kerman','Hormuz','Urgench','Almaliq','Herat','Alexandria','Trebizond','Bukhara','Samarkand','Kashgar',
 'Khotan','Turfan','Khanbaliq','Xanadu','Kinsay','Zaiton','Zhangye','Lanzhou',"Chang'an",'Yangzhou','Baghdad','Nishapur'}
SKIP={'Venice','Hormuz','Mangyshlak','Merv','Abaskun'}   # lagoon / bare salt rock / DEAD (Merv, razed 1221 - Kris: no fields, ruin symbol instead) / drowning (Abaskun)
LL.setdefault('Andijan',(72.34,40.78)); LL.setdefault('Damghan',(54.34,36.17))
for _n,_p in {'Osh':(72.80,40.53),'Khujand':(69.63,40.28),'Marghinan':(71.72,40.47),'Uzgend':(73.30,40.77)}.items():
    LL.setdefault(_n,_p)   # Fergana towns: quilt-only settlements (halts/known towns, not game nodes)
HUB.add('Andijan')   # the Ferghana valley - one of the most fertile in Central Asia (Kris)
LL.setdefault('Datong',(113.30,40.09)); HUB.add('Datong')   # Xijing, the old Western Capital - halt on the Tenduc-Khanbaliq post road (Kris): quilt-only, no chart of its own
MEGA={'Khanbaliq':62,'Kinsay':62,'Kenjanfu':55,'Constantinople':55,'Tabriz':52,'Samarkand':48,'Zaiton':46,'Yangzhou':48,'Baghdad':45}
SETTLE=[]
for n,(lo,la) in LL.items():
    if n in SKIP: continue
    r=MEGA.get(n, 42 if n in HUB else 26)
    SETTLE.append((n,lo,la,r))

# ---------------- the quilt ----------------
PALS={  # per-season WEIGHTED palettes - every season keeps green+earth mingled, like the 762 reference
 'summer':[((116,142,74),.24),((150,166,88),.16),((196,168,90),.22),((214,190,112),.16),((166,138,88),.12),((186,164,120),.10)],
 'spring':[((104,146,66),.30),((126,164,82),.24),((150,178,98),.16),((160,140,92),.14),((184,164,110),.08),((136,118,82),.08)],
 'autumn':[((172,142,84),.24),((196,168,102),.20),((148,120,74),.18),((128,140,76),.16),((210,186,124),.12),((110,124,66),.10)],
 'winter':[((146,126,96),.26),((128,110,82),.22),((166,148,116),.18),((112,100,74),.14),((172,158,128),.12),((120,128,92),.08)]}
SEASONS=['summer','winter','spring','autumn']
# maritime/canal grain import: fraction of the city's acreage NOT grown locally (Kris: Constantinople
# imports by sea; the Chinese megacities ride the grain barges)
SEAFED={'Constantinople':.45,'Kinsay':.5,'Zaiton':.4,'Yangzhou':.55,'Khanbaliq':.45,'Guangzhou':.5,
 'Alexandria':.6,'Acre':.5,'Trebizond':.5,'Caffa':.6,'Tana':.6,'Ayas':.6,'Candia':.7,'Ragusa':.5,'Basra':.5}
# Modern reservoirs/lakes that did NOT exist in 762/1271 (Kris): replace with salt pan (desert) or
# marsh (steppe); where we know specifics, an EPHEMERAL spring lake returns briefly. [W,E,S,N] boxes;
# blue raster inside is recoloured BEFORE fields, so nothing farms toward a lake that is not there.
ANACHRON=[
 {'name':'Aydar/Arnasay (1969 Chardara overflow)','box':[65.6,68.45,40.35,41.25],'kind':'saltpan',
  'ephemeral':{'box':[67.55,68.4,40.4,40.95],'seasons':['spring'],'col':(148,170,180)}},
 {'name':'Kayrakkum reservoir (1956)','box':[69.25,70.05,40.22,40.42],'kind':'marsh'},
 {'name':'Keban+Karakaya reservoirs (1970s, Euphrates)','box':[38.3,41.3,38.2,39.3],'kind':'marsh'},
 {'name':'Lake Assad (1970s, Euphrates)','box':[37.85,38.65,35.75,36.15],'kind':'saltpan'},
 {'name':'Mingachevir reservoir (1953, Kura)','box':[46.5,47.4,40.6,41.05],'kind':'marsh'},
 {'name':'Toktogul reservoir (1970s, Naryn)','box':[72.25,73.1,41.55,42.0],'kind':'marsh'},
 {'name':'Kapchagay reservoir (1970, Ili)','box':[77.05,78.25,43.70,44.0],'kind':'marsh','ne_poly':True},
 {'name':'Rybinsk reservoir (1941, Volga)','box':[37.5,39.2,57.8,59.1],'kind':'marsh'},
 {'name':'Uglich reservoir (1939, Volga)','box':[37.6,38.9,57.2,57.75],'kind':'marsh'},
 {'name':'Ivankovo reservoir (1937, Volga)','box':[36.5,37.6,56.4,56.9],'kind':'marsh'},
 {'name':'Dnieper cascade (Kyiv sea etc, 1930s-70s)','box':[30.0,33.5,49.5,51.5],'kind':'marsh'},
]
NATURAL_LAKES=[(76.78,42.40,False,None),(73.45,39.03,True,None),(75.12,41.83,True,None),(75.31,40.61,True,None),
 # AMBER BAND (step 6): all six freeze - no warm lake up here. Malaren whitelisted for 1271 ONLY
 # (762 renders it as open Baltic via the strip_00_762 relief; a lake on top would be wrong).
 (13.5,58.9,True,None),(14.55,58.3,True,None),(17.3,59.45,True,'1271'),
 (27.5,58.4,True,None),(31.3,58.3,True,None),(31.6,60.4,True,None)]  # (lon,lat,freezes,era)
_NELAKE_CACHE={}
def paint_natural_lakes(img,geo,eph,era='1271'):
    # rasterize the NE-lakes polygon for each whitelisted high lake that falls in frame
    import shapefile as _shp, cv2
    W,E,S,N=geo
    h,w=img.shape[:2]
    try: rd=_NELAKE_CACHE.setdefault('rd',_shp.Reader('/sessions/jolly-charming-gates/mnt/outputs/work/ne_lakes/ne_10m_lakes'))
    except Exception: return img
    ICE=(226,232,238)
    for lo,la,frz,lkera in NATURAL_LAKES:
        if lkera and lkera!=era: continue
        if not(W<lo<E and S<la<N): continue
        for sr in rd.iterShapes():
            bb=sr.bbox
            if not(bb[0]-0.05<=lo<=bb[2]+0.05 and bb[1]-0.05<=la<=bb[3]+0.05): continue
            if (bb[2]-bb[0])>3.5: continue
            pts=[]
            parts=list(sr.parts)+[len(sr.points)]
            ring=[((x-W)/(E-W)*w,(N-y)/(N-S)*h) for x,y in sr.points[parts[0]:parts[1]]]
            if len(ring)<3: continue
            mask=np.zeros((h,w),np.uint8)
            cv2.fillPoly(mask,[np.array(ring,np.int32)],1)
            if mask.sum()<6: continue
            img[mask>0]=(112,148,188)                       # CRISP shoreline (Kris)
            if frz: eph.append((mask>0,ICE,['winter']))
            break
        else:
            # not in the NE shapefile (only the giants are): FLOOD THE DEM - high lakes sit as flat
            # plateaus in GEBCO, so the connected near-level region around the point IS the lake.
            R=0.35
            px0=int((lo-R-W)/(E-W)*w); px1=int((lo+R-W)/(E-W)*w)
            py0=int((N-la-R)/(N-S)*h); py1=int((N-la+R)/(N-S)*h)
            px0=max(0,px0); py0=max(0,py0); px1=min(w,px1); py1=min(h,py1)
            if px1-px0<6 or py1-py0<6: continue
            gw2=px1-px0; gh2=py1-py0
            dg=np.zeros((gh2,gw2),np.float32)
            for gy in range(gh2):
                for gx in range(0,gw2):
                    dg[gy,gx]=dem_at(W+(px0+gx)/w*(E-W),N-(py0+gy)/h*(N-S))[0]
            e0=dem_at(lo,la)[0]
            level=(dg<e0+4.0).astype(np.uint8)   # <= surface+4: includes lake BATHYMETRY (Karakul's floor is 200 m down in GEBCO)
            ncc,lab3=cv2.connectedComponents(level,8)
            cy0=min(gh2-1,max(0,int((N-la)/(N-S)*h)-py0)); cx0=min(gw2-1,max(0,int((lo-W)/(E-W)*w)-px0))
            l0=lab3[cy0,cx0]
            if l0>0 and (lab3==l0).sum()>=8:
                mk=(lab3==l0)>0
                sub2=img[py0:py1,px0:px1]
                sub2[mk]=(112,148,188)                        # CRISP shoreline (Kris)
                img[py0:py1,px0:px1]=sub2
                if frz:
                    M=np.zeros((h,w),np.bool_); M[py0:py1,px0:px1]=mk
                    eph.append((M,(226,232,238),['winter']))
    return img
MARSH_POLYS=[
 {'name':'Pripyat marshes','box':[26.0,30.0,51.3,52.3],'maxelev':165,'maxrel':35},
]
def paint_marsh_polys(img,geo,FORBID,rng):
    # natural wetlands: the v3.7 marsh wash over LOW FLAT ground in the box; the baked rivers
    # thread through untouched (excluded from the wash) - no skeleton needed, they are real.
    import cv2
    W,E,S,N=geo
    h,w=img.shape[:2]
    b16=img.astype(np.int16)
    blue=((b16[:,:,2]>b16[:,:,0]+12)&(b16[:,:,2]>b16[:,:,1]+4)).astype(np.uint8)
    for MP in MARSH_POLYS:
        lw,le,ls,ln=MP['box']
        if le<W or lw>E or ln<S or ls>N: continue
        x0=int(max(0,(lw-W)/(E-W)*w)); x1=int(min(w,(le-W)/(E-W)*w))
        y0=int(max(0,(N-ln)/(N-S)*h)); y1=int(min(h,(N-ls)/(N-S)*h))
        if x1-x0<8 or y1-y0<8: continue
        bh0,bw0=y1-y0,x1-x0
        step=max(3,bw0//160)
        wet=np.zeros((bh0//step+2,bw0//step+2),np.uint8)
        for gy in range(wet.shape[0]):
            for gx in range(wet.shape[1]):
                px=x0+gx*step; py=y0+gy*step
                if px>=w or py>=h: continue
                lon=W+px/w*(E-W); lat=N-py/h*(N-S)
                ev,rel=dem_at(lon,lat)
                if ev<=MP['maxelev'] and rel<=MP['maxrel']: wet[gy,gx]=1
        wet=cv2.resize(wet,(bw0,bh0),interpolation=cv2.INTER_NEAREST)
        wet=cv2.morphologyEx(wet,cv2.MORPH_CLOSE,np.ones((7,7),np.uint8))
        wet=cv2.morphologyEx(wet,cv2.MORPH_OPEN,np.ones((5,5),np.uint8))
        if not wet.any(): continue
        az=cv2.GaussianBlur(wet.astype(np.float32),(0,0),3.0)
        # a GREAT marsh is a MOSAIC of bog and dry islands, not a blanket: big-scale cloud noise
        # gates presence; glyphs only in the bog hearts
        nz=rng.uniform(0,1,(max(2,bh0//14),max(2,bw0//14))).astype(np.float32)
        nz=cv2.resize(cv2.GaussianBlur(nz,(0,0),1.0),(bw0,bh0))
        big=rng.uniform(0,1,(max(2,bh0//60),max(2,bw0//60))).astype(np.float32)
        big=cv2.resize(cv2.GaussianBlur(big,(0,0),1.2),(bw0,bh0))
        big=(big-big.min())/(np.ptp(big)+1e-9)
        marshiness=np.clip((big-0.30)/0.40,0,1)
        aw=np.clip(az,0,1)*marshiness*(0.72+0.15*nz)
        subblue=blue[y0:y1,x0:x1]>0
        aw[subblue]=0                                   # the real rivers thread through untouched
        wash=np.array((148,163,126),np.float32)
        patch=img[y0:y1,x0:x1].astype(np.float32)
        patch=patch*(1-aw[...,None])+wash[None,None,:]*aw[...,None]
        rvpx=img[y0:y1,x0:x1][subblue]
        rcol=tuple(int(v) for v in np.median(rvpx,axis=0)) if subblue.sum()>8 else (95,150,205)
        inner=(cv2.erode(wet,np.ones((5,5),np.uint8))>0)&(aw>0.52)   # bars only in the bog hearts
        rivwide=cv2.dilate(subblue.astype(np.uint8),np.ones((5,5),np.uint8))>0
        rng2=np.random.default_rng(31)
        gy=4
        while gy<bh0-3:
            for jx in range(5,bw0-5,9):
                if not inner[gy,jx] or rivwide[gy,jx]: continue
                cv2.line(patch,(jx-3,gy),(jx+3,gy),rcol,1)
            gy+=7+int(rng2.uniform(0,4))
        img[y0:y1,x0:x1]=np.clip(patch,0,255).astype(np.uint8)
        FORBID[y0:y1,x0:x1]|=(aw>0.3)
    return img
def anachronize(img,geo,seed=5,era='1271'):
    FORBID=np.zeros(img.shape[:2],np.bool_)
    # v3.4 (Kris round 3): recolour only the LAKE CORE (morph-OPEN kills thin river lines so the
    # rivers survive untouched); feathered pan edge; marsh = 762 convention (light green wash +
    # horizontal-dash glyphs); ephemeral lake = contiguous inset region of the pan, not a bbox.
    import cv2
    W,E,S,N=geo
    h,w=img.shape[:2]
    b16=img.astype(np.int16)
    blue=((b16[:,:,2]>b16[:,:,0]+12)&(b16[:,:,2]>b16[:,:,1]+4)).astype(np.uint8)
    rng=np.random.default_rng(seed)
    eph=[]
    img=paint_natural_lakes(img,geo,eph,era)
    img=paint_marsh_polys(img,geo,FORBID,rng)
    for L in ANACHRON:
        lw,le,ls,ln=L['box']
        if le<W or lw>E or ln<S or ls>N: continue
        x0=int(max(0,(lw-W)/(E-W)*w)); x1=int(min(w,(le-W)/(E-W)*w))
        y0=int(max(0,(N-ln)/(N-S)*h)); y1=int(min(h,(N-ls)/(N-S)*h))
        if x1<=x0+4 or y1<=y0+4: continue
        subb=blue[y0:y1,x0:x1]
        if not subb.any() and not L.get('ne_poly'): continue
        if L.get('ne_poly'):
            try:
                import shapefile as _shp
                rd=_NELAKE_CACHE.setdefault('rd',_shp.Reader('/sessions/jolly-charming-gates/mnt/outputs/work/ne_lakes/ne_10m_lakes'))
                cxl=(lw+le)/2.0; cyl=(ls+ln)/2.0
                for sr in rd.iterShapes():
                    bb=sr.bbox
                    if not(bb[0]<=cxl<=bb[2] and bb[1]<=cyl<=bb[3]): continue
                    parts=list(sr.parts)+[len(sr.points)]
                    ring=[((x-W)/(E-W)*w-x0,(N-y)/(N-S)*h-y0) for x,y in sr.points[parts[0]:parts[1]]]
                    pm=np.zeros((y1-y0,x1-x0),np.uint8)
                    cv2.fillPoly(pm,[np.array(ring,np.int32)],1)
                    if pm.sum()>=30: subb=np.maximum(subb,pm)
                    break
            except Exception: pass
        if not subb.any(): continue
        # lake body by LOCAL WIDTH: rivers are <=2px (thickness ~0.95) on every chart, reservoir
        # blobs run >=1.2; seed there and grow geodesically inside the blue (4 steps - stays on the
        # blob, barely leaks down connected rivers)
        _dt=cv2.distanceTransform(subb,cv2.DIST_L2,3)
        core=(_dt>=1.2).astype(np.uint8)
        for _gi in range(4): core=cv2.dilate(core,np.ones((3,3),np.uint8))&subb
        nl,ll=cv2.connectedComponents(core,8)
        keep=np.zeros_like(core)
        for l3 in range(1,nl):
            if (ll==l3).sum()>=40: keep|=(ll==l3).astype(np.uint8)
        core=keep
        if not core.any(): continue
        fill_mask=cv2.dilate(core,np.ones((5,5),np.uint8)).astype(np.float32)
        a=cv2.GaussianBlur(fill_mask,(0,0),2.4)                              # SOFT-EDGED pan/marsh (Kris)
        a=np.clip(a,0,1)
        patch=img[y0:y1,x0:x1].astype(np.float32)
        bh0,bw0=y1-y0,x1-x0
        if L['kind']=='saltpan':
            base=np.array((212,206,190),np.float32)
            nz=rng.uniform(-7,7,(bh0,bw0,1)).astype(np.float32)
            fill=np.clip(base[None,None,:]+nz,0,255)
            patch=patch*(1-a[...,None])+fill*a[...,None]
        else:
            # MARSH v3.7: opaque 762 wash; river = SKELETON of the drowned bed (every reservoir arm
            # was a river valley - no invented centrelines); bars on an even offset grid.
            wash=np.array((145,160,122),np.float32)   # Kris's exact sampled 762 marsh green
            zone=cv2.dilate(core,np.ones((9,9),np.uint8))
            az=cv2.GaussianBlur(zone.astype(np.float32),(0,0),2.0)
            nz=rng.uniform(0,1,(max(2,bh0//14),max(2,bw0//14))).astype(np.float32)
            nz=cv2.resize(cv2.GaussianBlur(nz,(0,0),1.0),(bw0,bh0))
            aw=np.clip(az,0,1)                                      # fully opaque; only the rim feathers
            patch=patch*(1-aw[...,None])+wash[None,None,:]*aw[...,None]
            rvpx=img[y0:y1,x0:x1][(subb>0)&(core==0)]
            rcol=tuple(int(v) for v in np.median(rvpx,axis=0)) if len(rvpx)>8 else (95,150,205)
            from skimage.morphology import skeletonize
            skel=skeletonize(core>0)
            riv=cv2.dilate(skel.astype(np.uint8),np.ones((2,2),np.uint8))
            rivwide=cv2.dilate(riv,np.ones((5,5),np.uint8))
            inner=cv2.erode(zone,np.ones((3,3),np.uint8))
            gy=3
            while gy<bh0-2:
                for jx in range(4,bw0-4,7):                          # EVEN spacing along the row (Kris's rule)
                    if not inner[gy,jx] or rivwide[gy,jx]: continue
                    cv2.line(patch,(jx-2,gy),(jx+1,gy),rcol,1)       # dash in the PRIMARY RIVER colour
                gy+=5+int(rng.uniform(0,3))                          # rows: vertical distance varies slightly
            patch[riv>0]=rcol                                        # the river rides on top
        img[y0:y1,x0:x1]=np.clip(patch,0,255).astype(np.uint8)
        FORBID[y0:y1,x0:x1]|=(fill_mask>0)   # nothing farms a salt pan or a marsh
        if L.get('ephemeral'):
            # the spring lake = ONE CONTIGUOUS inset section of the pan (Kris's model): interior
            # pixels a set distance in from the pan edge, largest component inside the seed box.
            E2=L['ephemeral']
            dist=cv2.distanceTransform(core,cv2.DIST_L2,3)
            inset=(dist>max(3.0,float(dist.max())*0.38)).astype(np.uint8)
            ew,ee,es,en=E2['box']
            ex0=int(max(0,(ew-W)/(E-W)*w))-x0; ex1=int(min(w,(ee-W)/(E-W)*w))-x0
            ey0=int(max(0,(N-en)/(N-S)*h))-y0; ey1=int(min(h,(N-es)/(N-S)*h))-y0
            ncc,lab2=cv2.connectedComponents(inset,8)
            best=0; bestn=0
            for l2 in range(1,ncc):
                m2=(lab2==l2)
                sel=m2[max(0,ey0):max(0,ey1),max(0,ex0):max(0,ex1)].sum()
                if sel>bestn: bestn=sel; best=l2
            if best>0:
                lk=(lab2==best).astype(np.float32)
                lk=cv2.GaussianBlur(lk,(0,0),2.0)>0.4
                m=np.zeros((h,w),np.bool_)
                m[y0:y1,x0:x1]=lk
                if m.any(): eph.append((m,E2['col'],E2['seasons']))
    return img,eph,FORBID
def _pick(rng,pal):
    r=rng.uniform(); acc=0
    for col,wt in pal:
        acc+=wt
        if r<=acc: return col
    return pal[-1][0]
def fields_multi(img,geo,settle,seed=7,seasons=None,roads=None,forbid=None):
    """Quilt v3 (Kris, matching the 762 Bukhara reference): a CONTIGUOUS voronoi mosaic of irregular
    polygonal patches, banded along rivers and roads, clipped per-pixel to a flat-land mask (so it can
    never lap onto water), with thin dark boundaries between patches. Acreage ~ r^2, discounted for
    maritime/canal grain imports (SEAFED); megacity acreage farms OUT along the corridors."""
    import cv2
    W,E,S,N=geo
    h,w=img.shape[:2]
    ppx=w/(E-W); ppy=h/(N-S)
    seasons=seasons or SEASONS
    rng=np.random.default_rng(seed)
    b16=img.astype(np.int16)
    blue=((b16[:,:,2]>b16[:,:,0]+12)&(b16[:,:,2]>b16[:,:,1]+4)).astype(np.uint8)
    water_hard=cv2.dilate(blue,np.ones((3,3),np.uint8))          # only the water itself (fields run to the bank - Kris)
    water_wide=water_hard
    river_near=cv2.dilate(blue,np.ones((25,25),np.uint8))       # and LOVE the riverside
    driver=cv2.distanceTransform(1-blue,cv2.DIST_L2,3)           # px to nearest watercourse
    rg=b16[:,:,0]-b16[:,:,1]
    arid=(rg>4).astype(np.uint8)                                 # tan/sand ground (r>g): crops live by water or not at all
    arid=cv2.medianBlur(arid,5)
    labelmap=np.zeros((h,w),np.int32); nextlab=1
    labcol={}
    for name,lo,la,rkm in settle:
        if not(W-0.5<lo<E+0.5 and S-0.5<la<N+0.5): continue
        e0,_=dem_at(lo,la)
        rdeg=rkm/(111.0*math.cos(math.radians(la)))
        rpx=max(6.0,rdeg*ppx)
        cx=(lo-W)*ppx; cy=(N-la)*ppy
        frac=1.0-SEAFED.get(name,0.0)
        target_area=math.pi*rpx*rpx*0.58*frac                    # the acreage, in px^2
        reach=rpx*(4.0 if rkm>=45 else 2.6)                      # megacities farm out farther
        x0=int(max(0,cx-reach)); x1=int(min(w,cx+reach)); y0=int(max(0,cy-reach)); y1=int(min(h,cy+reach))
        if x1-x0<8 or y1-y0<8: continue
        bw=x1-x0; bh=y1-y0
        # ---- flatness on a coarse grid ----
        step=max(3,int(rpx/14))
        flat=np.zeros((bh//step+2,bw//step+2),np.uint8)
        for gy in range(flat.shape[0]):
            for gx in range(flat.shape[1]):
                px=x0+gx*step; py=y0+gy*step
                if px>=w or py>=h: continue
                lon=W+px/ppx; lat=N-py/ppy
                ev,rel=dem_at(lon,lat)
                if ev<=e0+140 and rel<=90: flat[gy,gx]=1
                elif ((px-cx)**2+(py-cy)**2)<(rpx*0.55)**2 and ev<=e0+220 and rel<=170: flat[gy,gx]=1   # QUILT v3.1b (Kris, Chach): the garden disc is levelled ground even where the DEM smears foothills over the town
        flat=cv2.resize(flat,(bw,bh),interpolation=cv2.INTER_NEAREST)
        # ---- desirability: near town, near road, near river; must be flat and dry ----
        yy,xx=np.mgrid[y0:y1,x0:x1]
        dtown=np.hypot(xx-cx,yy-cy)
        des=np.clip(1.0-dtown/(rpx*1.3),0,1)**0.6                # strong core: the town disc fills first
        if roads:
            rmask=np.zeros((bh,bw),np.uint8)
            for poly in roads:
                pts=np.array([[int(qx-x0),int(qy-y0)] for qx,qy in poly],np.int32)
                if len(pts)>1: cv2.polylines(rmask,[pts],False,1,1)
            if rmask.any():
                dro=cv2.distanceTransform(1-rmask,cv2.DIST_L2,3)
                roaddes=np.clip(1.0-dro/(rpx*0.7),0,1)*0.66
                _arid0=arid[y0:y1,x0:x1]>0
                _dryish=driver[y0:y1,x0:x1]>(rpx*0.4)
                roaddes[_arid0&_dryish]=0
                des=np.maximum(des,roaddes)
        des=np.maximum(des,river_near[y0:y1,x0:x1].astype(np.float32)*0.9)   # the river pull, strengthened (Kris)
        # ARID RULE (Kris: the Balkh-road leg was crops marching into desert): on arid-coloured ground,
        # fields may not stand farther than ~half a town-radius from a watercourse - except the small
        # qanat-garden belt at the town itself.
        _ar=arid[y0:y1,x0:x1]>0
        _dry=driver[y0:y1,x0:x1]>(rpx*0.5)
        _gard=dtown<(rpx*0.35)
        des[_ar&_dry&~_gard]=0
        des*= flat.astype(np.float32)
        des*=(1-water_wide[y0:y1,x0:x1].astype(np.float32))
        des*=np.clip(1.0-dtown/reach,0,1)**0.5                   # everything fades with distance from town
        _nz=rng.uniform(0,1,(max(2,bh//24),max(2,bw//24))).astype(np.float32)
        _nz=cv2.resize(cv2.GaussianBlur(_nz,(0,0),1.1),(bw,bh))
        des*=(0.7+0.6*_nz)                                       # low-freq noise breaks the circular rim
        if forbid is not None: des[forbid[y0:y1,x0:x1]]=0
        # ---- grow the mask from most-desirable pixels down, until the acreage is met ----
        order=np.argsort(des,axis=None)[::-1]
        need=int(target_area)
        flatidx=order[:max(1,need)]
        good=des.flatten()[flatidx]>0.12
        flatidx=flatidx[good]
        if flatidx.size<30: continue
        mask=np.zeros(bh*bw,np.uint8); mask[flatidx]=1; mask=mask.reshape(bh,bw)
        mask=cv2.morphologyEx(mask,cv2.MORPH_CLOSE,np.ones((5,5),np.uint8))
        mask=cv2.morphologyEx(mask,cv2.MORPH_OPEN,np.ones((3,3),np.uint8))
        mask&=(1-water_wide[y0:y1,x0:x1])
        # ---- QUILT v3.1 (Kris, the Chach bug): the docstring promised CONTIGUOUS and the greedy
        # top-K never enforced it - a far riverbank could outscore the town's own edge and the quilt
        # spawned detached. Keep components touching the town; a large detached block is not dropped
        # but JOINED by a canal-side strip (the arik that would water it).
        _cxl=int(cx-x0); _cyl=int(cy-y0)
        _n,_cl=cv2.connectedComponents(mask,connectivity=8)
        _win=_cl[max(0,_cyl-4):_cyl+5,max(0,_cxl-4):_cxl+5]
        _tl=set(int(v) for v in np.unique(_win) if v>0)
        if not _tl and mask.any():
            _ys,_xs=np.nonzero(mask)
            _j=int(np.argmin((_xs-_cxl)**2+(_ys-_cyl)**2))
            cv2.line(mask,(_cxl,_cyl),(int(_xs[_j]),int(_ys[_j])),1,3)
            _n,_cl=cv2.connectedComponents(mask,connectivity=8)
            _win=_cl[max(0,_cyl-4):_cyl+5,max(0,_cxl-4):_cxl+5]
            _tl=set(int(v) for v in np.unique(_win) if v>0)
        if _tl:
            _keep=np.isin(_cl,list(_tl))
            _det=(mask>0)&~_keep
            if _det.sum()>0.30*max(1,int(mask.sum())):
                _n2,_c2,_st2,_ce2=cv2.connectedComponentsWithStats(_det.astype(np.uint8),connectivity=8)
                if _n2>1:
                    _big=1+int(np.argmax(_st2[1:,cv2.CC_STAT_AREA]))
                    _bx,_by=_ce2[_big]
                    _m2=(_keep|(_c2==_big)).astype(np.uint8)
                    cv2.line(_m2,(_cxl,_cyl),(int(_bx),int(_by)),1,3)
                    mask=_m2&(1-water_wide[y0:y1,x0:x1])
                else:
                    mask=_keep.astype(np.uint8)
            else:
                mask=_keep.astype(np.uint8)
        # ---- voronoi tessellation inside the mask ----
        kmpp2=(E-W)*111.0*math.cos(math.radians((S+N)/2))/w
        cell=max(3.5,6.0/kmpp2)   # UNIFORM ~6 km patches for every settlement (Kris) - acreage varies by EXTENT, not patch size
        seedsim=np.ones((bh,bw),np.uint8)
        nseeds=0
        gstep=int(cell)
        for gy in range(0,bh,gstep):
            for gx in range(0,bw,gstep):
                sx=int(gx+rng.uniform(0,gstep)); sy=int(gy+rng.uniform(0,gstep))
                if sx<bw and sy<bh and mask[sy,sx]:
                    seedsim[sy,sx]=0; nseeds+=1
        if nseeds<3: continue
        dist,labs=cv2.distanceTransformWithLabels(seedsim,cv2.DIST_L2,3,labelType=cv2.DIST_LABEL_PIXEL)
        labs=labs.astype(np.int32)
        labs[mask==0]=0
        sub=labelmap[y0:y1,x0:x1]
        put=(labs>0)&(sub==0)
        sub[put]=labs[put]+nextlab
        labelmap[y0:y1,x0:x1]=sub
        for l in np.unique(labs[put]):
            labcol[int(l)+nextlab]=int(rng.integers(0,10**9))
        nextlab+=int(labs.max())+1
    # ---- paint per season: colour LUT by label, thin dark boundaries, feathered alpha ----
    import cv2 as _cv
    inside=(labelmap>0)
    if not inside.any():
        return {sn:img.copy() for sn in seasons}
    alpha=_cv.GaussianBlur(inside.astype(np.float32)*0.72,(0,0),1.7)   # soft OUTER fade only (762 look)
    inv=(~inside).astype(np.uint8)
    _d2,_lab2=_cv.distanceTransformWithLabels(inv,_cv.DIST_L2,3,labelType=_cv.DIST_LABEL_PIXEL)
    _zeros=np.argwhere(inv==0)
    _lab2=_lab2.astype(np.int64)
    out={}
    labs_all=np.array(sorted(labcol.keys()),np.int32)
    for season in seasons:
        pal=PALS[season]
        lut={}
        for l in labs_all:
            r2=np.random.default_rng(labcol[int(l)]+hash(season)%10**6)
            lut[int(l)]=_pick(r2,pal)
        colimg=np.zeros((h,w,3),np.float32)
        flatl=labelmap[inside]
        cols=np.zeros((int(labelmap.max())+1,3),np.float32)
        for l,c in lut.items(): cols[l]=c
        colimg[inside]=cols[flatl]
        _near=_zeros[np.clip(_lab2-1,0,len(_zeros)-1)]
        _ext=colimg[_near[...,0],_near[...,1]]
        colimg=np.where(inside[...,None],colimg,_ext)   # rim blends CROP colour, never raster black
        o=img.astype(np.float32)
        o=o*(1-alpha[...,None])+colimg*alpha[...,None]
        out[season]=np.clip(o,0,255).astype(np.uint8)
    return out
def add_fields(img,geo,settle,seed=7,season='summer',roads=None):
    return fields_multi(img,geo,settle,seed=seed,seasons=[season],roads=roads)[season]

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

def relief_boost(img,geo,OW,OH,dem_grid_fn=None,alpine=False):
    """slice-time contrast + snow (Kris: 1271 charts read flatter than 762; Taurus should look like mountains)"""
    import numpy as np, cv2, math
    W,E,S,N=geo
    d=_dem_for_rect(W,E,S,N,OW,OH)
    gy,gx=np.gradient(d,(N-S)/OH*111000.0,(E-W)/OW*111000.0*math.cos(math.radians((S+N)/2)))
    az=math.radians(315); alt=math.radians(45)
    slope=np.arctan(np.hypot(gx,gy)*3.0); aspect=np.arctan2(-gx,gy)
    hs=np.clip(np.sin(alt)*np.cos(slope)+math.cos(alt)*np.sin(slope)*np.cos(az-aspect),0.0,1.2)
    boost=np.clip(0.54+0.55*hs,0.46,1.06)   # DRIFT FIX: flatland x0.93 as in the approved bakes (was 0.72+: x1.10, +7 bright everywhere)
    out=img.astype(np.float32)
    land=(d>0)
    out[land]*=boost[land][...,None]
    if alpine and E>64 and W<96 and N>36:   # OPT-IN (drift root-cause: this overlay, added for the Ili bake, greened and flattened every southern chart in 64-96E - approved charts predate it)
        lat=np.linspace(N,S,OH,dtype=np.float32)[:,None].repeat(OW,1)
        lon=np.linspace(W,E,OW,dtype=np.float32)[None,:].repeat(OH,0)
        inband=(lon>64)&(lon<96)&(lat>36)
        spr=np.clip((d-1500.0)/300.0,0,1)*np.clip((2950.0-d)/400.0,0,1)*inband
        spr=cv2.GaussianBlur(spr.astype(np.float32),(0,0),2.2)
        SPRUCE=np.array((58,94,60),np.float32)   # canonical conifer green (MAP_NOTES _bake_ili recipe)
        out=out*(1-0.45*spr[...,None])+SPRUCE[None,None,:]*(0.45*spr[...,None])
        fruit=(np.clip((d-900.0)/250.0,0,1)*np.clip((1700.0-d)/250.0,0,1)*((lon>66)&(lon<82)&(lat>39.5)&(lat<45.5)))
        fruit=cv2.GaussianBlur(fruit.astype(np.float32),(0,0),2.2)
        LEAF=np.array((106,130,58),np.float32)   # canonical walnut-fruit broadleaf (MAP_NOTES)
        out=out*(1-0.30*fruit[...,None])+LEAF[None,None,:]*(0.30*fruit[...,None])
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

if __name__=='__main__':
    import sys
    _i0=int(sys.argv[1]) if len(sys.argv)>1 else 0
    _n0=int(sys.argv[2]) if len(sys.argv)>2 else len(CHARTS)
    for fn,geo,OW,OH in CHARTS[_i0:_i0+_n0]:
        W,E,S,N=geo
        slice_master(W,E,S,N,OW,OH,'_tmp_slice.png')
        img=np.array(Image.open('_tmp_slice.png').convert('RGB'))
        img=relief_boost(img,geo,OW,OH)
        img=add_fields(img,geo,SETTLE)
        Image.fromarray(img).save(fn)
        print('rebaked',fn)
