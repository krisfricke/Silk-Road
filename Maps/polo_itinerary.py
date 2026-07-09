# polo_itinerary.py -- the Polos' day-precise itinerary over OUR travel network (Zaiton, Kris's spec).
# Day 1 = 17 Mar 1271 (game start). They leave Venice on day 2, one day behind the player.
# Anchors: Acre & the legate Teobaldo; Jerusalem for the oil of the Sepulchre; recalled from Ayas when
# Teobaldo becomes Gregory X; Tabriz winter; the Hormuz sewn-ships refusal; Marco's year-long illness in
# Badakhshan; the attested year at Ganzhou; XANADU ~1 MAY 1275 (game day ~1506). Travel legs use our
# live edge day-counts; stays are attested where sources speak and plausible where they are silent.
LEGS={('Venice','Ragusa'):5,('Ragusa','Candia'):9,('Candia','Acre'):6,('Acre','Jerusalem'):3,
 ('Acre','Ayas'):4,('Ayas','Sivas'):12,('Sivas','Erzurum'):12,('Erzurum','Tabriz'):12,
 ('Tabriz','Yazd'):22,('Yazd','Kerman'):10,('Kerman','Hormuz'):12,('Kerman','Herat'):22,
 ('Herat','Balkh'):14,('Balkh','Badakhshan'):10,('Badakhshan','Kashgar'):18,('Kashgar','Yarkand'):5,
 ('Yarkand','Khotan'):8,('Khotan','Lop'):22,('Lop','Dunhuang'):12,('Dunhuang','Jiuquan'):8,
 ('Jiuquan','Zhangye'):5,('Zhangye','Ningxia'):12,('Ningxia','Tenduc'):14,('Tenduc','Xanadu'):10}
def d(a,b): return LEGS.get((a,b)) or LEGS[(b,a)]
PLAN=[('Venice',1),('Ragusa',1),('Candia',2),('Acre',30),('Jerusalem',3),('Acre',6),('Ayas',10),
 ('Acre',20),('Ayas',20),('Sivas',3),('Erzurum',3),('Tabriz',90),('Yazd',4),('Kerman',30),
 ('Hormuz',20),('Kerman',8),('Herat',10),('Balkh',5),('Badakhshan',460),('Kashgar',20),('Yarkand',3),
 ('Khotan',15),('Lop',7),('Dunhuang',10),('Jiuquan',3),('Zhangye',None),('Ningxia',3),('Tenduc',3),('Xanadu',None)]
TARGET_XANADU=1506   # ~1 May 1275
# forward pass with Zhangye as the free variable
fixed=0; travel=0
prev=None
for i,(p,st) in enumerate(PLAN):
    if prev: travel+=d(prev,p)
    if st: fixed+=st
    prev=p
zhangye=TARGET_XANADU-(1+travel+fixed)   # day1 is Venice day; depart day2 handled by stay=1
assert 380<=zhangye<=470, zhangye
rows=[]; day=1; prev=None
for p,st in PLAN:
    if prev: day+=d(prev,p)
    stay=st if st is not None else (zhangye if p=='Zhangye' else 0)
    a=day; b=day+max(0,stay)-1 if stay else day
    rows.append((a,b if stay else a,p))
    day=b+1 if stay else day
    prev=p
import json
print('Ganzhou stay:',zhangye,'days (~%.1f yr)'%(zhangye/365))
for a,b,p in rows: print('%5d-%5d  %s'%(a,b,p))
json.dump(rows,open('polo_itin.json','w'))
print('Xanadu arrival day', rows[-1][0])
