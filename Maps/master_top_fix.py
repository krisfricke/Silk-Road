# master_top_fix.py -- flatten the master's north-edge FADE (top ~0.2 deg darkens ~24 RGB, a bake
# artifact) by matching each top row's land tone to the 51.55-51.80N reference, per column.
# Only strips under the amber band's seam need it. Usage: python3 master_top_fix.py 2
import numpy as np, json, sys, cv2, os
from PIL import Image
k=int(sys.argv[1])
man=json.load(open('master1271/manifest.json'))
SW,SE,SS,SN=man['bounds']; sppd=man['ppd']; sstep=man['step']
im=np.array(Image.open('master1271/strip_%02d.png'%k).convert('RGB')).astype(np.float32)
H,Wpx=im.shape[:2]
r0=int((SN-51.80)*sppd); r1=int((SN-51.55)*sppd)   # reference belt rows
wat=(im[:,:,2]>im[:,:,0]+8)
ref=np.zeros((Wpx,3),np.float32)
for c in range(Wpx):
    m=~wat[r0:r1,c]
    ref[c]=im[r0:r1,c][m].mean(0) if m.sum()>4 else np.nan
for c3 in range(3):
    v=ref[:,c3]; idx=np.isnan(v)
    if not idx.all():
        v[idx]=np.interp(np.flatnonzero(idx),np.flatnonzero(~idx),v[~idx])
    ref[:,c3]=cv2.GaussianBlur(np.nan_to_num(v).reshape(1,-1),(0,0),25).ravel()
top_rows=int((SN-51.80)*sppd)     # rows 0 .. 51.80N
bak='master1271/strip_%02d_pre_topfix.png'%k
if not os.path.exists(bak): Image.fromarray(im.astype('uint8')).save(bak)
for y in range(top_rows):
    m=~wat[y]
    if m.sum()<6: continue
    rowt=np.zeros((Wpx,3),np.float32)
    # smoothed row tone per column: use a windowed mean along the row
    for c3 in range(3):
        ch=np.where(m,im[y,:,c3],np.nan)
        idx=np.isnan(ch)
        if idx.all(): continue
        ch[idx]=np.interp(np.flatnonzero(idx),np.flatnonzero(~idx),ch[~idx])
        rowt[:,c3]=cv2.GaussianBlur(ch.reshape(1,-1),(0,0),25).ravel()
    delta=ref-rowt
    im[y][m]+=delta[m]
Image.fromarray(np.clip(im,0,255).astype('uint8')).save('master1271/strip_%02d.png'%k)
print('strip',k,'top fade flattened (%d rows)'%top_rows)
