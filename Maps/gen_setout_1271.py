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
LL.update({'Luoyang':(112.45,34.62),'Aylah':(35.0,29.53),'Medina':(39.61,24.47),'Mecca':(39.83,21.42),'Sanaa':(44.21,15.35),'Fustat':(31.25,30.05),'Qus':(32.76,25.92),'Aydhab':(36.49,22.33),'Jeddah':(39.17,21.5),'Aden':(45.03,12.80),'Dhofar':(54.10,17.02),'Shibam':(48.63,15.93),'Puttalam':(79.83,8.03),'Kedah':(100.37,6.12),'Tumasik':(103.85,1.29),'Guangzhou':(113.26,23.13),'Basra':(47.81,30.40),'Kish':(53.98,26.53),'Varamin':(51.65,35.32),'Mangyshlak':(51.0,44.3),'Ispijab':(69.75,42.30),'Talas':(71.40,42.90),'Chach':(69.28,41.31),'Lop':(88.30,39.50),'Miran':(88.90,39.23),'Aksu':(80.26,41.17),'Kucha':(82.96,41.72),'Alexandria':(29.90,31.20),'Socotra':(53.9,12.5),'Shiraz':(52.54,29.61),'Delhi':(77.2,28.61),'Lahore':(74.35,31.55),'Cambay':(72.62,22.31),'Chittagong':(91.8,22.33),'Butuan':(125.53,8.95),'Hakata':(130.4,33.6),'Kaesong':(126.55,37.97),'Kauthara':(109.20,12.25),'Kollam':(76.60,8.90),'Andijan':(72.34,40.78),'Abaskun':(54.00,36.90),'Damghan':(54.34,36.17),'Kabul':(69.18,34.53),'Kashmir':(74.80,34.08),'Baku':(49.87,40.37),'Saraichik':(51.75,47.50),'the Perevoloka':(44.55,48.70),'the Don landing':(43.80,48.72),'Asyut':(31.19,27.18),'Kharga':(30.55,25.44)})

