# gen_elbistan_map.py -- ANATOLIA news map: the Battle of Elbistan / Abulustayn, 15 April 1277.
# Baybars marches north out of Mamluk Syria and destroys an Ilkhanid Mongol army on the plain of
# Abulustayn in Rum. SAME pipeline as gen_crusader_maps.py: gebco_relief background from
# gen_setout_1271, real route geometry from GEO, city dots, a battle marker + army arrows.
# Permanent (Ozymandias rule). Usage:
#   python3 gen_elbistan_map.py bake     (once; writes _anatolia_bg.npy)
#   python3 gen_elbistan_map.py          (renders ../Pictures/elbistan_map_1277.jpg)
import sys, math, numpy as np
from PIL import Image, ImageDraw, ImageFont

W,E,S0,N = 31.8, 42.8, 35.2, 41.7
OW = 1150
OH = int(OW*(N-S0)/((E-W)*math.cos(math.radians((S0+N)/2))))

src=open('gen_setout_1271.py').read(); ns={}
exec(src[:src.index('def slug(')], ns)
GEO=ns['GEO']; LL=ns['LL']

if len(sys.argv)>1 and sys.argv[1]=='bake':
    bg=ns['gebco_relief'](W,E,S0,N,OW,OH)
    np.save('_anatolia_bg.npy', np.asarray(bg,np.uint8) if not isinstance(bg,Image.Image) else np.asarray(bg.convert('RGB')))
    print('anatolia bg baked',OW,OH); sys.exit()

BLUE=(32,66,140); GOLD=(176,138,32); STEEL=(78,96,120); GREEN=(70,120,60)
INK=(58,42,30); ROAD=(112,50,26); PARCH=(244,233,203); RED=(176,26,20); GREY=(78,78,82)
F_T=ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSerif-Bold.ttf',34)
F_C=ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSerif-Bold.ttf',25)
F_S=ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSerif-Italic.ttf',19)
F_L=ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSerif.ttf',20)

im=Image.fromarray(np.load('_anatolia_bg.npy')).convert('RGB'); d=ImageDraw.Draw(im)
def px(lon,lat): return ((lon-W)/(E-W)*OW,(N-lat)/(N-S0)*OH)
def st(xy,txt,f,fill,ow=2,anchor='la'):
    x,y=xy
    if anchor=='ra': x-=d.textlength(txt,font=f)
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
BLADE=(46,38,28)
def crossed_swords(cx,cy,sc=1.0):
    # two swords crossing at ~90deg; hilts splayed (not touching); pointed tips
    hilts=[(16,16),(-16,16)]
    for sgx in (1,-1):
        hx,hy=cx+sgx*16*sc,cy+16*sc; tx,ty=cx-sgx*16*sc,cy-16*sc
        dx,dy=tx-hx,ty-hy; L=math.hypot(dx,dy); ux,uy=dx/L,dy/L; nx,ny=-uy,ux
        w=2.7*sc+1.7; nt=9*sc; bx,by=tx-ux*nt,ty-uy*nt
        d.polygon([(hx+nx*w,hy+ny*w),(bx+nx*w,by+ny*w),(tx+ux*2,ty+uy*2),(bx-nx*w,by-ny*w),(hx-nx*w,hy-ny*w)],fill=PARCH)
    for sgx in (1,-1):
        hx,hy=cx+sgx*16*sc,cy+16*sc; tx,ty=cx-sgx*16*sc,cy-16*sc
        dx,dy=tx-hx,ty-hy; L=math.hypot(dx,dy); ux,uy=dx/L,dy/L; nx,ny=-uy,ux
        w=2.7*sc; nt=9*sc; bx,by=tx-ux*nt,ty-uy*nt
        d.polygon([(hx+nx*w,hy+ny*w),(bx+nx*w,by+ny*w),(tx,ty),(bx-nx*w,by-ny*w),(hx-nx*w,hy-ny*w)],fill=BLADE)
        gx,gy=hx+ux*7*sc,hy+uy*7*sc; gg=10*sc
        d.line([gx-nx*gg,gy-ny*gg,gx+nx*gg,gy+ny*gg],fill=BLADE,width=max(2,int(3.4*sc)))
        pr=max(2,int(3.6*sc)); d.ellipse([hx-pr,hy-pr,hx+pr,hy+pr],fill=BLADE,outline=PARCH)

