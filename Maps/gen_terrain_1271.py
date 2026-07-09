# gen_terrain_1271.py -- 12-slot terrain profiles for every 1271 land leg (Talas).
# Samples routes_master geometry against the GEBCO DEM (multi-tile), classifies underfoot
# terrain (elevation+slope+coast distance+regional climate priors), emits LEG_TERRAIN_1271
# keyed by CANONICAL node names, slot 0 at the alphabetically-first city (matching legTerr).
import numpy as np, tifffile, json, glob, os, math
TILES=[]
for f in glob.glob('/sessions/jolly-charming-gates/mnt/outputs/work/geb3/*.tif')+[x for x in glob.glob('/sessions/jolly-charming-gates/mnt/outputs/work/geb/*.tif') if 'w24.246' not in x]:
    b=os.path.basename(f)  # gebco_2026_n47.5_s33.0_w8.0_e24.5_geotiff.tif
    parts=b.split('_')
    n=float(parts[2][1:]); s=float(parts[3][1:]); w=float(parts[4][1:]); e=float(parts[5][1:])
    TILES.append([f,w,e,s,n,None])
def sample(lon,lat):
    for t in TILES:
        f,w,e,s,n,arr=t
        if w<=lon<=e and s<=lat<=n:
            if arr is None:
                t[5]=tifffile.imread(f).astype(np.float32); arr=t[5]
            h,wd=arr.shape
            c=min(wd-1,max(0,int((lon-w)/(e-w)*wd))); r=min(h-1,max(0,int((n-lat)/(n-s)*h)))
            # elevation + local relief window (~5km)
            win=arr[max(0,r-10):r+11,max(0,c-10):c+11]
            eV=float(arr[r,c]); relief=float(win.max()-win.min())
            return eV,relief
    return 300.0,0.0
def prior(lon,lat):
    if 70.0<lon<73.6 and 40.0<lat<41.6: return 'settled'   # Ferghana
    if 105<lon<=123.5 and 30<lat<41.5: return 'settled'    # north China plain / river valleys
    if lon>110 and lat<=32: return 'settled'               # Yangtze delta & south
    if 93<lon<105 and 36<lat<41.5: return 'desert'         # Gansu corridor
    if lon>95 and lat>41.5: return 'steppe'                # Mongolia / Onggut plain
    if 74<lon<95 and 34<lat<42.5: return 'desert'          # Tarim
    if 77<lon<86 and 42.5<lat<45.5: return 'steppe'        # Ili valley
    if 46<lon<62 and 39.5<lat<46.5: return 'desert'        # Ustyurt/Karakum-Kyzylkum belt
    if 60<lon<74 and 34<lat<43: return 'desert'            # Transoxiana margins
    if 44<lon<63 and lat<38.5: return 'desert'             # Persian interior
    if lat>43: return 'steppe'                             # the great steppe
    if 26<lon<44 and lat>36.5: return 'steppe'             # Anatolian/Armenian plateau
    return 'steppe'
def classify(lon,lat,eV,relief,sead_ok):
    if eV<=0: return ('marsh' if sead_ok else prior(lon,lat))
    slope=relief/5000.0
    if eV>2400 or (eV>1600 and relief>700): return 'mountain'
    if relief>450 or eV>2000: return 'rugged'
    if eV<250 and sead_ok: return 'settled'
    return prior(lon,lat)
def coast_ok(lon,lat):
    # coarse: near Med/Black/Adriatic/China coasts count as watered lowland
    return (lon<45 and lat<47) or (lon>105)
