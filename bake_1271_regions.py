# bake_1271_regions.py — four 1271 region reliefs in one pass (Fadak). Ramps regressed from existing maps.
# Configs: armenia (Tabriz trunk), khwarezm (Horde east; ARAL hand-carved: GEBCO shows its bed as dry land),
# persiasouth (Yazd-Kerman-Hormuz), bactria (Herat-Balkh-Badakhshan-Kashgar).
import numpy as np, cv2, tifffile
from PIL import Image
M='/sessions/confident-gracious-edison/mnt/Claude Enclosure/Silk Road/Maps/'
TILES=[
       ('/tmp/geb/fc/gebco_2026_n33.0_s24.0_w8.0_e28.5_geotiff.tif',8.0,28.5,24.0,33.0),
       ('/tmp/geb/fc/gebco_2026_n52.0_s45.4_w110.0_e123.2_geotiff.tif',110.0,123.2,45.4,52.0),
       ('/tmp/geb/fc/gebco_2026_n52.0_s47.4_w8.0_e27.0_geotiff.tif',8.0,27.0,47.4,52.0),
       ('/tmp/geb/fc/gebco_2026_n61.0_s52.0_w8.0_e42.0_geotiff.tif',8.0,42.0,52.0,61.0),

       ('/tmp/geb/new/gebco_2026_n47.5_s33.0_w8.0_e24.5_geotiff.tif',8.0,24.5,33.0,47.5),
       ('/tmp/geb/new/gebco_2026_n52.0_s45.4_w62.0_e110.0_geotiff.tif',62.0,110.0,45.4,52.0),
('/tmp/geb/bc/gebco_2026_n52.0_s45.26_w27.0_e62.0_geotiff.tif',27.0,62.0,45.26,52.0),
       ('/tmp/geb/wr/gebco_2026_n45.562_s24.109_w24.246_e96.601_geotiff.tif',24.246,96.601,24.109,45.562),
       ('/tmp/geb/io/gebco_2026_n24.1_s0.0_w48.95_e82.609_geotiff.tif',48.95,82.609,0.0,24.1)]
def dem(W,E,S,N,DW,DH):
    res=1/240.; nx,ny=int((E-W)/res),int((N-S)/res)
    out=np.full((ny,nx),np.nan,np.float32)
    for path,tw,te,ts,tn in TILES:
        ow,oe=max(W,tw),min(E,te); os_,on=max(S,ts),min(N,tn)
        if ow>=oe or os_>=on: continue
        a=tifffile.imread(path).astype(np.float32); h,w=a.shape
        rx=(te-tw)/w; ry=(tn-ts)/h
        c0=int(round((ow-tw)/rx)); c1=int(round((oe-tw)/rx)); r0=int(round((tn-on)/ry)); r1=int(round((tn-os_)/ry))
        sub=a[r0:r1,c0:c1]; d0=int(round((ow-W)/res)); e0=int(round((N-on)/res))
        tgt=out[e0:e0+sub.shape[0],d0:d0+sub.shape[1]]
        m=np.isnan(tgt); tgt[m]=sub[:tgt.shape[0],:tgt.shape[1]][m]
    for _ in range(6):
        m=np.isnan(out)
        if not m.any(): break
        sh=np.nanmax(np.stack([np.roll(out,s_,axis=ax) for s_,ax in [(1,0),(-1,0),(1,1),(-1,1)]]),axis=0)
        out[m]=sh[m]
    out=np.nan_to_num(out,nan=300.0)
    return cv2.resize(out,(DW,DH),interpolation=cv2.INTER_AREA)
def ramp_from(imgpath,geo,latlo,lathi,lonlo,lonhi):
    im=np.array(Image.open(M+imgpath).convert('RGB')).astype(np.float32)
    GW,GE,GS,GN=geo; hh,ww=im.shape[:2]
    src=next(tt for tt in TILES if tt[1]<=lonlo and tt[2]>=lonhi and tt[3]<=latlo and tt[4]>=lathi)
    t=tifffile.imread(src[0]).astype(np.float32); TW,TE,TS,TN=src[1:]; th,tw2=t.shape
    lo=np.arange(lonlo,lonhi,0.03); la=np.arange(latlo,lathi,0.03)
    LO,LA=np.meshgrid(lo,la)
    col=im[((GN-LA)/(GN-GS)*hh).astype(int),((LO-GW)/(GE-GW)*ww).astype(int)]
    elev=t[((TN-LA)/(TN-TS)*th).astype(int),((LO-TW)/(TE-TW)*tw2).astype(int)]
    ok=(col.min(axis=2)>60)&(col.max(axis=2)<235)&(elev>0)
    bins=np.array([0,150,400,800,1300,1900,2600,3400,4600])
    r=[]
    for i in range(len(bins)-1):
        m=ok&(elev>=bins[i])&(elev<bins[i+1])
        if m.sum()>60: r.append(((bins[i]+bins[i+1])/2,*col[m].reshape(-1,3).mean(axis=0)))
    return np.array(r,np.float32)