# ROADS: the real caravan legs through Rum (from the geometry registry)
for k in ('Konya|Sivas','Erzurum|Sivas','Sivas|Trebizond','Erzurum|Trebizond',
          'Ayas|Konya','Ayas|Sivas','Aleppo|Ayas','Aleppo|Iconium','Constantinople|Konya','Erzurum|Tabriz'):
    if k in GEO: dashline(GEO[k],ROAD,4,14,9)

def arrow(a,b,color,width=7):
    ax,ay=px(*a); bx,by=px(*b)
    d.line([ax,ay,bx,by],fill=color,width=width)
    ang=math.atan2(by-ay,bx-ax)
    for da in (0.42,-0.42):
        d.line([bx,by, bx-26*math.cos(ang-da), by-26*math.sin(ang-da)],fill=color,width=width)
ELB=(37.19,38.20)
arrow((37.15,36.7),(37.19,37.9),GOLD,7)     # Baybars north out of Aleppo / Syria
arrow((40.4,39.3),(37.8,38.35),GREY,7)      # the Ilkhan's army down from the NE
st(px(35.7,37.05),'Baybars marches north',F_S,GOLD)
st(px(39.3,39.05),"the Ilkhan's army",F_S,GREY,anchor='ra')

# cities: (lon,lat, colour, r, font, (dx,dy), anchor)
CITIES={
 'Konya':(32.5,37.87,STEEL,7,F_C,(14,-4),'la'),
 'Kayseri':(35.48,38.72,STEEL,7,F_C,(14,-6),'la'),
 'Sivas':(37.02,39.75,STEEL,7,F_C,(14,-8),'la'),
 'Erzurum':(41.28,39.9,STEEL,7,F_C,(-14,-8),'ra'),
 'Trebizond':(39.72,41.0,BLUE,7,F_C,(-14,10),'ra'),
 'Aleppo':(37.15,36.21,GOLD,8,F_C,(14,-6),'la'),
 'Ayas':(35.79,36.77,GREEN,6,F_C,(-14,8),'ra'),
}
for nm,(lon,lat,col,r,f,(dx,dy),anc) in CITIES.items():
    x,y=px(lon,lat)
    d.ellipse([x-r,y-r,x+r,y+r],fill=col,outline=PARCH,width=2)
    st((x+dx,y+dy),nm,f,col,anchor=anc)

# THE BATTLE at Elbistan / Abulustayn
ex,ey=px(*ELB)
crossed_swords(ex,ey,1.2)
st((ex-d.textlength('ELBISTAN',font=F_C)/2,ey+40),'ELBISTAN',F_C,RED,ow=3)
st((ex-d.textlength('the plain of Abulustayn',font=F_S)/2,ey+66),'the plain of Abulustayn',F_S,RED)

# title + legend
title='ANATOLIA (RUM) - April 1277'
tw=d.textlength(title,font=F_T)
d.rectangle([20,18,34+tw+16,66],fill=PARCH,outline=INK,width=3); d.text((34,25),title,font=F_T,fill=(140,30,20))
d.rectangle([20,84,404,236],fill=PARCH,outline=INK,width=3)
d.ellipse([36,102,56,122],fill=GOLD,outline=PARCH,width=2); d.text((66,102),'Mamluk Sultanate',font=F_L,fill=GOLD)
d.ellipse([36,134,56,154],fill=STEEL,outline=PARCH,width=2); d.text((66,134),'Seljuk Rum, held for the Ilkhan',font=F_L,fill=STEEL)
crossed_swords(46,176,0.55); d.text((66,166),'the battle, 15 April 1277',font=F_L,fill=INK)
d.text((34,202),'Tabriz & the Ilkhan lie east, off-chart',font=F_S,fill=INK)

out='../Pictures/elbistan_map_1277.jpg'
im.save(out,quality=90); print('saved',out,im.size)
