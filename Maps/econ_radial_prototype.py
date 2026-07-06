import json, heapq
d=json.load(open('econ_dump.json'))
GOODS={g['id']:g for g in d['GOODS']}; OVR=d['OVR']; cities=d['cities']
adj={}
def link(a,b,days): adj.setdefault(a,{})[b]=min(adj.get(a,{}).get(b,1e9),days); adj.setdefault(b,{})[a]=min(adj.get(b,{}).get(a,1e9),days)
for e in d['edges']:
    if e['era']=='762': link(e['a'],e['b'],max(1,e['d']))
seq=sorted([(v['frac'],n) for n,v in cities.items() if v.get('dist') is not None]); names=[n for _,n in seq]
for i in range(len(names)-1): link(names[i],names[i+1],max(2,(cities[names[i+1]].get('dist') or 700)/70.0))
DREF=140.0
# SRC: good -> (peak, {source_city: floor, ...})  -- per-source floors (Kris: Zanzibar cheapest, hubs pegged higher)
SRC={
 'silk':(58,{"Chang'an":8}),'tea':(26,{"Chang'an":4,'Luoyang':5}),'paper':(34,{"Chang'an":5,'Luoyang':6,'Samarkand':7}),
 'musk':(150,{'Khotan':22,'Kucha':30}),'jade':(55,{'Khotan':12}),'pepper':(72,{'Kollam':40,'Mantai':44}),
 'lapis':(55,{'Samarkand':11}),'turq':(46,{'Nishapur':28}),'glass':(60,{'Baghdad':12,'Aleppo':14,'Alexandria':16}),
 'coral':(135,{'Constantinople':34,'Aleppo':40}),'amber':(120,{'Constantinople':40,'Trebizond':42}),
 'wine':(78,{'Turfan':15,'Aleppo':22,'Constantinople':24}),'pearls':(120,{'Basra':26,'Mantai':30}),
 'ivory':(90,{'Zanzibar':55,'Kollam':70}),'frank':(66,{'Dhofar':12,'Aden':18}),'indigo':(62,{'Kollam':44}),
 'cinn':(70,{'Mantai':56,'Kollam':58}),'wax':(46,{'Constantinople':28,'Aleppo':30}),'nutmeg':(95,{'Palembang':55}),
 'pelts':(90,{'Zanzibar':60}),'conut':(14,{'Kollam':10,'Mantai':10,'Zanzibar':11}),
 'linen':(30,{'Alexandria':12,'Aleppo':16}),'furs':(95,{'Constantinople':30,'Trebizond':30,'Suyab':32}),
 'slaves':(120,{'Zanzibar':66,'Samarkand':72,'Constantinople':74}),'aloe':(46,{'Socotra':14,'Dhofar':18}),
 'felt':(32,{'Kucha':11,'Kashgar':12}),'naphtha':(74,{'Baghdad':9}),'asbestos':(232,{'Khotan':55}),
 'dates':(40,{'Medina':7,'Basra':8,'Baghdad':10}),'saffron':(144,{'Rey':120,'Kashan':122}),
}
BIG={'Constantinople':1.18,'Baghdad':1.15,"Chang'an":1.12,'Samarkand':1.08,'Aleppo':1.08,'Basra':1.06,'Alexandria':1.08}
LUX={'silk','musk','jade','coral','amber','pearls','saffron','asbestos','ivory','nutmeg'}
PORTD={'naphtha':{c:1.5 for c in ['Basra','Aden','Qulzum','Alexandria','Guangzhou','Yangzhou','Hormuz','Muscat']}}
def field(gid):
    peak,srcs=SRC[gid]; pd=PORTD.get(gid,{})
    best={}; prov={}; pq=[]
    for s,fl in srcs.items():
        if s not in adj and s not in cities: continue
        v=fl*pd.get(s,1.0); best[s]=v; prov[s]=s; heapq.heappush(pq,(v,s))
    while pq:
        p,u=heapq.heappop(pq)
        if p>best.get(u,1e18): continue
        per=(peak-srcs[prov[u]])/DREF
        for v,dd in adj.get(u,{}).items():
            np_=(p+dd*per)*pd.get(v,1.0)
            if np_<best.get(v,1e18): best[v]=np_; prov[v]=prov[u]; heapq.heappush(pq,(np_,v))
    return best,prov
def px(gid):
    best,prov=field(gid); out={}
    for c,p in best.items():
        if gid in LUX:
            if c in BIG: p*=BIG[c]
            elif cities.get(c,{}).get('hub')=='minor': p*=0.88
        out[c]=(round(p),prov[c])
    return out
# ---- HISTORICAL TRADE-FLOW VALIDATION: (good, market, expected cheapest source) ----
TESTS=[('slaves','Basra','Zanzibar'),('slaves','Baghdad','Zanzibar'),('slaves','Samarkand','Samarkand'),
 ('slaves','Constantinople','Constantinople'),('silk','Constantinople',"Chang'an"),('jade','Baghdad','Khotan'),
 ('frank','Baghdad','Dhofar'),('frank','Constantinople','Dhofar'),('pepper','Baghdad','Kollam'),
 ('pearls','Baghdad','Basra'),('furs','Baghdad','Constantinople'),('amber','Baghdad','Constantinople'),
 ('naphtha','Basra','Baghdad'),('paper','Baghdad','Samarkand'),('lapis','Baghdad','Samarkand'),
 ('linen','Baghdad','Alexandria'),('ivory','Baghdad','Zanzibar'),('nutmeg','Baghdad','Palembang'),
 ('coral','Samarkand','Constantinople'),('aloe','Baghdad','Socotra')]
print("HISTORICAL TRADE-FLOW VALIDATION (does the cheapest delivered source match history?)")
fail=0
for gid,mkt,exp in TESTS:
    f=px(gid); got=f.get(mkt,('?','?'))
    ok='OK ' if got[1]==exp else 'XX '
    if got[1]!=exp: fail+=1
    print("  %s %-9s @ %-14s want %-14s got %-14s (%s s)"%(ok,gid,mkt,exp,got[1],got[0]))
print("FAILURES:",fail,"/",len(TESTS))

# --- EXPORT: bake RADIAL[city][good] for all 762 nodes ---
import json as _j
RAD={}
for gid in SRC:
    f=px(gid)
    for city,(pr,prov) in f.items():
        RAD.setdefault(city,{})[gid]=pr
_j.dump(RAD,open('/tmp/radial_table.json','w'))
print('BAKED',len(RAD),'cities x',len(SRC),'goods')
# sanity: every good has a source floor as its global min
for gid in SRC:
    vals=[RAD[c][gid] for c in RAD if gid in RAD[c]]
    print('  %-9s min %-4s max %-4s'%(gid,min(vals),max(vals)))