# ---------- geometry registry (lonlat) ----------
GEO={}
# SORTED KEYS WIN (Fadak 8/03): the master holds a few legacy UNSORTED keys ('Baghdad|Aleppo',
# 'Iconium|Aleppo') which are 762-era legs. They canon-collide with the curated 1271 sorted keys,
# and plain dict-order setdefault let the 762 chord shadow the 1271 right-bank road -> Kris's
# 'doubled Baghdad-Aleppo route' on the Gulf exhibit. Two passes: sorted (1271) first, legacy second.
for _pass in (0,1):
    for k,pts in RM.items():
        if k.startswith('_'): continue
        if (k=='|'.join(sorted(k.split('|'))))!=(_pass==0): continue
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
for f in (glob.glob('gebco_local/*.tif')  # w24.246 exclusion REMOVED (Fadak 8/03): it banned the whole western master tile - Oxus's guard against the then-truncated copy, since healed (full 178MB in dem_west)+glob.glob('/sessions/jolly-charming-gates/mnt/outputs/work/geb3/*.tif')
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
# --- THE MARRIAGE KNOBS (Kris 8/04: 'marry the mountain prominence + forest of the master slice
# with the aridity-informed sand of the GEBCO path'). One pipeline, four dials:
RELIEF_PROMINENCE=1.45   # 1.0 = old GEBCO look. Raises slope response and deepens the shadow floor.
FOREST_SHARP=3.0         # forest EDGE sharpness: forest layer blurs climate at _k/FOREST_SHARP
                         # (wetness/dune keep the full smooth _k - only the forest edge crispens)
FOREST_GREENS=((52,106,60),(70,120,56),(54,94,70))  # jungle / broadleaf / conifer - true forest-green
FOREST_ALPHA=0.85        # forest overlay opacity (was 0.75 - reads washy over pale ground)
def gebco_relief(W,E,S0,N,OW,OH,lakeclip=False):
    d=gebco_grid(W,E,S0,N,OW,OH)
    img=np.zeros((OH,OW,3),np.float32)
    sea=d<=0
    if lakeclip:
        _m=sea.astype(np.uint8); _nc,_lab=cv2.connectedComponents(_m,8)
        _bord=set(np.unique(_lab[0])).union(set(np.unique(_lab[-1])),set(np.unique(_lab[:,0])),set(np.unique(_lab[:,-1]))); _bord.discard(0)
        _ocean=np.isin(_lab,list(_bord)); _iso=sea&(~_ocean)
        _k5=np.ones((5,5),np.uint8); _rr2=cv2.dilate(d,_k5)-cv2.erode(d,_k5)
        _flat=(_iso&(_rr2<12)).astype(np.uint8); _fn,_flab=cv2.connectedComponents(_flat,8)
        _keep=np.zeros(_flat.shape,bool)
        for _ci in range(1,_fn):
            _cm=(_flab==_ci)
            if _cm.sum()>=140: _keep|=_cm   # only LARGE flat lakes (Sea of Galilee) - drop speckle patches
        sea=_ocean|_keep|(_iso&(d<-380))  # ocean + real standing lakes + Dead Sea deep core; sloping Ghor stays land
        d=np.where(sea,d,np.maximum(d,0.0))
    sd=np.clip(-d/2500.0,0,1)
    img[sea]=(np.array([132,175,208])+ (np.array([96,141,184])-np.array([132,175,208]))*sd[...,None])[sea]
    # per-pixel arid<->tropical blend (Kris: Arabia on the Hormuz chart must be sand, not
    # monsoon green - a chart-wide latitude switch painted the whole frame tropical).
    # Tropical weight needs BOTH low latitude AND longitude east of ~62E (the monsoon lands:
    # India's west coast, Bengal, SE Asia). Arabia/Persia/Makran stay arid.
    TROP=[(0,(172,204,144)),(120,(163,196,136)),(400,(150,183,124)),(900,(168,178,128)),(1800,(196,182,146)),(2800,(216,204,176)),(4500,(240,238,232))]
    ARID=[(0,(238,224,196)),(150,(237,222,192)),(500,(234,219,188)),(1200,(230,214,182)),(2200,(230,216,188)),(3200,(238,228,202)),(5000,(248,246,240))]  # near-flat with height: aridity is a colour, not an altitude (Kris)
    land=~sea
    # WETNESS-INFORMED LANDCOVER (Kris's WorldClim drop, 8/03): per-pixel annual precipitation
    # (wc2.1 10-arcmin bio12) drives the arid<->green blend; the old lon/lat monsoon box is the
    # fallback when the climate raster is absent. Cairo 24mm -> sand, Acre 576 -> mediterranean
    # green, Zanzibar 1665 -> lush; the Taklamakan (33) stays properly dead.
    wt=None
    try:
        global _BIO12
        try: _BIO12
        except NameError:
            _b=tifffile.imread('climate information/wc2.1_10m_bio_12.tif').astype(np.float32)
            _b=np.where(_b<-1000,np.nan,_b)
            for _ in range(4):
                _m=np.isnan(_b)
                if not _m.any(): break
                _f=np.nanmean(np.stack([np.roll(_b,1,0),np.roll(_b,-1,0),np.roll(_b,1,1),np.roll(_b,-1,1)]),axis=0)
                _b[_m]=_f[_m]
            _b=np.nan_to_num(_b,nan=250.0)
            _BIO12=_b
        _res=1.0/6.0
        lonpx=np.linspace(W,E,OW,dtype=np.float32)
        latpx=np.linspace(N,S0,OH,dtype=np.float32)
        # BILINEAR climate sampling (Kris 8/04: 'forests in grid squares - never'): nearest-neighbor
        # np.ix_ indexing leaked the 10-arcmin cells once FOREST_SHARP thinned the blur that had been
        # hiding them. cv2.remap interpolates the climate FIELD to pixel space - biome edges stay
        # climatic (Kris's hierarchy: climate first, polygons only as fallback) but curve naturally.
        _gx,_gy=np.meshgrid(((lonpx+180.0)/_res-0.5).astype(np.float32),((90.0-latpx)/_res-0.5).astype(np.float32))
        P=cv2.remap(_BIO12,_gx,_gy,cv2.INTER_LINEAR,borderMode=cv2.BORDER_REPLICATE)
        _ppd=OW/max(1e-6,(E-W)); _k=int(max(3,round(_ppd*(1.0/6.0)))); _k+=(_k%2==0)
        _PRAW=P.copy()
        P=cv2.GaussianBlur(P,( _k,_k),0)  # smooth the 10-arcmin climate cells to the raster grid
        wt=np.clip((P-95.0)/480.0,0,1).astype(np.float32)  # Oxus 8/04 (Kris): greens moderate-rainfall highlands (Yemen ~300-500mm) - the Sanaa terraces are not sand; true desert (P<95) still reads dead
    except Exception as _e:
        print('  (bio12 unavailable, falling back to lon/lat monsoon box:',_e,')')
    if wt is None:
        lonpx=np.linspace(W,E,OW,dtype=np.float32)[None,:].repeat(OH,0)
        latpx=np.linspace(N,S0,OH,dtype=np.float32)[:,None].repeat(OW,1)
        wt=np.clip((lonpx-62.0)/6.0,0,1)*np.clip((28.0-latpx)/6.0,0,1)
    blend=interp_ramp(d,ARID)*(1-wt[...,None])+interp_ramp(d,TROP)*wt[...,None]
    try:
        dune=np.clip((95.0-P)/95.0,0,1).astype(np.float32)*0.70  # reach further into the near-desert: SW Arabia reads pale, not muddy  # the true sand seas (Rub' al-Khali, Taklamakan): pale dune colour, not khaki (Kris)
        blend=blend*(1-dune[...,None])+np.array([246,236,205],np.float32)*dune[...,None]
    except NameError: pass
    # FOREST CLASSING (Kris): coniferous / broadleaf / tropical jungle, Whittaker-style off
    # precip (P) + mean annual temp (bio1). Overlaid on the hypsometric base; treeline ~3200m.
    try:
        global _BIO1
        try: _BIO1
        except NameError:
            _t=tifffile.imread('climate information/wc2.1_10m_bio_1.tif').astype(np.float32)
            _t=np.where(_t<-1000,np.nan,_t)
            for _ in range(4):
                _m=np.isnan(_t)
                if not _m.any(): break
                _f=np.nanmean(np.stack([np.roll(_t,1,0),np.roll(_t,-1,0),np.roll(_t,1,1),np.roll(_t,-1,1)]),axis=0)
                _t[_m]=_f[_m]
            _BIO1=np.nan_to_num(_t,nan=10.0)
        _kf=int(max(3,round(_k/FOREST_SHARP))); _kf+=(_kf%2==0)
        try: Pf=cv2.GaussianBlur(_PRAW,(_kf,_kf),0)   # sharper climate field for the forest EDGE only
        except NameError: Pf=P
        T=cv2.remap(_BIO1,_gx,_gy,cv2.INTER_LINEAR,borderMode=cv2.BORDER_REPLICATE)
        T=cv2.GaussianBlur(T,(_kf,_kf),0)
        ffor=np.clip((Pf-550.0)/400.0,0,1)*np.clip((3300.0-d)/700.0,0,1)
        JUNGLE=np.array(FOREST_GREENS[0],np.float32); BROAD=np.array(FOREST_GREENS[1],np.float32); CONIF=np.array(FOREST_GREENS[2],np.float32)
        fc=np.where((T>=20)[...,None], JUNGLE, np.where((T>=6)[...,None], BROAD, CONIF))
        # jungle needs real monsoon rain; conifers tolerate less
        ffor=ffor*np.where(T>=20, np.clip((Pf-1000.0)/500.0,0,1), np.where(T>=6, 1.0, np.clip((Pf-380.0)/300.0,0,1)+0.15))
        ffor=np.clip(ffor,0,1)*FOREST_ALPHA
        blend=blend*(1-ffor[...,None])+fc*ffor[...,None]
    except Exception as _fe:
        print('  (forest classing skipped:',_fe,')')
    img[land]=blend[land]
    # RIVERS (Kris: GEBCO has no rivers - the master had them drawn): Natural Earth centerlines,
    # scalerank-filtered, painted river-blue with an IRRIGATION-GREEN valley band where rain alone
    # is scarce (Mesopotamia, the Indus, the Nile country - the green is the river's, not the sky's)
    try:
        global _NERIV
        try: _NERIV
        except NameError:
            import json as _json
            _g=_json.load(open('ne_10m_rivers_lake_centerlines.geojson'))
            _NERIV=[]
            for _f in _g['features']:
                _sr=_f['properties'].get('scalerank',9)
                if _sr is None or _sr>4: continue  # Tigris is rank 4; the Bushehr phantom was rank 5+  # MAJORS only (Kris: minor rivers were seeding phantom farmland at Bushehr)
                _geo=_f['geometry']
                _ls=_geo['coordinates'] if _geo['type']=='MultiLineString' else [_geo['coordinates']]
                for _l in _ls: _NERIV.append((_sr,[(pt[0],pt[1]) for pt in _l]))
        rmask=np.zeros((OH,OW),np.uint8)
        for _sr,_line in _NERIV:
            pts=[]
            for lo,la in _line:
                if W-0.5<=lo<=E+0.5 and S0-0.5<=la<=N+0.5:
                    pts.append((int((lo-W)/(E-W)*OW),int((N-la)/(N-S0)*OH)))
                else:
                    if len(pts)>1: cv2.polylines(rmask,[np.array(pts,np.int32)],False,1,1)
                    pts=[]
            if len(pts)>1: cv2.polylines(rmask,[np.array(pts,np.int32)],False,1,1)
        if rmask.any():
            _ppdeg=OW/max(1e-6,(E-W))
            vk=max(3,int(_ppdeg*0.10))|1  # a slim ribbon of green at the banks (Kris pared the belt back)
            valley=cv2.dilate(rmask,np.ones((vk,vk),np.uint8)).astype(np.float32)
            valley=cv2.GaussianBlur(valley,(vk|1,vk|1),0)
            irr=np.clip((450.0-P)/250.0,0,1)*np.clip(valley,0,1)*np.where(d>0,1.0,0.0)*np.clip((900.0-d)/700.0,0,1)
            GREENV=np.array([150,178,118],np.float32)
            blend=blend*(1-(irr*0.55)[...,None])+GREENV*(irr*0.55)[...,None]
            # NILE FLOODPLAIN FARMLAND (Kris 8/05): the Nile valley is cultivated, but NOT uniformly. The
            # floodplain is widest at the Delta and TAPERS almost linearly upstream to no more than the
            # river's own width by Aswan (1st cataract); south of Aswan (Nubia) only the banks are green,
            # save local patches at the towns (Faras, Old Dongola). NILE ONLY - other desert rivers are
            # not this fertile - so gate to the Egyptian/Nubian Nile corridor.
            try:
                if W<33.5 and E>29.5 and S0<30.0:   # Egypt-proper (excludes wide Med charts that only clip the delta coast)
                    _dr=cv2.distanceTransform((1-rmask).astype(np.uint8),cv2.DIST_L2,3)
                    _kf2=np.ones((5,5),np.uint8); _rel=cv2.dilate(d,_kf2)-cv2.erode(d,_kf2)
                    _lat=np.linspace(N,S0,OH,dtype=np.float32)[:,None]                 # per-row latitude
                    _taper=np.clip((_lat-24.0)/(30.0-24.0),0.0,1.0)                     # 0 at Aswan (24N) -> 1 at the Delta (30N)
                    _wdeg=0.012+_taper*(0.130-0.012)                                    # river-width at Aswan, full at the Delta
                    _wdeg=_wdeg+0.050*np.exp(-((_lat-22.20)/0.35)**2)                   # Faras patch
                    _wdeg=_wdeg+0.065*np.exp(-((_lat-18.22)/0.40)**2)                   # Old Dongola patch
                    _wpx=_wdeg*_ppdeg                                                   # (OH,1), broadcast over columns
                    _flood=((_dr<_wpx)&(_rel<55)&(d>0)&(P<170)).astype(np.float32)
                    _flood=cv2.GaussianBlur(_flood,(0,0),max(1.0,_ppdeg*0.015))
                    FARM=np.array([120,150,82],np.float32)
                    blend=blend*(1-(_flood*0.82)[...,None])+FARM*(_flood*0.82)[...,None]
            except Exception as _fe2:
                print('  (nile floodplain skipped:',_fe2,')')
            # THE GREAT MARSHES of lower Mesopotamia (al-Bata'ih): famous then, drained now - hand region
            if W<49.5 and E>45.5 and S0<32.2 and N>30.0:
                # tint EVERY canonical marsh polygon (MARSH_POLYS_1271, defined below gebco_relief -
                # resolved at call time) so tint and tussock strokes can never drift apart again
                _mm=np.zeros((OH,OW),np.uint8)
                for _poly in MARSH_POLYS_1271:
                    _mpx=np.array([[ int((lo-W)/(E-W)*OW), int((N-la)/(N-S0)*OH)] for (lo,la) in _poly],np.int32)
                    cv2.fillPoly(_mm,[_mpx],1)
                _mk=max(5,int(_ppdeg*0.25))|1
                _mmf=cv2.GaussianBlur(_mm.astype(np.float32),(_mk,_mk),0)*np.where(d>0,1.0,0.0)*np.clip((45.0-d)/45.0,0,1)
                MARSH=np.array([124,150,104],np.float32)
                blend=blend*(1-(_mmf*0.6)[...,None])+MARSH*(_mmf*0.6)[...,None]
            # NILE DELTA (Kris 8/05): the hand polygon 'missed the delta'. Flood-fill the land that the two
            # Nile distributaries + the Mediterranean coast enclose - real rivers/coast as the boundary.
            try:
                if W<32.4 and E>30.0 and N>30.2:  # any Egyptian chart showing the fork/delta
                    _rivbar=cv2.dilate(rmask,np.ones((max(3,int(_ppdeg*0.03))|1,)*2,np.uint8))
                    _free=(((d>0)&(_rivbar==0)).astype(np.uint8))
                    _nl,_lab=cv2.connectedComponents(_free,8)
                    _hull=np.zeros((OH,OW),np.uint8)
                    _hpx=np.array([[int((lo-W)/(E-W)*OW),int((N-la)/(N-S0)*OH)] for (lo,la) in DELTA_POLY],np.int32)
                    cv2.fillPoly(_hull,[_hpx],1)
                    # SEEDLESS (Kris): the delta = river/sea-ENCLOSED land inside the hull. Desert is the OPEN
                    # region reaching the L/R/bottom frame edge; enclosed land (the delta wedge, even where the
                    # frame clips it at the top) never does - so green every enclosed component within the hull.
                    _bord=set(np.unique(_lab[:,0]))|set(np.unique(_lab[:,-1]))|set(np.unique(_lab[-1,:]))
                    _delta=(~np.isin(_lab,list(_bord)))&(_lab>0)&(_hull>0)
                    if _delta.any():
                        _dmf=cv2.GaussianBlur(_delta.astype(np.float32),(7,7),0)
                        DELTAG=np.array([104,158,82],np.float32)
                        blend=blend*(1-(_dmf*0.9)[...,None])+DELTAG*(_dmf*0.9)[...,None]
            except Exception as _de:
                print('  (delta flood-fill skipped:',_de,')')
            rk=max(1,int(_ppdeg*0.01))  # Oxus 8/05 (Kris): halved - the fat ribbon looked silly
            rline=cv2.dilate(rmask,np.ones((rk*2+1,rk*2+1),np.uint8)).astype(bool)&(d>0)
            blend[rline]=np.array([84,126,158],np.float32)
            img[land]=blend[land]
    except Exception as _re:
        print('  (rivers skipped:',_re,')')
    gy,gx=np.gradient(d,(N-S0)/OH*111000,(E-W)/OW*111000*math.cos(math.radians((S0+N)/2)))
    az=math.radians(315); alt=math.radians(45)
    slope=np.arctan(np.hypot(gx,gy)*3.4*RELIEF_PROMINENCE); aspect=np.arctan2(-gx,gy)  # the Zagros must LOOK like the Zagros (Kris); RELIEF_PROMINENCE dials master-grade drama
    hs=np.clip(np.sin(alt)*np.cos(slope)+np.cos(alt)*np.sin(slope)*np.cos(az-aspect),0.25,1.0)
    _fl=0.58-0.10*(RELIEF_PROMINENCE-1.0)   # prominence deepens the shadow floor, flats stay bright
    img[land]*=(_fl+(1.12-_fl)*hs[land])[...,None]  # bright flats, deep honest shadows  # brighter flats, honest shadows - relief kept (Kris)  # lifted floor: charts read in daylight, not under cloud (Kris)
    rng=np.random.default_rng(11)
    img[land]*=(1+0.03*rng.standard_normal(img.shape)[land])
    
    return np.clip(img,0,255).astype(np.uint8)

# ---------- generate ----------
import sys
try: CHARTS_OUT=json.load(open('setout_charts_1271.json'))
except: CHARTS_OUT={}
# ---------- marsh tussock symbology (Kris 8/03: the classic thin-blue-dash marsh convention; an
# early map iteration had it, the method was never logged, later attempts "got bogged in a quagmire".
# THE METHOD, LOGGED: staggered rows of short horizontal strokes + an optional shorter stroke 3px
# above, drawn on an RGBA overlay AFTER terrain and BEFORE routes, clipped to hand lonlat polygons.
# Row spacing scales with px-per-degree so density survives reframing. See MAP_NOTES.md.) ----------
# ONE LIST DRIVES BOTH the baked green tint (gebco_relief) AND the stroke hatch (marsh_hatch).
# Kris 8/03: strokes without tint under them = the two had drifted apart. Never define marsh
# extent twice. Changing POLYGONS => tint changes => REBAKE needed. Changing STROKE colour/density
# => overlay only, no rebake.
MARSH_POLYS_1271=[
  [(45.8,31.05),(46.35,31.65),(47.2,31.95),(47.75,31.45),(47.65,30.85),(46.95,30.5),(46.1,30.6)],  # al-Bata'ih
  [(47.35,31.05),(47.45,31.8),(48.15,31.7),(48.35,31.15),(47.9,30.78)],                            # Hawizeh, NE of Basra
  [(48.0,30.45),(48.15,31.05),(48.75,31.15),(49.05,30.7),(48.6,30.3)],                             # Karun mouth, E of the Basra-Ahwaz road (Kris's purple circle - why the road bends)
]
MARSH_STROKE=(56,138,150)   # OXUS: the tussock stroke colour - tweak HERE (Kris wants it cyan-ish); overlay-only, no rebake
# NILE DELTA cultivation polygon (Kris 8/05): the delta is irrigation-fed, max lushness - forced green
DELTA_POLY=[(31.35,29.90),(30.35,30.95),(30.05,31.50),(30.85,31.75),(31.55,31.72),(32.10,31.45),(31.85,30.80)]  # generous leak-guard hull around the delta
def marsh_hatch(im,geo,polys=None,seed=7,col=None):
    col=col or MARSH_STROKE
    from PIL import Image as _I, ImageDraw as _D
    W,E,S0,N=geo; OW,OH=im.size
    polys=polys or MARSH_POLYS_1271
    def _px(lon,lat): return ((lon-W)/(E-W)*OW,(N-lat)/(N-S0)*OH)
    mask=_I.new('L',(OW,OH),0); md=_D.Draw(mask)
    for p in polys: md.polygon([_px(*q) for q in p],fill=255)
    mk=np.asarray(mask)>0
    if not mk.any(): return
    ov=_I.new('RGBA',(OW,OH),(0,0,0,0)); od=_D.Draw(ov)
    rng=np.random.default_rng(seed)
    ry=max(6,int(OW/(E-W)*0.13)); cx=int(ry*2.0); y=ry//2; row=0
    while y<OH:
        x=(cx//2 if row%2 else 0)+int(rng.integers(0,max(1,ry//2)))
        while x<OW:
            xi=int(min(OW-1,max(0,x)))
            if mk[int(y),xi]:
                L=int(rng.integers(7,13))
                od.line([x-L/2,y,x+L/2,y],fill=col+(200,),width=2)
                if rng.random()<0.45:
                    od.line([x-L*0.2,y-3,x+L*0.2,y-3],fill=col+(170,),width=1)
            x+=cx+int(rng.integers(-3,4))
        y+=ry; row+=1
    im.paste(ov,(0,0),ov)

def slug(n): return re.sub(r"[^a-z]","",n.lower())
BBOX_OVERRIDE={'Hormuz':(51.5,73.5,15.5,33.0)}
ARID_FORCE={'Jerusalem','Aylah','Medina','Mecca','Sanaa','Aden','Dhofar','Jeddah','Shibam','Aydhab','Qus','Asyut','Fustat','Alexandria'}
MED_CLIMATE={'Jerusalem','Acre','Damascus','Aleppo'}  # Mediterranean climate: inverted growing year (green winter, dry summer) - takes effect on rebake  # Oxus: force the GEBCO arid/sand ramp instead of the olive master slice (Fadak's coloring doctrine)
EXTRA_LEGS={'Hormuz':['Varamin|Yazd'],'Asyut':['Asyut|Kharga']}  # Oxus 8/05: Darb al-Arba'in context road off toward Kharga  # Oxus: force a 2nd-order onward stub the neighbour-walk misses  # Oxus 8/3: frame Dhofar+Cambay; Kollam/Baghdad/Varamin fall off-frame as stubs
if len(sys.argv)>1 and sys.argv[1]=='--rerender':
    # Oxus 8/05: re-render terrain JPGs in place (keep hand-tuned JSON); force gebco for the thin river + lush delta
    for _name in sys.argv[2:]:
        e=CHARTS_OUT[_name]; geo=e['geo']; OW=e['vbw']; OH=e['vbh']; W,E,S0,N=geo
        img=gebco_relief(W,E,S0,N,OW,OH,lakeclip=True)
        img,_eph,_forbid=anachronize(img,(W,E,S0,N))
        _roadpx=[]
        for _src in (e.get('legs',{}),e.get('sealegs',{})):
            for _poly in _src.values():
                _roadpx.append([[float(_a),float(_b)] for _a,_b in (q.split(',') for q in _poly.split())])
        _slug=_name[3:]
        _sea=fields_multi(img,(W,E,S0,N),SETTLE,seasons=SEASONS,roads=_roadpx,forbid=_forbid,medclimate=False)
        for _sn,_img in _sea.items():
            for _m,_col,_ss in _eph:
                if _sn in _ss: _img=_img.copy(); _img[_m]=np.array(_col,np.uint8)
            Image.fromarray(_img).save('so1271_%s_%s.jpg'%(_slug,_sn),quality=87)
        Image.fromarray(_sea['summer']).save('so1271_%s.jpg'%_slug,quality=87)
        print('re-rendered',_name,geo)
    sys.exit(0)
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
    if C in BBOX_OVERRIDE: W,E,S0,N=BBOX_OVERRIDE[C]
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
    from rebake_1271_fields import relief_boost
    if C in ARID_FORCE:
        img=gebco_relief(W,E,S0,N,OW,OH,lakeclip=True)  # arid ramp + Dead-Sea/rift declamp
    elif S0>=MS and W>=MW and E<=ME and N<=MN:
        slice_master(max(W,MW),min(E,ME),max(S0,MS),min(N,MN),OW,OH,'_tmp_so.png')
        img=relief_boost(np.array(Image.open('_tmp_so.png').convert('RGB')),(W,E,S0,N),OW,OH)
    elif S0<MS<N and W>=MW and E<=ME:  # Oxus: straddle 24N -> master relief above, GEBCO below
        yb=max(1,min(OH-1,int(round((N-MS)/(N-S0)*OH))))
        slice_master(max(W,MW),min(E,ME),MS,min(N,MN),OW,yb,'_tmp_so_n.png')
        _top=relief_boost(np.array(Image.open('_tmp_so_n.png').convert('RGB')),(W,E,MS,N),OW,yb)
        _bot=gebco_relief(W,E,S0,MS,OW,OH-yb).astype(np.uint8)
        img=np.vstack([_top,_bot])
    else:
        img=gebco_relief(W,E,S0,N,OW,OH)
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
    _sea=fields_multi(img,(W,E,S0,N),SETTLE,seasons=SEASONS,roads=_roadpx,forbid=_forbid,medclimate=(C in MED_CLIMATE))
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
        if terr in ('med','sea','coast','deep'): centry['sealegs'][k]=poly  # Oxus 8/04 (Kris): coast+deep are sea routes too - draw them blue like Aden-Socotra
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
            if terr2 in ('med','sea','coast','deep'): centry.setdefault('sealegs',{})[k2]=poly2
            else: centry['legs'][k2]=poly2
            drawn.add(k2)
            if m in LL and m not in centry['cities']:
                mx,my=px(*LL[m])
                if -40<=mx<=OW+40 and -40<=my<=OH+40:
                    centry['cities'][m]={'x':int(mx),'y':int(my),'r':6,'ldx':12,'ldy':-10,'faint':True}
    if not centry['sealegs']: del centry['sealegs']
    # IN-FRAME LANDMARKS (Oxus 8/04, Kris): any node whose coords fall inside the chart gets a faint dot,
    # even with no road to it from here - e.g. Aydhab simply IS within the Medina frame, so it shows.
    for _ln,_lll in LL.items():
        if _ln in centry['cities']: continue
        _lmx,_lmy=px(*_lll)
        if 0<=_lmx<=OW and 0<=_lmy<=OH:
            centry['cities'][_ln]={'x':int(_lmx),'y':int(_lmy),'r':6,'ldx':12,'ldy':-10,'faint':True}
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
    for _ek in EXTRA_LEGS.get(C,[]):
        _eg=GEO.get(_ek) or RM.get(_ek)
        if not _eg or _ek in centry['legs'] or _ek in centry.get('sealegs',{}): continue
        _ep=np.array([[px(lon,la)[0],px(lon,la)[1]] for lon,la in _eg],float)
        if len(_ep)>36:
            _dd=np.r_[0,np.cumsum(np.hypot(np.diff(_ep[:,0]),np.diff(_ep[:,1])))]
            _t=np.linspace(0,_dd[-1],36); _ep=np.c_[np.interp(_t,_dd,_ep[:,0]),np.interp(_t,_dd,_ep[:,1])]
        _epoly=' '.join('%.1f,%.1f'%(x,y) for x,y in _ep)
        if EDGE_TERR.get(_ek,'land') in ('med','sea'): centry.setdefault('sealegs',{})[_ek]=_epoly
        else: centry['legs'][_ek]=_epoly
    CHARTS_OUT['so_'+slug(C)]=centry
    made.append(fn)
json.dump(CHARTS_OUT,open('setout_charts_1271.json','w'))
print('generated',len(made),'this batch; total',len(CHARTS_OUT),'of',len(cities))
