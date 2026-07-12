# econ_radial_amber.py -- STEP 8: fold the Amber Road into the radial economy, BOTH eras (Zaiton).
# Reads econ_dump_full.json (dumped live from index.html: chains, sea towns, edges, GOODS).
# Emits amber_radial_baked.json:
#   AMBER762 / AMBER1271: { town: {good: price} }
#     - rows for every AMBER town (all goods that reach it)
#     - rows for every OTHER town carrying ONLY the humble northern goods (so hauled wares
#       price sanely anywhere: mead in Baghdad, wadmal in Samarkand)
# Method identical to econ_radial_1271.py: per-source floors, Dijkstra cost fields,
# per-good gradient (peak-floor)/DREF per day, LUX hub premiums / minor discounts.
# KRIS RULINGS folded in: Lubeck stub-leg priced AS IF supplied up the RHINE ROAD
# (Lueneburg salt via the Old Salt Road; Rhenish glass/wine, Flemish linen); in 762 the
# same role falls to HEDEBY (the Frisian trade out of Dorestad). Amber dovetail Truso 8
# -> Kiev ~30 -> the sea. Humble goods stay humble: gentle peaks, real gradients.
import json, heapq
d=json.load(open('econ_dump_full.json'))
GOODS={g['id']:g for g in d['GOODS']}
AMBER={t['n'] for t in d['sea'] if t['amber']}
CAMPS={t['n'] for t in d['sea'] if t['camp']}
HUMBLE=['salt','iron','beads','wadmal','mead','honey','antler']
DREF=140.0

def build_adj(era):
    adj={}
    def link(a,b,days):
        adj.setdefault(a,{})[b]=min(adj.get(a,{}).get(b,1e9),days)
        adj.setdefault(b,{})[a]=min(adj.get(b,{}).get(a,1e9),days)
    if era=='762':
        # the caravan chains, junctions by geography (Dunhuang forks, Kashgar->Fergana, steppe->Samarkand)
        ch=d['chains']
        for arr in ('m1','no','so','m2','st'):
            seq=ch[arr]
            for i in range(1,len(seq)):
                link(seq[i-1]['n'],seq[i]['n'],max(2,(seq[i]['d'] or 500)/70.0))
        link('Dunhuang','Hami',max(2,(ch['no'][0]['d'] or 600)/70.0))
        link('Dunhuang','Miran',max(2,(ch['so'][0]['d'] or 600)/70.0))
        link('Kashgar','Akhsikath',max(2,(ch['m2'][0]['d'] or 600)/70.0))
        link('Chach','Samarkand',7.0)
        for e in d['edges']:
            if e['era'] in (None,'762'):
                dd=e['d']
                if e['terr'] in ('canal','river'): dd*=1.5
                link(e['a'],e['b'],max(1,dd))   # 762 sea legs raw, as in the live prototype bake
    else:
        DEEP={('Kauthara','Kollam')}
        FRONTIER={('Baghdad','Damascus'),('Aleppo','Baghdad')}
        NORTHD={('Sarai','Urgench'),('Urgench','Otrar'),('Otrar','Almaliq'),('Mangyshlak','Urgench'),
                ('Tana','Sarai'),('Almaliq','Talas'),('Otrar','Ispijab'),('Ispijab','Talas'),
                ('Sarai','Abaskun'),('Sarai','Mangyshlak')}
        def mult(a,b):
            if (a,b) in FRONTIER or (b,a) in FRONTIER: return 1.6
            return 1.45 if ((a,b) in NORTHD or (b,a) in NORTHD) else 1.0
        for e in d['edges']:
            if e['era'] in (None,'1271'):
                dd=e['d']
                if e['terr']=='med': dd=dd*3+(120 if (e['a'],e['b']) in DEEP or (e['b'],e['a']) in DEEP else 0)
                elif e['terr'] in ('canal','river'): dd*=1.5
                link(e['a'],e['b'],max(1,dd*mult(e['a'],e['b'])))
    return adj

