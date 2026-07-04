# bake_master.py - THE 1271 MASTER RELIEF (Kris ruling 07-04): one contiguous base, sliced per chart.
# Bounds [8,123]x[24,52] @ 147 px/deg -> 16,905 x 4,116 total, baked as 8 lon-strips with 0.5-deg overlap
# margins (hillshade continuity), cropped to butt-joint. Summer only in v1; seasons + biome passes accrete.
# Carves: Aral +53, Issyk-Kul +1607, Dead Sea -395, Galilee -205 (boxed); lifts: Jordan rift, Turfan, Qattara.
# Caspian: regional sea-level -26.5 in its box. Tibet: hypsometric BROWN plateau >3000m, snow only >5300m
# (the Oxus rule - no more all-white Tibet). Slice with slice_master.py.
import numpy as np, cv2, json, sys, math
from PIL import Image
exec(open(__file__.replace('bake_master.py','bake_1271_regions.py')).read().split("R_ANAT=")[0])
MW,ME,MS,MN=8.0,123.0,24.0,52.0; PPD=147.0
R_PERS=ramp_from('persiacorridor762_summer.png',(43.0,66.0,31.4,40.9),31.6,40.6,43.2,65.7)
LAKES=[(59.5,45.0,53.0,(56.0,62.5,43.0,47.5)),(77.5,42.45,1607.0,(76.0,78.5,41.9,42.8)),
       (35.50,31.50,-395.0,(35.2,35.75,30.9,31.9)),(35.59,32.83,-205.0,(35.45,35.72,32.6,33.05))]
LIFTS=[(35.0,36.05,29.8,33.45),(87.0,90.5,41.8,43.6),(26.0,29.6,28.3,30.8)]
CASP=(44.5,56.5,36.0,48.2,-26.5)
def bake_strip(i,W,E):
    Wm,Em=max(MW,W-0.5),min(ME,E+0.5)
    DW=int(round((Em-Wm)*PPD)); DH=int(round((MN-MS)*PPD))
    d=dem(Wm,Em,MS,MN,DW,DH)
    lon=np.linspace(Wm,Em,DW)[None,:].repeat(DH,0); lat=np.linspace(MN,MS,DH)[:,None].repeat(DW,1)
    SL=np.zeros_like(d)
    cb=CASP; SL=np.where((lon>=cb[0])&(lon<=cb[1])&(lat>=cb[2])&(lat<=cb[3]),cb[4],SL)
    lakem=np.zeros(d.shape,bool)
    for slo,sla,lvl,box in LAKES:
        if slo<Wm-0.2 or slo>Em+0.2: continue
        below=((d<lvl)&(lon>=box[0])&(lon<=box[1])&(lat>=box[2])&(lat<=box[3])).astype(np.uint8)
        n_,lab_=cv2.connectedComponents(below,8)
        r0=int((MN-sla)/(MN-MS)*DH); c0=int((slo-Wm)/(Em-Wm)*DW)
        if not (0<=r0<DH and 0<=c0<DW): continue
        cid=lab_[r0,c0]
        if cid>0: d=np.where(lab_==cid,d-lvl,d); lakem|=(lab_==cid)
    seac=(d<SL).astype(np.uint8)
    n0,lab0=cv2.connectedComponents(seac,8)
    edge=set(lab0[0,:]); edge|=set(lab0[-1,:]); edge|=set(lab0[:,0]); edge|=set(lab0[:,-1]); edge.discard(0)
    ocean=np.isin(lab0,list(edge)) if edge else np.zeros(d.shape,bool)
    ocean|=((lon>=cb[0])&(lon<=cb[1])&(lat>=cb[2])&(lat<=cb[3])&(d<SL))
    for lo,hi,la0,la1 in LIFTS:
        dry=(lon>=lo)&(lon<=hi)&(lat>=la0)&(lat<=la1)&(d<SL)&~lakem&~ocean
        d=np.where(dry,1.0+(np.maximum(d,-450.0)+450.0)/6.0,d)
    land=interp(np.clip(d,0,4600),R_PERS)
    pl=np.clip((d-3000.0)/800.0,0,1)*0.7
    for c,bv in enumerate((139,105,72)): land[:,:,c]=land[:,:,c]*(1-pl)+bv*pl
    sn=np.clip((d-5300.0)/500.0,0,1)
    for c in range(3): land[:,:,c]=land[:,:,c]*(1-sn)+245*sn
    gy,gx=np.gradient(np.where(d<SL,0,d),450.0)
    sh=np.clip(np.cos(np.arctan2(gy,-gx)-np.deg2rad(225))*np.arctan(np.hypot(gx,gy)*2.2)/2.2+1.0,0.78,1.18)
    for c in range(3): land[:,:,c]=np.clip(land[:,:,c]*sh,0,255)
    water=(d<SL)&(ocean|lakem|( (d<SL)&~np.zeros(d.shape,bool) ))
    water=(d<SL)
    sea=interp(np.clip(SL-d,0,3000),SEAR)
    img=np.where(water[:,:,None],sea,land)
    cm=cv2.dilate(water.astype(np.uint8),np.ones((3,3),np.uint8))-water.astype(np.uint8)
    img=np.where(cm[:,:,None]>0,img*0.88,img)
    img=np.clip(img+np.random.default_rng(1000+i).normal(0,3.0,(DH,DW,1)),0,255)
    x0=int(round((W-Wm)*PPD)); x1=x0+int(round((E-W)*PPD))
    out=img[:,x0:x1]
    Image.fromarray(out.astype('uint8')).save('master1271/strip_%02d.png'%i)
    return out.shape
import os
os.makedirs('master1271',exist_ok=True)
strips=[]; n=8; step=(ME-MW)/n
if __name__=='__main__':
    which=[int(a) for a in sys.argv[1:]] or list(range(n))
    for i in which:
        W=MW+i*step; E=MW+(i+1)*step
        sh=bake_strip(i,W,E); print('strip',i,'done',sh,flush=True)
    json.dump({'bounds':[MW,ME,MS,MN],'ppd':PPD,'n':n,'step':step,'files':['master1271/strip_%02d.png'%i for i in range(n)]},open('master1271/manifest.json','w'))
    print('MANIFEST OK')
