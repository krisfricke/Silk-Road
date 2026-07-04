# master_detail.py - phase 2: forests + DEM-derived rivers onto master strips (flow from /tmp/flow_block_*.npy)
import numpy as np, cv2, json, os
from PIL import Image
exec(open('bake_1271_regions.py').read().split("R_ANAT=")[0])
MW,ME,MS,MN=8.0,123.0,24.0,52.0
man=json.load(open('master1271/manifest.json')); step=man['step']; n=man['n']
from PIL import ImageDraw
import shapefile as _shp
RIV=json.load(open('ne_10m_rivers_lake_centerlines.geojson'))['features']
_lk=_shp.Reader('/tmp/ne_lakes/ne_10m_lakes')
LAKES=[]
for sr in _lk.iterShapeRecords():
    rec=sr.record.as_dict()
    LAKES.append((rec.get('featurecla',''),sr.shape))
ANCIENT_OK=lambda fc: 'Reservoir' not in (fc or '')
def draw_hydro(W,E,DW,DH,dd):
    def px(lo,la): return ((lo-W)/(E-W)*DW,(MN-la)/(MN-MS)*DH)
    lakeim=Image.new('L',(DW,DH),0); marshim=Image.new('L',(DW,DH),0)
    dl=ImageDraw.Draw(lakeim); dm=ImageDraw.Draw(marshim)
    for fc,shp in LAKES:
        bb=shp.bbox
        if bb[2]<W-0.2 or bb[0]>E+0.2 or bb[3]<MS-0.2 or bb[1]>MN+0.2: continue
        parts=list(shp.parts)+[len(shp.points)]
        for pi in range(len(parts)-1):
            ring=[px(x,y) for x,y in shp.points[parts[pi]:parts[pi+1]]]
            if len(ring)<3: continue
            (dl if ANCIENT_OK(fc) else dm).polygon(ring,fill=255)
    rivim=Image.new('L',(DW,DH),0); dr=ImageDraw.Draw(rivim)
    for f in RIV:
        pr=f['properties']; g=f['geometry']
        if g is None: continue
        wdt=1+int(max(0,(6-(pr.get('scalerank') or 6)))//2)
        coords=g['coordinates'] if g['type']=='MultiLineString' else [g['coordinates']]
        for line in coords:
            xs=[c[0] for c in line]
            if max(xs)<W-0.2 or min(xs)>E+0.2: continue
            dr.line([px(x,y) for x,y in line],fill=255,width=wdt)
    lake=(np.array(lakeim)>0); marsh=(np.array(marshim)>0); riv=(np.array(rivim)>0)
    return lake&(dd>0), marsh&(dd>0), riv&(dd>0)
FB=[(8,30,43,52,50,1800),(22,42,40,45.5,0,2000),(37,50,40.5,44.5,200,2200),(48.5,55,35.5,39.2,0,2500),
    (26,52,36,40,1200,2600),(44,54,32,37.5,1600,2900),(66,96,39,45.5,1500,2900),(83,96,45,52,900,2600),
    (8,17,43.5,48,400,2100),(20,27,44.5,49.5,300,1900),(88,100,24,30.5,100,3000),
    (100,123,24,35,0,2800),(108,123,35,42,200,2200),(116,123,42,52,200,1700)]
rng=np.random.default_rng(7)
import sys
_which=[int(a) for a in sys.argv[1:]] or list(range(n))
for i in _which:
    W=MW+i*step; E=MW+(i+1)*step
    src='master1271/strip_%02d_relief.png'%i
    if not os.path.exists(src): os.rename('master1271/strip_%02d.png'%i,src)
    img0=np.array(Image.open(src).convert('RGB')).astype(np.float32)
    DH,DW0=img0.shape[:2]
    PAD=74
    img=np.pad(img0,((0,0),(PAD,PAD),(0,0)),mode='edge')
    DW=DW0+2*PAD
    W_,E_=W,E; W=W-PAD/147.0; E=E+PAD/147.0
    dd=dem(W,E,MS,MN,DW,DH).astype(np.float32)
    lon=np.linspace(W,E,DW)[None,:].repeat(DH,0); lat=np.linspace(MN,MS,DH)[:,None].repeat(DW,1)
    blotch=cv2.GaussianBlur(rng.random((DH,DW)).astype(np.float32),(0,0),4)
    forest=np.zeros((DH,DW),np.float32)
    euro=np.clip((lat-(43.2+(lon-8.0)*0.185))/3.0,0,1)*np.clip((1900-dd)/1900,0,1)*(lon<52).astype(np.float32)
    forest=np.maximum(forest,euro)  # moisture-gradient treeline: forest-steppe boundary climbs NE across Ukraine, no box edges
    for (bw,be_,bs,bn,elo,ehi) in FB[2:]:
        if be_<W or bw>E: continue
        m=((lon>=bw)&(lon<=be_)&(lat>=bs)&(lat<=bn)&(dd>=elo)&(dd<=ehi)).astype(np.float32)
        forest=np.maximum(forest,m)
    forest=cv2.GaussianBlur(forest,(0,0),55)  # wide feather: box edges must never read as lines 
    forest=np.clip(forest*1.35,0,1)
    blotch2=cv2.GaussianBlur(rng.random((DH,DW)).astype(np.float32),(0,0),7)
    forest*=0.62+0.18*(blotch2>0.45)
    forest=cv2.GaussianBlur(forest,(0,0),4)*0.80
    conif=(dd>1400)
    colB=np.array([58,84,46],np.float32); colC=np.array([46,72,44],np.float32)
    col=np.where(conif[:,:,None],colC[None,None,:],colB[None,None,:])
    canA=cv2.GaussianBlur(rng.standard_normal((DH,DW)).astype(np.float32),(0,0),1.5)
    canB=cv2.GaussianBlur(rng.standard_normal((DH,DW)).astype(np.float32),(0,0),6.0)
    tex=np.clip(1.0+canA*0.10+canB*0.14,0.72,1.30)
    col=col*tex[:,:,None]
    fm=forest[:,:,None]*(dd>0)[:,:,None]
    img=img*(1-fm)+col*fm
    _rw=(img[:,:,2]>img[:,:,0]+6)&(img[:,:,2]>img[:,:,1]+2)   # relief already shows water (Caspian/Aral/lakes)
    lake,marsh,riv=draw_hydro(W,E,DW,DH,dd)
    lake&=~_rw   # never repaint a shoreline the relief owns - Kris's doubled north-Caspian
    ROSY=[(29.5,50,24,35.8),(50,64,24,34)]
    rosy=np.zeros((DH,DW),np.float32)
    for (bw,be_,bs,bn) in ROSY:
        rosy=np.maximum(rosy,((lon>=bw)&(lon<=be_)&(lat>=bs)&(lat<=bn)).astype(np.float32))
    rosy=cv2.GaussianBlur(rosy,(0,0),55)*np.clip(1-dd/1000,0,1)*(dd>0)*0.38*(1-np.clip(forest*3,0,1))
    for c,rv in enumerate((216,168,136)): img[:,:,c]=img[:,:,c]*(1-rosy)+rv*rosy
    DUNEP=[[(38.6,28.8),(40.2,27.5),(42.5,27.6),(44.6,28.2),(44.9,28.9),(42.8,29.7),(40.6,29.9),(39.2,29.6)],
           [(32.4,31.05),(33.4,31.2),(34.25,31.25),(34.2,30.85),(33.3,30.7),(32.5,30.7)],
           [(24.5,30.6),(27.5,30.3),(30.4,30.0),(30.2,27.0),(27.0,24.2),(24.5,24.2)],
           [(57.8,38.0),(60.0,37.3),(62.8,37.8),(64.4,39.2),(63.0,40.9),(60.5,41.9),(58.5,40.5),(57.5,39.0)],
           [(60.5,41.8),(63.0,41.2),(65.6,41.5),(66.8,42.9),(65.0,44.4),(62.3,44.6),(60.8,43.4)],
           [(77.6,38.8),(80.0,37.6),(84.0,37.2),(88.0,38.0),(89.4,39.5),(87.0,40.6),(83.0,41.1),(79.5,40.5),(77.8,39.8)],
           [(64.2,31.6),(65.8,29.6),(67.2,29.9),(66.9,31.5),(65.4,32.1)],
           [(69.3,28.9),(71.5,26.5),(73.5,24.6),(75.3,24.4),(74.5,27.0),(72.4,29.2),(70.4,29.5)]]
    dune=np.zeros((DH,DW),np.float32)
    for poly in DUNEP:
        pts=[((x-W)/(E-W)*DW,(MN-y)/(MN-MS)*DH) for x,y in poly]
        if max(p[0] for p in pts)<0 or min(p[0] for p in pts)>DW: continue
        tmp=Image.new('L',(DW,DH),0); ImageDraw.Draw(tmp).polygon(pts,fill=255)
        dune=np.maximum(dune,(np.array(tmp)>0).astype(np.float32))
    fx=cv2.GaussianBlur(rng.standard_normal((DH,DW)).astype(np.float32),(0,0),26)*48
    fy=cv2.GaussianBlur(rng.standard_normal((DH,DW)).astype(np.float32),(0,0),26)*48
    mxq,myq=np.meshgrid(np.arange(DW,dtype=np.float32),np.arange(DH,dtype=np.float32))
    dune=cv2.remap(dune,mxq+fx,myq+fy,cv2.INTER_LINEAR,borderMode=cv2.BORDER_REPLICATE)
    gyq,gxq=np.gradient(np.where(dd<0,0,dd),450.0)
    dune=cv2.GaussianBlur(dune*((np.hypot(gxq,gyq)<0.5)&(dd>0)&(dd<1500)).astype(np.float32),(0,0),55)*0.58
    for c,dv in enumerate((240,222,158)): img[:,:,c]=img[:,:,c]*(1-dune)+dv*dune
    fert=cv2.GaussianBlur((cv2.dilate(riv.astype(np.uint8),np.ones((5,5),np.uint8))).astype(np.float32),(0,0),12)
    fert=np.clip(fert*2.2,0,1)*np.clip(1-dd/500,0,1)*(dd>0)*0.5
    LUSHP=[([(31.05,30.1),(30.3,31.55),(31.95,31.55)],40),
           ([(34.95,36.9),(35.6,37.05),(36.35,37.0),(36.5,36.3),(36.1,36.25),(35.3,36.55)],140),
           ([(70.6,40.6),(71.5,41.05),(72.6,41.15),(73.4,40.6),(72.4,40.25),(71.2,40.35)],600),
           ([(45.9,32.2),(47.6,32.0),(48.5,30.4),(47.5,29.9),(46.2,30.9)],25)]
    lush=np.zeros((DH,DW),np.float32)
    lim=Image.new('L',(DW,DH),0); ldr=ImageDraw.Draw(lim)
    for poly,emax in LUSHP:
        pts=[((x-W)/(E-W)*DW,(MN-y)/(MN-MS)*DH) for x,y in poly]
        if max(p[0] for p in pts)<0 or min(p[0] for p in pts)>DW: continue
        tmp=Image.new('L',(DW,DH),0); ImageDraw.Draw(tmp).polygon(pts,fill=255)
        m=(np.array(tmp)>0)&(dd<emax)&(dd>0)
        lush=np.maximum(lush,m.astype(np.float32))
    lush=cv2.remap(lush,mxq+fx,myq+fy,cv2.INTER_LINEAR,borderMode=cv2.BORDER_REPLICATE)
    lush=cv2.GaussianBlur(lush,(0,0),18)*0.7
    g=np.clip(fert+lush,0,0.75)
    for c,gv in enumerate((104,128,78)): img[:,:,c]=img[:,:,c]*(1-g)+gv*g
    mm=cv2.GaussianBlur((lush>0.3).astype(np.float32),(0,0),3)
    wfl=(cv2.GaussianBlur(rng.random((DH,DW)).astype(np.float32),(0,0),2.2)>0.66)&(mm>0.4)&(dd>0)&(dd<80)
    rivcol=interp(np.full((1,1),80.0),SEAR)[0,0]
    lakecol=interp(np.full((1,1),140.0),SEAR)[0,0]
    img=np.where(wfl[:,:,None],img*0.55+lakecol[None,None,:]*0.45,img)
    img=np.where(lake[:,:,None],lakecol[None,None,:],img)
    rim=(cv2.dilate(lake.astype(np.uint8),np.ones((3,3),np.uint8)).astype(bool))&~lake
    img=np.where(rim[:,:,None],img*0.88,img)
    mg=cv2.GaussianBlur(marsh.astype(np.float32),(0,0),2)[:,:,None]*0.55
    mcol=np.array([104,126,88],np.float32)
    img=img*(1-mg)+mcol[None,None,:]*mg
    wf=(cv2.GaussianBlur(rng.random((DH,DW)).astype(np.float32),(0,0),2.2)>0.62)&marsh
    img=np.where(wf[:,:,None],img*0.5+lakecol[None,None,:]*0.5,img)
    img=np.where(riv[:,:,None],rivcol[None,None,:]*0.97,img)
    img=np.clip(img+rng.normal(0,1.2,(DH,DW,1)),0,255)
    img=img[:,PAD:-PAD]; W,E=W_,E_
    Image.fromarray(img.astype('uint8')).save('master1271/strip_%02d.png'%i)
    print('strip',i,'detailed',flush=True)
print('DETAIL DONE',flush=True)
