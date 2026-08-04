# gen_crusader_maps.py -- THE SYRIAN COAST news maps (Krak April 1271 / Montfort June 1271).
# Rebuilt PERMANENTLY 8/03 (the originals were /tmp one-offs; Ozymandias rule). Kris's fixes:
#  - fortress STATUS text colour follows the CASTLE's current allegiance: Frankish blue while it
#    'still holds' or is 'under siege'; Mamluk gold once 'fallen'/'yielded'. (Was: gold for some.)
#  - fortress icons: THREE merlons, wider base (was two - 'they look like legos').
# Usage: python3 gen_crusader_maps.py bake   (once; writes _levant_bg.npy, >41s-safe on its own)
#        python3 gen_crusader_maps.py krak | montfort | both
import sys, json, math, numpy as np
from PIL import Image, ImageDraw, ImageFont

W,E,S0,N = 34.55, 37.45, 32.30, 35.55
OW = 1000
OH = int(OW*(N-S0)/((E-W)*math.cos(math.radians((S0+N)/2))))

src=open('gen_setout_1271.py').read(); ns={}
exec(src[:src.index('def slug(')], ns)

if len(sys.argv)>1 and sys.argv[1]=='bake':
    bg=ns['gebco_relief'](W,E,S0,N,OW,OH)
    np.save('_levant_bg.npy', np.asarray(bg,np.uint8) if not isinstance(bg,Image.Image) else np.asarray(bg.convert('RGB')))
    print('levant bg baked',OW,OH); sys.exit()

GEO=ns['GEO']
BLUE=(32,66,140); GOLD=(176,138,32); INK=(58,42,30); ROAD=(112,50,26); PARCH=(244,233,203); RED=(188,30,22)
F_T=ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSerif-Bold.ttf',34)
F_C=ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSerif-Bold.ttf',26)
F_S=ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSerif-Italic.ttf',19)
F_L=ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSerif.ttf',20)

