# retrace_fergana_abaskun.py -- v2.09.72 (Zaiton): Andijan + Abaskun + Damghan legs.
# Route-stickiness rule (Kris): roads leaving a city together SHARE geometry until they part.
#  - Samarkand|Andijan reuses the Samarkand|Chach road until the Jizzakh parting, then runs by Khujand.
#  - Abaskun|Nishapur and Abaskun|Damghan share the one Alborz crossing (Astarabad->Shahrud gap) by
#    construction, parting at Shahrud/Bostam.
#  - Andijan|Kashgar / Damghan halves reuse split geometry of the retired long legs.
# Caspian note: ok-mask threshold -27 m, NOT 0 - the Gorgan lowland lies below sea level and the
# Caspian's own surface is ~-28; d>=0 would wall off the whole shore plain.
import numpy as np, cv2, json, heapq, math, glob, os, tifffile
RES=0.03; MN,MS=43.0,34.0; BW,BE=51.0,75.0
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
    sub=cv2.resize(a[r0:r1,c0:c1],(int((oe-ow)/RES),int((on-os_)/RES)),interpolation=cv2.INTER_AREA)
    tgt=d[gy0:gy0+sub.shape[0],gx0:gx0+sub.shape[1]]
    m=np.isnan(tgt); tgt[m]=sub[m]
nanfrac=float(np.isnan(d).mean())
print('DEM nan fraction:',round(nanfrac,4),flush=True)
d=np.nan_to_num(d,nan=300.0)
ok=(d>-27.0)
n_,lab=cv2.connectedComponents(ok.astype(np.uint8),8); main=np.argmax(np.bincount(lab[lab>0])); ok=(lab==main)
gy,gx=np.gradient(d,RES*111000.0); slope=np.hypot(gx,gy).astype(np.float32)
k=np.ones((5,5),np.uint8); rr=(cv2.dilate(d,k)-cv2.erode(d,k)).astype(np.float32)
LL={'Samarkand':(66.95,39.67),'Jizzakh':(67.85,40.12),'Khujand':(69.63,40.28),'Andijan':(72.34,40.78),
    'Abaskun':(54.00,36.90),'Astarabad':(54.44,36.85),'Shahrud':(54.98,36.42),'Damghan':(54.34,36.17),
    'Nishapur':(58.80,36.20),'Sabzavar':(57.65,36.21),'Semnan':(53.39,35.57),'Varamin':(51.65,35.32)}
KM=RES*111.3
def snap(lo,la):
    r0,c0=int((MN-la)/RES),int((lo-BW)/RES)
    for rad in range(0,80):
        best=None
        for dr in range(-rad,rad+1):
            for dc in range(-rad,rad+1):
                r,c=r0+dr,c0+dc
                if 0<=r<GY and 0<=c<GX and ok[r,c]:
                    dd2=dr*dr+dc*dc
                    if best is None or dd2<best[0]: best=(dd2,(r,c))
        if best: return best[1]
def seg(a,b):
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
    return [[BW+c*RES,MN-r*RES] for r,c in p[::-1]]
def polish(raw,ends):
    pts=np.array(raw,float)
    for _ in range(3):
        q=pts.copy(); q[1:-1]=.5*pts[1:-1]+.25*pts[:-2]+.25*pts[2:]; pts=q
    dd2=np.r_[0,np.cumsum(np.hypot(np.diff(pts[:,0]),np.diff(pts[:,1])))]
    t=np.linspace(0,dd2[-1],max(40,min(96,int(dd2[-1]*8))))
    pts=np.c_[np.interp(t,dd2,pts[:,0]),np.interp(t,dd2,pts[:,1])]
    pts[0]=ends[0]; pts[-1]=ends[1]
    return [[round(x,4),round(y,4)] for x,y in pts]
def kmdist(p,q):
    return math.hypot((p[1]-q[1])*111.3,(p[0]-q[0])*111.3*math.cos(math.radians((p[1]+q[1])/2)))

R=json.load(open('routes_master.json'))
RL=R['legs']

# ---- 1. Samarkand|Andijan: trace, then STICK the west end to the Chach road ----
raw=seg('Samarkand','Jizzakh')+seg('Jizzakh','Khujand')[1:]+seg('Khujand','Andijan')[1:]
ch=RL['Chach|Samarkand']
if kmdist(ch[0],list(LL['Samarkand']))>kmdist(ch[-1],list(LL['Samarkand'])): ch=ch[::-1]  # Samarkand first
P=Q=None
for i,cp in enumerate(ch):
    dm,j=min((kmdist(cp,tp),j) for j,tp in enumerate(raw))
    if dm<8.0: P,Q=i,j
    else:
        if P is not None: break
if P is not None and P>2:
    raw=ch[:P+1]+raw[Q:]
    print('stickiness: Samarkand|Andijan shares',P+1,'Chach-road points before parting',flush=True)
RL['Andijan|Samarkand']=polish(raw,(LL['Samarkand'],LL['Andijan']))[::-1]  # key order A<S: store Andijan-first
RL['Andijan|Samarkand']=[[p[0],p[1]] for p in RL['Andijan|Samarkand']]

# ---- 2. Andijan|Kashgar: split the retired long leg at Andijan ----
old=RL['Kashgar|Samarkand']  # [Samarkand ... Kashgar]
j=min(range(len(old)),key=lambda i:kmdist(old[i],list(LL['Andijan'])))
print('Kashgar|Samarkand split at idx',j,'of',len(old),'dist to Andijan',round(kmdist(old[j],list(LL['Andijan'])),1),'km',flush=True)
tail=[list(LL['Andijan'])]+old[j:]
RL['Andijan|Kashgar']=polish(tail,(LL['Andijan'],old[-1]))
del RL['Kashgar|Samarkand']

# ---- 3. the Alborz crossing: shared Abaskun->Astarabad->Shahrud trunk, parting at Shahrud ----
trunk=seg('Abaskun','Astarabad')+seg('Astarabad','Shahrud')[1:]
RL['Abaskun|Nishapur']=polish(trunk+seg('Shahrud','Sabzavar')[1:]+seg('Sabzavar','Nishapur')[1:],(LL['Abaskun'],LL['Nishapur']))
RL['Abaskun|Damghan']=polish(trunk+seg('Shahrud','Damghan')[1:],(LL['Abaskun'],LL['Damghan']))

# ---- 4. Damghan halves: FRESH traces (the old Nishapur|Varamin geometry ran ~155 km south of
# Damghan, straight over the kavir - a mis-trace; the real road hugs the rim by Semnan and Damghan) ----
RL['Damghan|Varamin']=polish(seg('Damghan','Semnan')+seg('Semnan','Varamin')[1:],(LL['Damghan'],LL['Varamin']))
RL['Damghan|Nishapur']=polish(seg('Damghan','Shahrud')+seg('Shahrud','Sabzavar')[1:]+seg('Sabzavar','Nishapur')[1:],(LL['Damghan'],LL['Nishapur']))
if 'Nishapur|Varamin' in RL: del RL['Nishapur|Varamin']

json.dump(R,open('routes_master.json','w'))
print('DONE:',[k for k in ('Andijan|Samarkand','Andijan|Kashgar','Abaskun|Nishapur','Abaskun|Damghan','Damghan|Nishapur','Damghan|Varamin')],flush=True)
