# aral_fix.py -- the HISTORICAL ARAL (Kris caught the half-dry sea + ruler-straight carve edge in
# the live master). Rebuild the lake in master1271 strip 3 from the DEM: flood dem<53m from
# multiple seeds across both basins, close the inter-basin strait (silted above 53 in modern
# GEBCO; one lake historically), render sea colours + shore rim, paste only where water.
import numpy as np, cv2, json, os
from PIL import Image
exec(open('bake_1271_regions_local.py').read().split("R_ANAT=")[0])
man=json.load(open('master1271/manifest.json'))
SW,SE,SS,SN=man['bounds']; sppd=man['ppd']; sstep=man['step']
i=3; Wst=SW+i*sstep
img=np.array(Image.open('master1271/strip_%02d.png'%i).convert('RGB')).astype(np.float32)
# build the Aral-box DEM straight from the GEBCO tiles (no strip cache exists)
TILES=[('/sessions/jolly-charming-gates/mnt/outputs/work/geb/gebco_2026_n52.0_s45.26_w27.0_e62.0_geotiff.tif',27.0,62.0,45.26,52.0),
       ('/sessions/jolly-charming-gates/mnt/outputs/work/geb3/gebco_2026_n45.562_s24.109_w24.246_e96.601_geotiff.tif',24.246,96.601,24.109,45.562)]
BW,BE,BS,BN=56.5,62.5,43.2,47.2
DWb=int((BE-BW)*sppd); DHb=int((BN-BS)*sppd)
sub=dem(BW,BE,BS,BN,DWb,DHb).astype(np.float32)
def gx(lon): return int(round((lon-BW)*sppd))
def gy(lat): return int(round((BN-lat)*sppd))
x0,y0=0,0
below=(sub<53.0).astype(np.uint8)
n,lab=cv2.connectedComponents(below,8)
SEEDS=[(59.0,45.0),(58.55,44.8),(58.4,45.6),(60.5,46.2),(59.5,46.5),(60.0,44.5)]
keep=set()
for slo,sla in SEEDS:
    r,c=gy(sla),gx(slo)
    if 0<=r<sub.shape[0] and 0<=c<sub.shape[1] and lab[r,c]>0: keep.add(lab[r,c])
mask=np.isin(lab,list(keep)).astype(np.uint8)
# close the silted strait + smooth the shore: close(9) then keep only dem<56
mask=cv2.morphologyEx(mask,cv2.MORPH_CLOSE,np.ones((11,11),np.uint8))
mask&=(sub<56.0).astype(np.uint8)
# drop specks
n2,lab2,stats,_=cv2.connectedComponentsWithStats(mask,8)
big=[k for k in range(1,n2) if stats[k,4]>200]
mask=np.isin(lab2,big).astype(np.uint8)
# soften the staircase from the close(): blur + rethreshold
mask=(cv2.GaussianBlur(mask.astype(np.float32),(0,0),2.2)>0.5).astype(np.uint8)
depth=np.clip(53.0-sub,2,3000)
sea=interp(depth,SEAR)
# paste into the strip at the box's strip coordinates
sx0=int(round((BW-Wst)*sppd)); sx1=sx0+DWb
sy0=int(round((SN-BN)*sppd)); sy1=sy0+DHb
region=img[sy0:sy1,sx0:sx1]
m3=mask.astype(bool)
region[m3]=sea[m3]
rim=(cv2.dilate(mask,np.ones((3,3),np.uint8)).astype(bool))&~m3
region[rim]*=0.88
img[sy0:sy1,sx0:sx1]=region
Image.fromarray(np.clip(img,0,255).astype('uint8')).save('master1271/strip_%02d.png'%i)
print('ARAL rebuilt: %d water px, lon %.2f-%.2f lat %.2f-%.2f'%(mask.sum(),
 BW+np.where(mask.any(0))[0].min()/sppd, BW+np.where(mask.any(0))[0].max()/sppd,
 BN-np.where(mask.any(1))[0].max()/sppd, BN-np.where(mask.any(1))[0].min()/sppd))
