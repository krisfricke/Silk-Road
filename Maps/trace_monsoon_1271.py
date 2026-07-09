# trace_monsoon_1271.py -- the three far-eastern monsoon lanes, A* on the GEBCO sea mask in LONLAT (Zaiton).
# Zaiton|Kauthara (South China Sea), Kauthara|Kollam (via the Strait of Malacca), Kollam|Hormuz (Arabian Sea).
import numpy as np, tifffile, cv2, heapq, math, json
TILES=[('/sessions/jolly-charming-gates/mnt/outputs/work/geb4/gebco_2026_n28.0_s0.0_w82.0_e123.0_geotiff.tif',82.0,123.0,0.0,28.0),
       ('/sessions/jolly-charming-gates/mnt/outputs/work/geb5/gebco_2026_n24.1_s0.0_w48.95_e82.609_geotiff.tif',48.95,82.609,0.0,24.1),
       ('/sessions/jolly-charming-gates/mnt/outputs/work/geb3/gebco_2026_n45.562_s24.109_w24.246_e96.601_geotiff.tif',24.246,96.601,24.109,45.562)]
RES=0.05
def grid(W,E,S,N):
    GX=int((E-W)/RES); GY=int((N-S)/RES)
    d=np.full((GY,GX),np.nan,np.float32)
    for f,tw,te,ts,tn in TILES:
        ow,oe=max(W,tw),min(E,te); os_,on=max(S,ts),min(N,tn)
        if ow>=oe or os_>=on: continue
        a=tifffile.imread(f).astype(np.float32); h,w2=a.shape
        rx=(te-tw)/w2; ry=(tn-ts)/h
        c0=int((ow-tw)/rx); c1=int((oe-tw)/rx); r0=int((tn-on)/ry); r1=int((tn-os_)/ry)
        sub=cv2.resize(a[r0:r1,c0:c1],(int((oe-ow)/RES),int((on-os_)/RES)),interpolation=cv2.INTER_AREA)
        dr0=int((N-on)/RES); dc0=int((ow-W)/RES)
        tgt=d[dr0:dr0+sub.shape[0],dc0:dc0+sub.shape[1]]
        m=np.isnan(tgt); tgt[m]=sub[:tgt.shape[0],:tgt.shape[1]][m]
    d=np.nan_to_num(d,nan=300.0)
    sea=(d<-2)
    dist=cv2.distanceTransform(sea.astype(np.uint8),cv2.DIST_L2,3)
    return d,sea,dist,W,E,S,N,GX,GY
def trace(g,A,B):
    d,sea,dist,W,E,S,N,GX,GY=g
    def rc(lo,la): return int((N-la)/RES),int((lo-W)/RES)
    def near(lo,la):
        r0,c0=rc(lo,la)
        for rad in range(0,80):
            best=None
            for dr in range(-rad,rad+1):
                for dc in range(-rad,rad+1):
                    r,c=r0+dr,c0+dc
                    if 0<=r<GY and 0<=c<GX and sea[r,c]:
                        dd=dr*dr+dc*dc
                        if best is None or dd<best[0]: best=(dd,(r,c))
            if best: return best[1]
    s0=near(*A); gl=near(*B)
    KM=RES*111.3; kmx=KM*math.cos(math.radians((A[1]+B[1])/2))
    def cost(r,c):
        dd=dist[r,c]
        return 1.0+6.0*max(0.0,(6-dd))/6.0
    def hh(x): return math.hypot((x[0]-gl[0])*KM,(x[1]-gl[1])*kmx)
    ds={s0:0.0}; prev={}; pq=[(hh(s0),s0)]
    seen=set()
    while pq:
        f,cur=heapq.heappop(pq)
        if cur in seen: continue
        seen.add(cur)
        if cur==gl: break
        r,c=cur
        for dr in(-1,0,1):
            for dc in(-1,0,1):
                if not dr and not dc: continue
                nr,nc=r+dr,c+dc
                if not(0<=nr<GY and 0<=nc<GX) or not sea[nr,nc]: continue
                km=math.hypot(dr*KM,dc*kmx)
                nd=ds[cur]+km*cost(nr,nc)
                if nd<ds.get((nr,nc),1e18): ds[(nr,nc)]=nd; prev[(nr,nc)]=cur; heapq.heappush(pq,(nd+hh((nr,nc)),(nr,nc)))
    p=[gl]
    while p[-1]!=s0: p.append(prev[p[-1]])
    p=p[::-1]
    pts=np.array([[W+c*RES,N-r*RES] for r,c in p],float)
    for _ in range(5):
        q=pts.copy(); q[1:-1]=.5*pts[1:-1]+.25*pts[:-2]+.25*pts[2:]; pts=q
    dd2=np.r_[0,np.cumsum(np.hypot(np.diff(pts[:,0]),np.diff(pts[:,1])))]
    t=np.linspace(0,dd2[-1],70)
    pts=np.c_[np.interp(t,dd2,pts[:,0]),np.interp(t,dd2,pts[:,1])]
    pts[0]=A; pts[-1]=B
    return pts
LL={'Zaiton':(118.60,24.90),'Kauthara':(109.20,12.25),'Kollam':(76.60,8.90),'Hormuz':(56.28,27.10)}
print('gridding east...')
gE=grid(104,123,8,28)
zk=trace(gE,LL['Zaiton'],LL['Kauthara'])
print('Zaiton|Kauthara traced',len(zk))
print('gridding strait...')
gS=grid(72,115,-2,16)
kk=trace(gS,LL['Kauthara'],LL['Kollam'])
print('Kauthara|Kollam traced',len(kk))
print('gridding arabian sea...')
gA=grid(52,80,4,29)
kh=trace(gA,LL['Kollam'],LL['Hormuz'])
print('Kollam|Hormuz traced',len(kh))
json.dump({'Kauthara|Zaiton':zk.tolist(),'Kauthara|Kollam':kk.tolist(),'Hormuz|Kollam':kh.tolist()},open('monsoon_lanes_lonlat.json','w'))
print('saved monsoon_lanes_lonlat.json')