SEAR=np.array([(25,85,131,169),(350,84,129,167),(750,81,127,165),(1500,78,123,162),(3000,72,117,157)],np.float32)
def interp(v,tab):
    o=np.zeros(v.shape+(3,))
    for c in range(3): o[:,:,c]=np.interp(v,tab[:,0],tab[:,c+1])
    return o
def bake(name,W,E,S,N,DW,DH,ramp,sealon=None,grass=None,carve=None,lift=None):
    d=dem(W,E,S,N,DW,DH)
    lon=np.linspace(W,E,DW)[None,:].repeat(DH,0); lat=np.linspace(N,S,DH)[:,None].repeat(DW,1)
    SL=np.where(lon>sealon,-26.5,0.0) if sealon is not None else np.zeros_like(d)
    if carve is not None:   # carve items: (seed_lon,seed_lat,surface_elev[,box]) box=(lonlo,lonhi,latlo,lathi)
      lakem=np.zeros(d.shape,bool)
      for cv_ in (carve if isinstance(carve,list) else [carve]):
        slo,sla,lvl=cv_[:3]; box=cv_[3] if len(cv_)>3 else None
        below=(d<lvl).astype(np.uint8)
        if box is not None: below&=((lon>=box[0])&(lon<=box[1])&(lat>=box[2])&(lat<=box[3])).astype(np.uint8)
        n_,lab_=cv2.connectedComponents(below,8)
        cid=lab_[int((N-sla)/(N-S)*DH),int((slo-W)/(E-W)*DW)]
        d=np.where(lab_==cid, d-lvl, d); lakem|=(lab_==cid)
    if lift is not None:    # lift = (lonlo,lonhi,latlo,lathi): dry below-0 land in an ENDORHEIC depression is
        lo,hi,la0,la1=lift  # NOT sea - remap it to gentle positive tones so the painter (d<=0 -> water) skips it
        dry=(lon>=lo)&(lon<=hi)&(lat>=la0)&(lat<=la1)&(d<0)
        if carve is not None: dry&=~lakem
        d=np.where(dry, 1.0+(np.maximum(d,-450.0)+450.0)/6.0, d)
    land=interp(np.clip(d,0,4600),ramp)
    if grass is not None:
        g=np.clip((lat-grass[0])/grass[1],0,1)*np.clip((900-d)/900,0,1)
        g=cv2.GaussianBlur(g.astype(np.float32),(0,0),8)*0.5
        for c,gv in enumerate((118,136,84)): land[:,:,c]=land[:,:,c]*(1-g)+gv*g
    gy,gx=np.gradient(np.where(d<0,0,d),450.0)
    sh=np.clip(np.cos(np.arctan2(gy,-gx)-np.deg2rad(225))*np.arctan(np.hypot(gx,gy)*2.2)/2.2+1.0,0.78,1.18)
    for c in range(3): land[:,:,c]=np.clip(land[:,:,c]*sh,0,255)
    sea=interp(np.clip(SL-d,0,3000),SEAR)
    img=np.where((d<=SL)[:,:,None],sea,land)
    cm=cv2.dilate((d<=SL).astype(np.uint8),np.ones((3,3),np.uint8))-(d<=SL).astype(np.uint8)
    img=np.where(cm[:,:,None]>0,img*0.88,img)
    img=np.clip(img+np.random.default_rng(1271).normal(0,3.0,(DH,DW,1)),0,255)
    Image.fromarray(img.astype('uint8')).save(M+name); print('baked',name)
R_ANAT=ramp_from('anatolia_relief_setout_summer.png',(23.803,40.49,30.402,42.295),35.2,42.0,28.6,40.3)
R_PERS=ramp_from('persiacorridor762_summer.png',(43.0,66.0,31.4,40.9),31.6,40.6,43.2,65.7)
R_TAK=ramp_from('taklamakan762_summer.png',(71,95,35,44.7),35.2,44.5,71.2,94.8)
ARAL=(59.5,45.0,53.0)
bake('armenia1271.png',28.5,49.5,35.0,42.5,1980,714,R_ANAT,sealon=48.0)
bake('khwarezm1271.png',45.0,72.0,37.0,49.5,1980,917,R_TAK,sealon=None,grass=(43,6),carve=ARAL)
bake('persiasouth1271.png',44.0,60.0,25.5,34.5,1980,1114,R_PERS)
bake('bactria1271.png',58.0,78.0,32.0,41.0,1980,891,R_PERS)