# ---- classic sources (verbatim from the live bakes) + the NORTHERN taps ----
SRC762={
 'silk':(58,{"Chang'an":8}),'tea':(26,{"Chang'an":4,'Luoyang':5}),'paper':(34,{"Chang'an":5,'Luoyang':6,'Samarkand':7}),
 'musk':(150,{'Khotan':22,'Kucha':30}),'jade':(55,{'Khotan':12}),'pepper':(72,{'Kollam':40,'Mantai':44,'Yarkand':52}),
 'lapis':(55,{'Samarkand':11}),'turq':(46,{'Nishapur':28}),'glass':(60,{'Baghdad':12,'Aleppo':14,'Alexandria':16,'Hedeby':20}),
 'coral':(135,{'Constantinople':34,'Aleppo':40}),
 'amber':(120,{'Truso':8,'Paviken':15}),   # THE ROAD ITSELF: the source moves to the Baltic shore
 'wine':(78,{'Turfan':15,'Aleppo':22,'Constantinople':24,'Hedeby':24}),'pearls':(120,{'Basra':26,'Mantai':30}),
 'ivory':(90,{'Zanzibar':55,'Kollam':70}),'frank':(66,{'Dhofar':12,'Aden':18}),'indigo':(62,{'Kollam':44}),
 'cinn':(70,{'Mantai':56,'Kollam':58}),'wax':(46,{'Constantinople':28,'Aleppo':30,'the Vitba village':15,'Aldeigjuborg':15}),
 'nutmeg':(95,{'Palembang':55}),'pelts':(90,{'Zanzibar':60}),'conut':(14,{'Kollam':10,'Mantai':10,'Zanzibar':11}),
 'linen':(30,{'Alexandria':12,'Aleppo':16,'Hedeby':18}),
 'furs':(95,{'Constantinople':30,'Trebizond':30,'Suyab':32,'Aldeigjuborg':13,'Grobina':16,'Kiev hillfort':16,'Sarskoye fort':12}),   # Kiev: poliudie; Sarskoye: the Merya fur mart
 'slaves':(120,{'Zanzibar':66,'Samarkand':72,'Constantinople':74,'Atil':62}),'aloe':(46,{'Socotra':14,'Dhofar':18}),   # Atil: THE northern slave mart
 'felt':(32,{'Kucha':11,'Kashgar':12}),'naphtha':(74,{'Baghdad':9}),'asbestos':(232,{'Khotan':55}),
 'dates':(40,{'Medina':7,'Basra':8,'Baghdad':10}),'saffron':(144,{'Rey':120,'Kashan':122}),
 # the humble wares (762 names)
 'salt':(34,{'Hedeby':9,'Cherson':8}),
 'iron':(34,{'Birka':9,'Vadet':8}),           # Bergslagen / osmund iron
 'beads':(30,{'Hedeby':8,'Birka':10}),        # the bead-workshops of the emporia
 'wadmal':(26,{'Paviken':8}),                 # Gotland wool cloth
 'mead':(28,{'Old Uppsala':10,'Lejre':11}),
 'honey':(26,{'Kiev hillfort':6,'Aldeigjuborg':9}),
 'antler':(20,{'Vadet':5,'the Vitba village':4}),
}
SRC1271={
 'silk':(58,{'Kinsay':8,"Chang'an":9,'Tabriz':20}),'tea':(26,{'Kinsay':4,"Chang'an":5}),
 'musk':(150,{'Ningxia':22,'Khotan':26}),'jade':(55,{'Khotan':12}),
 'pepper':(72,{'Kollam':40,'Zaiton':50,'Yarkand':52,'Balkh':60}),'lapis':(55,{'Badakhshan':9}),
 'ruby':(200,{'Badakhshan':95}),'turq':(46,{'Nishapur':28}),
 'glass':(60,{'Venice':12,'Damascus':13,'Acre':14,'Alexandria':16,'Lubeck':18}),   # Rhenish glass up the Rhine Road
 'coral':(135,{'Venice':30,'Candia':36}),
 'amber':(120,{'Gdansk':11,'Visby':16}),      # the source moves to the shore; Venice/Tana floors retired
 'wine':(78,{'Venice':12,'Candia':14,'Turfan':15,'Taiyuan':16,'Lubeck':16}),        # Rhenish wine
 'pearls':(120,{'Hormuz':24,'Kollam':30}),'ivory':(150,{'Kollam':62,'Hormuz':66}),
 'frank':(66,{'Hormuz':20,'Alexandria':22}),'indigo':(62,{'Kollam':44,'Hormuz':50}),
 'cinn':(98,{'Kollam':56,'Zaiton':60}),
 'wax':(46,{'Ragusa':26,'Caffa':28,'Tana':28,'Novgorod':14,'Smolensk':15}),
 'nutmeg':(135,{'Zaiton':58,'Kollam':66}),'pelts':(90,{'Alexandria':52,'Hormuz':60}),
 'conut':(14,{'Kollam':10,'Kauthara':10}),
 'linen':(30,{'Alexandria':12,'Venice':18,'Lubeck':14}),                            # Flemish linen
 'furs':(95,{'Tana':26,'Caffa':28,'Sarai':28,'Urgench':30,'Karakorum':34,'Novgorod':12,'Turku':14,'Kiev':18,'Bolghar':16}),
 'slaves':(120,{'Caffa':60,'Tana':62,'Sarai':66,'Urgench':66,'Almaliq':70}),
 'aloe':(46,{'Hormuz':20,'Kollam':22}),'felt':(32,{'Almaliq':10,'Karakorum':10,'Sarai':12}),
 'naphtha':(74,{'Baghdad':9}),'asbestos':(232,{'Turfan':55,'Khotan':60}),
 'dates':(40,{'Baghdad':8,'Hormuz':8,'Kerman':10}),'saffron':(144,{'Nishapur':118,'Yazd':122}),
 'cotton':(44,{'Kashgar':10,'Khotan':11,'Yazd':12,'Kollam':12}),'porc':(160,{'Zaiton':30,'Kinsay':34}),
 # the humble wares (1271 names)
 'salt':(34,{'Lubeck':6}),                    # Lueneburg salt, the Old Salt Road -- THE Hanse staple
 'iron':(34,{'Stockholm':8,'Vadet':8,'Lodose':9}),
 'beads':(30,{'Lubeck':11,'Visby':14}),
 'wadmal':(26,{'Visby':7}),
 'mead':(28,{'Uppsala':12,'Roskilde':11}),
 'honey':(26,{'Novgorod':6,'Bolghar':7}),
 'antler':(20,{'Turku':5,'Aldeigjuborg':6}),
}
BIG762={'Constantinople':1.18,'Baghdad':1.15,"Chang'an":1.12,'Samarkand':1.08,'Aleppo':1.08,'Basra':1.06,'Alexandria':1.08,'Atil':1.10}
BIG1271={'Kinsay':1.18,'Khanbaliq':1.15,'Tabriz':1.15,'Venice':1.12,'Sarai':1.08,'Zaiton':1.08,'Constantinople':1.06}
LUX={'silk','musk','jade','coral','amber','pearls','saffron','asbestos','ivory','nutmeg','porc'}
HUBINFO={t['n']:(t['hub'] or '') for t in d['sea']}
for arr in d['chains'].values():
    for c in arr: HUBINFO.setdefault(c['n'],c.get('hub') or '')

