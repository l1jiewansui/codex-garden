"""Original pixel plants, six rooted animation frames per stage. No AI/assets API."""
from pathlib import Path
from PIL import Image,ImageDraw
import math,json,hashlib
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'assets/pixel-fantasy';OUT.mkdir(exist_ok=True)
NAMES=['豌豆炮手','双荚炮手','火炬辣椒','铃铛蘑菇','捕虫花','星月莲']
P={'ink':'#25252f','dark':'#263f35','stem':'#35553b','leaf':'#4c6f3e','green':'#6a8b48','lime':'#91ac58','light':'#bdd078','cream':'#f7f1dc','blue':'#37536a','sky':'#77a0ae','ice':'#b0c9c7','red':'#bc6261','hot':'#e38d7c','gold':'#f5c86c','orange':'#dca04a','purple':'#686575','violet':'#90879d','pink':'#d49b9c'}
def mature(kind,frame):
 im=Image.new('RGBA',(28,28));d=ImageDraw.Draw(im)
 def poly(points,c):d.polygon(points,fill=P[c])
 def box(rect,c):d.rectangle(rect,fill=P[c])
 def oval(rect,c,outline='ink'):d.ellipse(rect,fill=P[c],outline=P[outline] if outline else None)
 poly([(13,27),(7,26),(3,23),(3,21),(7,21),(13,24),(17,22),(24,21),(22,25),(16,27)],'ink')
 poly([(13,26),(6,24),(5,22),(10,23),(14,25),(19,23),(23,22),(20,25)],'leaf');box((13,13,15,26),'dark');box((14,14,14,25),'green')
 if kind in (0,1):
  def pea(cx,cy,blue=False):
   dark,base,hi=('blue','sky','ice') if blue else ('leaf','lime','light')
   oval((cx-7,cy-6,cx+5,cy+5),base);oval((cx-5,cy-5,cx+3,cy+2),hi,None)
   poly([(cx+1,cy-3),(cx+8,cy-4),(cx+10,cy-2),(cx+10,cy+3),(cx+7,cy+5),(cx+1,cy+3)],'ink')
   box((cx+2,cy-2,cx+7,cy+2),base);oval((cx+6,cy-3,cx+11,cy+4),dark);box((cx+8,cy-1,cx+10,cy+2),'ink');box((cx+7,cy-2,cx+9,cy-2),hi)
   if frame!=5:box((cx-3,cy-2,cx-2,cy),'ink');box((cx-3,cy-2,cx-3,cy-2),'cream')
   else:box((cx-4,cy,cx-2,cy),'ink')
   poly([(cx-3,cy-5),(cx-6,cy-8),(cx-2,cy-7),(cx,cy-5)],dark)
  if kind==0:pea(12,11)
  else:box((10,11,12,23),'dark');pea(10,8,True);pea(14,17)
 elif kind==2:
  poly([(12,24),(8,22),(7,18),(8,12),(11,7),(17,6),(20,9),(20,15),(17,20)],'ink')
  poly([(12,22),(9,20),(9,15),(12,9),(17,8),(18,10),(18,15),(15,20)],'red');box((11,12,12,18),'hot');box((15,10,16,12),'cream')
  poly([(12,8),(10,5),(14,6),(16,3),(18,6),(20,6),(17,9)],'leaf')
  flame=frame%3;poly([(8,10),(4,7),(6,2+flame),(8,5),(10,1),(11,7)],'orange');poly([(7,8),(7,5),(9,4),(9,8)],'gold')
  box((15,16,15,17),'ink');box((18,15,18,16),'ink')
 elif kind==3:
  box((11,13,16,24),'ink');box((12,14,15,23),'cream');box((12,21,14,23),'pink')
  poly([(4,16),(4,11),(7,6),(11,4),(17,4),(22,8),(24,14),(22,18),(18,16),(14,19),(10,16),(6,18)],'ink')
  poly([(5,14),(7,9),(11,6),(17,6),(21,10),(22,15),(18,14),(14,17),(10,14)],'violet');box((8,10,10,11),'cream');box((16,8,18,9),'pink');box((18,13,20,14),'cream')
  box((12,19,12,20),'ink');box((15,19,15,20),'ink')
 elif kind==4:
  oval((5,3,23,19),'purple');poly([(7,7),(12,4),(19,5),(22,10),(20,16),(13,18),(7,14)],'red')
  gap=frame%3;poly([(7,9),(13,10+gap),(21,8),(20,14),(13,16),(8,13)],'ink')
  for x in (9,13,17):poly([(x,10),(x+2,10),(x+1,12)],'cream')
  for x in (11,15,18):poly([(x,15),(x+2,14),(x+1,12)],'cream')
  poly([(5,9),(3,5),(7,7)],'lime');poly([(22,8),(25,4),(24,11)],'green')
 elif kind==5:
  poly([(4,19),(3,13),(10,15),(13,8),(17,15),(24,11),(23,19),(18,23),(11,24)],'ink')
  poly([(5,16),(11,18),(13,12),(16,18),(22,14),(21,19),(17,21),(11,22)],'sky');poly([(9,18),(13,15),(17,20),(14,22)],'ice')
  oval((8,2,17,11),'gold');oval((12,1,19,8),'ink');box((8,7,9,8),'cream')
  x,y=21,4+frame%2;box((x,y-1,x,y+1),'cream');box((x-1,y,x+1,y),'cream')
 # Root contact is invariant across every stage and animation frame.
 box((12,27,16,27),'dark')
 return im

atlas=Image.new('RGBA',(112,28*6*len(NAMES)))
for kind in range(len(NAMES)):
 for stage in range(4):
  for f in range(6):
   adult=mature(kind,f);cell=Image.new('RGBA',(28,28))
   if stage==0:
    d=ImageDraw.Draw(cell);d.line((14,24,14,27),fill=P['stem']);d.line((12,24,15,26),fill=P['lime']);d.point((14,27),fill=P['dark'])
   else:
    size={1:14,2:21,3:28}[stage];scaled=adult.resize((size,size),Image.Resampling.NEAREST);cell.paste(scaled,((28-size)//2,28-size))
   swayed=Image.new('RGBA',(28,28));wave=math.sin(f*math.tau/6)
   for y in range(28):
    shift=round(wave*1.6*((27-y)/27)**1.7);swayed.paste(cell.crop((0,y,28,y+1)),(shift,y))
   atlas.paste(swayed,(stage*28,(kind*6+f)*28))
atlas.save(OUT/'plants.png')
(OUT/'manifest.json').write_text(json.dumps({'names':NAMES,'firstId':15,'frameSize':28,'frames':6,'rootY':28,'author':'risu1 / Codex Garden','method':'original pixel geometry, fixed-root scanline sway, no AI','sha256':hashlib.sha256((OUT/'plants.png').read_bytes()).hexdigest()},ensure_ascii=False,indent=2),encoding='utf-8')
print('Created six original fantasy plants, four stages, six rooted frames each.')
