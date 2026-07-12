# amber_overview.py -- Kris's verification chart: the whole Amber Road, all hubs + routes plotted.
# Composites the amber band (52-61N) over the top of the 1271 master (44-52N), draws every traced
# leg (era-coloured) and every node. Also VERIFIES sea lanes stay wet on the relief before drawing.
import numpy as np, json, os, sys
from PIL import Image, ImageDraw, ImageFont
os.chdir('/sessions/jolly-charming-gates/mnt/Silk-Road/Maps')
R=json.load(open('/sessions/jolly-charming-gates/mnt/outputs/work/routes_amber.json'))
D=json.load(open('/sessions/jolly-charming-gates/mnt/outputs/work/econ_dump_full.json'))
W,E,S,N=8.0,42.0,44.0,61.0
PPD=147.0
def load_row(man_dir):
    man=json.load(open(man_dir+'/manifest.json'))
    return man
def slice_row(man_dir,W0,E0,S0,N0):
    man=json.load(open(man_dir+'/manifest.json'))
    MW,ME,MS,MN=man['bounds']; ppd=man['ppd']; step=man['step']; n=man['n']
    x0=(W0-MW)*ppd; x1=(E0-MW)*ppd; y0=(MN-N0)*ppd; y1=(MN-S0)*ppd
    cols=[]
    for i in range(n):
        sx0=round(i*step*ppd); sx1=round((i+1)*step*ppd)
        if sx1<=x0 or sx0>=x1: continue
        im=np.array(Image.open(man_dir+'/strip_%02d.png'%i).convert('RGB'))
        a=max(0,int(x0-sx0)); b=min(im.shape[1],int(np.ceil(x1-sx0)))
        cols.append(im[int(y0):int(np.ceil(y1)), a:b])
    return np.concatenate(cols,axis=1)
top=slice_row('master_amber',W,E,52.0,N)      # 52-61N
bot=slice_row('master1271',W,E,S,52.0)        # 44-52N
w=min(top.shape[1],bot.shape[1])
img=np.concatenate([top[:,:w],bot[:,:w]],axis=0)
H_,W_=img.shape[:2]
def xy(lon,lat):
    x=(lon-W)/(E-W)*W_
    y=(N-lat)/(N-S)*H_
    return x,y
# ---- wetness check on sea lanes ----
def is_water(px):
    r,g,b=int(px[0]),int(px[1]),int(px[2])
    return b>r and b>g and b>90
fails=[]
for k,pts in R['legs'].items():
    terr=None
    for e in D['edges']:
        if '|'.join(sorted([e['a'],e['b']]))==k: terr=e['terr']; break
    if terr!='med': continue
    P=np.array(pts,float); tot=0; wet=0
    for i in range(len(P)-1):
        for t in np.linspace(0,1,60):
            lon,lat=P[i]*(1-t)+P[i+1]*t
            x,y=xy(lon,lat)
            if 0<=int(y)<H_ and 0<=int(x)<W_:
                tot+=1; wet+=is_water(img[int(y),int(x)])
    frac=wet/max(1,tot)
    if frac<0.90: fails.append((k,round(frac,2)))
print('SEA-LANE WETNESS:',len(fails),'below 90%:',fails[:10])
# ---- draw ----
pil=Image.fromarray(img); dr=ImageDraw.Draw(pil,'RGBA')
COL={'both':(120,40,20,255),'1271':(150,30,30,255),'762':(30,60,140,255)}
LEGERA={}
for e in D['edges']:
    k='|'.join(sorted([e['a'],e['b']]))
    prev=LEGERA.get(k)
    era=e['era'] or 'both'
    LEGERA[k]='both' if (prev and prev!=era) else era
def draw_leg(pts,col,wd,dash=None):
    P=[xy(a,b) for a,b in pts]
    # densify with simple chaikin for smooth curves
    for _ in range(2):
        Q=[P[0]]
        for i in range(len(P)-1):
            ax,ay=P[i]; bx,by=P[i+1]
            Q.append((ax*0.75+bx*0.25, ay*0.75+by*0.25)); Q.append((ax*0.25+bx*0.75, ay*0.25+by*0.75))
        Q.append(P[-1]); P=Q
    if dash:
        acc=0
        for i in range(len(P)-1):
            ax,ay=P[i]; bx,by=P[i+1]
            seg=((bx-ax)**2+(by-ay)**2)**0.5; acc+=seg
            if int(acc/dash)%2==0: dr.line([P[i],P[i+1]],fill=col,width=wd)
    else:
        dr.line(P,fill=col,width=wd)
TERR={ '|'.join(sorted([e['a'],e['b']])):e['terr'] for e in D['edges'] }
# era-twin legs (same water, era-variant names: Volkhov, Lovat, Dnieper, Neva) -> 'both'
SIG={}
for k,pts in R['legs'].items():
    SIG.setdefault(json.dumps(pts),[]).append(k)
