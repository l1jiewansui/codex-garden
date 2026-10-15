"""Author a tileable code-native terrain texture through the pinned pixel pipeline."""
import json, hashlib
from PIL import Image, ImageDraw
from pixelize_art_v04 import convert, ROOT, records

out=ROOT/'assets/pixel-v05'
out.mkdir(exist_ok=True)
source=Image.new('RGBA',(64,56))
d=ImageDraw.Draw(source)
d.rectangle((0,0,63,55),fill='#60443a')
d.rectangle((0,0,63,7),fill='#4c6f3e')
d.rectangle((0,0,63,3),fill='#91ac58')
for x in range(0,64,8):
    d.rectangle((x,4,x+3,11),fill='#6a8b48')
for x,y in [(4,20),(28,16),(48,28),(16,40),(40,44),(56,48)]:
    d.rectangle((x,y,x+7,y+3),fill='#9b6c47')
    d.rectangle((x+4,y+4,x+7,y+7),fill='#7b5740')
d.rectangle((0,52,63,55),fill='#4b3936')
tile=convert(source,[0,0,64,56],(16,14),'continuous-garden-ground')
tile.save(out/'land.png')
# Side-view farm corner; every coordinate is on a four-pixel authoring grid.
farm=Image.new('RGBA',(144,80));pen=ImageDraw.Draw(farm)
def rect(box,color):
    x,y,r,b=box;pen.rectangle((x*4,y*4,r*4+3,b*4+3),fill=color)
# Upright spade resting on the soil.
rect((4,0,7,1),'#60443a');rect((4,2,4,3),'#60443a');rect((7,2,7,3),'#60443a')
rect((5,3,6,15),'#bb8e5c');rect((3,15,8,18),'#4d7387');rect((4,19,7,19),'#37536a')
# Wooden produce crate, planted directly on the common ground baseline.
rect((10,10,23,19),'#60443a');rect((11,11,22,18),'#bb8e5c')
for y in (12,15,18):rect((11,y,22,y),'#7b5740')
rect((11,11,12,18),'#dca04a');rect((21,11,22,18),'#9b6c47')
rect((15,11,18,12),'#60443a')
# Metal watering can, handle and raised spout.
rect((26,9,30,9),'#37536a');rect((25,10,25,13),'#37536a');rect((31,10,31,13),'#37536a')
rect((25,14,31,18),'#37536a');rect((26,14,30,17),'#77a0ae')
rect((31,14,32,15),'#4d7387');rect((33,12,33,14),'#4d7387');rect((34,11,35,12),'#b0c9c7')
rect((25,19,31,19),'#26374b')
convert(farm,[0,0,144,80],(36,20),'fixed-left-farm-supplies').save(out/'farm-supplies.png')
# Six aligned, palette-constrained sunshine frames; alternating rays form a gentle shimmer.
sun=Image.new('RGBA',(16*6,16))
for frame in range(6):
    sourceSun=Image.new('RGBA',(64,64));sp=ImageDraw.Draw(sourceSun)
    def box(coords,color):
        x,y,r,b=coords;sp.rectangle((x*4,y*4,r*4+3,b*4+3),fill=color)
    long=frame%3==0
    for boxCoords in [(7,0 if long else 1,8,2),(7,13,8,15 if long else 14),(0 if long else 1,7,2,8),(13,7,15 if long else 14,8),(2,2,3,3),(12,2,13,3),(2,12,3,13),(12,12,13,13)]:box(boxCoords,'#dca04a')
    box((5,3,10,12),'#895a30');box((3,5,12,10),'#895a30')
    box((5,4,10,11),'#f5c86c');box((4,5,11,10),'#f5c86c')
    box((5,5,8,6),'#ffe3a3');box((5,7,6,8),'#ffe3a3')
    if frame!=4:
        box((6,8,6,8),'#60443a');box((9,8,9,8),'#60443a')
    else:
        box((6,9,6,9),'#60443a');box((9,9,9,9),'#60443a')
    box((7,10,8,10),'#b57b35')
    sun.paste(convert(sourceSun,[0,0,64,64],(16,16),'sun-anchor-'+str(frame)),(16*frame,0))
sun.save(out/'sun.png')
(out/'pixel-checks.json').write_text(json.dumps({'records':records,'sha256':hashlib.sha256((out/'land.png').read_bytes()).hexdigest()},indent=2))
print('Ground texture: pinned FrameRonin, shared palette, binary alpha, 16x14.')
