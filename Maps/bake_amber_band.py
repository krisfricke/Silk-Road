# bake_amber_band.py -- STEP 5: the AMBER BAND master row (SPEC_amber_band_step5.md, executed by Zaiton).
# [8,42]x[52,61] @147ppd, 3 strips; sea level 0 everywhere; Swedish/Rus lakes carved; Malaren is a
# LAKE in 1271 and OPEN SEA in 762 (post-glacial rise - strip 0 gets a _762 variant); biomes painted
# by the climate classifier from day one (no eyeballing). Usage: python bake_amber_band.py <strip> [762]
import numpy as np, cv2, json, sys, os, math
from PIL import Image
from scipy.ndimage import gaussian_filter
exec(open('bake_1271_regions_local.py').read().split("R_ANAT=")[0])
import climate_biome as cb

MW,ME,MS,MN=8.0,64.666666666667,52.0,61.0; PPD=147.0   # extended E per Kris (the Volga/Urals tile)
# the land ramp samples PERSIA - build it with the ORIGINAL tiles (or the cache) BEFORE overriding
import pickle
if os.path.exists('_ramp_pers2.pkl'):
    R_PERS=pickle.load(open('_ramp_pers2.pkl','rb'))
else:
    R_PERS=ramp_from('persiacorridor762_summer.png',(43.0,66.0,31.4,40.9),31.6,40.6,43.2,65.7)
    pickle.dump(R_PERS,open('_ramp_pers2.pkl','wb'))
TILES=[('work/geb_amber/gebco_2026_n61.0_s52.0_w8.0_e42.0_geotiff.tif',8.0,42.0,52.0,61.0),
       ('work/geb_amber/gebco_2026_n61.0_s52.0_w42.0_e62.0_geotiff.tif',42.0,62.0,52.0,61.0)]
LAKES=[
 (13.5,58.9, 47.0,(12.2,14.3,58.2,59.5)),   # Vanern
 (14.55,58.3,90.0,(14.2,15.05,57.6,58.9)),  # Vattern
 (27.5,58.4, 33.0,(26.7,28.3,57.7,59.4)),   # Peipus
 (31.3,58.3, 20.0,(30.8,31.9,57.8,58.7)),   # Ilmen
 (31.6,60.4,  8.0,(29.7,33.6,59.7,61.0)),   # Ladoga
]
MALAREN=(17.3,59.45,9.0,(15.8,18.35,59.15,59.75))
COL_BROAD=np.array([78,108,50],np.float32)
COL_CONIF=np.array([48,82,52],np.float32)

def paint_biomes(relief,W,E,S,N,seed=7):
    H,Wpx=relief.shape[:2]
    codes,T,P,ocean=cb.classify_bbox(W,E,S,N,Wpx,H)
    A_FOR=0.62
    rng=np.random.default_rng(seed)
    pres=np.zeros((H,Wpx),np.float32)
    pres[(codes==cb.FOREST)|(codes==cb.TAIGA)]=1.0
    mfs=codes==cb.FSTEP
    if mfs.any():
        ff=gaussian_filter(cb.forest_fraction(T,P),3.0)
        mnoise=gaussian_filter(rng.random((H,Wpx)).astype(np.float32),2.2)
        mnoise=(mnoise-mnoise.min())/(np.ptp(mnoise)+1e-9)
        pres[mfs&(mnoise<ff)]=1.0
    pres=gaussian_filter(pres,1.6)
    blotch=gaussian_filter(rng.random((H,Wpx)).astype(np.float32),4)
    blotch=(blotch-blotch.min())/(np.ptp(blotch)+1e-9)
    pres=pres*A_FOR*(0.85+0.15*blotch)
    water=relief[:,:,2]>relief[:,:,0]+8
    snow=relief.min(2)>195
    pres*=((~water)&(~snow)&(~ocean))
    conif=(codes==cb.TAIGA)[:,:,None]
    col=np.where(conif,COL_CONIF,COL_BROAD)
    fm=pres[:,:,None]
    return relief*(1-fm)+col*fm

