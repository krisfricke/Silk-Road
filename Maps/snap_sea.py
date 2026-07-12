# snap_sea.py -- snap every amber SEA lane to open water (Zaiton).
# Least-cost path on the composite relief's own water mask (block-2 max-pooled so the Danish
# straits stay open), coast-distance penalty keeps lanes offshore, hand waypoints as via-points.
import numpy as np, json, heapq, os
from PIL import Image
os.chdir('/sessions/jolly-charming-gates/mnt/Silk-Road/Maps')
R=json.load(open('/sessions/jolly-charming-gates/mnt/outputs/work/routes_amber.json'))
D=json.load(open('/sessions/jolly-charming-gates/mnt/outputs/work/econ_dump_full.json'))
W,E,S,N=8.0,42.0,40.5,61.0
def slice_row(man_dir,W0,E0,S0,N0):
    man=json.load(open(man_dir+'/manifest.json'))
    MW,ME,MS,MN=man['bounds']; ppd=man['ppd']; step=man['step']; n=man['n']
    x0=(W0-MW)*ppd; x1=(E0-MW)*ppd; y0=(MN-N0)*ppd; y1=(MN-S0)*ppd
    cols=[]
    for i in range(n):
        sx0=round(i*step*ppd); sx1=round((i+1)*step*ppd)
        if sx1<=x0 or sx0>=x1: continue
        im=np.array(Image.open(man_dir+'/strip_%02d.png'%i).convert('RGB'))
        a=max(0,int(x0-sx0)); b=min(im.shape[1],int(np.ceil(x1-sx0)))
        cols.append(im[int(y0):int(np.ceil(y1)), a:b])
    return np.concatenate(cols,axis=1)
top=slice_row('master_amber',W,E,52.0,N); bot=slice_row('master1271',W,E,S,52.0)
w=min(top.shape[1],bot.shape[1])
img=np.concatenate([top[:,:w],bot[:,:w]],axis=0)
# 762 variant of strip_00 (Malaren as sea-bay): second mask for 762-era legs
import shutil
top762=top.copy()
man=json.load(open('master_amber/manifest.json'))
im762=np.array(Image.open('master_amber/strip_00_762.png').convert('RGB'))
MW,ME,MS,MN=man['bounds']; ppd=man['ppd']
x1=min(im762.shape[1],top762.shape[1]); y0=int((MN-61.0)*ppd); y1=int((MN-52.0)*ppd)
top762[:,:x1]=im762[y0:y1,:x1][:top762.shape[0]]
img762=np.concatenate([top762[:,:w],bot[:,:w]],axis=0)
H_,W_=img.shape[:2]
def mkmask(im):
    return (im[:,:,2]>im[:,:,0])&(im[:,:,2]>im[:,:,1])&(im[:,:,2]>90)
water=mkmask(img); water762=mkmask(img762)
B=2
h2,w2=H_//B,W_//B
def pool(m): return m[:h2*B,:w2*B].reshape(h2,B,w2,B).any(axis=(1,3))
wat2_1271=pool(water); wat2_762=pool(water762)
wat2=wat2_1271
import cv2
PEN={}
for nm,m in (('1271',wat2_1271),('762',wat2_762)):
    d=cv2.distanceTransform(m.astype(np.uint8),cv2.DIST_L2,3)
    PEN[nm]=1.0+5.0*np.exp(-d/4.0)
def xy(lon,lat): return ((lon-W)/(E-W)*W_/B, (N-lat)/(N-S)*H_/B)
def ll(x,y): return (W+x*B/W_*(E-W), N-y*B/H_*(N-S))
LAB={}
for nm,m in (('1271',wat2_1271),('762',wat2_762)):
    LAB[nm]=cv2.connectedComponents(m.astype(np.uint8))[1]
def snapw(x,y,wat2,lab=None,comp=None,rad=40):
    x,y=int(round(x)),int(round(y))
    ok=lambda yy,xx: wat2[yy,xx] and (comp is None or lab[yy,xx]==comp)
    if 0<=y<h2 and 0<=x<w2 and ok(y,x): return x,y
    best=None;bd=1e9
    for dy in range(-rad,rad+1):
        for dx in range(-rad,rad+1):
            yy,xx=y+dy,x+dx
            if 0<=yy<h2 and 0<=xx<w2 and ok(yy,xx):
                d=dx*dx+dy*dy
                if d<bd: bd=d;best=(xx,yy)
    return best