def bake(era):
    adj=build_adj(era); SRC=SRC762 if era=='762' else SRC1271; BIG=BIG762 if era=='762' else BIG1271
    out={}; provs={}
    for gid,(peak,srcs) in SRC.items():
        best={}; prov={}; pq=[]
        for s,fl in srcs.items():
            if s not in adj: continue
            best[s]=fl; prov[s]=s; heapq.heappush(pq,(fl,s))
        while pq:
            p,u=heapq.heappop(pq)
            if p>best.get(u,1e18): continue
            per=(peak-srcs[prov[u]])/DREF
            for v,dd in adj.get(u,{}).items():
                np_=p+dd*per
                if np_<best.get(v,1e18): best[v]=np_; prov[v]=prov[u]; heapq.heappush(pq,(np_,v))
        for c,p in best.items():
            p=min(p,peak*1.25)
            if gid in LUX:
                if c in BIG: p*=BIG[c]
                elif HUBINFO.get(c)=='minor': p*=0.88
            out.setdefault(c,{})[gid]=round(p)
            provs.setdefault(c,{})[gid]=prov[c]
    return out,provs

def emit(era,full):
    """rows: AMBER towns (all goods) + everyone else (humble goods only). Camps excluded (no market)."""
    tbl={}
    for c,row in full.items():
        if c in CAMPS: continue
        if c in AMBER: tbl[c]=dict(row)
        else:
            h={g:row[g] for g in HUMBLE if g in row}
            if h: tbl[c]=h
    return tbl

