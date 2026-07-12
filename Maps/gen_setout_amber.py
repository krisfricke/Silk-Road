# gen_setout_amber.py -- set-out charts for the AMBER ROAD + VOLGA nodes, BOTH ERAS (Zaiton, task 7).
# Pattern of gen_setout_1271.py; geometry from routes_amber.json (rivers real, sea lanes snapped);
# nodes/edges era-filtered from econ_dump_full.json; base via slice_master (52N straddle composite,
# 762 relief variants); quilt via fields_multi with per-era SETTLE (amber towns + northern acreage
# taper); anachronize(era=...) gates Malaren-as-lake to 1271. Keys: so_<slug> (1271) / so762_<slug>.
# Usage: python3 gen_setout_amber.py <era> <TownName>   (one node per run; 45s windows)
import numpy as np, json, math, re, os, sys
from PIL import Image
from slice_master import slice_master
from rebake_1271_fields import fields_multi, anachronize, SEASONS, SETTLE, relief_boost, SEAFED

ERA=sys.argv[1]; TARGET=sys.argv[2]
R=json.load(open('routes_amber.json'))
D=json.load(open('econ_dump_full.json'))
LL={**{n:tuple(v) for n,v in R['LL'].items()}}
SEA={t['n']:t for t in D['sea']}
def inera(t): return (t.get('era') in (None,ERA))
NBR={}
for e in D['edges']:
    if e['era'] in (None,ERA) and e['a'] in LL and e['b'] in LL and inera(SEA.get(e['a'],{})) and inera(SEA.get(e['b'],{})):
        NBR.setdefault(e['a'],set()).add(e['b']); NBR.setdefault(e['b'],set()).add(e['a'])
EDGE_TERR={'|'.join(sorted([e['a'],e['b']])):e['terr'] for e in D['edges']}
def legkey(a,b): return '|'.join(sorted([a,b]))
def geom(a,b):
    g=R['legs'].get(legkey(a,b))
    return g if g else [list(LL[a]),list(LL[b])]
# per-era SETTLE: base southern towns + amber towns (non-camp), radius by hub, acreage lat-taper
AM_SETTLE=list(SETTLE)
SEAFED2=dict(SEAFED); SEAFED2.update({'Visby':.5,'Lubeck':.5,'Havn':.4,'Riga':.4,'Novgorod':.3})
for t in D['sea']:
    n=t['n']
    if n not in LL or t.get('camp') or not inera(t): continue
    if any(s[0]==n for s in AM_SETTLE): continue
    lo,la=LL[n]
    BIG={'Novgorod','Visby','Lubeck','Riga','Bolghar','Nizhny Novgorod','Atil'}
    MID={'Gdansk','Reval','Havn','Stockholm','Uppsala','Smolensk','Tver','Yaroslavl','Polotsk','Vitebsk','Cherson','Truso','Paviken','Old Uppsala','Kiev hillfort','Kiev','Hedeby','Birka'}
    r=36 if n in BIG else (22 if n in MID else 14)
    if la>60: r=int(r*0.63)
    elif la>58: r=int(r*0.78)
    AM_SETTLE.append((n,lo,la,r))
MW,ME=8.0,64.666667; MS,MN=24.0,61.0
C=TARGET
nodes=[C]+sorted(NBR.get(C,[]))
lons=[];lats=[]
for n in nodes:
    if n in LL: lons.append(LL[n][0]); lats.append(LL[n][1])
for n in NBR.get(C,[]):
    for pt in geom(C,n): lons.append(pt[0]); lats.append(pt[1])
W,E=min(lons),max(lons); S0,N=min(lats),max(lats)
padx=max(0.6,(E-W)*0.10); pady=max(0.5,(N-S0)*0.10)
W-=padx; E+=padx; S0-=pady; N+=pady
if E-W<4: c0=(E+W)/2; W,E=c0-2,c0+2
if N-S0<3: c0=(N+S0)/2; S0,N=c0-1.5,c0+1.5
W=max(W,MW); E=min(E,ME); S0=max(S0,MS); N=min(N,MN)
OW=1400
_latm=math.cos(math.radians((S0+N)/2))
OH=int(OW*(N-S0)/((E-W)*_latm))
# ASPECT IS SACRED: expand the rect, never clamp pixels
if OH<500:
    _span=500.0*(E-W)*_latm/OW; _ext=(_span-(N-S0))/2; S0-=_ext; N+=_ext
