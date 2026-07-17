# gen_setout_1271.py -- per-city SET-OUT charts for 1271 (Zaiton; Kris's ask).
# For every 1271 town: a rect of the master (or GEBCO bake south of 24N) covering the city, all its
# edge-destinations AND desert-crossing options, plus their route geometries; fields quilt; legs
# reprojected from the canonical geometry registry; JPEG bases; CHARTS entries emitted as JSON.
import numpy as np, json, math, re, glob, io, os
from PIL import Image
import tifffile, cv2
from slice_master import slice_master
from rebake_1271_fields import add_fields, fields_multi, anachronize, SEASONS, SETTLE, dem_at

DUMP=json.load(open('setout_net_dump.json'))
RM=json.load(open('routes_master.json'))['legs']
MONSOON=json.load(open('monsoon_lanes_lonlat.json'))
RENAME={'Ganzhou':'Zhangye','Suzhou':'Jiuquan','Kamul':'Hami','Shazhou':'Dunhuang','Kenjanfu':"Chang'an",'Champa':'Kauthara'}
def canon(n): return RENAME.get(n,n)

# ---------- city lonlats ----------
LL=eval(re.search(r'LL=\{.*?\}',open('route_1271.py').read(),re.S).group(0)[3:])
LL={canon(k):v for k,v in LL.items()}
LL.update({'Varamin':(51.65,35.32),'Mangyshlak':(51.0,44.3),'Ispijab':(69.75,42.30),'Talas':(71.40,42.90),'Chach':(69.28,41.31),'Lop':(88.30,39.50),'Miran':(88.90,39.23),'Aksu':(80.26,41.17),'Kucha':(82.96,41.72),'Alexandria':(29.90,31.20),'Kauthara':(109.20,12.25),'Kollam':(76.60,8.90),'Andijan':(72.34,40.78),'Abaskun':(54.00,36.90),'Damghan':(54.34,36.17),'Kabul':(69.18,34.53),'Kashmir':(74.80,34.08),'Baku':(49.87,40.37),'Saraichik':(51.75,47.50),'the Perevoloka':(44.55,48.70),'the Don landing':(43.80,48.72)})

# ---------- geometry registry (lonlat) ----------
GEO={}
for k,pts in RM.items():
    if k.startswith('_'): continue
    a,b=k.split('|'); key='|'.join(sorted([canon(a),canon(b)]))
    GEO.setdefault(key,pts)
def px2ll(pts_str,geo,W,H):
    w,e,s0,n=geo
    out=[]
    for p in pts_str.split():
        x,y=map(float,p.split(','))
        out.append([w+x/W*(e-w), n-y/H*(n-s0)])
    return out
# sea lanes: back-project the traced voymaps/sealegs
IMG_GEO={'Maps/medlevant1271.png':((23,37.5,30.5,42),1600,1574),
         'Maps/caspian1271.png':((46,61,34,48.5),1400,1793),
         'Maps/adriatic1271.png':((11,29.5,34,46.5),1980,1338),
         'Maps/southchinasea1271.png':((104,123,8,28),1400,1549),
         'Maps/pontic1271.png':((27,56,39,52),1980,888)}
for k,v in DUMP['voymaps'].items():
    if v['img'] in IMG_GEO:
        g,W,H=IMG_GEO[v['img']]
        key='|'.join(sorted([canon(x) for x in k.split('|')]))
        GEO.setdefault(key,px2ll(v['pts'],g,W,H))
for k,pts in DUMP['sealegs'].items():
    ck,pair=k.split('::')
    img='Maps/'+ck+'.png'
    if img in IMG_GEO:
        g,W,H=IMG_GEO[img]
        key='|'.join(sorted([canon(x) for x in pair.split('|')]))
        GEO.setdefault(key,px2ll(pts,g,W,H))
for k,pts in MONSOON.items():
    key='|'.join(sorted([canon(x) for x in k.split('|')]))
    GEO.setdefault(key,pts)

# ---------- per-city node sets ----------
NBR={}
for e in DUMP['edges']:
    NBR.setdefault(e['a'],set()).add(e['b']); NBR.setdefault(e['b'],set()).add(e['a'])
SC=DUMP['shortcuts']
for c,ds in SC.items():
    NBR.setdefault(c,set()).update(ds)
EDGE_TERR={}
for e in DUMP['edges']:
    EDGE_TERR['|'.join(sorted([e['a'],e['b']]))]=e['terr']

MW,ME,MS,MN=8.0,123.0,24.0,52.0
def legkey(a,b): return '|'.join(sorted([a,b]))
def geom(a,b):
    g=GEO.get(legkey(a,b))
    if g: return g
    return [list(LL[a]),list(LL[b])]