for sig,keys in SIG.items():
    if len(keys)>1 and len({LEGERA.get(k,'both') for k in keys})>1:
        for k in keys: LEGERA[k]='both'
seen=set()
for k,pts in R['legs'].items():
    sig=json.dumps(pts)
    if sig in seen: continue
    seen.add(sig)
    era=LEGERA.get(k,'both'); terr=TERR.get(k,'med')
    col=COL[era]
    if terr=='med': draw_leg(pts,col,3,dash=14)          # sea lanes dashed
    elif terr=='river': draw_leg(pts,(col[0],col[1],col[2],235),4)
    else: draw_leg(pts,col,4)                             # land solid
# nodes
try: font=ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSerif-Bold.ttf',26)
except: font=ImageFont.load_default()
try: font2=ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSerif.ttf',21)
except: font2=font
SEATOWN={t['n']:t for t in D['sea']}
drawn=set()
OFF={'Roskilde':(-130,6),'Lejre':(-100,26),'Havn':(10,-30),'Lubeck':(-40,18),'Hedeby':(-120,-8),
 'Old Uppsala':(12,-32),'Uppsala':(12,4),'Birka':(-90,12),'Stockholm':(14,2),'Paviken':(-124,10),
 'Visby':(12,-24),'Vadet':(-24,-34),'Lodose':(-104,0),'Kalmar':(-104,-6),'Truso':(10,8),'Gdansk':(-40,-32),
 'Grobina':(10,-6),'Riga':(-70,10),'Reval':(-4,-34),'Turku':(-30,-36),'the Neva landing':(-70,-38),
 'Aldeigjuborg':(16,-16),'Novgorod':(16,-6),'Holmgard camp':(16,22),'Velikiye Luki':(-210,-10),
 'Luki camp':(-160,18),'Toropets':(10,-28),'Usvyaty':(-140,-4),'Vitebsk':(-130,4),'the Vitba village':(-230,28),
 'Polotsk':(-16,-36),'Polotsk camp':(-40,20),'Orsha':(-100,8),'Smolensk':(14,-8),'Gnezdovo camp':(16,18),
 'Kiev':(18,-10),'Kiev hillfort':(18,16),'Oleshye':(14,-26),'Berezan camp':(-210,-6),'Cherson':(12,10),
 'Caffa':(12,-24),'Rzhev':(8,-32),'Tver':(12,-8)}
for n,(lon,lat) in R['LL'].items():
    if n=='Constantinople': continue
    x,y=xy(lon,lat)
    if not (0<=y<H_): continue
    t=SEATOWN.get(n,{})
    era=t.get('era') or 'both'
    col=COL[era]
    r=9 if not t.get('camp') else 6
    if t.get('hub')=='' or t.get('hub') is None: r=11
    if (round(x),round(y)) in drawn:   # co-located era pairs: ring the second
        dr.ellipse([x-r-5,y-r-5,x+r+5,y+r+5],outline=col,width=3)
    else:
        dr.ellipse([x-r,y-r,x+r,y+r],fill=col,outline=(250,244,230,255),width=2)
        drawn.add((round(x),round(y)))
    ox,oy=OFF.get(n,(12,-10))
    label=n
    f=font if not t.get('camp') else font2
    dr.text((x+ox+1,y+oy+1),label,font=f,fill=(250,246,235,220))
    dr.text((x+ox,y+oy),label,font=f,fill=(40,24,12,255))
# legend + title
dr.rectangle([30,30,760,215],fill=(250,244,228,215),outline=(90,60,30,255),width=3)
dr.text((52,44),'THE AMBER ROAD — hubs & routes as plotted',font=font,fill=(40,24,12,255))
dr.line([(52,110),(150,110)],fill=COL['1271'],width=5); dr.text((165,96),'1271 legs',font=font2,fill=(40,24,12,255))
dr.line([(52,145),(150,145)],fill=COL['762'],width=5); dr.text((165,131),'762 legs',font=font2,fill=(40,24,12,255))
dr.line([(52,180),(150,180)],fill=COL['both'],width=5); dr.text((165,166),'both eras · dashed = sea lane, solid = river/land',font=font2,fill=(40,24,12,255))
# exit labels
def exlab(lon,lat,txt):
    x,y=xy(lon,lat); dr.text((x,y),txt,font=font2,fill=(60,30,16,255))
exlab(29.6,44.6,'to Constantinople \u2193')
exlab(36.7,56.9,'down the Volga \u2192 (Bolghar, Sarai \u2014 planned)')
out=pil.resize((2400,int(H_*2400/W_)),Image.LANCZOS)
out.save('/sessions/jolly-charming-gates/mnt/outputs/work/amber_overview.png')
print('overview saved',out.size)
