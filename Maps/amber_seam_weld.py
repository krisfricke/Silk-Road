# amber_seam_weld.py -- FINAL seam pass: per-column empirical weld of the band's bottom belt
# onto the south's measured tone (land pixels only; rivers/water untouched). Feathers to zero
# by 0.6 deg north. Run AFTER amber_detail on any eastern strip. Usage: python3 amber_seam_weld.py 3
import numpy as np, json, sys, cv2
from PIL import Image
i=int(sys.argv[1])
man=json.load(open('master_amber/manifest.json'))
MW,ME,MS,MN=man['bounds']; step=man['step']; ppd=man['ppd']
W=MW+i*step; E=MW+(i+1)*step
band=np.array(Image.open('master_amber/strip_%02d.png'%i).convert('RGB')).astype(np.float32)
DH,DW=band.shape[:2]
manS=json.load(open('master1271/manifest.json'))
SW,SE,SS,SN=manS['bounds']; sstep=manS['step']; sppd=manS['ppd']; sn=manS['n']
x0=(W-SW)*sppd; x1=(E-SW)*sppd; y0=(SN-52.0)*sppd; y1=(SN-51.8)*sppd
cols=[]
for k in range(sn):
    sx0=round(k*sstep*sppd); sx1=round((k+1)*sstep*sppd)
    if sx1<=x0 or sx0>=x1: continue
    im=np.array(Image.open('master1271/strip_%02d.png'%k).convert('RGB'))
    a=max(0,int(x0-sx0)); b=min(im.shape[1],int(np.ceil(x1-sx0)))
    cols.append(im[int(y0):int(np.ceil(y1)), a:b])
south=np.concatenate(cols,axis=1).astype(np.float32)[:, :DW]
def colmean(a):
    wat=(a[:,:,2]>a[:,:,0]+8)
    out=np.zeros((a.shape[1],3),np.float32)
    for c in range(a.shape[1]):
        m=~wat[:,c]
        out[c]=a[m,c].mean(0) if m.sum()>4 else np.nan
    return out
belt_rows=int(0.25*ppd)   # band 52.0-52.25N
sm=colmean(south); bm=colmean(band[DH-belt_rows:DH])
delta=sm-bm
# WATER GUARD: where either belt lacks land (the Baltic strips!), apply NO correction -
# do not interpolate across seas (the strips 0/1 lesson: garbage deltas smeared the coasts)
nomeas=np.isnan(delta).any(axis=1)
delta[nomeas]=0
# fill nans, smooth along columns
for c in range(3):
    v=delta[:,c]; idx=np.isnan(v)
    if idx.all(): v[:]=0
    else:
        v[idx]=np.interp(np.flatnonzero(idx),np.flatnonzero(~idx),v[~idx])
    delta[:,c]=cv2.GaussianBlur(v.reshape(1,-1),(0,0),30).ravel()
lat=np.linspace(MN,MS,DH)[:,None]
feather=np.clip((52.6-lat)/0.6,0,1)   # 0 above 52.6N -> 1 at the seam
wat=(band[:,:,2]>band[:,:,0]+8)
adj=feather[:,:,None]*delta[None,:,:]
out=band+np.where(wat[:,:,None],0,adj)
Image.fromarray(np.clip(out,0,255).astype('uint8')).save('master_amber/strip_%02d.png'%i)
print('strip',i,'welded; mean |delta| applied at seam:',np.abs(delta).mean(0).round(1))