def seapath(a,b,wat2,pen):
    ax,ay=a; bx,by=b
    x0,x1=int(min(ax,bx))-280,int(max(ax,bx))+280
    y0,y1=int(min(ay,by))-280,int(max(ay,by))+280
    x0,y0=max(0,x0),max(0,y0); x1,y1=min(w2,x1),min(h2,y1)
    sub=wat2[y0:y1,x0:x1]; sp=pen[y0:y1,x0:x1]
    hh,ww=sub.shape
    start=(int(ay)-y0,int(ax)-x0); goal=(int(by)-y0,int(bx)-x0)
    INF=np.inf; dst=np.full((hh,ww),INF,np.float32)
    dst[start]=0; pq=[(0.0,start)]; par={}
    NB=[(-1,0,1),(1,0,1),(0,-1,1),(0,1,1),(-1,-1,1.414),(-1,1,1.414),(1,-1,1.414),(1,1,1.414)]
    while pq:
        d,(y,x)=heapq.heappop(pq)
        if (y,x)==goal: break
        if d>dst[y,x]: continue
        for dy,dx,c in NB:
            yy,xx=y+dy,x+dx
            if 0<=yy<hh and 0<=xx<ww and sub[yy,xx]:
                nd=d+c*sp[yy,xx]
                if nd<dst[yy,xx]: dst[yy,xx]=nd; par[(yy,xx)]=(y,x); heapq.heappush(pq,(nd,(yy,xx)))
    if dst[goal]==INF: return None
    path=[goal]
    while path[-1]!=start: path.append(par[path[-1]])
    return [(x+x0,y+y0) for y,x in path[::-1]]
def rdp(pts,eps):
    if len(pts)<3: return pts
    a=np.array(pts[0],float); b=np.array(pts[-1],float)
    ab=b-a; L=np.hypot(*ab) or 1
    dmax,idx=0,0
    for i in range(1,len(pts)-1):
        p=np.array(pts[i],float)
        d=abs(np.cross(ab,p-a))/L
        if d>dmax: dmax,idx=d,i
    if dmax>eps:
        return rdp(pts[:idx+1],eps)[:-1]+rdp(pts[idx:],eps)
    return [pts[0],pts[-1]]
TERR={ '|'.join(sorted([e['a'],e['b']])):e['terr'] for e in D['edges'] }
ERA={}
for e in D['edges']:
    k='|'.join(sorted([e['a'],e['b']]))
    prev=ERA.get(k); era=e['era'] or 'both'
    ERA[k]='both' if (prev and prev!=era) else era
out={}; failed=[]
for k,pts in R['legs'].items():
    if TERR.get(k)!='med': out[k]=pts; continue
    era=ERA.get(k,'both')
    m=wat2_762 if era=='762' else wat2_1271
    sp=PEN['762'] if era=='762' else PEN['1271']
    vias=[pts[0]]+pts[1:-1][::2]+[pts[-1]]
    lab=LAB['762'] if era=='762' else LAB['1271']
    # constrain to the lane's OWN sea: snap every via unconstrained, take the water
    # component that the most vias (weighted by component size) agree on. Stockholm's nearest
    # water is Malaren (a separate 1271 component); the Black Sea lanes must not inherit the
    # Baltic. Majority-of-vias picks the right basin for each lane.
    import numpy as _np
    _cands=[snapw(*xy(lon,lat),m) for lon,lat in vias]
    _labs=[lab[g[1],g[0]] for g in _cands if g]
    if not _labs: failed.append((k,'snap')); out[k]=pts; continue
    _bc={}
    for _l in _labs: _bc[_l]=_bc.get(_l,0)+1
    comp=max(_bc.items(), key=lambda kv:(kv[1], int((lab==kv[0]).sum())))[0]
    grid=[snapw(*xy(lon,lat),m,lab,comp) for lon,lat in vias]
    if any(g is None for g in grid): failed.append((k,'snap')); out[k]=pts; continue
    full=[]
    ok=True
    for i in range(len(grid)-1):
        seg=seapath(grid[i],grid[i+1],m,sp)
        if seg is None: ok=False; break
        full+= seg if not full else seg[1:]
    if not ok: failed.append((k,'path')); out[k]=pts; continue
    simp=rdp(full,1.5)
    out[k]=[[round(a,4) for a in ll(x,y)] for x,y in simp]
json.dump({'LL':R['LL'],'legs':out},open('/sessions/jolly-charming-gates/mnt/outputs/work/routes_amber.json','w'))
print('snapped; failures:',failed)
# re-verify
fails=[]
for k,pts in out.items():
    if TERR.get(k)!='med': continue
    P=np.array(pts,float); tot=0; wet=0
    for i in range(len(P)-1):
        for t in np.linspace(0,1,60):
            lon,lat=P[i]*(1-t)+P[i+1]*t
            x=int((lon-W)/(E-W)*W_); y=int((N-lat)/(N-S)*H_)
            if 0<=y<H_ and 0<=x<W_: tot+=1; wet+=(water762 if ERA.get(k)=='762' else water)[y,x]
    if wet/max(1,tot)<0.93: fails.append((k,round(wet/max(1,tot),2)))
print('WETNESS after snap, below 93%:',fails)
