# slice_master.py - cut a chart-ready base from the 1271 master relief.
# Usage: python3 slice_master.py W E S N OUTW OUTH out.png   (bounds in lon/lat; resamples to OUTWxOUTH)
import numpy as np, json, sys
from PIL import Image
def slice_master(W,E,S,N,OW,OH,out,era='1271'):
    # TWO ROWS (step 5) + STRADDLE COMPOSITE (task 7): charts wholly >=52N slice the AMBER band;
    # wholly <52N the 1271 master; STRADDLING charts composite both rows at the welded 52N seam.
    import os
    if S<52.0 and N>52.0 and os.path.exists('master_amber/manifest.json'):
        manA=json.load(open('master_amber/manifest.json')); manM=json.load(open('master1271/manifest.json'))
        def cut(man,row,S0,N0):
            MW,ME,MS,MN=man['bounds']; ppd=man['ppd']; step=man['step']; n=man['n']
            x0=(W-MW)*ppd; x1=(E-MW)*ppd; y0=(MN-N0)*ppd; y1=(MN-S0)*ppd
            cols=[]
            for i in range(n):
                sx0=round(i*step*ppd); sx1=round((i+1)*step*ppd)
                if sx1<=x0 or sx0>=x1: continue
                f=row+'/strip_%02d.png'%i
                if era=='762' and row=='master_amber' and os.path.exists(row+'/strip_%02d_762.png'%i): f=row+'/strip_%02d_762.png'%i
                im=np.array(Image.open(f).convert('RGB'))
                a=max(0,int(x0-sx0)); b=min(im.shape[1],int(np.ceil(x1-sx0)))
                cols.append(im[int(y0):int(np.ceil(y1)), a:b])
            return np.concatenate(cols,axis=1)
        top=cut(manA,'master_amber',52.0,N); bot=cut(manM,'master1271',S,52.0)
        w2=min(top.shape[1],bot.shape[1])
        full=np.concatenate([top[:,:w2],bot[:,:w2]],axis=0)
        Image.fromarray(full).resize((OW,OH),Image.LANCZOS).save(out)
        return full.shape
    if S>=52.0 and os.path.exists('master_amber/manifest.json'):
        man=json.load(open('master_amber/manifest.json')); row='master_amber'
    else:
        man=json.load(open('master1271/manifest.json')); row='master1271'
    MW,ME,MS,MN=man['bounds']; ppd=man['ppd']; step=man['step']; n=man['n']
    assert MW<=W<E<=ME and MS<=S<N<=MN, 'slice outside master bounds (row %s)'%row
    x0=(W-MW)*ppd; x1=(E-MW)*ppd
    y0=(MN-N)*ppd; y1=(MN-S)*ppd
    cols=[]
    for i in range(n):
        sx0=round(i*step*ppd); sx1=round((i+1)*step*ppd)
        if sx1<=x0 or sx0>=x1: continue
        f=row+'/strip_%02d.png'%i
        if era=='762' and row=='master_amber':
            import os as _os
            f762=row+'/strip_%02d_762.png'%i
            if _os.path.exists(f762): f=f762
        im=np.array(Image.open(f).convert('RGB'))
        a=max(0,int(x0-sx0)); b=min(im.shape[1],int(np.ceil(x1-sx0)))
        cols.append(im[int(y0):int(np.ceil(y1)), a:b])
    full=np.concatenate(cols,axis=1)
    Image.fromarray(full).resize((OW,OH),Image.LANCZOS).save(out)
    return full.shape
if __name__=='__main__':
    W,E,S,N=map(float,sys.argv[1:5]); OW,OH=int(sys.argv[5]),int(sys.argv[6])
    print('sliced',slice_master(W,E,S,N,OW,OH,sys.argv[7]))