# ---------- GEBCO renderer for rects dipping south of the master ----------
TILES=[]
for f in (glob.glob('/sessions/jolly-charming-gates/mnt/outputs/work/geb3/*.tif')
         +glob.glob('/sessions/jolly-charming-gates/mnt/outputs/work/geb4/*.tif')
         +glob.glob('/sessions/jolly-charming-gates/mnt/outputs/work/geb5/*.tif')
         +glob.glob('/sessions/jolly-charming-gates/mnt/outputs/work/geb6/*.tif')+[x for x in glob.glob('/sessions/jolly-charming-gates/mnt/outputs/work/geb/*.tif') if 'w24.246' not in x and 'w28.475' not in x]):
    b=os.path.basename(f).split('_')
    TILES.append([f,float(b[4][1:]),float(b[5][1:]),float(b[3][1:]),float(b[2][1:]),None])
def gebco_grid(W,E,S0,N,GX,GY):
    d=np.full((GY,GX),np.nan,np.float32)
    for t in TILES:
        f,tw,te,ts,tn,_=t
        ow,oe=max(W,tw),min(E,te); os_,on=max(S0,ts),min(N,tn)
        if ow>=oe or os_>=on: continue
        a=tifffile.imread(f).astype(np.float32); h,w2=a.shape
        rx=(te-tw)/w2; ry=(tn-ts)/h
        c0=int((ow-tw)/rx); c1=int((oe-tw)/rx); r0=int((tn-on)/ry); r1=int((tn-os_)/ry)
        gx0=int((ow-W)/(E-W)*GX); gx1=int((oe-W)/(E-W)*GX); gy0=int((N-on)/(N-S0)*GY); gy1=int((N-os_)/(N-S0)*GY)
        if gx1<=gx0 or gy1<=gy0: continue
        sub=cv2.resize(a[r0:r1,c0:c1],(gx1-gx0,gy1-gy0),interpolation=cv2.INTER_AREA)
        tgt=d[gy0:gy1,gx0:gx1]
        m=np.isnan(tgt); tgt[m]=sub[m]
    return np.nan_to_num(d,nan=300.0)
def interp_ramp(v,tab):
    out=np.zeros(v.shape+(3,),np.float32)
    for i in range(len(tab)-1):
        k0,c0_=tab[i]; k1,c1_=tab[i+1]
        m=(v>=k0)&(v<k1)
        f=((v-k0)/(k1-k0))[m][...,None]
        out[m]=np.array(c0_)+(np.array(c1_)-np.array(c0_))*f
    out[v>=tab[-1][0]]=np.array(tab[-1][1])
    return out
def gebco_relief(W,E,S0,N,OW,OH):
    d=gebco_grid(W,E,S0,N,OW,OH)
    img=np.zeros((OH,OW,3),np.float32)
    sea=d<=0
    sd=np.clip(-d/2500.0,0,1)
    img[sea]=(np.array([88,133,170])+ (np.array([66,110,150])-np.array([88,133,170]))*sd[...,None])[sea]
    # per-pixel arid<->tropical blend (Kris: Arabia on the Hormuz chart must be sand, not
    # monsoon green - a chart-wide latitude switch painted the whole frame tropical).
    # Tropical weight needs BOTH low latitude AND longitude east of ~62E (the monsoon lands:
    # India's west coast, Bengal, SE Asia). Arabia/Persia/Makran stay arid.
    TROP=[(0,(150,158,110)),(120,(136,150,96)),(400,(110,124,80)),(900,(93,96,71)),(1800,(140,132,100)),(2800,(182,171,131)),(4500,(210,205,185))]
    ARID=[(0,(168,158,112)),(150,(160,152,104)),(500,(140,140,92)),(1200,(120,118,84)),(2200,(150,140,108)),(3200,(185,174,134)),(5000,(212,207,187))]
    land=~sea
    lonpx=np.linspace(W,E,OW,dtype=np.float32)[None,:].repeat(OH,0)
    latpx=np.linspace(N,S0,OH,dtype=np.float32)[:,None].repeat(OW,1)
    wt=np.clip((lonpx-62.0)/6.0,0,1)*np.clip((28.0-latpx)/6.0,0,1)
    blend=interp_ramp(d,ARID)*(1-wt[...,None])+interp_ramp(d,TROP)*wt[...,None]
    img[land]=blend[land]
    gy,gx=np.gradient(d,(N-S0)/OH*111000,(E-W)/OW*111000*math.cos(math.radians((S0+N)/2)))
    az=math.radians(315); alt=math.radians(45)
    slope=np.arctan(np.hypot(gx,gy)*2.2); aspect=np.arctan2(-gx,gy)
    hs=np.clip(np.sin(alt)*np.cos(slope)+np.cos(alt)*np.sin(slope)*np.cos(az-aspect),0.25,1.0)
    img[land]*=(0.55+0.55*hs[land])[...,None]
    rng=np.random.default_rng(11)
    img[land]*=(1+0.03*rng.standard_normal(img.shape)[land])
    return np.clip(img,0,255).astype(np.uint8)