elif OH>2100:
    _spanl=OW*(N-S0)/(2100.0*_latm); _extl=(_spanl-(E-W))/2; W-=_extl; E+=_extl
    if W<MW: E+=(MW-W); W=MW
    if E>ME: W-=(E-ME); E=ME
N=min(N,MN); S0=max(S0,MS)
_latm=math.cos(math.radians((S0+N)/2))
OH=max(60,min(2400,int(OW*(N-S0)/((E-W)*_latm))))
pref='so762_' if ERA=='762' else 'so_'
def slug(n): return re.sub(r"[^a-z]","",n.lower())
fn='%s%s.jpg'%(pref.rstrip('_')+'1271_' if False else ('so762amber_' if ERA=='762' else 'so1271_'),slug(C))
slice_master(W,E,S0,N,OW,OH,'_tmp_soA.png',era=ERA)
img=np.array(Image.open('_tmp_soA.png').convert('RGB'))
img=relief_boost(img,(W,E,S0,N),OW,OH)
img,_eph,_forbid=anachronize(img,(W,E,S0,N),era=ERA)
geo=(round(W,2),round(E,2),round(S0,2),round(N,2))
def px(lon,lat): return (round((lon-geo[0])/(geo[1]-geo[0])*OW,1),round((geo[3]-lat)/(geo[3]-geo[2])*OH,1))
_roadpx=[]
_towns=set([C])|set(NBR.get(C,[]))
for _a in list(_towns):
    for _b in NBR.get(_a,[]):
        _g=geom(_a,_b)
        if _g: _roadpx.append([px(_lo,_la) for _lo,_la in _g[::3]])
import rebake_1271_fields as RB
RB.SEAFED=SEAFED2
_sea=fields_multi(img,(W,E,S0,N),AM_SETTLE,seasons=SEASONS,roads=_roadpx,forbid=_forbid)
for _sn,_img in _sea.items():
    _img=_img.copy()
    if _sn=='winter':
        # SNOW DUSTING (Kris): land whitens where January would freeze it. Jan-temp proxy fitted
        # to TOWN_JAN (Havn 0, Novgorod -10, Kiev -5): T = 0.573*(55.7-lat) - 0.449*(lon-12.6).
        latg=np.linspace(N,S0,OH,dtype=np.float32)[:,None].repeat(OW,1)
        long_=np.linspace(W,E,OW,dtype=np.float32)[None,:].repeat(OH,0)
        tj=0.573*(55.7-latg)-0.449*(long_-12.6)
        tj=-tj   # tj now = degrees below the Havn baseline... (sign: north/east = colder)
        sw=np.clip((tj-1.0)/8.0,0,1)*0.62   # dust begins ~-1C, full by ~-9C
        _rngD=np.random.default_rng(3)
        import cv2 as _cv
        _no=_cv.GaussianBlur(_rngD.random((OH,OW)).astype(np.float32),(0,0),3)
        sw=sw*(0.82+0.18*(_no-_no.min())/(np.ptp(_no)+1e-9))
        _wat=(_img[:,:,2].astype(int)>_img[:,:,0].astype(int)+8)
        sw[_wat]=0
        _img=_img.astype(np.float32)
        _img=_img*(1-sw[:,:,None])+np.array([233,236,242],np.float32)*sw[:,:,None]
        _img=np.clip(_img,0,255).astype(np.uint8)
        # ALL cold inland lakes freeze (Kris): compact water components that do not touch the
        # frame edge (the open sea does) and are lake-fat (dt>2px), where Jan-proxy is freezing.
        # Rivers stay blue - the winter roads must stay legible.
        _nw,_labw,_stats,_=_cv.connectedComponentsWithStats(_wat.astype(np.uint8),8)
        _edgeids=set(_labw[0,:])|set(_labw[-1,:])|set(_labw[:,0])|set(_labw[:,-1])
        for _k in range(1,_nw):
            if _k in _edgeids or _stats[_k,4]<24: continue
            _cm=(_labw==_k)
            _dt=_cv.distanceTransform(_cm.astype(np.uint8),_cv.DIST_L2,3)
            if _dt.max()<2.0: continue                      # river-thin: leave blue
            if sw[np.clip(_stats[_k,1],0,OH-1),np.clip(_stats[_k,0],0,OW-1)]==0 and tj[_cm].mean()<2.0: continue
            if tj[_cm].mean()>2.0: _img[_cm]=np.array([226,232,238],np.uint8)
    for _m,_col,_ss in _eph:
        if _sn in _ss:
            _img[_m]=np.array(_col,np.uint8)
    Image.fromarray(_img).save(fn.replace('.jpg','_%s.jpg'%_sn),quality=87)
