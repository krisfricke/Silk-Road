# amber_detail.py v2 -- Kris's ruling: IGNORE the climate layers; bake the band to the OLD SPEC
# (the southern master_detail recipe) straight from the relief. Same forest formula, same colours
# (colB 58,84,46 / colC 46,72,44, conifer by ELEVATION), same blotch/texture/alpha chain, plus the
# hydro pass (NE rivers/lakes, reservoir->marsh ANACHRON, fert margins, cream halos). Baked from
# the same DEM to the same spec, the 52N seam merges by construction.
import numpy as np, cv2, json, sys, os
from PIL import Image, ImageDraw
exec(open('bake_1271_regions_local.py').read().split("R_ANAT=")[0])
import shapefile as _shp

MW,ME,MS,MN=8.0,42.0,52.0,61.0; PPD=147.0
man=json.load(open('master_amber/manifest.json')); step=man['step']; n=man['n']
RIV=json.load(open('ne_10m_rivers_lake_centerlines.geojson'))['features']
_lk=_shp.Reader('/sessions/jolly-charming-gates/mnt/outputs/work/ne_lakes/ne_10m_lakes')
LAKES=[]
for sr in _lk.iterShapeRecords():
    rec=sr.record.as_dict()
    LAKES.append((rec.get('featurecla',''),sr.shape))
ANCIENT_OK=lambda fc: 'Reservoir' not in (fc or '')
ANACHRON=[(37.3,39.4,57.8,59.0),(38.0,38.7,57.1,57.8),(36.4,37.6,56.5,57.1)]

