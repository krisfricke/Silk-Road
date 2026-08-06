# gen_aydhab_sack_map.py -- THE NUBIANS SACK AYDHAB, 1272 (Seignobos 2018). King David of Makuria
# throws off the baqt tribute and strikes north out of the desert onto the Red Sea port of Aydhab -
# the provocation that brings Baybars up the Nile to sack Dongola in 1276. Reuses _nubia_bg.npy (the
# tapered-floodplain Nubia relief). Permanent. Usage: python3 gen_aydhab_sack_map.py  (needs _nubia_bg.npy)
import math, numpy as np
from PIL import Image, ImageDraw, ImageFont
W,E,S0,N = 28.8, 37.2, 17.3, 30.6
OW = 880
OH = int(OW*(N-S0)/((E-W)*math.cos(math.radians((S0+N)/2))))
src=open('gen_setout_1271.py').read(); ns={}
exec(src[:src.index('def slug(')], ns); GEO=ns['GEO']

BLUE=(32,66,140); GOLD=(176,138,32); GREEN=(58,110,64); INK=(58,42,30)
ROAD=(120,60,30); PARCH=(244,233,203); RED=(176,26,20); BLADE=(46,38,28)
F_T=ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSerif-Bold.ttf',30)
F_C=ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSerif-Bold.ttf',24)
F_S=ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSerif-Italic.ttf',18)
F_L=ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSerif.ttf',19)
F_X=ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSerif-Italic.ttf',15)

im=Image.fromarray(np.load('_nubia_bg.npy')).convert('RGB'); d=ImageDraw.Draw(im)
def px(lon,lat): return ((lon-W)/(E-W)*OW,(N-lat)/(N-S0)*OH)
def st(xy,txt,f,fill,ow=2,anchor='la'):
    x,y=xy
    if anchor=='ra': x-=d.textlength(txt,font=f)
    if anchor=='ma': x-=d.textlength(txt,font=f)/2
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
    for da in (0.42,-0.42): d.line([bx,by, bx-26*math.cos(ang-da), by-26*math.sin(ang-da)],fill=color,width=width)
def crossed_swords(cx,cy,sc=1.0):
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
def cataract(lon,lat,label,ldx,ldy,anc='la'):
    x,y=px(lon,lat)
    for k in (-7,0,7):
        d.line([x-8,y+k,x-2,y+k-4],fill=(240,246,251),width=2); d.line([x+2,y+k-4,x+8,y+k],fill=(240,246,251),width=2)
    st((x+ldx,y+ldy),label,F_X,(60,96,140),ow=2,anchor=anc)

# context road: Qus <-> Aydhab (the normal Karimi road the raiders' target sat on)
if 'Aydhab|Qus' in GEO: dashline(GEO['Aydhab|Qus'],ROAD,4,15,10)
cataract(32.87,24.07,'1st Cataract',-12,8,'ra')
cataract(31.247,21.821,'2nd Cataract',-12,7,'ra')

# THE RAID: David of Makuria strikes north out of the desert onto Aydhab
arrow((31.6,20.6),(35.9,22.25),GREEN,7)
arrow((30.85,18.6),(31.5,20.5),GREEN,6)   # up out of the Dongola heartland first
st(px(33.3,20.4),"David of Nubia's raiders",F_S,GREEN,anchor='ma')

PLACES={ # (lon,lat, colour, r, font, (dx,dy), anchor)
 'Dongola':(30.75,18.22,GREEN,8,F_C,(18,-6),'la'),
 'Faras':(31.47,22.20,GREEN,5,F_L,(-12,-4),'ra'),
 'Aswan':(32.90,24.09,GOLD,6,F_C,(14,-6),'la'),
 'Qus':(32.76,25.92,GOLD,6,F_C,(14,-6),'la'),
 'Aydhab':(36.49,22.33,GOLD,9,F_C,(-16,10),'ra'),
}
for nm,(lon,lat,col,r,f,(dx,dy),anc) in PLACES.items():
    x,y=px(lon,lat); d.ellipse([x-r,y-r,x+r,y+r],fill=col,outline=PARCH,width=2)
    st((x+dx,y+dy),nm,f,col,anchor=anc)
ax,ay=px(36.49,22.33); crossed_swords(ax,ay,1.2)
st((ax-d.textlength('SACKED, 1272',font=F_X)/2,ay+34),'SACKED, 1272',F_X,RED,ow=2)
st(px(31.6,19.6),'MAKURIA (Christian Nubia)',F_S,GREEN,anchor='ma')
st(px(35.6,26.5),'the Red Sea',F_S,(40,86,150),anchor='ma')
st(px(31.25,30.15),'to Cairo & the Sultan',F_S,INK,anchor='ma')

title='THE NUBIANS SACK AYDHAB, 1272'
tw=d.textlength(title,font=F_C)
d.rectangle([18,16,32+tw+14,54],fill=PARCH,outline=INK,width=3); d.text((32,22),title,font=F_C,fill=(140,30,20))
d.rectangle([18,70,392,214],fill=PARCH,outline=INK,width=3)
d.ellipse([34,88,52,106],fill=GREEN,outline=PARCH,width=2); d.text((62,86),'Makuria (Christian Nubia)',font=F_L,fill=GREEN)
d.ellipse([34,118,52,136],fill=GOLD,outline=PARCH,width=2); d.text((62,116),'Mamluk Egypt',font=F_L,fill=GOLD)
crossed_swords(44,182,0.5); d.text((62,172),'the sack of Aydhab',font=F_L,fill=INK)

out='../Pictures/aydhab_sack_1272.jpg'
im.save(out,quality=90); print('saved',out,im.size)
