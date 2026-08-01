# paint_nile_1271.py -- the Nile ribbon + cultivated valley band on GEBCO-based Egypt charts (Fadak).
# The GEBCO fallback renders relief but no river (the Nile is above sea level), so the charts south
# of the master's 24N edge get the river painted here, from the canonical course. Re-run after any
# rebake of so_qus / so_aydhab (and future Egypt/Nubia charts).
import json, numpy as np
from PIL import Image
import sys

COURSE=[  # lon,lat -- western branch + valley + Nubia reach (smoothed)
 [30.35,31.42],[30.82,30.83],[31.00,30.55],[31.15,30.18],[31.25,30.05],
 [31.23,29.75],[31.10,29.07],[30.95,28.70],[30.75,28.10],[30.80,27.75],
 [31.18,27.18],[31.45,26.85],[31.70,26.55],[31.95,26.30],[32.24,26.05],
 [32.50,26.10],[32.72,26.16],[32.76,25.92],[32.62,25.55],[32.55,25.29],
 [32.87,24.98],[32.93,24.47],[32.90,24.09],[32.55,23.40],[31.90,22.70],[31.35,21.90]]
RIVER=(86,124,158); VALLEY=(118,136,84)
def paint(chart_key):
    charts=json.load(open('setout_charts_1271.json'))
    c=charts[chart_key]; W,E,S0,N=c['geo']; OW,OH=c['vbw'],c['vbh']
    px=lambda lon,lat: ((lon-W)/(E-W)*OW,(N-lat)/(N-S0)*OH)
    # densify course in px
    pts=[px(lo,la) for lo,la in COURSE]
    dense=[]
    for i in range(1,len(pts)):
        x0,y0=pts[i-1]; x1,y1=pts[i]
        n=max(3,int(np.hypot(x1-x0,y1-y0)/1.5))
        for t in np.linspace(0,1,n): dense.append((x0+t*(x1-x0),y0+t*(y1-y0)))
    dense=np.array(dense)
    base=c['img'].split('/')[-1].rsplit('.',1)[0]
    rng=np.random.default_rng(7)
    for suff in ('','_spring','_summer','_autumn','_winter'):
        fn=base+suff+'.jpg'
        try: img=np.array(Image.open(fn).convert('RGB'),np.float32)
        except FileNotFoundError: continue
        H,Wd=img.shape[:2]
        yy,xx=np.mgrid[0:H,0:Wd]
        # distance to course (chunked for memory)
        dmin=np.full((H,Wd),1e9,np.float32)
        for k in range(0,len(dense),40):
            seg=dense[k:k+40]
            for sx,sy in seg[::2]:
                d2=(xx-sx)**2+(yy-sy)**2
                np.minimum(dmin,d2,out=dmin)
        dmin=np.sqrt(dmin)
        scale=OW/1400.0
        vw=14.0*scale+rng.standard_normal((H,Wd)).astype(np.float32)*1.2  # valley half-width px
        rw=3.6*scale
        valley=np.clip(1.0-(dmin-rw)/np.maximum(vw,1.0),0,1)*0.8
        img=img*(1-valley[...,None])+np.array(VALLEY,np.float32)*valley[...,None]
        river=np.clip(1.0-dmin/rw,0,1)
        img=img*(1-river[...,None])+np.array(RIVER,np.float32)*river[...,None]
        Image.fromarray(np.clip(img,0,255).astype(np.uint8)).save(fn,quality=87)
        print('painted',fn)
if __name__=='__main__':
    for k in (sys.argv[1:] or ['so_qus','so_aydhab']): paint(k)
