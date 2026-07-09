# trace_mangyshlak.py -- A* the Mangyshlak->Urgench Ustyurt road on the GEBCO DEM (Zaiton).
# Same cost model as route_1271.py (slope*45 + local-relief/500 + high-altitude tax), lonlat out,
# appended to routes_master.json as canonical 'Mangyshlak|Urgench'.
import numpy as np, json, heapq, math, glob, tifffile, cv2
W,E,S,N=48.5,61.5,40.0,47.0; RES=0.03
GX=int((E-W)/RES); GY=int((N-S)/RES)
TILES=[]
for f in glob.glob('/sessions/jolly-charming-gates/mnt/outputs/work/geb3/*.tif')+[x for x in glob.glob('/sessions/jolly-charming-gates/mnt/outputs/work/geb/*.tif') if 'w24.246' not in x]:
    b=f.split('/')[-1].split('_')
    TILES.append([f,float(b[4][1:]),float(b[5][1:]),float(b[3][1:]),float(b[2][1:]),None])
d=np.full((GY,GX),np.nan,np.float32)
for t in TILES:
    f,tw,te,ts,tn,_=t
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
ok=(d>=0)
n_,lab=cv2.connectedComponents(ok.astype(np.uint8),8)
main=np.argmax(np.bincount(lab[lab>0])); ok=(lab==main)
gy,gx=np.gradient(d,RES*111000.0); slope=np.hypot(gx,gy).astype(np.float32)
k=np.ones((5,5),np.uint8); rr=(cv2.dilate(d,k)-cv2.erode(d,k)).astype(np.float32)
LLm=(51.00,44.30); LLu=(59.15,42.30)
KM=RES*111.3
def snap(lo,la):
    r0,c0=int((N-la)/RES),int((lo-W)/RES)
    for rad in range(0,60):
        best=None
        for dr in range(-rad,rad+1):
            for dc in range(-rad,rad+1):
                r,c=r0+dr,c0+dc
                if 0<=r<GY and 0<=c<GX and ok[r,c]:
                    dd2=dr*dr+dc*dc
                    if best is None or dd2<best[0]: best=(dd2,(r,c))
        if best: return best[1]
s0=snap(*LLm); g=snap(*LLu)
kmx=KM*math.cos(math.radians((LLm[1]+LLu[1])/2))
def hh(rc): return math.hypot((rc[0]-g[0])*KM,(rc[1]-g[1])*kmx)
dist={s0:0.0}; prev={}; pq=[(hh(s0),s0)]
while pq:
    f,cur=heapq.heappop(pq)
    if cur==g: break
    r,c=cur
    for dr in(-1,0,1):
        for dc in(-1,0,1):
            if not dr and not dc: continue
            nr,nc=r+dr,c+dc
            if not(0<=nr<GY and 0<=nc<GX) or not ok[nr,nc]: continue
            km=math.hypot(dr*KM,dc*kmx)
            nd=dist[cur]+km*(1.0+slope[nr,nc]*45.0+rr[nr,nc]/500.0+(0.35 if d[nr,nc]>2400 else 0))
            if nd<dist.get((nr,nc),1e18): dist[(nr,nc)]=nd; prev[(nr,nc)]=cur; heapq.heappush(pq,(nd+hh((nr,nc)),(nr,nc)))
p=[g]
while p[-1]!=s0: p.append(prev[p[-1]])
p=p[::-1]
pts=np.array([[W+c*RES,N-r*RES] for r,c in p],float)
# smooth + resample to ~90 pts
for _ in range(4):
    q=pts.copy(); q[1:-1]=.5*pts[1:-1]+.25*pts[:-2]+.25*pts[2:]; pts=q
dd=np.r_[0,np.cumsum(np.hypot(np.diff(pts[:,0]),np.diff(pts[:,1])))]
t=np.linspace(0,dd[-1],90)
pts=np.c_[np.interp(t,dd,pts[:,0]),np.interp(t,dd,pts[:,1])]
pts[0]=LLm; pts[-1]=LLu
km_total=sum(math.hypot((pts[i+1][1]-pts[i][1])*111,(pts[i+1][0]-pts[i][0])*111*math.cos(math.radians(pts[i][1]))) for i in range(len(pts)-1))
R=json.load(open('routes_master.json'))
R['legs']['Mangyshlak|Urgench']=[[round(x,4),round(y,4)] for x,y in pts]
json.dump(R,open('routes_master.json','w'))
print('traced Mangyshlak|Urgench: %d pts, ~%d km'%(len(pts),km_total))
