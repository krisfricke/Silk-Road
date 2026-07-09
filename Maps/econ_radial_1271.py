# econ_radial_1271.py -- the 1271 radial price bake (Talas), mirroring econ_radial_prototype.py.
# World: the Pax Mongolica. Tabriz inherits Baghdad's hub role; Baghdad is wreckage (no BIG premium,
# naphtha floor only); Chinese goods flow freely; the Black Sea (Caffa/Tana) is the fur+slave gate;
# Venice/Candia/Acre are the western sources; Badakhshan (now a node) is the TRUE lapis source;
# Hormuz carries the Gulf trade. NEW 1271 goods: cotton (Kris: 'cotton matters'), porcelain.
# Graph = live era:'1271' SEA_EDGES (Maps/econ_dump_1271.json) + the Mangyshlak|Urgench leg being
# wired this round. Sea cost: med days x3 (risk), +120d monsoon on the two deep crossings
# (Kauthara|Kollam, Kollam|Hormuz), river/canal x1.5 -- same treatment as the live 762 model.
import json, heapq
d=json.load(open('econ_dump_1271.json'))
DEEP={('Kauthara','Kollam')}   # the Bay of Bengal + Strait run; Kollam<->Hormuz is a routine monsoon passage
adj={}
def link(a,b,days): adj.setdefault(a,{})[b]=min(adj.get(a,{}).get(b,1e9),days); adj.setdefault(b,{})[a]=min(adj.get(b,{}).get(a,1e9),days)
for e in d['edges']:
    dd=e['d']
    if e['terr']=='med': dd=dd*3+(120 if (e['a'],e['b']) in DEEP or (e['b'],e['a']) in DEEP else 0)
    elif e['terr'] in ('canal','river'): dd=dd*1.5
    link(e['a'],e['b'],max(1,dd))
# NORTHERN DETOUR COST (Fadak item C, 2.09.49): the steppe circuit is slow, escorted, toll-ridden -
# tropical luxuries should NOT propagate north as cheaply as the day-count suggests. x1.45 effective days.
NORTH={('Sarai','Urgench'),('Urgench','Otrar'),('Otrar','Almaliq'),('Mangyshlak','Urgench'),('Tana','Sarai'),
 ('Almaliq','Talas'),('Otrar','Ispijab'),('Ispijab','Talas'),('Sarai','Abaskun'),('Sarai','Mangyshlak')}
for e in list(adj.keys()):
    pass
FRONTIER={('Baghdad','Damascus'),('Aleppo','Baghdad')}   # the Mamluk-Ilkhanid war frontier: licensed, taxed, watched by both sides
def _northmult(a,b):
    if (a,b) in FRONTIER or (b,a) in FRONTIER: return 1.6
    return 1.45 if ((a,b) in NORTH or (b,a) in NORTH) else 1.0
# rebuild adj with the multiplier
_adj2={}
for a in adj:
    for b,dd in adj[a].items():
        _adj2.setdefault(a,{})[b]=dd*_northmult(a,b)