def draw_hydro(W,E,DW,DH,dd):
    def px(lo,la): return ((lo-W)/(E-W)*DW,(MN-la)/(MN-MS)*DH)
    lakeim=Image.new('L',(DW,DH),0); marshim=Image.new('L',(DW,DH),0)
    dl=ImageDraw.Draw(lakeim); dm=ImageDraw.Draw(marshim)
    for fc,shp in LAKES:
        bb=shp.bbox
        if bb[2]<W-0.2 or bb[0]>E+0.2 or bb[3]<MS-0.2 or bb[1]>MN+0.2: continue
        anach=any((bb[0]<b[1] and bb[2]>b[0] and bb[1]<b[3] and bb[3]>b[2]) for b in ANACHRON)
        parts=list(shp.parts)+[len(shp.points)]
        for pi in range(len(parts)-1):
            ring=[px(x,y) for x,y in shp.points[parts[pi]:parts[pi+1]]]
            if len(ring)<3: continue
            (dl if (ANCIENT_OK(fc) and not anach) else dm).polygon(ring,fill=255)
    rivim=Image.new('L',(DW,DH),0); dr=ImageDraw.Draw(rivim)
    for f in RIV:
        pr=f['properties']; g=f['geometry']
        if g is None: continue
        wdt=1+int(max(0,(6-(pr.get('scalerank') or 6)))//2)
        coords=g['coordinates'] if g['type']=='MultiLineString' else [g['coordinates']]
        for line in coords:
            xs=[c[0] for c in line]; ys=[c[1] for c in line]
            if max(xs)<W-0.2 or min(xs)>E+0.2 or max(ys)<MS-0.2 or min(ys)>MN+0.2: continue
            dr.line([px(x,y) for x,y in line],fill=255,width=wdt)
    lake=(np.array(lakeim)>0); marsh=(np.array(marshim)>0); riv=(np.array(rivim)>0)
    return lake&(dd>0), marsh&(dd>0), riv&(dd>0)

def detail_strip(i,era='1271'):
    W=MW+i*step; E=MW+(i+1)*step
    suff=('_762' if era=='762' else '')
    rp='master_amber/strip_%02d%s_relief.png'%(i,suff)
    if era=='762' and not os.path.exists(rp): rp='master_amber/strip_%02d_relief.png'%i
    relief=np.array(Image.open(rp).convert('RGB')).astype(np.float32)
    DH,DW=relief.shape[:2]
    Wm,Em=max(MW,W-0.5),min(ME,E+0.5)
    dd_full=np.load('_dem_amber_%02d.npy'%i).astype(np.float32)
    x0=int(round((W-Wm)*PPD)); dd=dd_full[:,x0:x0+DW]
    rng=np.random.default_rng(7)   # SAME seed as the southern detail pass
    img=relief.copy()
    # ---- THE SOUTHERN FOREST RECIPE, verbatim chain (master_detail_local.py) ----
    # euro moisture-gradient treeline saturates to 1 at these latitudes - exactly as it would
    # had the master extended north; then the identical blotch/blur/alpha/texture chain.
    lon=np.linspace(W,E,DW)[None,:].repeat(DH,0); lat=np.linspace(MN,MS,DH)[:,None].repeat(DW,1)
    mxq0,myq0=np.meshgrid(np.arange(DW,dtype=np.float32),np.arange(DH,dtype=np.float32))
    euro=np.clip((lat-(43.2+(lon-8.0)*0.185))/3.0,0,1)*np.clip((1900-dd)/1900,0,1)
    forest=euro
    _wfx=cv2.GaussianBlur(rng.standard_normal((DH,DW)).astype(np.float32),(0,0),30)*55
    _wfy=cv2.GaussianBlur(rng.standard_normal((DH,DW)).astype(np.float32),(0,0),30)*55
    forest=cv2.remap(forest,mxq0+_wfx,myq0+_wfy,cv2.INTER_LINEAR,borderMode=cv2.BORDER_REPLICATE)
    forest=cv2.GaussianBlur(forest,(0,0),55)
    forest=np.clip(forest*1.35,0,1)
    blotch2=cv2.GaussianBlur(rng.random((DH,DW)).astype(np.float32),(0,0),7)
    forest*=0.62+0.18*(blotch2>0.45)
    forest=cv2.GaussianBlur(forest,(0,0),4)*0.80
    conif=(dd>1400)   # elevation split, the old spec - the Scandes go conifer-dark
    colB=np.array([58,84,46],np.float32); colC=np.array([46,72,44],np.float32)
    col=np.where(conif[:,:,None],colC[None,None,:],colB[None,None,:])
    canA=cv2.GaussianBlur(rng.standard_normal((DH,DW)).astype(np.float32),(0,0),1.5)
    canB=cv2.GaussianBlur(rng.standard_normal((DH,DW)).astype(np.float32),(0,0),6.0)
    tex=np.clip(1.0+canA*0.10+canB*0.14,0.72,1.30)
    col=col*tex[:,:,None]
    water0=relief[:,:,2]>relief[:,:,0]+8
    snow0=relief.min(2)>195
    fm=(forest*(dd>0)*(~water0)*(~snow0))[:,:,None]
    img=img*(1-fm)+col*fm
    # ---- hydro (cached; identical to v1) ----
    _mz='master_amber/_masks_%02d.npz'%i
    if os.path.exists(_mz):
        _z=np.load(_mz); lake=_z['lake']; marsh=_z['marsh']; riv=_z['riv']
    else:
        lake,marsh,riv=draw_hydro(W,E,DW,DH,dd)
        np.savez_compressed(_mz,lake=lake,marsh=marsh,riv=riv)
    _rw=(img[:,:,2]>img[:,:,0]+6)&(img[:,:,2]>img[:,:,1]+2)
    lake=lake&~_rw
    fert=cv2.GaussianBlur((cv2.dilate(riv.astype(np.uint8),np.ones((5,5),np.uint8))).astype(np.float32),(0,0),12)
    fert=np.clip(fert*2.2,0,1)*np.clip(1-dd/500,0,1)*(dd>0)*0.5
    for c,gv in enumerate((104,128,78)): img[:,:,c]=img[:,:,c]*(1-fert)+gv*fert
    lakecol=interp(np.full((1,1),140.0),SEAR)[0,0]
    img=np.where(lake[:,:,None],lakecol[None,None,:],img)
    rim=(cv2.dilate(lake.astype(np.uint8),np.ones((3,3),np.uint8)).astype(bool))&~lake&~_rw
    img=np.where(rim[:,:,None],img*0.88,img)
    mg=cv2.GaussianBlur(marsh.astype(np.float32),(0,0),2)[:,:,None]*0.55
    mcol=np.array([104,126,88],np.float32)
    img=img*(1-mg)+mcol[None,None,:]*mg
    wf=(cv2.GaussianBlur(rng.random((DH,DW)).astype(np.float32),(0,0),2.2)>0.62)&marsh
    img=np.where(wf[:,:,None],img*0.5+lakecol[None,None,:]*0.5,img)
    _rl=interp(np.full((1,1),45.0),SEAR)[0,0]
    # NO cream halo: the south's halos were eaten by its ecotone pass (rivers restored, halos
    # not), so the live southern look is halo-free - match it (Kris caught the border mismatch)
    img=np.where(riv[:,:,None],_rl[None,None,:]*0.97,img)
    img=np.clip(img+rng.normal(0,1.2,(DH,DW,1)),0,255)
    dst='master_amber/strip_%02d%s.png'%(i,suff)
    Image.fromarray(img.astype('uint8')).save(dst)
    print('amber strip',i,era,'OLD-SPEC DETAILED',img.shape,flush=True)

if __name__=='__main__':
    i=int(sys.argv[1]); era=sys.argv[2] if len(sys.argv)>2 else '1271'
    detail_strip(i,era)
