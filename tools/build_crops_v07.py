"""Code-native side-view plants, stable roots, processed by pinned FrameRonin."""
import json,hashlib
from PIL import Image,ImageDraw
from pixelize_art_v04 import convert,ROOT,records,COLORS
out=ROOT/'assets/pixel-v07';out.mkdir(exist_ok=True)
atlas=Image.new('RGBA',(112,756))
for variety in range(3):
 for kind in range(3):
  for stage in range(4):
   for frame in range(3):
    im=Image.new('RGBA',(112,112));d=ImageDraw.Draw(im)
    shift=[0,1,0][frame]
    def rect(box,col):
     x,y,r,b=box;d.rectangle((x*4,y*4,r*4+3,b*4+3),fill=col)
    def poly(points,col):d.polygon([(x*4,y*4) for x,y in points],fill=col)
    def leaf(x,y,flip=1):
     x+=shift+variety-1;poly([(x,y+4),(x-6*flip,y),(x-5*flip,y+4),(x,y+6)],'#35553b')
     poly([(x,y+3),(x-5*flip,y),(x-3*flip,y+3),(x,y+4)],'#91ac58')
    # Soil contact is always row 27. Stage zero is a planted seed, never a floating bag.
    if stage==0:
     rect((11,26,16,27),'#60443a');rect((13,26,15,26),'#bb8e5c')
    elif stage==1:
     rect((13,22,14,27),'#35553b');leaf(13,20);leaf(14,18,-1)
    elif stage==2:
     # Unripe silhouettes: open foliage and buds, with no full-size harvestable produce.
     if kind==0:
      rect((13,17,14,27),'#35553b');leaf(13,16);leaf(14,14,-1);leaf(13,11)
      rect((12,25,15,25),'#895a30')
     elif kind==1:
      rect((13,22,14,27),'#35553b');leaf(12,18);leaf(15,18,-1);leaf(13,15);leaf(14,14,-1)
      rect((12,22,16,24),'#6a8b48');rect((13,21,15,22),'#91ac58')
     else:
      rect((13,13,14,27),'#35553b');leaf(13,12);leaf(14,17,-1);leaf(13,21)
      rect((17,18,19,20),'#35553b');rect((17,18,18,19),'#6a8b48')
      rect((10,15,11,16),'#f5c86c')
    elif kind==0:
     poly([(9,15),(19,15),(18,22),(14,27),(10,22)],'#895a30')
     poly([(10,16),(18,16),(17,22),(14,26),(11,22)],'#dca04a')
     rect((12,18,13,22),'#f5c86c');rect((15,20,17,20),'#b57b35')
     rect((13,12,14,17),'#35553b');leaf(13,9);leaf(14,7,-1);leaf(13,5)
     if stage==3:leaf(14,3,-1)
     rect((10,18,12,19),'#f5c86c');rect((16,21,18,21),'#b57b35');rect((12,24,13,24),'#b57b35')
    elif kind==1:
     poly([(5,20),(7,15),(12,13),(18,14),(23,19),(21,25),(15,27),(8,25)],'#35553b')
     poly([(6,20),(9,16),(14,15),(20,17),(22,22),(18,26),(11,26)],'#6a8b48')
     poly([(8,18),(13,14),(18,16),(20,21),(17,24),(11,24)],'#91ac58')
     poly([(11,17),(15,16),(18,19),(17,22),(13,23),(10,20)],'#bdd078')
     rect((13,18,14,20),'#e3d5a9');leaf(7,20);leaf(21,20,-1)
     rect((9,20,10,23),'#4c6f3e');rect((17,18,18,21),'#6a8b48');rect((12,22,15,22),'#91ac58');
     if variety==1:leaf(8,18)
     if variety==2:leaf(20,18,-1)
    else:
     rect((13,7,14,27),'#35553b');rect((14,8,14,25),'#6a8b48')
     leaf(13,5);leaf(14,10,-1);leaf(13,16);leaf(14,19,-1)
     for x,y in [[(6,12),(18,16),(9,22)],[(6,12),(18,14),(7,21),(18,22)],[(8,11),(18,17),(8,22)]][variety]:
      col='#bc6261' if stage==3 else '#6a8b48'
      rect((x,y,x+4,y+4),'#6b393d' if stage==3 else '#35553b');rect((x,y,x+3,y+3),col)
      rect((x+1,y,x+1,y),'#e38d7c' if stage==3 else '#bdd078')
      rect((x+1,y-1,x+2,y-1),'#35553b')
    if stage>0:d.rectangle((0,104,111,111),fill=(0,0,0,0))
    if stage>0:rect((13,26,14,27),'#895a30' if kind==0 and stage>=2 else '#35553b')
    atlas.paste(convert(im,[0,0,112,112],(28,28),f'plant-{variety}-{kind}-{stage}-{frame}'),(stage*28,(variety*9+kind*3+frame)*28))
atlas.save(out/'crops.png')
# Moist opened earth: irregular clods and shallow furrows above a layered soil cutaway.
im=Image.new('RGBA',(144,56));d=ImageDraw.Draw(im)
def r(box,col):
 x,y,a,b=box;d.rectangle((x*4,y*4,a*4+3,b*4+3),fill=col)
r((0,0,35,13),'#60443a');r((0,0,35,1),'#9b6c47');r((0,3,35,3),'#4b3936');r((0,12,35,13),'#4b3936')
for x in range(2,35,7):
 r((x,0,x+3,0),'#bb8e5c');r((x+1,2,x+4,2),'#7b5740');r((x,6,x+2,6),'#7b5740');r((x+2,9,x+3,10),'#9b6c47')
convert(im,[0,0,144,56],(36,14),'tilled-earth').save(out/'tilled.png')
(out/'manifest.json').write_text(json.dumps({'frameSize':28,'frames':3,'varieties':3,'rootY':28,'palette':COLORS,'records':records,'sha256':{f:hashlib.sha256((out/f).read_bytes()).hexdigest() for f in ['crops.png','tilled.png']}},indent=2))
print('109 processed plant/soil assets; fixed 28px root anchors; binary alpha.')
