# bake_southchina1271.py -- relief base for the South China Sea voyage legs (Zaiton).
# Master-matched palette (sampled off medlevant/tarim slices), hillshade, humid-green lowlands.
import numpy as np, tifffile, cv2
from PIL import Image
W,E,S,N=104.0,123.0,8.0,28.0
OW=1400; OH=int(OW/((E-W)*np.cos(np.deg2rad((S+N)/2))/(N-S)))
t=tifffile.imread('/sessions/jolly-charming-gates/mnt/outputs/work/geb4/gebco_2026_n28.0_s0.0_w82.0_e123.0_geotiff.tif').astype(np.float32)
th,tw=t.shape; TW,TE,TS,TN=82.0,123.0,0.0,28.0
c0=int((W-TW)/(TE-TW)*tw); c1=int((E-TW)/(TE-TW)*tw); r0=int((TN-N)/(TN-TS)*th); r1=int((TN-S)/(TN-TS)*th)
d=cv2.resize(t[r0:r1,c0:c1],(OW,OH),interpolation=cv2.INTER_AREA)
img=np.zeros((OH,OW,3),np.float32)
sea=d<=0
# sea: deep -> shelf
sd=np.clip(-d/2500.0,0,1)
deep=np.array([66,110,150],np.float32); shelf=np.array([88,133,170],np.float32)
img[sea]=(shelf+(deep-shelf)*sd[...,None][sea])
# land ramp: humid tropical lowland green -> mid olive -> high pale (tropics: less tan than the west)
def interp(v,tab):
    ks=[k for k,_ in tab]
    out=np.zeros(v.shape+(3,),np.float32)
    for i in range(len(tab)-1):
        k0,c0_=tab[i]; k1,c1_=tab[i+1]
        m=(v>=k0)&(v<k1)
        f=((v-k0)/(k1-k0))[m][...,None]
        out[m]=np.array(c0_)+ (np.array(c1_)-np.array(c0_))*f
    out[v>=tab[-1][0]]=np.array(tab[-1][1])
    return out
ramp=[(0,(150,158,110)),(120,(136,150,96)),(400,(110,124,80)),(900,(93,96,71)),(1800,(140,132,100)),(2800,(182,171,131)),(4500,(210,205,185))]
land=~sea
img[land]=interp(d,ramp)[land]
# hillshade
gy,gx=np.gradient(d, (N-S)/OH*111000, (E-W)/OW*111000*np.cos(np.deg2rad((S+N)/2)))
az=np.deg2rad(315); alt=np.deg2rad(45)
slope=np.arctan(np.hypot(gx,gy)*2.2); aspect=np.arctan2(-gx,gy)
hs=np.sin(alt)*np.cos(slope)+np.cos(alt)*np.sin(slope)*np.cos(az-aspect)
hs=np.clip(hs,0.25,1.0)
img[land]*= (0.55+0.55*hs[land])[...,None]
# subtle grain
rng=np.random.default_rng(3)
img[land]*= (1+0.035*rng.standard_normal(img.shape)[land])
img=np.clip(img,0,255).astype(np.uint8)
# coast feather
mask=cv2.GaussianBlur(sea.astype(np.float32),(0,0),1.0)[...,None]
base=img.astype(np.float32)
img=np.clip(base,0,255).astype(np.uint8)
Image.fromarray(img).save('southchinasea1271.png')
print('baked southchinasea1271.png',img.shape,'geo',(W,E,S,N))
