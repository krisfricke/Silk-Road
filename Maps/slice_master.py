# slice_master.py - cut a chart-ready base from the 1271 master relief.
# Usage: python3 slice_master.py W E S N OUTW OUTH out.png   (bounds in lon/lat; resamples to OUTWxOUTH)
import numpy as np, json, sys
from PIL import Image
def slice_master(W,E,S,N,OW,OH,out):
    man=json.load(open('master1271/manifest.json'))
    MW,ME,MS,MN=man['bounds']; ppd=man['ppd']; step=man['step']; n=man['n']
    assert MW<=W<E<=ME and MS<=S<N<=MN, 'slice outside master bounds'
    x0=(W-MW)*ppd; x1=(E-MW)*ppd
    y0=(MN-N)*ppd; y1=(MN-S)*ppd
    cols=[]
    for i in range(n):
        sx0=round(i*step*ppd); sx1=round((i+1)*step*ppd)
        if sx1<=x0 or sx0>=x1: continue
        im=np.array(Image.open('master1271/strip_%02d.png'%i).convert('RGB'))
        a=max(0,int(x0-sx0)); b=min(im.shape[1],int(np.ceil(x1-sx0)))
        cols.append(im[int(y0):int(np.ceil(y1)), a:b])
    full=np.concatenate(cols,axis=1)
    Image.fromarray(full).resize((OW,OH),Image.LANCZOS).save(out)
    return full.shape
if __name__=='__main__':
    W,E,S,N=map(float,sys.argv[1:5]); OW,OH=int(sys.argv[5]),int(sys.argv[6])
    print('sliced',slice_master(W,E,S,N,OW,OH,sys.argv[7]))
