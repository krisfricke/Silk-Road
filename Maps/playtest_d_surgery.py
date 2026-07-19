# playtest_d_surgery.py (Kris 7/17, round 2)
import re
s = open('index.html', encoding='utf-8').read()

# ---- 1. naphtha burns anywhere it travels (Kris: a knocked lamp doesn't check the terrain) ----
old = "function buildEvent(terr){\n  const pool=[];\n  const add=(w,f)=>{for(let i=0;i<w;i++)pool.push(f)};"
assert s.count(old) == 1
s = s.replace(old, old + "\n  { var _nphA=(S.goods&&S.goods.naphtha)||0; if(_nphA>0 && rnd()<0.35) add(1, evCampFire); } /* Kris: naphtha is naphtha on any road; the 90-day cooldown keeps it rare */", 1)
old = "if(_nph>0 && rnd()<0.45) add(1, evCampFire); /* Kris 7/17: -25% - naphtha must be a trade, not a curse */"
assert s.count(old) == 1
s = s.replace(old, "/* naphtha fire moved to the universal pool head (Kris): terrain-blind */", 1)

# ---- 2. Balkh's tavern rerolled ----
old = "'Balkh':'The Mother of Cities'"
assert s.count(old) == 1
s = s.replace(old, "'Balkh':'The Melon Garden'", 1)  # Balkh's melons were famous across the east

# ---- 3. treasury promotions: ten more full purses; Abaskun stays limited ----
def promote(s, name):
    hits = 0
    for pat in ("name:'%s'" % name, 'name:"%s"' % name):
        start = 0
        while True:
            i = s.find(pat, start)
            if i < 0: break
            seg = s[i:i+1800]
            seg2 = re.sub(r"hub:'minor',\s*(cash:\d+,\s*)?", '', seg, count=1)
            if seg2 != seg:
                s = s[:i] + seg2 + s[i+1800:]; hits += 1
            start = i + 10
    return s, hits
total = 0
for nm in ('Erzurum','Yazd','Otrar','Balkh','Badakhshan','Lop','Karakorum','Ningxia','Tenduc','Damghan'):
    s, h = promote(s, nm)
    assert h >= 1, 'no minor flag found on ' + nm
    total += h
print('promoted 10 cities (%d node records)' % total)

# ---- 4. Polo pass-by polish: a true detail for each stretch of their road ----
anchor = "S.onceFlags.poloMet=true; if(typeof ach==='function')ach('polosMet');"
assert s.count(anchor) == 1
s = s.replace(anchor, anchor + '''
  var POLO_LEGNOTE={
   'Ayas|Sivas':"They are barely a month out of Acre, the sea-salt still on their baggage, and the letters of Pope Gregory carried like glass.",
   'Erzurum|Sivas':"They ask what the road east is like, and listen to the answer like men memorizing it.",
   'Erzurum|Tabriz':"The older two compare Tabriz prices from their FIRST crossing, fifteen years gone, and are pleased to find themselves still right.",
   'Baghdad|Tabriz':"They speak carefully of the Ilkhan's peace, and keep the Pope's letters buried in a flour sack.",
   'Tabriz|Varamin':"The young one has begun keeping a tally of caravanserais in his head; he recites it, flawlessly, when asked.",
   'Varamin|Yazd':"They travel the kavir stages by night, as you do, and Marco wants to know if the desert is like this all the way to Cathay.",
   'Kerman|Yazd':"Marco turns a Kerman turquoise in his fingers and asks its price in three cities you have been to and two you have not.",
   'Hormuz|Kerman':"They have turned BACK from Hormuz \\u2014 the ships there, the elder says flatly, are sewn with cord and not worth three lives and the Pope's letters. Overland, then, the whole way.",
   'Herat|Kerman':"They ride the Lut's rim stages grim and short-spoken, and thaw only when the talk turns to profits.",
   'Balkh|Herat':"At Balkh the young one walked the broken walls a whole evening, the elder says, as if ruin were a thing that could be learned.",
   'Badakhshan|Balkh':"The young one is thin and coughs \\u2014 the low-country fever, the elders say; they mean to rest him in the high valleys, however long it takes.",
   'Badakhshan|Kashgar':"Marco is brown and well again \\u2014 a year in the Badakhshan air, he says, would raise the dead; he says it like a man quoting his own book.",
   'Kashgar|Yarkand':"They fall in with your column through the oasis stages, and Marco prices every bolt of cloth in the bazaar from memory.",
   'Khotan|Yarkand':"Marco asks to see river-jade pulled from the water with his own eyes, and is late to camp for it.",
   'Khotan|Lop':"They are provisioning like men who have been warned: a month of sand ahead, and the elder counts the water-skins twice.",
   'Dunhuang|Lop':"They speak low of the desert voices \\u2014 drums in the empty dunes at night \\u2014 and the young one will NOT admit he is afraid.",
   'Dunhuang|Jiuquan':"They have seen the painted caves and the young one cannot stop describing them \\u2014 a thousand Buddhas, he says, holding up his hands.",
   'Jiuquan|Zhangye':"They talk of wintering at Ganzhou \\u2014 the great sleeping Buddha there, and the Khan's summons that will not wait forever."};''', 1)
old = "]}; })();\n  render(); return true; }\nfunction checkNephewMarmot(){"
assert s.count(old) == 1
s = s.replace(old, "]}; })();\n  if(POLO_LEGNOTE[k]&&S.pendingEvent&&S.pendingEvent.t){ S.pendingEvent.t+=' '+POLO_LEGNOTE[k]; }\n  render(); return true; }\nfunction checkNephewMarmot(){", 1)

oldv = "const VERSION='3.1.75'; const BUILD='0717.1040';"
assert s.count(oldv) == 1
s = s.replace(oldv, "const VERSION='3.1.76'; const BUILD='0717.1110';")
open('index.html', 'w', encoding='utf-8').write(s)
print('SURGERY D COMPLETE, v3.1.76')