R762,P762=bake('762'); R1271,P1271=bake('1271')
T762=emit('762',R762); T1271=emit('1271',R1271)

# ---- VALIDATION: dovetail vs Kris's hand table + historical flows ----
HAND={'Truso':{'amber':8},'Visby':{'amber':16},'Hedeby':{'amber':18,'beads':8},'Kiev':{'amber':30},
 'Kiev hillfort':{'amber':30},'Cherson':{'amber':38},'Novgorod':{'furs':12,'honey':6},
 'Aldeigjuborg':{'furs':13},'Uppsala':{'iron':10},'Lubeck':{'salt':6}}
print('=== DOVETAIL vs hand AMBER_PRICES (want within ~35%) ===')
bad=0
for t,gs in HAND.items():
    for g,hv in gs.items():
        for era,tbl in (('762',T762),('1271',T1271)):
            if t in tbl and g in tbl[t]:
                bv=tbl[t][g]; rel=abs(bv-hv)/hv
                flag='OK ' if rel<=0.35 else 'XX '; bad+=(rel>0.35)
                print(' %s %-14s %-7s hand %-3d baked %-3d (%s)'%(flag,t,g,hv,bv,era))
print('=== FLOWS ===')
FLOW=[('762','amber','Kiev hillfort','Truso'),('762','amber','Cherson','Truso'),
 ('762','furs','Cherson',('Aldeigjuborg','Grobina','Kiev hillfort')),('762','salt','Birka','Hedeby'),
 ('762','glass','Birka','Hedeby'),('762','honey','Paviken',('Kiev hillfort','Aldeigjuborg')),
 ('1271','amber','Kiev','Gdansk'),('1271','salt','Novgorod','Lubeck'),
 ('1271','iron','Novgorod',('Stockholm','Vadet','Lodose')),('1271','wadmal','Riga','Visby'),
 ('1271','honey','Visby','Novgorod'),('1271','glass','Visby',('Lubeck','Venice')),
 ('1271','furs','Kiev',('Novgorod','Kiev')),('1271','wax','Riga',('Novgorod','Smolensk'))]
fail=0
for era,g,mkt,exp in FLOW:
    P=P762 if era=='762' else P1271
    got=P.get(mkt,{}).get(g,'?')
    exp=(exp,) if isinstance(exp,str) else exp
    ok='OK ' if got in exp else 'XX '; fail+=(got not in exp)
    tbl=T762 if era=='762' else T1271
    print(' %s %s %-7s @ %-14s want %-24s got %-14s (%s s)'%(ok,era,g,mkt,'/'.join(exp),got,tbl.get(mkt,{}).get(g,'?')))
print('DOVETAIL misses:',bad,' FLOW failures:',fail)
json.dump({'AMBER762':T762,'AMBER1271':T1271},open('amber_radial_baked.json','w'))
print('BAKED rows: 762=%d towns, 1271=%d towns -> amber_radial_baked.json'%(len(T762),len(T1271)))