Image.fromarray(_sea['summer']).save(fn,quality=87)
key=('so762_' if ERA=='762' else 'so_')+slug(C)
centry={'img':'Maps/'+fn,'era':ERA,'vbw':OW,'vbh':OH,'geo':list(geo),'title':C+' — set out','cities':{},'legs':{},'sealegs':{},'open':[C],'seasonal':True}
for n in nodes:
    if n not in LL: continue
    x,y=px(*LL[n])
    cc={'x':int(x),'y':int(y),'r':9,'ldx':14,'ldy':-12}
    if x>OW*0.78: cc['ldx']=-(14+11*len(n))
    if y<40: cc['ldy']=24
    if SEA.get(n,{}).get('camp'): cc['r']=6
    centry['cities'][n]=cc
for n in sorted(NBR.get(C,[])):
    g=geom(C,n)
    p=np.array([[px(lon,la)[0],px(lon,la)[1]] for lon,la in g],float)
    if len(p)>44:
        dd=np.r_[0,np.cumsum(np.hypot(np.diff(p[:,0]),np.diff(p[:,1])))]
        t=np.linspace(0,dd[-1],44)
        p=np.c_[np.interp(t,dd,p[:,0]),np.interp(t,dd,p[:,1])]
    poly=' '.join('%.1f,%.1f'%(x,y) for x,y in p)
    k=legkey(C,n); terr=EDGE_TERR.get(k,'land')
    if terr in ('med','sea'): centry['sealegs'][k]=poly
    else: centry['legs'][k]=poly
drawn=set(centry['legs'])|set(centry['sealegs'])
for n in sorted(NBR.get(C,[])):
    for m in sorted(NBR.get(n,[])):
        if m==C: continue
        k2=legkey(n,m)
        if k2 in drawn: continue
        g2=geom(n,m)
        p2=np.array([[px(lon,la)[0],px(lon,la)[1]] for lon,la in g2],float)
        if len(p2)>36:
            dd2=np.r_[0,np.cumsum(np.hypot(np.diff(p2[:,0]),np.diff(p2[:,1])))]
            t2=np.linspace(0,dd2[-1],36)
            p2=np.c_[np.interp(t2,dd2,p2[:,0]),np.interp(t2,dd2,p2[:,1])]
        poly2=' '.join('%.1f,%.1f'%(x,y) for x,y in p2)
        terr2=EDGE_TERR.get(k2,'land')
        if terr2 in ('med','sea'): centry['sealegs'][k2]=poly2
        else: centry['legs'][k2]=poly2
        drawn.add(k2)
        if m in LL and m not in centry['cities']:
            mx,my=px(*LL[m])
            if -40<=mx<=OW+40 and -40<=my<=OH+40:
                centry['cities'][m]={'x':int(mx),'y':int(my),'r':6,'ldx':12,'ldy':-10,'faint':True}
if not centry['sealegs']: del centry['sealegs']
# era RUINS
RUINS={'1271':{'Bilyar':(50.39,54.98),'Atil (ruin)':(47.60,46.10),'Gnezdovo mounds':(31.87,54.78),'Old Uppsala':(17.63,59.90),'Truso (ruin)':(19.40,54.09)},
       '762':{}}
for _rn,(_rlo,_rla) in RUINS[ERA].items():
    if _rn in centry['cities'] or _rn.split(' (')[0] in centry['cities']: continue
    _rx,_ry=px(_rlo,_rla)
    if 20<=_rx<=OW-20 and 20<=_ry<=OH-20:
        centry['cities'][_rn]={'x':int(_rx),'y':int(_ry),'ruin':True}
try: OUT=json.load(open('setout_charts_amber.json'))
except: OUT={}
OUT[key]=centry
json.dump(OUT,open('setout_charts_amber.json','w'))
print('CHART',key,fn,OW,'x',OH,'geo',geo,'legs',len(centry['legs']),'sealegs',len(centry.get('sealegs',{})))
