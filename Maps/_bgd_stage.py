import sys, math, numpy as np
from PIL import Image
src=open('gen_setout_1271.py').read(); ns={}
exec(src[:src.index('def slug(')], ns)
W,E,S0,N=34.68,54.16,28.76,38.96
OW=1400; OH=int(OW*(N-S0)/((E-W)*math.cos(math.radians((S0+N)/2))))
half=int(sys.argv[1]); mid=(W+E)/2; hw=OW//2
if half==0: bg=ns['gebco_relief'](W,mid,S0,N,hw,OH)
else:       bg=ns['gebco_relief'](mid,E,S0,N,OW-hw,OH)
a=np.asarray(bg,np.uint8) if not isinstance(bg,Image.Image) else np.asarray(bg.convert('RGB'))
np.save('_bgd_bg_%d.npy'%half,a); print('half',half,'done',a.shape)