def bake_strip(i,W,E,era='1271'):
    Wm,Em=max(MW,W-0.5),min(ME,E+0.5)
    DW=int(round((Em-Wm)*PPD)); DH=int(round((MN-MS)*PPD))
    cache='_dem_amber_%02d.npy'%i
    if os.path.exists(cache): d=np.load(cache)
    else: d=dem(Wm,Em,MS,MN,DW,DH); np.save(cache,d)
    d=d.copy()
    lon=np.linspace(Wm,Em,DW)[None,:].repeat(DH,0); lat=np.linspace(MN,MS,DH)[:,None].repeat(DW,1)
    lakes=list(LAKES)
    if era=='1271': lakes.append(MALAREN)
    else:
        # 762: Malaren is a BAY. Flood-select the SAME basin component the 1271 lake carve uses,
        # sink it below sea level, and carve a generous channel to open Baltic water (the real
        # sluice is sub-pixel at 147ppd).
        slo,sla,lvl,b=MALAREN
        below=((d<lvl)&(lon>=b[0])&(lon<=b[1])&(lat>=b[2])&(lat<=b[3])).astype(np.uint8)
        nmm,labm=cv2.connectedComponents(below,8)
        rm=int((MN-sla)/(MN-MS)*DH); cmn=int((slo-Wm)/(Em-Wm)*DW)
        if 0<=rm<DH and 0<=cmn<DW and labm[rm,cmn]>0:
            d=np.where(labm==labm[rm,cmn],np.minimum(d,-1.0),d)
        # the SODERTALJE passage - Birka's historic southern approach: a thin sound from the
        # lake's south arm to the Himmerfjarden inlet (2px ribbon, no canal-rectangle)
        chan=np.zeros(d.shape,np.uint8)
        pts=[(17.66,59.30),(17.63,59.19),(17.68,59.10),(17.78,59.02)]
        pxs=[(int((lo2-Wm)/(Em-Wm)*DW),int((MN-la2)/(MN-MS)*DH)) for lo2,la2 in pts]
        for k2 in range(len(pxs)-1):
            cv2.line(chan,pxs[k2],pxs[k2+1],1,2)
        d=np.where(chan>0,np.minimum(d,-2.0),d)
    lakem=np.zeros(d.shape,bool)
    for slo,sla,lvl,box in lakes:
        if slo<Wm-0.2 or slo>Em+0.2: continue
        below=((d<lvl)&(lon>=box[0])&(lon<=box[1])&(lat>=box[2])&(lat<=box[3])).astype(np.uint8)
        n_,lab_=cv2.connectedComponents(below,8)
        r0=int((MN-sla)/(MN-MS)*DH); c0=int((slo-Wm)/(Em-Wm)*DW)
        if not (0<=r0<DH and 0<=c0<DW): continue
        cid=lab_[r0,c0]
        if cid>0: d=np.where(lab_==cid,d-lvl,d); lakem|=(lab_==cid)
    SL=np.zeros_like(d)                       # sea level 0 everywhere; no Caspian, no lifts
    seac=(d<SL).astype(np.uint8)
    n0,lab0=cv2.connectedComponents(seac,8)
    edge=set(lab0[0,:]); edge|=set(lab0[-1,:]); edge|=set(lab0[:,0]); edge|=set(lab0[:,-1]); edge.discard(0)
    ocean=np.isin(lab0,list(edge)) if edge else np.zeros(d.shape,bool)
    land=interp(np.clip(d,0,4600),R_PERS)
    sn=np.clip((d-1400.0)/800.0,0,1)*0.55     # the Scandes get a little snow (spec)
    for c in range(3): land[:,:,c]=land[:,:,c]*(1-sn)+245*sn
    gy,gx=np.gradient(np.where(d<SL,0,d),450.0)
    sh=np.clip(np.cos(np.arctan2(gy,-gx)-np.deg2rad(225))*np.arctan(np.hypot(gx,gy)*2.2)/2.2+1.0,0.78,1.18)
    for c in range(3): land[:,:,c]=np.clip(land[:,:,c]*sh,0,255)
    water=(d<SL)&(ocean|lakem)
    sea=interp(np.clip(SL-d,0,3000),SEAR)
    img=np.where(water[:,:,None],sea,land)
    cm=cv2.dilate(water.astype(np.uint8),np.ones((3,3),np.uint8))-water.astype(np.uint8)
    img=np.where(cm[:,:,None]>0,img*0.88,img)
    x0=int(round((W-Wm)*PPD)); x1=x0+int(round((E-W)*PPD))
    relief=np.clip(img,0,255)[:,x0:x1]
    suff=('_762' if era=='762' else '')
    Image.fromarray(relief.astype('uint8')).save('master_amber/strip_%02d%s_relief.png'%(i,suff))
    out=paint_biomes(relief.astype(np.float32),W,E,MS,MN)
    out=np.clip(out+np.random.default_rng(2000+i).normal(0,3.0,(out.shape[0],out.shape[1],1)),0,255)
    Image.fromarray(out.astype('uint8')).save('master_amber/strip_%02d%s.png'%(i,suff))
    return out.shape

os.makedirs('master_amber',exist_ok=True)
n=5; step=11.333333333333334   # strips 0-2 unchanged; 3-4 are the eastern extension
if __name__=='__main__':
    i=int(sys.argv[1]); era=sys.argv[2] if len(sys.argv)>2 else '1271'
    W=MW+i*step; E=MW+(i+1)*step
    sh=bake_strip(i,W,E,era)
    print('amber strip',i,era,'done',sh,flush=True)
    if i==n-1 and era=='1271':
        json.dump({'bounds':[MW,ME,MS,MN],'ppd':PPD,'n':n,'step':step,'files':['master_amber/strip_%02d.png'%k for k in range(n)]},open('master_amber/manifest.json','w'))
        print('MANIFEST OK')
