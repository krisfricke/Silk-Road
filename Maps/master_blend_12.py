# master_blend_12.py -- soften the master's 36.75E ecotone-commit boundary (strip 1 euro vs
# strip 2 classifier): blend strip 1's EAST margin (34.75-36.75E, lat>46) toward the classifier
# paint over a 2-deg ramp. Rivers preserved. Backup kept.
import numpy as np, cv2, json, os
from PIL import Image
from scipy.ndimage import gaussian_filter
import climate_biome as cb
man=json.load(open('master1271/manifest.json'))
MW,ME,MS,MN=man['bounds']; step=man['step']; ppd=man['ppd']
i=1; W=MW+i*step; E=MW+(i+1)*step
cur=np.array(Image.open('master1271/strip_%02d.png'%i).convert('RGB')).astype(np.float32)
rel=np.array(Image.open('master1271/strip_%02d_relief.png'%i).convert('RGB')).astype(np.float32)
H,Wpx=cur.shape[:2]
codes,T,P,ocean=cb.classify_bbox(W,E,MS,MN,Wpx,H)
rng=np.random.default_rng(7)
pres=np.zeros((H,Wpx),np.float32)
pres[(codes==cb.FOREST)|(codes==cb.TAIGA)]=1.0
mfs=codes==cb.FSTEP
if mfs.any():
    ff=np.clip(cb.forest_fraction(T,P),0,1); ff=ff*ff*(3-2*ff)
    mn=gaussian_filter(rng.random((H,Wpx)).astype(np.float32),2.2)
    mn=(mn-mn.min())/(np.ptp(mn)+1e-9)
    pres[mfs&(mn<ff)]=1.0
pres=gaussian_filter(pres,1.6)
bl=gaussian_filter(rng.random((H,Wpx)).astype(np.float32),4); bl=(bl-bl.min())/(np.ptp(bl)+1e-9)
pres=pres*0.62*(0.85+0.15*bl)
water=cur[:,:,2]>cur[:,:,0]+8
snow=cur.min(2)>195
pres*=((~water)&(~snow)&(~ocean))
colE=np.where((codes==cb.TAIGA)[:,:,None],np.array([48,82,52],np.float32),np.array([78,108,50],np.float32))
imgC=rel*(1-pres[:,:,None])+colE*pres[:,:,None]
lon=np.linspace(W,E,Wpx)[None,:].repeat(H,0); lat=np.linspace(MN,MS,H)[:,None].repeat(Wpx,1)
wgt=np.clip((lon-34.75)/2.0,0,1)*np.clip((lat-46.0)/1.5,0,1)
wgt*=(~water)
out=cur*(1-wgt[:,:,None])+imgC*wgt[:,:,None]
# restore rivers (pixels bluer in cur than relief)
bluer=cur[:,:,2]-rel[:,:,2]; greener=cur[:,:,1]-rel[:,:,1]
riv=(bluer>4)&(bluer>=greener)
out[riv]=cur[riv]
bak='master1271/strip_%02d_pre_blend12.png'%i
if not os.path.exists(bak): Image.fromarray(cur.astype('uint8')).save(bak)
Image.fromarray(np.clip(out,0,255).astype('uint8')).save('master1271/strip_%02d.png'%i)
print('strip 1 east margin blended toward classifier')
