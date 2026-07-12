# retrace_fine_sk.py -- Samarkand->Kashgar corridor at GEBCO NATIVE 15" (Kris/Oxus 3D follow-up):
# least-cost per segment so the road threads valley floors instead of hopping ridges.
import numpy as np, cv2, json, heapq, math, glob, os, tifffile, sys
SEGS={
 'sj':('Samarkand','Jizzakh',(66.6,68.2,39.3,40.5)),
 'jk':('Jizzakh','Khujand',(67.5,70.0,39.8,40.7)),
 'ka':('Khujand','Andijan',(69.3,72.6,40.0,41.1)),
 'ao':('Andijan','Osh',(72.1,73.1,40.3,41.0)),
 'oi':('Osh','Irkeshtam',(72.6,74.2,39.4,40.8)),
 'ik':('Irkeshtam','Kashgar',(73.7,76.2,39.1,40.0)),
}
LL={'Samarkand':(66.95,39.67),'Jizzakh':(67.85,40.12),'Khujand':(69.63,40.28),'Andijan':(72.34,40.78),
    'Osh':(72.80,40.53),'Irkeshtam':(73.92,39.68),'Kashgar':(75.99,39.47)}
RES=1/240.0
def build(BW,BE,MS,MN):
    TILES=[]
    for d in ('geb3','geb4','geb5','geb6','geb'):
        for f in glob.glob('/sessions/jolly-charming-gates/mnt/outputs/work/%s/*.tif'%d):
            if 'w24.246' in f or 'w28.475' in f: continue   # truncated tiles (known)
            b=os.path.basename(f).split('_')
            TILES.append((f,float(b[4][1:]),float(b[5][1:]),float(b[3][1:]),float(b[2][1:])))
    GX=int((BE-BW)/RES); GY=int((MN-MS)/RES)
    dm=np.full((GY,GX),np.nan,np.float32)
    for f,tw,te,ts,tn in TILES:
        ow,oe=max(BW,tw),min(BE,te); os_,on=max(MS,ts),min(MN,tn)
        if ow>=oe or os_>=on: continue
        a=tifffile.imread(f).astype(np.float32); h,w2=a.shape
        rx=(te-tw)/w2; ry=(tn-ts)/h
        c0=int((ow-tw)/rx); c1=int((oe-tw)/rx); r0=int((tn-on)/ry); r1=int((tn-os_)/ry)
        sub=a[r0:r1,c0:c1]
        gx0=int((ow-BW)/RES); gy0=int((MN-on)/RES)
        sub=cv2.resize(sub,(int((oe-ow)/RES),int((on-os_)/RES)),interpolation=cv2.INTER_LINEAR)
        tgt=dm[gy0:gy0+sub.shape[0],gx0:gx0+sub.shape[1]]
        m=np.isnan(tgt); tgt[m]=sub[m]
    dm=np.nan_to_num(dm,nan=300.0)
    return dm,GX,GY
def trace(seg):
    a,b,(BW,BE,MS,MN)=SEGS[seg]
    dm,GX,GY=build(BW,BE,MS,MN)
    KM=RES*111.3
    gy,gx=np.gradient(dm,RES*111000.0); slope=np.hypot(gx,gy).astype(np.float32)
    k=np.ones((5,5),np.uint8); rr=(cv2.dilate(dm,k)-cv2.erode(dm,k)).astype(np.float32)
    def snap(lo,la): return (int((MN-la)/RES),int((lo-BW)/RES))
    s0=snap(*LL[a]); g=snap(*LL[b])
    kmx=KM*math.cos(math.radians((MS+MN)/2))
    def hh(rc): return math.hypot((rc[0]-g[0])*KM,(rc[1]-g[1])*kmx)
    dist={s0:0.0}; prev={}; pq=[(hh(s0),s0)]; seen=set()
    while pq:
        f,cur=heapq.heappop(pq)
        if cur in seen: continue
        seen.add(cur)
        if cur==g: break
        r,c=cur
        for dr in(-1,0,1):
            for dc in(-1,0,1):
                if not dr and not dc: continue
                nr,nc=r+dr,c+dc
                if not(0<=nr<GY and 0<=nc<GX): continue
                km=math.hypot(dr*KM,dc*kmx)
                nd=dist[cur]+km*(1.0+slope[nr,nc]*45.0+rr[nr,nc]/300.0+(0.5 if dm[nr,nc]>3200 else 0))
                if nd<dist.get((nr,nc),1e18): dist[(nr,nc)]=nd; prev[(nr,nc)]=cur; heapq.heappush(pq,(nd+hh((nr,nc)),(nr,nc)))
    p=[g]
    while p[-1]!=s0: p.append(prev[p[-1]])
    pts=np.array([[BW+c*RES,MN-r*RES] for r,c in p[::-1]],float)
    for _ in range(2):
        q=pts.copy(); q[1:-1]=.5*pts[1:-1]+.25*pts[:-2]+.25*pts[2:]; pts=q
    dd=np.r_[0,np.cumsum(np.hypot(np.diff(pts[:,0]),np.diff(pts[:,1])))]
    t=np.linspace(0,dd[-1],max(60,min(240,int(dd[-1]*40))))
    pts=np.c_[np.interp(t,dd,pts[:,0]),np.interp(t,dd,pts[:,1])]
    pts[0]=LL[a]; pts[-1]=LL[b]
    out=[[round(x,4),round(y,4)] for x,y in pts]
    json.dump(out,open('_fine_%s.json'%seg,'w'))
    print('traced',a,'->',b,len(out),'pts',flush=True)
if __name__=='__main__':
    trace(sys.argv[1])