adj=_adj2
cities=d['cities']
DREF=140.0
SRC={
 'silk':(58,{'Kinsay':8,"Chang'an":9,'Tabriz':20}),
 'tea':(26,{'Kinsay':4,"Chang'an":5}),
 'musk':(150,{'Ningxia':22,'Khotan':26}),
 'jade':(55,{'Khotan':12}),
 'pepper':(72,{'Kollam':40,'Zaiton':50,'Yarkand':52,'Balkh':60}),   # Fadak: +Yarkand (Karakoram/Leh tap) +Balkh (Kabul tap). On re-bake add a Med pepper route (e.g. Alexandria) or the overland tap over-reaches to Venice; Fadak hand-capped that in live RADIAL1271.
 'lapis':(55,{'Badakhshan':9}),
 'ruby':(200,{'Badakhshan':95}),   # Fadak: balas rubies (Kuh-i-Lal spinels, Polo's 'Balascia')
 'turq':(46,{'Nishapur':28}),
 'glass':(60,{'Venice':12,'Damascus':13,'Acre':14,'Alexandria':16}),   # Damascus glass: the pre-Timur ateliers
 'coral':(135,{'Venice':30,'Candia':36}),
 'amber':(120,{'Venice':40,'Tana':42,'Sarai':46,'Caffa':48}),
 'wine':(78,{'Venice':12,'Candia':14,'Turfan':15,'Taiyuan':16}),
 'pearls':(120,{'Hormuz':24,'Kollam':30}),
 'ivory':(150,{'Kollam':62,'Hormuz':66}),   # steepened (Fadak C): flat fields let remote marts stock tropical luxuries
 'frank':(66,{'Hormuz':20,'Alexandria':22}),
 'indigo':(62,{'Kollam':44,'Hormuz':50}),
 'cinn':(98,{'Kollam':56,'Zaiton':60}),
 'wax':(46,{'Ragusa':26,'Caffa':28,'Tana':28}),
 'nutmeg':(135,{'Zaiton':58,'Kollam':66}),
 'pelts':(90,{'Alexandria':52,'Hormuz':60}),
 'conut':(14,{'Kollam':10,'Kauthara':10}),
 'linen':(30,{'Alexandria':12,'Venice':18}),
 'furs':(95,{'Tana':26,'Caffa':28,'Sarai':28,'Urgench':30,'Karakorum':34}),
 'slaves':(120,{'Caffa':60,'Tana':62,'Sarai':66,'Urgench':66,'Almaliq':70}),
 'aloe':(46,{'Hormuz':20,'Kollam':22}),
 'felt':(32,{'Almaliq':10,'Karakorum':10,'Sarai':12}),
 'naphtha':(74,{'Baghdad':9}),
 'asbestos':(232,{'Turfan':55,'Khotan':60}),
 'dates':(40,{'Baghdad':8,'Hormuz':8,'Kerman':10}),
 'saffron':(144,{'Nishapur':118,'Yazd':122}),
 'cotton':(44,{'Kashgar':10,'Khotan':11,'Yazd':12,'Kollam':12}),
 'porc':(160,{'Zaiton':30,'Kinsay':34}),
}
BIG={'Kinsay':1.18,'Khanbaliq':1.15,'Tabriz':1.15,'Venice':1.12,'Sarai':1.08,'Zaiton':1.08,'Constantinople':1.06}
LUX={'silk','musk','jade','coral','amber','pearls','saffron','asbestos','ivory','nutmeg','porc'}
PORTD={'naphtha':{c:1.5 for c in ['Venice','Zaiton','Hormuz','Alexandria','Acre']}}
def field(gid):
    peak,srcs=SRC[gid]; pd=PORTD.get(gid,{})
    best={}; prov={}; pq=[]
    for s,fl in srcs.items():
        if s not in adj: continue
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
        peak=SRC[gid][0]
        p=min(p,peak*1.25)   # cap runaway gradients on the far side of the deep-sea legs
        if gid in LUX:
            if c in BIG: p*=BIG[c]
            elif cities.get(c,{}).get('hub')=='minor': p*=0.88
        out[c]=(round(p),prov[c])
    return out
TESTS=[
 ('slaves','Alexandria',('Caffa','Tana')),   # Black Sea slaves to the Mamluks -- THE trade of the age
 ('slaves','Venice',('Caffa','Tana')),
 ('furs','Constantinople',('Caffa','Tana')),
 ('amber','Sarai',('Tana',)),                # Baltic amber down the Rus rivers
 ('silk','Venice',('Tabriz','Kinsay',"Chang'an")),  # Gilan/China silk via Tabriz-Ayas
 ('pepper','Venice',('Kollam',)),
 ('pepper','Khanbaliq',('Zaiton','Kollam')),
 ('jade','Khanbaliq',('Khotan',)),
 ('lapis','Tabriz',('Badakhshan',)),
 ('pearls','Tabriz',('Hormuz',)),
 ('porc','Tabriz',('Zaiton','Kinsay')),
 ('wine','Khanbaliq',('Taiyuan',)),
 ('dates','Tabriz',('Baghdad',)),
 ('glass','Tabriz',('Acre','Venice','Alexandria','Damascus')),
 ('frank','Tabriz',('Hormuz','Alexandria')),
 ('musk','Khanbaliq',('Ningxia',)),
 ('turq','Venice',('Nishapur',)),
 ('saffron','Tabriz',('Nishapur','Yazd')),
 ('cotton','Venice',('Kollam','Yazd','Kashgar','Khotan')),
 ('felt','Samarkand',('Almaliq','Sarai','Karakorum')),
 ('naphtha','Hormuz',('Baghdad',)),
 ('wine','Venice',('Venice',)),
 ('furs','Urgench',('Urgench','Tana','Sarai','Caffa')),
]
print("1271 HISTORICAL TRADE-FLOW VALIDATION")
fail=0
for gid,mkt,exp in TESTS:
    f=px(gid); got=f.get(mkt,('?','?'))
    ok='OK ' if got[1] in exp else 'XX '
    if got[1] not in exp: fail+=1
    print("  %s %-8s @ %-14s want %-28s got %-12s (%s s)"%(ok,gid,mkt,'/'.join(exp),got[1],got[0]))
print("FAILURES:",fail,"/",len(TESTS))
RAD={}
for gid in SRC:
    f=px(gid)
    for city,(pr,prov) in f.items(): RAD.setdefault(city,{})[gid]=pr
GP={gid:max(v[gid] for v in RAD.values() if gid in v) for gid in SRC}
json.dump({'RADIAL1271':RAD,'GPEAK1271':GP},open('radial1271_baked.json','w'))
print('BAKED',len(RAD),'cities x',len(SRC),'goods -> radial1271_baked.json')
for gid in SRC:
    vals=[RAD[c][gid] for c in RAD if gid in RAD[c]]
    print('  %-9s min %-4s max %-4s'%(gid,min(vals),max(vals)))
