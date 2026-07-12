# master_fix_ne.py -- surgical: paint the classifier ecotone onto master1271 strip_03's NORTH
# (>48N, feathered) so its 51.125E boundary with committed strip_02 disappears. Composites onto
# the CURRENT strip (dunes/rosy/lakes south of the feather untouched); rivers/water never painted.
import numpy as np, cv2, json, os
from PIL import Image
from scipy.ndimage import gaussian_filter
import climate_biome as cb
man=json.load(open('master1271/manifest.json'))
MW,ME,MS,MN=man['bounds']; step=man['step']; ppd=man['ppd']
i=3; W=MW+i*step; E=MW+(i+1)*step
cur=np.array(Image.open('master1271/strip_%02d.png'%i).convert('RGB')).astype(np.float32)
H,Wpx=cur.shape[:2]
codes,T,P,ocean=cb.classify_bbox(W,E,MS,MN,Wpx,H)
rng=np.random.default_rng(7)
pres=np.zeros((H,Wpx),np.float32)
pres[(codes==cb.FOREST)|(codes==cb.TAIGA)]=1.0
mfs=codes==cb.FSTEP
if mfs.any():
    ff=np.clip(cb.forest_fraction(T,P),0,1); ff=ff*ff*(3-2*ff)
    mnoise=gaussian_filter(rng.random((H,Wpx)).astype(np.float32),2.2)
    mnoise=(mnoise-mnoise.min())/(np.ptp(mnoise)+1e-9)
    pres[mfs&(mnoise<ff)]=1.0
pres=gaussian_filter(pres,1.6)
blotch=gaussian_filter(rng.random((H,Wpx)).astype(np.float32),4)
blotch=(blotch-blotch.min())/(np.ptp(blotch)+1e-9)
pres=pres*0.62*(0.85+0.15*blotch)
lat=np.linspace(MN,MS,H)[:,None].repeat(Wpx,1)
feather=np.clip((lat-47.5)/3.0,0,1)          # soft: nothing south of 47.5N, full by 50.5N (Kris saw the 48N edge)
pres*=feather
water=cur[:,:,2]>cur[:,:,0]+8                 # never repaint water or the rivers
snow=cur.min(2)>195
greenish=(cur[:,:,1]-cur[:,:,0])>12           # already forest-painted (euro boxes etc)
pres*=((~water)&(~snow)&(~ocean)&(~greenish))
colE=np.where((codes==cb.TAIGA)[:,:,None],np.array([48,82,52],np.float32),np.array([78,108,50],np.float32))
out=cur*(1-pres[:,:,None])+colE*pres[:,:,None]
bak='master1271/strip_%02d_pre_nefix.png'%i
if not os.path.exists(bak): Image.fromarray(cur.astype('uint8')).save(bak)
Image.fromarray(np.clip(out,0,255).astype('uint8')).save('master1271/strip_%02d.png'%i)
print('master strip 3 NE corner ecotone-painted (backup %s)'%bak)
