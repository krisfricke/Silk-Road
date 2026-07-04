import numpy as np, heapq, json, gc
exec(open('bake_1271_regions.py').read().split("R_ANAT=")[0])
MS,MN=24.0,52.0; RES=0.03
BLOCKS=[(8.0,52.0),(50.0,96.0),(94.0,123.0)]
for bi,(BW,BE) in enumerate(BLOCKS):
    GX=int((BE-BW)/RES); GY=int((MN-MS)/RES)
    print('block',bi,GX,GY,flush=True)
    d=dem(BW,BE,MS,MN,GX,GY).astype(np.float32); gc.collect()
    print('dem ok',flush=True)
    sea=(d<0)
    filled=np.where(sea,np.float32(-1000.0),d).astype(np.float32)
    visited=np.zeros(d.shape,bool); pq=[]
    for c in range(GX):
        for r in (0,GY-1):
            if not visited[r,c]: visited[r,c]=True; heapq.heappush(pq,(float(filled[r,c]),r,c))
    for r in range(GY):
        for c in (0,GX-1):
            if not visited[r,c]: visited[r,c]=True; heapq.heappush(pq,(float(filled[r,c]),r,c))
    ys,xs=np.where(sea)
    for k in range(0,len(ys),5):
        r,c=int(ys[k]),int(xs[k])
        if not visited[r,c]: visited[r,c]=True; heapq.heappush(pq,(float(filled[r,c]),r,c))
    EPS=1e-3
    while pq:
        e,r,c=heapq.heappop(pq)
        for dr in(-1,0,1):
            for dc in(-1,0,1):
                if not dr and not dc: continue
                nr,nc=r+dr,c+dc
                if 0<=nr<GY and 0<=nc<GX and not visited[nr,nc]:
                    visited[nr,nc]=True
                    ne=max(float(filled[nr,nc]),e+EPS)
                    filled[nr,nc]=ne
                    heapq.heappush(pq,(ne,nr,nc))
    print('fill ok',flush=True)
    del visited,pq; gc.collect()
    order=np.argsort(filled,axis=None)[::-1]
    acc=np.ones(d.shape,np.float32); acc[sea]=0
    fr=(order//GX).astype(np.int32); fc=(order%GX).astype(np.int32)
    NB=[(-1,-1),(-1,0),(-1,1),(0,-1),(0,1),(1,-1),(1,0),(1,1)]
    for k in range(len(order)):
        r=int(fr[k]); c=int(fc[k])
        if sea[r,c]: continue
        be=filled[r,c]; bdr=0; bdc=0
        for dr,dc in NB:
            nr,nc=r+dr,c+dc
            if 0<=nr<GY and 0<=nc<GX and filled[nr,nc]<be:
                be=filled[nr,nc]; bdr=dr; bdc=dc
        if bdr or bdc: acc[r+bdr,c+bdc]+=acc[r,c]
    print('accum ok',float(acc.max()),flush=True)
    cell=(RES*111.3)*(RES*111.3*0.75)
    lvl=np.zeros(d.shape,np.uint8)
    A=acc*cell
    lvl[(A>4000)&~sea]=1; lvl[(A>25000)&~sea]=2; lvl[(A>120000)&~sea]=3
    np.save('/tmp/flow_block_%d.npy'%bi,lvl)
    json.dump({'BW':BW,'BE':BE,'RES':RES},open('/tmp/flow_block_%d.json'%bi,'w'))
    del d,sea,filled,order,acc,A,lvl,fr,fc; gc.collect()
print('FLOW ALL DONE',flush=True)
