# route_1271.py - batch-route ALL 1271 land legs on the master DEM (ruggedness-aware cost), lonlat out.
import numpy as np, cv2, json, heapq, math, gc
exec(open('bake_1271_regions.py').read().split("R_ANAT=")[0])
MS,MN=24.0,52.0; RES=0.03
LL={'Venice':(12.34,45.43),'Ragusa':(18.11,42.64),'Candia':(25.13,35.34),'Constantinople':(28.97,41.01),
'Ayas':(35.79,36.77),'Acre':(35.07,32.93),'Sivas':(37.02,39.75),'Erzurum':(41.28,39.90),'Trebizond':(39.72,41.00),
'Caffa':(35.38,45.03),'Tana':(39.32,47.27),'Sarai':(47.47,47.18),'Mangyshlak':(51.00,44.30),
'Tabriz':(46.29,38.08),'Baghdad':(44.42,33.35),'Kashan':(51.44,33.98),'Yazd':(54.37,31.90),
'Kerman':(57.08,30.28),'Hormuz':(56.28,27.10),'Nishapur':(58.80,36.20),'Sarakhs':(61.16,36.53),
'Urgench':(59.15,42.30),'Otrar':(68.30,42.85),'Bukhara':(64.42,39.77),'Samarkand':(66.97,39.65),
'Balkh':(66.90,36.76),'Herat':(62.20,34.35),'Badakhshan':(70.80,37.00),'Kashgar':(75.99,39.47),
'Yarkand':(77.25,38.42),'Khotan':(79.92,37.11),'Charchan':(85.53,38.13),'Lop':(88.30,39.50),
'Shazhou':(94.66,40.14),'Kamul':(93.51,42.83),'Suzhou':(98.50,39.77),'Ganzhou':(100.45,38.93),
'Lanzhou':(103.80,36.06),'Kenjanfu':(108.95,34.27),'Khanbaliq':(116.40,39.90),'Etzina':(101.07,41.95),
'Karakorum':(102.85,47.20),'Almaliq':(81.30,44.05),'Aleppo':(37.15,36.21),'Damascus':(36.31,33.51),
'Jerusalem':(35.23,31.78),'Sultaniyya':(48.80,36.43),'Saveh':(50.35,35.02),'Konya':(32.50,37.87),'Kayseri':(35.48,38.72),'Turfan':(89.19,42.95),'Xanadu':(116.18,42.36),'Tenduc':(111.15,40.35),'Taiyuan':(112.55,37.87),'Ningxia':(106.27,38.47),'Yangzhou':(119.42,32.39),'Kinsay':(120.17,30.25),'Zaiton':(118.60,24.90)}
net=json.load(open('/tmp/net1271.json'))
R=json.load(open('routes_master.json'))
land=[l for l in net['legs'] if l.get('terr') not in ('sea','caspian','river')]
todo=[]
miss=set()
for l in land:
    key='|'.join(sorted([l['a'],l['b']]))
    if key in R['legs']: continue
    if l['a'] not in LL: miss.add(l['a'])
    if l['b'] not in LL: miss.add(l['b'])
    if l['a'] in LL and l['b'] in LL: todo.append((l['a'],l['b']))
print('land legs to route:',len(todo),'missing coords:',sorted(miss),flush=True)
BLOCKS=[(8.0,52.0),(44.0,90.0),(84.0,123.0)]
def build(bi):
    BW,BE=BLOCKS[bi]
    GX=int((BE-BW)/RES); GY=int((MN-MS)/RES)
    d=dem(BW,BE,MS,MN,GX,GY).astype(np.float32); gc.collect()
    ok=(d>=0)
    n_,lab=cv2.connectedComponents(ok.astype(np.uint8),8); main=np.argmax(np.bincount(lab[lab>0])); ok=(lab==main)
    gy,gx=np.gradient(d,RES*111000.0); slope=np.hypot(gx,gy).astype(np.float32)
    k=np.ones((5,5),np.uint8)
    rr=(cv2.dilate(d,k)-cv2.erode(d,k)).astype(np.float32)   # local relief ~ valley narrowness/exposure
    print('block',bi,'ready',flush=True)
    return BW,BE,GX,GY,d,ok,slope,rr
CUR={'bi':-1}
def route(a,b):
    lo1,la1=LL[a]; lo2,la2=LL[b]
    for bi,(BW,BE) in enumerate(BLOCKS):
        if BW+0.3<=min(lo1,lo2) and max(lo1,lo2)<=BE-0.3: break
    if CUR['bi']!=bi:
        CUR.update(dict(zip(('BW','BE','GX','GY','d','ok','slope','rr'),build(bi)))); CUR['bi']=bi
    BW,GX,GY=CUR['BW'],CUR['GX'],CUR['GY']; d,ok,slope,rr=CUR['d'],CUR['ok'],CUR['slope'],CUR['rr']
    KM=RES*111.3
    def snap(lo,la):
        r0,c0=int((MN-la)/RES),int((lo-BW)/RES)
        for rad in range(0,50):
            best=None
            for dr in range(-rad,rad+1):
                for dc in range(-rad,rad+1):
                    r,c=r0+dr,c0+dc
                    if 0<=r<GY and 0<=c<GX and ok[r,c]:
                        dd2=dr*dr+dc*dc
                        if best is None or dd2<best[0]: best=(dd2,(r,c))
            if best: return best[1]
    s0=snap(lo1,la1); g=snap(lo2,la2)
    kmx=KM*math.cos(math.radians((la1+la2)/2))
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
    arr=np.array([[BW+c*RES,MN-r*RES] for r,c in p],float)
    for _ in range(4): arr[1:-1]=(arr[:-2]+arr[1:-1]*2+arr[2:])/4
    keep=[arr[0]]
    for q in arr[1:]:
        if math.hypot((q[0]-keep[-1][0])*111,(q[1]-keep[-1][1])*111)>=9: keep.append(q)
    keep.append(arr[-1])
    return [[round(x,4),round(y,4)] for x,y in keep]
done=0
todo.sort(key=lambda ab:(min(LL[ab[0]][0],LL[ab[1]][0])))
for a,b in todo:
    try:
        pts=route(a,b)
        R['legs']['|'.join(sorted([a,b]))]=pts
        done+=1
        print('ROUTED %s|%s (%d pts) [%d/%d]'%(a,b,len(pts),done,len(todo)),flush=True)
        if done%5==0: json.dump(R,open('routes_master.json','w'))
    except Exception as e:
        print('FAIL',a,b,repr(e)[:90],flush=True)
json.dump(R,open('routes_master.json','w'))
print('ROUTE1271 ALL DONE',done,'legs; registry',len(R['legs']),flush=True)
