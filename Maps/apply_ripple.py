# apply_ripple.py <strip#> [seed] -- tunable dune-sea ripple over the saved dune masks (Zaiton).
import numpy as np, cv2, sys
from PIL import Image
i=int(sys.argv[1])
img=np.array(Image.open('master1271/strip_%02d.png'%i).convert('RGB')).astype(np.float32)
dune=np.load('master1271/_dune_%02d.npy'%i).astype(np.float32)
DH,DW=dune.shape
rng=np.random.default_rng(400+i)
mx,my=np.meshgrid(np.arange(DW,dtype=np.float32),np.arange(DH,dtype=np.float32))
ang=np.deg2rad(115.0)
u=mx*np.cos(ang)+my*np.sin(ang)
# granulated dune texture: fine chaotic ridges (the over-warped fine band turned out to be the right
# look - crepe-like granulation, mildly directional), two scales, amplitude-modulated
g1=np.sin(u/4.6+cv2.GaussianBlur(rng.standard_normal((DH,DW)).astype(np.float32),(0,0),3)*5.0)
g2=np.sin(u/9.5+cv2.GaussianBlur(rng.standard_normal((DH,DW)).astype(np.float32),(0,0),6)*6.0)
ampn=np.clip(cv2.GaussianBlur(rng.standard_normal((DH,DW)).astype(np.float32),(0,0),12)*0.7+0.7,0.25,1.15)
ripple=(g1*4.5+g2*5.5)*ampn*np.clip(dune*1.7,0,1)
for c in range(3): img[:,:,c]=np.clip(img[:,:,c]+ripple*(1.0 if c<2 else 0.72),0,255)
Image.fromarray(img.astype('uint8')).save('master1271/strip_%02d.png'%i)
print('rippled strip',i)
