# retrace_east.py -- re-run the A* route tracer for every land leg that was traced over the
# pre-China-tile DEM HOLE (east of ~96.6E): they came out straight (Kris caught it). Zaiton.
import numpy as np, cv2, json, heapq, math, glob, os, tifffile
RES=0.03; MS,MN=24.0,52.0; BW,BE=30.0,42.0
TILES=[]
for f in (glob.glob('/sessions/jolly-charming-gates/mnt/outputs/work/geb3/*.tif')
         +glob.glob('/sessions/jolly-charming-gates/mnt/outputs/work/geb4/*.tif')
         +glob.glob('/sessions/jolly-charming-gates/mnt/outputs/work/geb5/*.tif')
         +glob.glob('/sessions/jolly-charming-gates/mnt/outputs/work/geb6/*.tif')+[x for x in glob.glob('/sessions/jolly-charming-gates/mnt/outputs/work/geb/*.tif') if 'w24.246' not in x and 'w28.475' not in x]):
    b=os.path.basename(f).split('_')
    TILES.append((f,float(b[4][1:]),float(b[5][1:]),float(b[3][1:]),float(b[2][1:])))
GX=int((BE-BW)/RES); GY=int((MN-MS)/RES)
d=np.full((GY,GX),np.nan,np.float32)
for f,tw,te,ts,tn in TILES:
    ow,oe=max(BW,tw),min(BE,te); os_,on=max(MS,ts),min(MN,tn)
    if ow>=oe or os_>=on: continue
    a=tifffile.imread(f).astype(np.float32); h,w2=a.shape
    rx=(te-tw)/w2; ry=(tn-ts)/h
    c0=int((ow-tw)/rx); c1=int((oe-tw)/rx); r0=int((tn-on)/ry); r1=int((tn-os_)/ry)
    gx0=int((ow-BW)/RES); gy0=int((MN-on)/RES)
    sub=cv2.resize(a[r0:r1,c0:c1],(int((oe-ow)/RES),int((on-os_)/RES)),interpolation=cv2.INTER_AREA)
    tgt=d[gy0:gy0+sub.shape[0],gx0:gx0+sub.shape[1]]
    m=np.isnan(tgt); tgt[m]=sub[m]
d=np.nan_to_num(d,nan=300.0)
ok=(d>=0)
n_,lab=cv2.connectedComponents(ok.astype(np.uint8),8); main=np.argmax(np.bincount(lab[lab>0])); ok=(lab==main)
gy,gx=np.gradient(d,RES*111000.0); slope=np.hypot(gx,gy).astype(np.float32)
k=np.ones((5,5),np.uint8); rr=(cv2.dilate(d,k)-cv2.erode(d,k)).astype(np.float32)
LL={'Acre':(35.07,32.93),'Jerusalem':(35.23,31.78),'Damascus':(36.31,33.51),'Aleppo':(37.15,36.21),'Ayas':(35.79,36.77),'Shazhou':(94.66,40.14),'Kamul':(93.51,42.83),'Suzhou':(98.50,39.77),'Ganzhou':(100.45,38.93),
'Lanzhou':(103.80,36.06),'Kenjanfu':(108.95,34.27),'Khanbaliq':(116.40,39.90),'Etzina':(101.07,41.95),
'Karakorum':(102.85,47.20),'Turfan':(89.19,42.95),'Xanadu':(116.18,42.36),'Tenduc':(111.15,40.35),
'Taiyuan':(112.55,37.87),'Ningxia':(106.27,38.47),'Yangzhou':(119.42,32.39),'Kinsay':(120.17,30.25),'Zaiton':(118.60,24.90),'Lop':(88.30,39.50)}
KM=RES*111.3
def snap(lo,la):
    r0,c0=int((MN-la)/RES),int((lo-BW)/RES)
    for rad in range(0,60):
        best=None
        for dr in range(-rad,rad+1):
            for dc in range(-rad,rad+1):
                r,c=r0+dr,c0+dc
                if 0<=r<GY and 0<=c<GX and ok[r,c]:
                    dd2=dr*dr+dc*dc
                    if best is None or dd2<best[0]: best=(dd2,(r,c))
        if best: return best[1]
def route(a,b):
    lo1,la1=LL[a]; lo2,la2=LL[b]
    s0=snap(lo1,la1); g=snap(lo2,la2)
    kmx=KM*math.cos(math.radians((la1+la2)/2))
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
                if not(0<=nr<GY and 0<=nc<GX) or not ok[nr,nc]: continue
                km=math.hypot(dr*KM,dc*kmx)
                nd=dist[cur]+km*(1.0+slope[nr,nc]*45.0+rr[nr,nc]/500.0+(0.35 if d[nr,nc]>2400 else 0))
                if nd<dist.get((nr,nc),1e18): dist[(nr,nc)]=nd; prev[(nr,nc)]=cur; heapq.heappush(pq,(nd+hh((nr,nc)),(nr,nc)))
    p=[g]
    while p[-1]!=s0: p.append(prev[p[-1]])
    p=p[::-1]
    pts=np.array([[BW+c*RES,MN-r*RES] for r,c in p],float)
    for _ in range(3):
        q=pts.copy(); q[1:-1]=.5*pts[1:-1]+.25*pts[:-2]+.25*pts[2:]; pts=q
    dd2=np.r_[0,np.cumsum(np.hypot(np.diff(pts[:,0]),np.diff(pts[:,1])))]
    t=np.linspace(0,dd2[-1],max(40,min(90,int(dd2[-1]*8))))
    pts=np.c_[np.interp(t,dd2,pts[:,0]),np.interp(t,dd2,pts[:,1])]
    pts[0]=(lo1,la1); pts[-1]=(lo2,la2)
    return [[round(x,4),round(y,4)] for x,y in pts]
LEGS=[('Acre','Jerusalem'),('Acre','Damascus'),('Aleppo','Ayas')]
import sys
R=json.load(open('routes_master.json'))
done=0
for a,b in LEGS:
    key='|'.join(sorted([a,b]))
    if key not in R['legs']:
        alt=[k for k in R['legs'] if set(k.split('|'))=={a,b}]
        key=alt[0] if alt else key
    R['legs'][key]=route(a,b)
    print('re-traced',key,len(R['legs'][key]),'pts',flush=True)
    done+=1
json.dump(R,open('routes_master.json','w'))
print('DONE',done,flush=True)
