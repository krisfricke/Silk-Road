# gen_homs_map.py -- the SECOND BATTLE OF HOMS, 29 October 1281: Qalawun throws back the Ilkhan's
# great invasion. Reuses the crusader Syrian-coast relief bake (_levant_bg.npy) - "the same map that
# carried the falling fortresses" (Kris). gebco_relief bg + real routes from GEO + crossed-swords marker.
# Permanent. Usage: python3 gen_homs_map.py   (needs _levant_bg.npy from gen_crusader_maps.py bake)
import sys, math, numpy as np
from PIL import Image, ImageDraw, ImageFont

W,E,S0,N = 34.55, 37.45, 32.30, 35.55
OW = 1000
OH = int(OW*(N-S0)/((E-W)*math.cos(math.radians((S0+N)/2))))
src=open('gen_setout_1271.py').read(); ns={}
exec(src[:src.index('def slug(')], ns); GEO=ns['GEO']

BLUE=(32,66,140); GOLD=(176,138,32); STEEL=(78,96,120); INK=(58,42,30)
ROAD=(112,50,26); PARCH=(244,233,203); RED=(176,26,20); GREY=(78,78,82); BLADE=(46,38,28)
F_T=ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSerif-Bold.ttf',33)
F_C=ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSerif-Bold.ttf',25)
F_S=ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSerif-Italic.ttf',19)
F_L=ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSerif.ttf',20)

im=Image.fromarray(np.load('_levant_bg.npy')).convert('RGB'); d=ImageDraw.Draw(im)
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
def arrow(a,b,color,width=7):
    ax,ay=px(*a); bx,by=px(*b); d.line([ax,ay,bx,by],fill=color,width=width)
    ang=math.atan2(by-ay,bx-ax)
    for da in (0.42,-0.42):
        d.line([bx,by, bx-26*math.cos(ang-da), by-26*math.sin(ang-da)],fill=color,width=width)
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

for k in ('Acre|Damascus','Aleppo|Damascus','Acre|Jerusalem'):
    if k in GEO: dashline(GEO[k],ROAD,4,14,9)

# armies: Qalawun up from Damascus (south); the Ilkhan's host down from the north (Aleppo, off-frame)
arrow((36.45,33.95),(36.66,34.5),GOLD,7)     # Qalawun north to Homs
arrow((37.05,35.5),(36.86,34.9),GREY,7)      # the Ilkhan's army down from the north
st(px(35.9,34.02),'Qalawun',F_S,GOLD)
st(px(37.1,35.42),"the Ilkhan's host",F_S,GREY,anchor='ra')

CITIES={ # (lon,lat, colour, r, font, (dx,dy), anchor)
 'Homs':(36.72,34.73,GOLD,8,F_C,(16,-40),'la'),
 'Hama':(36.75,35.13,GOLD,6,F_C,(16,-8),'la'),
 'Damascus':(36.31,33.51,GOLD,8,F_C,(16,-22),'la'),
 'Tripoli':(35.84,34.44,BLUE,6,F_C,(-14,-30),'ra'),
 'Acre':(35.07,32.93,BLUE,7,F_C,(16,8),'la'),
}
for nm,(lon,lat,col,r,f,(dx,dy),anc) in CITIES.items():
    x,y=px(lon,lat); d.ellipse([x-r,y-r,x+r,y+r],fill=col,outline=PARCH,width=2)
    st((x+dx,y+dy),nm,f,col,anchor=anc)

hx,hy=px(36.72,34.73); crossed_swords(hx,hy,1.2)
st((hx-d.textlength('THE FIELD OF HOMS',font=F_S)/2,hy+34),'THE FIELD OF HOMS',F_S,RED,ow=2)

title='SYRIA - the Second Battle of Homs, 29 Oct 1281'
tw=d.textlength(title,font=F_C)
d.rectangle([20,18,34+tw+16,60],fill=PARCH,outline=INK,width=3); d.text((34,26),title,font=F_C,fill=(140,30,20))
d.rectangle([20,78,392,228],fill=PARCH,outline=INK,width=3)
d.ellipse([36,96,56,116],fill=GOLD,outline=PARCH,width=2); d.text((66,96),'Mamluk Sultanate',font=F_L,fill=GOLD)
d.ellipse([36,128,56,148],fill=STEEL,outline=PARCH,width=2); d.text((66,128),'the Ilkhan (Mongol Persia)',font=F_L,fill=STEEL)
d.ellipse([36,160,56,180],fill=BLUE,outline=PARCH,width=2); d.text((66,160),'Frankish coast (still held)',font=F_L,fill=BLUE)
crossed_swords(46,204,0.5); d.text((66,194),'the battle',font=F_L,fill=INK)

out='../Pictures/homs_map_1281.jpg'
im.save(out,quality=90); print('saved',out,im.size)
