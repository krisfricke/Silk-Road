# gen_mamluk_coast_maps.py -- the end of Outremer on the Syrian coast:
#   the FALL OF TRIPOLI (27 April 1289, Qalawun) and the FALL OF ACRE (18 May 1291, al-Ashraf Khalil).
# Reuses the crusader Syrian-coast relief bake (_levant_bg.npy) -- "the same map that carried the falling
# fortresses" (Kris). gebco_relief bg + real routes from GEO + the crossed-swords assault marker.
# Permanent. Usage: python3 gen_mamluk_coast_maps.py [tripoli|acre|both]   (needs _levant_bg.npy)
import sys, math, numpy as np
from PIL import Image, ImageDraw, ImageFont

W,E,S0,N = 34.55, 37.45, 32.30, 35.55
OW = 1000
OH = int(OW*(N-S0)/((E-W)*math.cos(math.radians((S0+N)/2))))
src=open('gen_setout_1271.py').read(); ns={}
exec(src[:src.index('def slug(')], ns); GEO=ns['GEO']

BLUE=(32,66,140); GOLD=(176,138,32); INK=(58,42,30)
ROAD=(112,50,26); PARCH=(244,233,203); RED=(176,26,20); GREY=(78,78,82); BLADE=(46,38,28)
F_T=ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSerif-Bold.ttf',31)
F_C=ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSerif-Bold.ttf',24)
F_S=ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSerif-Italic.ttf',18)
F_L=ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSerif.ttf',20)

def px(lon,lat): return ((lon-W)/(E-W)*OW,(N-lat)/(N-S0)*OH)

def make(which):
    im=Image.fromarray(np.load('_levant_bg.npy')).convert('RGB'); d=ImageDraw.Draw(im)
    def st(xy,txt,f,fill,ow=2,anchor='la'):
        x,y=xy
        if anchor=='ra': x-=d.textlength(txt,font=f)
        elif anchor=='ma': x-=d.textlength(txt,font=f)/2
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
    def town(lon,lat,col,r,name,sub,dx,dy,anc='la'):
        x,y=px(lon,lat); d.ellipse([x-r,y-r,x+r,y+r],fill=col,outline=PARCH,width=2)
        st((x+dx,y+dy),name,F_C,col,anchor=anc)
        if sub: st((x+dx,y+dy+24),sub,F_S,col,anchor=anc)

    for k in ('Acre|Damascus','Aleppo|Damascus','Acre|Jerusalem'):
        if k in GEO: dashline(GEO[k],ROAD,4,14,9)

    if which=='tripoli':
        # the shrinking Frankish coast, spring 1289
        town(36.295,34.757,GOLD,6,'Krak des Chevaliers','fell 1271',30,-8)
        town(35.95,35.15, GOLD,6,'Margat','Hospitaller — fell 1285',18,-30)
        town(35.89,34.89, BLUE,6,'Tortosa','Templar — still holds',18,4)
        town(35.50,33.89, BLUE,6,'Beirut','still holds',18,-8)
        town(35.07,32.93, BLUE,8,'Acre','the last great port — still holds',16,10)
        # Tripoli: stormed
        tx,ty=px(35.84,34.44); d.ellipse([tx-8,ty-8,tx+8,ty+8],fill=GOLD,outline=PARCH,width=2)
        st((tx-14,ty-30),'Tripoli',F_C,GOLD,anchor='ra'); st((tx-14,ty-6),'stormed by Qalawun, Apr 1289',F_S,GOLD,anchor='ra')
        crossed_swords(tx,ty,1.15)
        title='THE SYRIAN COAST — the Fall of Tripoli, April 1289'
        legend=[('Mamluk-taken',GOLD),('Frankish (still held)',BLUE)]
        sub2='The County of Tripoli is extinguished; Acre stands nearly alone.'
    else:
        # 1291: the whole coast goes
        town(35.84,34.44, GOLD,6,'Tripoli','fell 1289',18,-30)
        town(35.89,34.89, GOLD,6,'Tortosa','abandoned, Aug 1291',18,4)
        town(35.50,33.89, GOLD,6,'Beirut','abandoned, 1291',18,-8)
        town(35.37,33.56, GOLD,5,'Sidon','abandoned, 1291',16,-6)
        town(35.19,33.27, GOLD,5,'Tyre','abandoned, 1291',16,-4)
        town(34.94,32.70, GOLD,5,'’Atlit','last to fall, Aug 1291',16,6)
        # Acre: stormed
        tx,ty=px(35.07,32.93); d.ellipse([tx-9,ty-9,tx+9,ty+9],fill=GOLD,outline=PARCH,width=2)
        st((tx+18,ty+8),'ACRE',F_T,GOLD); st((tx+18,ty+40),'stormed 18 May 1291',F_S,GOLD)
        crossed_swords(tx,ty,1.3)
        title='THE FALL OF ACRE, 18 May 1291 — the end of Outremer'
        legend=[('Mamluk-taken / abandoned',GOLD)]
        sub2='The Kingdom of Jerusalem is no more; the Latin East is ended.'

    tw=d.textlength(title,font=F_C)
    d.rectangle([20,18,34+tw+16,60],fill=PARCH,outline=INK,width=3); d.text((34,26),title,font=F_C,fill=(140,30,20))
    lh=44+len(legend)*32
    d.rectangle([20,78,412,78+lh],fill=PARCH,outline=INK,width=3)
    yy=96
    for lab,col in legend:
        d.ellipse([36,yy,56,yy+20],fill=col,outline=PARCH,width=2); d.text((66,yy),lab,font=F_L,fill=col); yy+=32
    crossed_swords(46,yy+10,0.5); d.text((66,yy),'the assault',font=F_L,fill=INK); yy+=30
    d.text((34,yy),sub2,font=F_S,fill=INK)

    out='../Pictures/%s'%('tripoli_fall_1289.jpg' if which=='tripoli' else 'acre_fall_1291.jpg')
    im.save(out,quality=90); print('saved',out,im.size)

which=sys.argv[1] if len(sys.argv)>1 else 'both'
for w in (('tripoli','acre') if which=='both' else (which,)):
    make(w)