def profile(pts,nslots=12):
    # cumulative distances
    seg=[0.0]
    for i in range(len(pts)-1):
        a,b=pts[i],pts[i+1]
        seg.append(seg[-1]+math.hypot((b[1]-a[1])*111,(b[0]-a[0])*111*math.cos(math.radians(a[1]))))
    total=seg[-1]
    out=[]
    for k in range(nslots):
        # sample 5 points per slot, take the modal class (mountain wins ties)
        cs=[]
        for j in range(5):
            d=(k+ (j+0.5)/5.0)/nslots*total
            i=np.searchsorted(seg,d); i=min(max(i,1),len(pts)-1)
            f=(d-seg[i-1])/max(1e-9,seg[i]-seg[i-1])
            lon=pts[i-1][0]+(pts[i][0]-pts[i-1][0])*f; lat=pts[i-1][1]+(pts[i][1]-pts[i-1][1])*f
            eV,rel=sample(lon,lat)
            cs.append(classify(lon,lat,eV,rel,coast_ok(lon,lat)))
        # modal with mountain priority
        if cs.count('mountain')>=2: out.append('mountain')
        else:
            best=max(set(cs),key=lambda c:cs.count(c))
            out.append(best)
    return out,round(total)
RENAME={'Ganzhou':'Zhangye','Suzhou':'Jiuquan','Kamul':'Hami','Shazhou':'Dunhuang','Kenjanfu':"Chang'an",'Champa':'Kauthara'}
def canon(n): return RENAME.get(n,n)
import re as _re
_lls=_re.search(r'LL=\{.*?\}',open('route_1271.py').read(),_re.S).group(0)
CLL=eval(_lls[3:])
CLL={ (RENAME.get(k,k)):v for k,v in CLL.items() }
CLL.setdefault('Mangyshlak',(51.0,44.3))
rm=json.load(open('routes_master.json'))['legs']
dump=json.load(open('econ_dump_1271.json'))
LL={'Mangyshlak':(51.0,44.3),'Urgench':(59.15,42.30)}
legs=[(e['a'],e['b']) for e in dump['edges'] if e['terr']=='land']+[('Mangyshlak','Urgench')]
OUT={}
missing=[]
for a,b in legs:
    key='|'.join(sorted([a,b]))
    # find geometry under canonical OR renamed keys, either order
    cand=[]
    rev={v:k for k,v in RENAME.items()}
    names_a=[a]+([rev[a]] if a in rev else [])
    names_b=[b]+([rev[b]] if b in rev else [])
    for na in names_a:
        for nb in names_b:
            for kk in (na+'|'+nb, nb+'|'+na):
                if kk in rm: cand.append(kk)
    if cand:
        pts=rm[cand[0]]
        first=sorted([a,b])[0]
        fl=CLL.get(first)
        if fl:
            d0=(pts[0][0]-fl[0])**2+(pts[0][1]-fl[1])**2
            d1=(pts[-1][0]-fl[0])**2+(pts[-1][1]-fl[1])**2
            if d1<d0: pts=pts[::-1]
        else:
            kk=cand[0]; start=canon(kk.split('|')[0])
            if start!=first: pts=pts[::-1]
    else:
        missing.append(key); continue
    prof,km=profile(pts)
    OUT[key]=prof
HAND={   # 762 LEG_TERRAIN canon (Kris-tuned) reused where the 1271 road is the same corridor
 'Aksu|Kashgar':["desert","desert","rugged","desert","desert","desert","desert","desert","desert","desert","desert","desert"],
 'Aksu|Kucha':["desert"]*12,
 'Kucha|Turfan':["desert","desert","desert","desert","desert","rugged","desert","desert","desert","desert","desert","desert"],
 'Hami|Turfan':["desert"]*12,
 'Dunhuang|Hami':["desert"]*12,
 'Kashgar|Yarkand':["desert"]*12,
 'Khotan|Yarkand':["desert"]*12,
 'Bukhara|Samarkand':["steppe"]*12,
}
OUT.update(HAND)
json.dump(OUT,open('terrain1271_baked.json','w'),indent=0)
print('baked',len(OUT),'profiles; missing geometry:',missing)
for k in sorted(OUT): print('%-28s %s'%(k,','.join(c[:4] for c in OUT[k])))
