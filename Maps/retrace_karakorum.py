# retrace_karakorum.py (Kris 7/17): [F3]/[F4] — the Karakorum roads get the same hardened tracer — my
# waypoint courses replaced/never-had the A* treatment every other land leg got. Re-run the
# canonical tracer (retrace_east recipe: cost = km*(1 + slope*45 + roughness/500 + 0.35 above
# 2400 m)) for Tenduc->Datong->Khanbaliq (via, then concatenated) and Khanbaliq->Xanadu.
# NEW: +18 cost on Natural Earth river cells, so staying on one bank falls out of the economics
# instead of being hand-imposed (crossings only where the mountains leave no choice).
import numpy as np, cv2, json, heapq, math, glob, os, tifffile
from PIL import Image, ImageDraw
RES=0.03; MS,MN=24.0,52.0; BW,BE=(91.0,104.5) if __import__('sys').argv[1]=='hami' else (101.0,118.0)
TILES=[]
for f in (glob.glob('/sessions/jolly-charming-gates/mnt/outputs/work/geb3/*.tif')
         +glob.glob('/sessions/jolly-charming-gates/mnt/outputs/work/geb4/*.tif')
         +glob.glob('/sessions/jolly-charming-gates/mnt/outputs/work/geb5/*.tif')
         +glob.glob('/sessions/jolly-charming-gates/mnt/outputs/work/geb6/*.tif')
         +[x for x in glob.glob('/sessions/jolly-charming-gates/mnt/outputs/work/geb/*.tif') if 'w24.246' not in x and 'w28.475' not in x]):
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
    sub=cv2.resize(a[r0:r1,c0:c1],(int(round((oe-ow)/RES)),int(round((on-os_)/RES))),interpolation=cv2.INTER_AREA)
    tgt=d[gy0:gy0+sub.shape[0],gx0:gx0+sub.shape[1]]; sub=sub[:tgt.shape[0],:tgt.shape[1]]
    m=np.isnan(tgt); tgt[m]=sub[m]
d=np.nan_to_num(d,nan=300.0)
ok=(d>=0)
n_,lab=cv2.connectedComponents(ok.astype(np.uint8),8)
main=np.argmax(np.bincount(lab[lab>0])); ok=(lab==main)
gy,gx=np.gradient(d,RES*111000.0); slope=np.hypot(gx,gy).astype(np.float32)
k=np.ones((5,5),np.uint8); rr=(cv2.dilate(d,k)-cv2.erode(d,k)).astype(np.float32)
# rivers: cost, not walls
RIVJ=json.load(open('Maps/ne_10m_rivers_lake_centerlines.geojson'))['features']
rim=Image.new('L',(GX,GY),0); rdr=ImageDraw.Draw(rim)
for f in RIVJ:
    g=f['geometry']
    if g is None: continue
    coords=g['coordinates'] if g['type']=='MultiLineString' else [g['coordinates']]
    for line in coords:
        xs=[c[0] for c in line]
        if max(xs)<BW-0.3 or min(xs)>BE+0.3: continue
        rdr.line([((x-BW)/RES,(MN-y)/RES) for x,y in line],fill=255,width=2)   # width 2: a diagonal step cannot slip between cells of a 1px line
riv=(np.array(rim)>0).astype(np.float32)
KM=RES*111.3
LL={'Hami':(93.51,42.83),'Karakorum':(102.85,47.20),'Xanadu':(116.18,42.36)}
def snap(lo,la):
    r0,c0=int((MN-la)/RES),int((lo-BW)/RES)
    for rad in range(0,60):
        for r in range(max(0,r0-rad),min(GY,r0+rad+1)):
            for c in range(max(0,c0-rad),min(GX,c0+rad+1)):
                if ok[r,c]: return r,c
    raise RuntimeError('no land near %s %s'%(lo,la))
def route(a,b):
    (lo1,la1),(lo2,la2)=LL[a],LL[b]
    s0=snap(lo1,la1); g=snap(lo2,la2)
    kmx=KM*math.cos(math.radians((la1+la2)/2))
    def hh(n): return math.hypot((n[0]-g[0])*KM,(n[1]-g[1])*kmx)
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
                nd=dist[cur]+km*(1.0+slope[nr,nc]*45.0+rr[nr,nc]/500.0+(0.35 if d[nr,nc]>2400 else 0))+60.0*riv[nr,nc]
                if nd<dist.get((nr,nc),1e18): dist[(nr,nc)]=nd; prev[(nr,nc)]=cur; heapq.heappush(pq,(nd+hh((nr,nc)),(nr,nc)))
    p=[g]
    while p[-1]!=s0: p.append(prev[p[-1]])
    p=p[::-1]
    pts=np.array([[BW+c*RES,MN-r*RES] for r,c in p],float)
    # crossing-aware smoothing: points within 2 cells of a river keep their raw grid position,
    # so the smoother cannot drag the road across a meander it lawfully went around
    rivwide=cv2.dilate((riv>0).astype(np.uint8),np.ones((5,5),np.uint8))
    pin=np.array([bool(rivwide[min(GY-1,max(0,int((MN-y)/RES))),min(GX-1,max(0,int((x-BW)/RES)))]) for x,y in pts])
    raw=pts.copy()
    for _ in range(3):
        q=pts.copy(); q[1:-1]=.5*pts[1:-1]+.25*pts[:-2]+.25*pts[2:]; pts=q
        pts[pin]=raw[pin]
    pts[0]=(lo1,la1); pts[-1]=(lo2,la2)
    return pts
def rs(pts,n):
    dd2=np.r_[0,np.cumsum(np.hypot(np.diff(pts[:,0]),np.diff(pts[:,1])))]
    t=np.linspace(0,dd2[-1],n)
    return np.c_[np.interp(t,dd2,pts[:,0]),np.interp(t,dd2,pts[:,1])], dd2[-1]
import sys
if sys.argv[1]=='hami':
    P_,_=rs(route('Hami','Karakorum'),80); K='Hami|Karakorum'
else:
    P_,_=rs(route('Karakorum','Xanadu'),72); K='Karakorum|Xanadu'
R=json.load(open('Maps/routes_master.json'))
R['legs'][K]=[[round(x,4),round(y,4)] for x,y in P_]
json.dump(R,open('Maps/routes_master.json','w'))
print('traced',K,len(P_),'pts')
