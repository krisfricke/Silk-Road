# _rebake_married.py <City> <stage>  -- married-pipeline chart rebake (Fadak 8/04 control run).
# stage 0/1: bake lon-half of the chart frame -> _mar_<slug>_<half>.npy
# stage f  : stitch + anachronize + fields_multi seasons -> so1271_<slug>[_season].jpg
import sys, json, math, numpy as np
from PIL import Image
src=open('gen_setout_1271.py').read(); ns={}
exec(src[:src.index('def slug(')], ns)
import re
def slug(n): return re.sub(r"[^a-z]","",n.lower())
C=sys.argv[1]; stage=sys.argv[2]
ch=json.load(open('setout_charts_1271.json'))['so_'+slug(C)]
W,E,S0,N=ch['geo']; OW,OH=ch['vbw'],ch['vbh']
if stage in ('0','1'):
    half=int(stage); mid=(W+E)/2; hw=OW//2
    if half==0: bg=ns['gebco_relief'](W,mid,S0,N,hw,OH)
    else:       bg=ns['gebco_relief'](mid,E,S0,N,OW-hw,OH)
    np.save('_mar_%s_%d.npy'%(slug(C),half),np.asarray(bg,np.uint8))
    print('half',half,'done'); sys.exit()
img=np.hstack([np.load('_mar_%s_0.npy'%slug(C)),np.load('_mar_%s_1.npy'%slug(C))])
img,_eph,_forbid=ns['anachronize'](img,(W,E,S0,N))
geo=(W,E,S0,N)
def px(lon,lat): return (round((lon-W)/(E-W)*OW,1),round((N-lat)/(N-S0)*OH,1))
NBR=ns['NBR']; geom=ns['geom']
_roadpx=[]
_towns=set([C])|set(NBR.get(C,set()))
for _a in list(_towns):
    for _b in NBR.get(_a,[]):
        _g=geom(_a,_b)
        if _g: _roadpx.append([px(lo,la) for lo,la in _g[::3]])
_sea=ns['fields_multi'](img,geo,ns['SETTLE'],seasons=ns['SEASONS'],roads=_roadpx,forbid=_forbid)
for _sn,_img in _sea.items():
    for _m,_col,_ss in _eph:
        if _sn in _ss:
            _img=_img.copy(); _img[_m]=np.array(_col,np.uint8)
    Image.fromarray(_img).save('so1271_%s_%s.jpg'%(slug(C),_sn),quality=87)
Image.fromarray(_sea['summer']).save('so1271_%s.jpg'%slug(C),quality=87)
# marsh strokes on the final images (tint is baked; strokes are overlay per doctrine)
for f in ['so1271_%s.jpg'%slug(C)]+['so1271_%s_%s.jpg'%(slug(C),sn) for sn in _sea]:
    im=Image.open(f).convert('RGB'); ns['marsh_hatch'](im,geo); im.save(f,quality=87)
print('rebaked',C,'with',len(_sea),'seasons + marsh')