# ---------- generate ----------
import sys
try: CHARTS_OUT=json.load(open('setout_charts_1271.json'))
except: CHARTS_OUT={}
def slug(n): return re.sub(r"[^a-z]","",n.lower())
cities=sorted(NBR.keys())
BATCH=int(sys.argv[1]) if len(sys.argv)>1 else 6
made=[]
for C in cities:
    if ('so_'+slug(C)) in CHARTS_OUT: continue
    if len(made)>=BATCH: break
    nodes=[C]+sorted(NBR[C])
    lons=[]; lats=[]
    for n in nodes:
        if n not in LL: continue
        lons.append(LL[n][0]); lats.append(LL[n][1])
    for n in NBR[C]:
        for pt in geom(C,n):
            lons.append(pt[0]); lats.append(pt[1])
    W,E=min(lons),max(lons); S0,N=min(lats),max(lats)
    padx=max(0.6,(E-W)*0.10); pady=max(0.5,(N-S0)*0.10)
    W-=padx; E+=padx; S0-=pady; N+=pady
    if E-W<4: c0=(E+W)/2; W,E=c0-2,c0+2
    if N-S0<3: c0=(N+S0)/2; S0,N=c0-1.5,c0+1.5
    OW=1400
    _latm=math.cos(math.radians((S0+N)/2))
    OH=int(OW*(N-S0)/((E-W)*_latm))
    # ASPECT IS SACRED (Kris caught so_almaliq squashed 2.1x): never clamp pixels - EXPAND THE RECT.
    if OH<500:
        _span=500.0*(E-W)*_latm/OW
        _ext=(_span-(N-S0))/2
        S0-=_ext; N+=_ext
    elif OH>2100:
        _spanl=OW*(N-S0)/(2100.0*_latm)
        _extl=(_spanl-(E-W))/2
        W-=_extl; E+=_extl
        if W<MW: E+=(MW-W); W=MW
        if E>ME: W-=(E-ME); E=ME
    _latm=math.cos(math.radians((S0+N)/2))
    OH=int(OW*(N-S0)/((E-W)*_latm))
    OH=max(60,min(2400,OH))
    fn='so1271_%s.jpg'%slug(C)
    if S0>=MS and W>=MW and E<=ME and N<=MN:
        slice_master(max(W,MW),min(E,ME),max(S0,MS),min(N,MN),OW,OH,'_tmp_so.png')
        img=np.array(Image.open('_tmp_so.png').convert('RGB'))
    else:
        img=gebco_relief(W,E,S0,N,OW,OH)
    from rebake_1271_fields import relief_boost
    img=relief_boost(img,(W,E,S0,N),OW,OH)
    img,_eph,_forbid=anachronize(img,(W,E,S0,N))
    geo=(round(W,2),round(E,2),round(S0,2),round(N,2))
    def px(lon,lat): return (round((lon-geo[0])/(geo[1]-geo[0])*OW,1),round((geo[3]-lat)/(geo[3]-geo[2])*OH,1))
    # roads for field-hugging: every leg touching any town in frame (px space)
    _roadpx=[]
    _towns=set([C])|set(NBR[C])
    for _a in list(_towns):
        for _b in NBR.get(_a,[]):
            _g=geom(_a,_b)
            if _g: _roadpx.append([px(_lo,_la) for _lo,_la in _g[::3]])
    _sea=fields_multi(img,(W,E,S0,N),SETTLE,seasons=SEASONS,roads=_roadpx,forbid=_forbid)
    for _sn,_img in _sea.items():
        for _m,_col,_ss in _eph:
            if _sn in _ss:
                _img=_img.copy(); _img[_m]=np.array(_col,np.uint8)
        Image.fromarray(_img).save('so1271_%s_%s.jpg'%(slug(C),_sn),quality=87)
    Image.fromarray(_sea['summer']).save(fn,quality=87)
    centry={'img':'Maps/'+fn,'era':'1271','vbw':OW,'vbh':OH,'geo':list(geo),'title':C+' — set out','cities':{},'legs':{},'sealegs':{},'open':[C],'seasonal':True}
    for n in nodes:
        if n not in LL: continue
        x,y=px(*LL[n])
        cc={'x':int(x),'y':int(y),'r':9,'ldx':14,'ldy':-12}
        if x>OW*0.78: cc['ldx']=-(14+11*len(n))
        if y<40: cc['ldy']=24
        centry['cities'][n]=cc
    for n in sorted(NBR[C]):
        g=geom(C,n)
        p=np.array([[px(lon,la)[0],px(lon,la)[1]] for lon,la in g],float)
        if len(p)>44:
            dd=np.r_[0,np.cumsum(np.hypot(np.diff(p[:,0]),np.diff(p[:,1])))]
            t=np.linspace(0,dd[-1],44)
            p=np.c_[np.interp(t,dd,p[:,0]),np.interp(t,dd,p[:,1])]
        poly=' '.join('%.1f,%.1f'%(x,y) for x,y in p)
        k=legkey(C,n)
        terr=EDGE_TERR.get(k,'land')
        if terr in ('med','sea'): centry['sealegs'][k]=poly
        else: centry['legs'][k]=poly
    # ONWARD ROADS (Kris): draw each destination's onward legs dark so the network never looks like
    # a dead end; faint dots for the onward towns that land inside the rect; SVG clips the rest.
    drawn=set(centry['legs'].keys())|set(centry.get('sealegs',{}).keys())
    for n in sorted(NBR[C]):
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
            if terr2 in ('med','sea'): centry.setdefault('sealegs',{})[k2]=poly2
            else: centry['legs'][k2]=poly2
            drawn.add(k2)
            if m in LL and m not in centry['cities']:
                mx,my=px(*LL[m])
                if -40<=mx<=OW+40 and -40<=my<=OH+40:
                    centry['cities'][m]={'x':int(mx),'y':int(my),'r':6,'ldx':12,'ldy':-10,'faint':True}
    if not centry['sealegs']: del centry['sealegs']
    # RUIN SITES (Kris): dead cities marked with the three-dots-in-a-triangle, not a live dot
    RUINS_1271={'Merv':(61.83,37.66)}
    for _rn,(_rlo,_rla) in RUINS_1271.items():
        if _rn in centry['cities']: continue
        _rx,_ry=px(_rlo,_rla)
        if 20<=_rx<=OW-20 and 20<=_ry<=OH-20:
            centry['cities'][_rn]={'x':int(_rx),'y':int(_ry),'ruin':True}
    # WIDER-WORLD STUBS (Kris + Fadak): permanently grey stumps aimed at off-chart destinations,
    # full routed geometry so the exit bearing is true; hover hint handled game-side by key.
    STUBW={'Balkh':[('Balkh|Kabul','india_kabul')],'Yarkand':[('Kashmir|Yarkand','india_kashmir')]}
    for srcC,stl in STUBW.items():
        if srcC not in centry['cities']: continue
        for gkey,hint in stl:
            gg=GEO.get(gkey) or RM.get(gkey)
            if not gg: continue
            gp=list(gg)
            if abs(gp[0][0]-LL[srcC][0])+abs(gp[0][1]-LL[srcC][1])>abs(gp[-1][0]-LL[srcC][0])+abs(gp[-1][1]-LL[srcC][1]): gp=gp[::-1]
            p3=np.array([[px(lon,la)[0],px(lon,la)[1]] for lon,la in gp],float)
            dd3=np.r_[0,np.cumsum(np.hypot(np.diff(p3[:,0]),np.diff(p3[:,1])))]
            t3=np.linspace(0,dd3[-1],60)
            p3=np.c_[np.interp(t3,dd3,p3[:,0]),np.interp(t3,dd3,p3[:,1])]
            # STUMP, not road-to-nowhere: stop where it leaves the frame, or at 45% of the way
            # if the (unmarked) destination happens to fall inside this chart's rect.
            cut=len(p3)
            for i3 in range(1,len(p3)):
                if not(-8<=p3[i3][0]<=OW+8 and -8<=p3[i3][1]<=OH+8): cut=min(i3+2,len(p3)); break
            cut=min(cut,max(6,int(len(p3)*0.45)))
            p3=p3[:cut]
            centry.setdefault('stubs',[]).append({'pts':' '.join('%.1f,%.1f'%(x,y) for x,y in p3),'hint':hint})
    CHARTS_OUT['so_'+slug(C)]=centry
    made.append(fn)
json.dump(CHARTS_OUT,open('setout_charts_1271.json','w'))
print('generated',len(made),'this batch; total',len(CHARTS_OUT),'of',len(cities))