def make(when):
    im=Image.fromarray(np.load('_levant_bg.npy')).convert('RGB'); d=ImageDraw.Draw(im)
    def px(lon,lat): return ((lon-W)/(E-W)*OW,(N-lat)/(N-S0)*OH)
    def st(xy,txt,f,fill,ow=2):
        x,y=xy
        for dx in(-ow,0,ow):
            for dy in(-ow,0,ow):
                if dx or dy: d.text((x+dx,y+dy),txt,font=f,fill=PARCH)
        d.text((x,y),txt,font=f,fill=fill)
    def dashline(pts,color,width,on,off):
        P=[px(*p) for p in pts]; t=0.0
        for i in range(1,len(P)):
            x0,y0=P[i-1]; x1,y1=P[i]; L=math.hypot(x1-x0,y1-y0)
            if L<=0: continue
            a=0.0
            while a<L:
                ph=(t+a)%(on+off)
                if ph<on:
                    b=min(L,a+(on-ph)); f0,f1=a/L,b/L
                    d.line([x0+(x1-x0)*f0,y0+(y1-y0)*f0,x0+(x1-x0)*f1,y0+(y1-y0)*f1],fill=color,width=width); a=b
                else: a=min(L,a+(on+off-ph))
            t+=L
    for k in ('Acre|Damascus','Aleppo|Damascus','Acre|Jerusalem'):
        if k in GEO: dashline(GEO[k],ROAD,4,14,9)
    def fortress(x,y,col,fallen=False,siege=False):
        # three merlons on a broader keep (Kris: two looked like legos)
        bw,bh,mw,mh=34,16,8,9
        d.rectangle([x-bw/2,y-bh,x+bw/2,y],fill=col,outline=PARCH,width=2)
        for i,mx in enumerate((-bw/2, -mw/2, bw/2-mw)):
            d.rectangle([x+mx,y-bh-mh,x+mx+mw,y-bh],fill=col,outline=PARCH,width=1)
        if siege:
            for a in range(0,360,30):
                sx,sy=x+30*math.cos(math.radians(a)),y-8+26*math.sin(math.radians(a))
                d.ellipse([sx-3,sy-3,sx+3,sy+3],fill=GOLD)
        if fallen:
            d.line([x-20,y-bh-mh-4,x+20,y+4],fill=RED,width=5)
            d.line([x-20,y+4,x+20,y-bh-mh-4],fill=RED,width=5)
    # fortresses: (lon,lat,state,label)  state in holds/siege/fallen
    F={'Margat':(35.949,35.152,'holds','Hospitaller — still holds'),
       'Tortosa':(35.887,34.888,'holds','Templar — still holds'),
       'Chastel Blanc':(36.117,34.821,'fallen','Templar — yielded in February'),
       'Krak des Chevaliers':(36.295,34.757,'fallen','Hospitaller — fallen 8 April')}
    if when=='krak':
        F['Montfort (Starkenberg)']=(35.226,33.044,'holds','Teutonic — still holds')
        F['Beaufort']=(35.532,33.324,'siege','Templar — under siege')
        title='THE SYRIAN COAST — April 1271'
    else:
        F['Montfort (Starkenberg)']=(35.226,33.044,'fallen','Teutonic — fallen 23 June')
        F['Beaufort']=(35.532,33.324,'fallen','Templar — fallen in April')
        title='THE SYRIAN COAST — June 1271'
    LBL={'Margat':(26,-34),'Tortosa':(-158,-40),'Chastel Blanc':(30,-64),'Krak des Chevaliers':(30,6),
         'Montfort (Starkenberg)':(28,-30),'Beaufort':(28,-32)}
    for nm,(lon,lat,state,lab) in F.items():
        x,y=px(lon,lat)
        col=GOLD if state=='fallen' else BLUE
        fortress(x,y,col,fallen=(state=='fallen'),siege=(state=='siege'))
        dx,dy=LBL[nm]
        st((x+dx,y+dy),nm,F_C,BLUE if state!='fallen' else GOLD)
        # STATUS colour = castle's allegiance NOW: blue while Frankish (holds/siege), gold once lost
        st((x+dx,y+dy+27),lab,F_S,BLUE if state in('holds','siege') else GOLD)
    CITIES={'Acre':(35.07,32.93,BLUE,9,F_T,(16,10)),'Tripoli':(35.84,34.44,BLUE,5,F_C,(12,-16)),
            'Damascus':(36.31,33.51,GOLD,8,F_T,(18,-22)),'Homs':(36.72,34.73,GOLD,5,F_C,(12,-38)),
            'Hama':(36.75,35.13,GOLD,5,F_C,(16,-10))}
    for nm,(lon,lat,col,r,f,(dx,dy)) in CITIES.items():
        x,y=px(lon,lat)
        d.ellipse([x-r,y-r,x+r,y+r],fill=col,outline=PARCH,width=2)
        st((x+dx,y+dy),nm,f,col)
    # title + legend
    tw=d.textlength(title,font=F_T)
    d.rectangle([20,18,34+tw+16,66],fill=PARCH,outline=INK,width=3); d.text((34,26),title,font=F_T,fill=(140,30,20))
    d.rectangle([20,86,352,238],fill=PARCH,outline=INK,width=3)
    d.ellipse([36,104,56,124],fill=BLUE,outline=PARCH,width=2); d.text((66,104),'Frankish (Christian)',font=F_L,fill=BLUE)
    d.ellipse([36,138,56,158],fill=GOLD,outline=PARCH,width=2); d.text((66,138),'Mamluk Sultanate',font=F_L,fill=GOLD)
    d.text((34,176),'Ilkhan lands lie beyond the',font=F_S,fill=INK)
    d.text((34,200),'Euphrates, off this chart NE',font=F_S,fill=INK)
    out='../Pictures/%s_map_1271.jpg'%('krak' if when=='krak' else 'montfort')
    im.save(out,quality=90); print('saved',out)

which=sys.argv[1] if len(sys.argv)>1 else 'both'
for w in (('krak','montfort') if which=='both' else (which,)):
    make(w)
