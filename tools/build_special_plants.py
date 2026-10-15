"""Original pixel shapes: eight selectable plants and four hidden mature forms."""
import json,hashlib
from PIL import Image,ImageDraw
from pixelize_art_v04 import ROOT,convert,COLORS,records
out=ROOT/'assets/pixel-v07';atlas=Image.new('RGBA',(112,1008))
names=['南瓜','玉米','茄子','草莓','向日葵','月光花','水晶菇','星灯草','黄金萝卜','月玉卷心菜','星露番茄','琥珀南瓜']
for kind in range(12):
 for stage in range(4):
  for frame in range(3):
   im=Image.new('RGBA',(112,112));d=ImageDraw.Draw(im);shift=[0,1,0][frame]
   def box(b,col):
    x,y,r,t=b;d.rectangle((x*4,y*4,r*4+3,t*4+3),fill=col)
   def poly(p,col):d.polygon([(x*4,y*4) for x,y in p],fill=col)
   def leaf(x,y):
    poly([(13,y+5),(x+shift,y),(x+shift,y+3),(14,y+7)],'#4c6f3e');box((13,y+3,14,y+6),'#6a8b48')
   if stage==0:box((11,26,16,27),'#60443a');box((13,26,15,26),'#bb8e5c')
   else:
    box((13,17 if stage<3 else 9,14,27),'#35553b');leaf(7,20);leaf(20,18)
    if stage==1:pass
    elif stage==2:
     leaf(7,14);leaf(20,12);box((12,12,15,14),'#91ac58')
     if kind>=5:box((13,11,14,12),'#77a0ae')
    else:
     if kind in (0,11):
      poly([(5,17),(8,13),(19,13),(23,17),(22,23),(18,25),(9,25),(5,22)],'#895a30')
      box((7,16,21,22),'#dca04a');box((10,14,18,24),'#b57b35')
      for x in (9,13,17):box((x,16,x,22),'#f5c86c' if kind==11 else '#dca04a')
      box((13,11,15,14),'#4c6f3e')
     elif kind==1:
      box((11,6,16,22),'#895a30');box((12,7,15,21),'#f5c86c')
      for y in (8,11,14,17):box((12,y,13,y),'#ffe3a3')
      poly([(11,24),(6,14),(10,18),(13,25)],'#6a8b48');poly([(14,25),(21,13),(19,22)],'#91ac58')
     elif kind==2:
      leaf(7,10);leaf(21,10)
      for x,y in [(6,16),(17,14)]:
       box((x,y,x+5,y+7),'#26374b');box((x+1,y+1,x+4,y+6),'#686575');box((x+2,y+1,x+2,y+3),'#b8a7bb');box((x+1,y-1,x+4,y),'#4c6f3e')
     elif kind in (3,10):
      for x,y in [(5,18),(17,19),(11,12)]:
       poly([(x,y),(x+6,y),(x+5,y+5),(x+3,y+7),(x+1,y+5)],'#93464a' if kind==3 else '#37536a')
       box((x+1,y+1,x+5,y+3),'#e38d7c' if kind==3 else '#77a0ae')
       box((x+2,y+2,x+2,y+2),'#ffe3a3');box((x+1,y-1,x+4,y),'#4c6f3e')
     elif kind in (4,5):
      box((13,8,14,25),'#4c6f3e');leaf(6,16);leaf(21,17)
      for b in [(10,3,17,5),(7,6,20,10),(10,11,17,13)]:box(b,'#dca04a' if kind==4 else '#77a0ae')
      box((10,6,17,10),'#60443a' if kind==4 else '#b0c9c7');box((12,7,15,9),'#9b6c47' if kind==4 else '#f7f1dc')
     elif kind==6:
      box((12,16,15,26),'#b0c9c7');poly([(4,15),(8,7),(18,6),(24,15)],'#37536a');poly([(7,14),(11,8),(18,8),(21,14)],'#8cb6ad')
      box((10,11,11,12),'#f7f1dc');box((18,12,19,13),'#b0c9c7')
     elif kind==7:
      for x,y in [(7,12),(19,9),(13,4)]:
       box((x,y,x+1,y+6),'#dca04a');box((x-2,y+2,x+3,y+3),'#f5c86c');box((x,y+2,x+1,y+3),'#f7f1dc')
     elif kind==8:
      poly([(9,12),(19,12),(18,22),(14,27),(10,22)],'#895a30');poly([(10,13),(18,13),(16,23),(14,26),(11,22)],'#f5c86c');box((11,14,12,19),'#ffe3a3');leaf(6,4);leaf(21,3)
     elif kind==9:
      poly([(5,19),(9,12),(18,12),(23,19),(20,25),(8,25)],'#37536a');box((8,16,20,22),'#8cb6ad');box((11,14,17,23),'#b0c9c7');box((13,17,16,20),'#f7f1dc')
    d.rectangle((0,104,111,111),fill=(0,0,0,0));box((13,26,14,27),'#35553b')
   atlas.paste(convert(im,[0,0,112,112],(28,28),f'extra-{kind}-{stage}-{frame}'),(stage*28,(kind*3+frame)*28))
atlas.save(out/'specials.png')
(out/'specials.json').write_text(json.dumps({'names':names,'selectable':8,'hidden':4,'records':records,'palette':COLORS,'sha256':hashlib.sha256((out/'specials.png').read_bytes()).hexdigest()},ensure_ascii=False,indent=2),encoding='utf-8')
print('144 processed special-plant frames.')
