# trace_sea_1271.py -- A* sea-lane tracer over sliced master reliefs (Talas).
# Method per NOTES_1271_expansion: shortest navigable path with a coast-clearance cost,
# resampled + smoothed. Outputs VOYMAPS-style pixel polylines (JSON).
import numpy as np, json, heapq, sys
from PIL import Image
import cv2

def load(base):
    im=np.array(Image.open(base).convert('RGB')).astype(np.int16)
    # master sea = desaturated blue family; detect: blue dominant over red & green
    b,g,r=im[:,:,2],im[:,:,1],im[:,:,0]
    sea=(b>r+12)&(b>g+4)
    sea=cv2.morphologyEx(sea.astype(np.uint8),cv2.MORPH_CLOSE,np.ones((3,3),np.uint8)).astype(bool)
    d=cv2.distanceTransform(sea.astype(np.uint8),cv2.DIST_L2,3)  # px to land
    return sea,d

def px_of(lon,lat,geo,W,H):
    w,e,s,n=geo
    return (lon-w)/(e-w)*W,(n-lat)/(n-s)*H

def nearest_sea(sea,x,y):
    H,W=sea.shape
    x,y=int(round(x)),int(round(y))
    if 0<=y<H and 0<=x<W and sea[y,x]: return x,y
    best=None;bd=1e9
    for r in range(1,120):
        for dx in range(-r,r+1):
            for dy in (-r,r):
                xx,yy=x+dx,y+dy
                if 0<=yy<H and 0<=xx<W and sea[yy,xx]:
                    dd=dx*dx+dy*dy
                    if dd<bd: bd,best=dd,(xx,yy)
        for dy in range(-r+1,r):
            for dx in (-r,r):
                xx,yy=x+dx,y+dy
                if 0<=yy<H and 0<=xx<W and sea[yy,xx]:
                    dd=dx*dx+dy*dy
                    if dd<bd: bd,best=dd,(xx,yy)
        if best: return best
    raise Exception('no sea near %s,%s'%(x,y))

def astar(sea,dist,a,b,step=2):
    H,W=sea.shape
    # coarse grid for speed
    def cost(x,y):
        d=dist[y,x]
        return 1.0+(6.0*max(0.0,(10-d))/10.0)   # keep ~10px off the coast when possible
    sx,sy=a; tx,ty=b
    pq=[(0,sx,sy)]; came={}; gs={(sx,sy):0}
    NB=[(step,0),(-step,0),(0,step),(0,-step),(step,step),(step,-step),(-step,step),(-step,-step)]
    seen=set()
    while pq:
        f,x,y=heapq.heappop(pq)
        if (x,y) in seen: continue
        seen.add((x,y))
        if abs(x-tx)<=step and abs(y-ty)<=step:
            path=[(x,y)]
            while (x,y) in came: x,y=came[(x,y)]; path.append((x,y))
            return path[::-1]
        g0=gs[(x,y)]
        for dx,dy in NB:
            xx,yy=x+dx,y+dy
            if not(0<=yy<H and 0<=xx<W) or not sea[yy,xx]: continue
            L=(dx*dx+dy*dy)**.5
            ng=g0+L*cost(xx,yy)
            if ng<gs.get((xx,yy),1e18):
                gs[(xx,yy)]=ng; came[(xx,yy)]=(x,y)
                h=((xx-tx)**2+(yy-ty)**2)**.5
                heapq.heappush(pq,(ng+h,xx,yy))
    raise Exception('no path')

def smooth(path,iters=6):
    p=np.array(path,float)
    for _ in range(iters):
        q=p.copy()
        q[1:-1]=0.5*p[1:-1]+0.25*p[:-2]+0.25*p[2:]
        p=q
    return p

def resample(p,n=60):
    d=np.r_[0,np.cumsum(np.hypot(np.diff(p[:,0]),np.diff(p[:,1])))]
    t=np.linspace(0,d[-1],n)
    return np.c_[np.interp(t,d,p[:,0]),np.interp(t,d,p[:,1])]

def lane(sea,dist,geo,W,H,A,B,endpins=None):
    ax,ay=px_of(*A,geo,W,H); bx,by=px_of(*B,geo,W,H)
    a=nearest_sea(sea,ax,ay); b=nearest_sea(sea,bx,by)
    p=astar(sea,dist,a,b)
    p=resample(smooth(p),58)
    # pin the true port pixels at the ends
    p=np.vstack([[ax,ay],p,[bx,by]])
    return ' '.join('%.1f,%.1f'%(x,y) for x,y in p)

if __name__=='__main__':
    out={}
    # -------- east Med --------
    geo=(23,37.5,30.5,42); W,H=1600,1574
    sea,dist=load('medlevant1271.png')
    P={'Candia':(25.13,35.34),'Ayas':(35.80,36.60),'Acre':(35.07,32.93),'Alexandria':(29.90,31.20),}
    for a,b in [('Ayas','Candia'),('Acre','Candia'),('Alexandria','Candia'),('Acre','Ayas')]:
        key='%s|%s'%(a,b)
        out[key]={'img':'Maps/medlevant1271.png','w':W,'h':H,'from':b,'pts':lane(sea,dist,geo,W,H,P[b],P[a])}
        print('traced',key)
    json.dump(out,open('sea_lanes_1271_med.json','w'),indent=0)
    print('saved sea_lanes_1271_med.json')
