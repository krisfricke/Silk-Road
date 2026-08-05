# gen_dongola_map.py -- THE NUBIAN THEATRE, one base map in progressive states (like the crusader coast):
#   aswan   : 1275, David of Makuria raids Aswan (Nubian strike north)
#   atwa    : 1276, Baybars storms Gebel Adda (Atwa) - the invasion begins
#   meinarti: 1276, the army takes the island fort of Meinarti at the 2nd cataract (Gebel Adda & Faras now held)
#   dongola : 1276, Dongola sacked, puppet installed (all the northern forts held)
# Reuses _nubia_bg.npy (tapered-floodplain Nubia relief). Sites coloured by who holds them; the current
# battle gets crossed swords. Permanent. Usage: python3 gen_dongola_map.py   (renders all four states)
import sys, math, numpy as np
from PIL import Image, ImageDraw, ImageFont
W,E,S0,N = 28.8, 37.2, 17.3, 30.6
OW = 880
OH = int(OW*(N-S0)/((E-W)*math.cos(math.radians((S0+N)/2))))
src=open('gen_setout_1271.py').read(); ns={}
exec(src[:src.index('def slug(')], ns); GEO=ns['GEO']

BLUE=(32,66,140); GOLD=(176,138,32); GREEN=(58,110,64); INK=(58,42,30)
ROAD=(120,60,30); PARCH=(244,233,203); RED=(176,26,20); BLADE=(46,38,28)
F_T=ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSerif-Bold.ttf',26)
F_C=ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSerif-Bold.ttf',24)
F_S=ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSerif-Italic.ttf',18)
F_L=ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSerif.ttf',19)
F_X=ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSerif-Italic.ttf',15)

# lon,lat for every site (Wikipedia / known positions)
SITE={'Aswan':(32.90,24.09),'Faras':(31.47,22.20),'Gebel Adda':(31.65,22.32),
      'Meinarti':(31.28,21.72),'Dongola':(30.75,18.22),'Qus':(32.76,25.92),'Aydhab':(36.49,22.33)}
# per-state: title, out filename, the current battle, sites already TAKEN (Mamluk gold), whether it's a
# Nubian raid (green arrow to the battle) or a Mamluk advance (gold arrow up the Nile from Aswan).
STATES={
 'aswan':   dict(title='THE NUBIANS RAID ASWAN, 1275', out='aswan_raid_1275.jpg', battle='Aswan', taken=[], raid=True),
 'atwa':    dict(title='BAYBARS INVADES NUBIA — Gebel Adda, 1276', out='atwa_1276.jpg', battle='Gebel Adda', taken=[], raid=False),
 'meinarti':dict(title='THE ADVANCE ON DONGOLA — Meinarti, 1276', out='meinarti_1276.jpg', battle='Meinarti', taken=['Gebel Adda','Faras'], raid=False),
 'dongola': dict(title='BAYBARS SACKS DONGOLA, 1276', out='dongola_map_1276.jpg', battle='Dongola', taken=['Gebel Adda','Faras','Meinarti'], raid=False),
}

def render(when):
    st_=STATES[when]
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
        for da in (0.42,-0.42): d.line([bx,by, bx-24*math.cos(ang-da), by-24*math.sin(ang-da)],fill=color,width=width)
    def swords(cx,cy,sc=1.0):
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

    if 'Aydhab|Qus' in GEO: dashline(GEO['Aydhab|Qus'],ROAD,4,15,10)   # the Karimi road, context
    cataract(32.87,24.07,'1st Cataract',-12,8,'ra'); cataract(30.98,21.48,'2nd Cataract',11,-7,'la')

    # movement arrow
    bl,bt=SITE[st_['battle']]
    if st_['raid']:
        arrow((31.6,21.6),(bl-0.15,bt-0.12),GREEN,7)
        st(px(31.9,20.7),"David of Nubia's raiders",F_S,GREEN,anchor='ma')
    else:
        ax,ay=SITE['Aswan']; arrow((ax-0.15,ay-0.25),(bl+0.1,bt+0.15),GOLD,7)
        st(px((ax+bl)/2+0.9,(ay+bt)/2),"Baybars's army",F_S,GOLD,anchor='ma')

    # sites: green = Makuria (Nubian), gold = held by Egypt/taken; battle = crossed swords
    order=['Aswan','Faras','Gebel Adda','Meinarti','Dongola']
    LOFF={'Aswan':(14,-6,'la'),'Faras':(-12,-4,'ra'),'Gebel Adda':(15,-4,'la'),'Meinarti':(15,-2,'la'),'Dongola':(18,-6,'la')}
    for nm in order:
        lon,lat=SITE[nm]; x,y=px(lon,lat)
        egy=(nm=='Aswan') or (nm in st_['taken'])       # Egyptian/Mamluk-held
        col=GOLD if egy else GREEN
        r=8 if nm in ('Aswan','Dongola') else 6
        d.ellipse([x-r,y-r,x+r,y+r],fill=col,outline=PARCH,width=2)
        dx,dy,anc=LOFF[nm]; st((x+dx,y+dy),nm,F_C if r>=8 else F_L,col,anchor=anc)
    # the current battle marker on top
    swords(*px(*SITE[st_['battle']]),1.15)
    _bl='SACKED, '+('1275' if st_['raid'] else '1276') if st_['battle'] in ('Aswan','Dongola') else ('TAKEN, 1276')
    bx,by=px(*SITE[st_['battle']]); st((bx-d.textlength(_bl,font=F_X)/2,by+34),_bl,F_X,RED,ow=2)

    st(px(31.6,19.4),'MAKURIA (Christian Nubia)',F_S,GREEN,anchor='ma')
    st(px(35.6,26.5),'the Red Sea',F_S,(40,86,150),anchor='ma')
    st(px(31.25,30.15),'to Cairo & the Sultan',F_S,INK,anchor='ma')

    title=st_['title']; tw=d.textlength(title,font=F_T)
    d.rectangle([18,16,32+tw+14,52],fill=PARCH,outline=INK,width=3); d.text((32,21),title,font=F_T,fill=(140,30,20))
    d.rectangle([18,66,352,206],fill=PARCH,outline=INK,width=3)
    d.ellipse([34,84,52,102],fill=GOLD,outline=PARCH,width=2); d.text((62,82),'Mamluk Egypt',font=F_L,fill=GOLD)
    d.ellipse([34,114,52,132],fill=GREEN,outline=PARCH,width=2); d.text((62,112),'Makuria (Christian Nubia)',font=F_L,fill=GREEN)
    swords(44,178,0.5); d.text((62,168),('the raid' if st_['raid'] else 'the battle'),font=F_L,fill=INK)

    out='../Pictures/'+st_['out']; im.save(out,quality=90); print('saved',out)

for w in ('aswan','atwa','meinarti','dongola'):
    render(w)
