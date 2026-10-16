"""Build registered native parts with explicit ownership and a shared pose rig.

The archive stays immutable. Idle/walk preserve the source pixels; care poses
use the same head rig for all parts instead of guessing a new head every frame.
"""
import argparse,hashlib,json
from pathlib import Path
import numpy as np
from PIL import Image,ImageDraw
ROOT=Path(__file__).resolve().parents[1]
SOURCE=ROOT/'archives/default-gardeners-rc11'
OUT=ROOT/'assets/pixel-classic'
INK=(37,37,47,255)
SIZE=(432,192)
HEAD_PARTS=('scalp','face','hairBack','hairFront','hat')
BODY_PARTS=('boots','coat','shirt','tools')
SKIN=['#b47b5f','#d99d73','#f0c295','#f5d7ad','#f7f1dc','#e38d7c','#f0c1ae']
def color(p):return '#%02x%02x%02x'%tuple(p[:3])
def poly(points):
 im=Image.new('1',(48,48));ImageDraw.Draw(im).polygon(points,fill=1);return np.array(im,dtype=bool)
HATS=[poly([(10,26),(12,21),(16,17),(19,12),(22,9),(31,9),(34,12),(40,13),(42,17),(40,21),(35,22),(33,20),(31,18),(27,19),(24,21),(20,23),(16,26)]),np.zeros((48,48),bool),poly([(12,14),(18,14),(22,10),(25,8),(29,8),(33,11),(37,14),(40,14),(42,15),(42,19),(39,20),(35,19),(33,18),(31,19),(27,21),(23,23),(21,25),(17,27),(13,27),(12,25),(14,22),(16,20),(17,19),(14,18),(12,16)])]
SCALP=poly([(19,21),(20,18),(23,15),(28,15),(32,18),(34,22),(34,25),(31,28),(25,29),(21,27)])
POSES={'idle':[[0,0]]*2,'walk':[[0,0]]*9,'water':[[0,0],[0,0],[0,1],[0,1],[0,0],[0,0],[0,1],[0,0]],'feed':[[0,0],[-1,0],[-1,1],[-1,1],[-1,0],[0,0]]}
IRISES=[[(25,23),(30,23)],[(25,23),(30,23)],[(26,24),(31,24)]]
FACE_RAMP={'#b47b5f':1,'#d99d73':2,'#f0c295':3,'#f5d7ad':4,'#f7f1dc':5,'#e38d7c':2,'#f0c1ae':4}
HAIR_RAMP={'#4b3936':0,'#6b393d':0,'#93464a':1,'#bc6261':2,'#e38d7c':3,'#d49b9c':4,'#f0c1ae':5,'#f6eac3':5,'#f5d7ad':5,'#e3d5a9':4,'#c3ba8b':3,'#60443a':1,'#7b5740':2,'#9b6c47':3,'#bb8e5c':4}
CLOTH_RAMP={'#243f44':1,'#26374b':1,'#37536a':2,'#34636b':2,'#4d7387':3,'#548e91':3,'#77a0ae':4,'#8cb6ad':4,'#b0c9c7':5,'#6b393d':1,'#93464a':2,'#bc6261':3,'#e3d5a9':3,'#c3ba8b':2,'#f6eac3':4,'#f7f1dc':5}

def split_head(cell,actor):
 a=np.array(cell);bank={k:np.zeros_like(a) for k in HEAD_PARTS};ownership=np.zeros((48,48),np.uint8)
 for y in range(29):
  for x in range(48):
   p=a[y,x]
   if not p[3]:continue
   c=color(p);hat=HATS[actor][y,x]
   if actor==2 and (y<19 or c in {'#26374b','#37536a','#34636b','#243f44'}):hat=True
   if actor==0 and c in {'#dca04a','#b57b35','#895a30','#9b6c47'}:hat=True
   skin=21<=x<=33 and 21<=y<=28 and c in SKIN
   # The pink source uses the same hue for locks and cheek. Geometry owns it.
   if c in {'#e38d7c','#f0c1ae'}:skin=skin and ((y>=24 and 24<=x<=27) or (y>=25 and 21<=x<=27) or (22<=y<=24 and 26<=x<=29))
   eye=(25<=x<=26 and 22<=y<=24 or 30<=x<=32 and 23<=y<=24) and c=='#25252f'
   jaw=(25<=x<=30 and y in (27,28)) and c=='#25252f'
   part='hat' if hat else 'face' if skin or eye or jaw else 'hairBack' if y>=24 and x<24 else 'hairFront'
   bank[part][y,x]=p;ownership[y,x]=HEAD_PARTS.index(part)+1
 # A complete scalp is below hair/hat, confined to the original head silhouette.
 hidden=(bank['hairBack'][:,:,3]>0)|(bank['hairFront'][:,:,3]>0)|(bank['hat'][:,:,3]>0)
 for y,x in zip(*np.where(SCALP&hidden)):
  if bank['face'][y,x,3]:continue
  edge=any(not(0<=x+dx<48 and 0<=y+dy<48) or not SCALP[y+dy,x+dx] for dx,dy in [(1,0),(-1,0),(0,1),(0,-1)])
  bank['scalp'][y,x]=INK if edge else (217,157,115,255) if x<23 or y>26 else (240,194,149,255)
 return {k:Image.fromarray(v) for k,v in bank.items()},ownership

def alpha_compose(bank,body):
 out=Image.new('RGBA',SIZE)
 for name in ['scalp'+str(body),'hairBack'+str(body),'boots'+str(body),'coat'+str(body),'shirt'+str(body),'face'+str(body),'hairFront'+str(body),'hat'+str(body),'tools'+str(body)]:out.alpha_composite(bank[name])
 return out

def spread(cell,actions):
 out=Image.new('RGBA',SIZE)
 for name,(row,count,_) in actions.items():
  for f,(dx,dy) in enumerate(POSES[name]):out.paste(cell,(f*48+dx,row*48+dy),cell)
 return out

def build():
 OUT.mkdir(exist_ok=True)
 checks=json.loads((SOURCE/'SHA256.json').read_text(encoding='utf-8'))
 for name,digest in checks.items():
  if hashlib.sha256((SOURCE/name).read_bytes()).hexdigest()!=digest:raise ValueError('Archive changed: '+name)
 archive=json.loads((SOURCE/'manifest.json').read_text(encoding='utf-8'));actions=archive['actions'];heads=[];banks={};records={};ownerships=[]
 for actor in range(3):
  src=Image.open(SOURCE/f'gardener-{actor+1}.png').convert('RGBA');head,owner=split_head(src.crop((0,0,48,48)),actor);heads.append(head);ownerships.append(owner)
  for part in BODY_PARTS:
   im=Image.new('RGBA',SIZE);a=np.array(src)
   for name,(row,count,_) in actions.items():
    for f in range(count):
     cell=a[row*48:(row+1)*48,f*48:(f+1)*48].copy();keep=np.zeros((48,48),bool)
     for y in range(29,48):
      for x in range(48):
       c=color(cell[y,x]);kind='boots' if y>=39 else 'tools' if x>=31 and c not in SKIN else 'shirt' if c in {'#e3d5a9','#f6eac3','#f7f1dc','#c3ba8b'} else 'coat'
       keep[y,x]=kind==part
     cell[~keep]=0;im.paste(Image.fromarray(cell),(f*48,row*48))
   banks[part+str(actor)]=im
 # Restore hair under hats with native locks; no skin or iris pixels are donors.
 donor=Image.new('RGBA',(48,48));donor.alpha_composite(heads[1]['hairBack']);donor.alpha_composite(heads[1]['hairFront'])
 for actor in (0,2):
  source=np.array(donor);hat=np.array(heads[actor]['hat']);front=np.array(heads[actor]['hairFront']);back=np.array(heads[actor]['hairBack'])
  for y,x in zip(*np.where((hat[:,:,3]>0)&(source[:,:,3]>0))):
   if y>=28:continue
   rgba=source[y,x];c=color(rgba)
   if c!='#25252f':
    ramp=[(75,57,54),(107,57,61),(147,70,74),(188,98,97),(227,141,124),(240,193,174)] if actor==0 else [(37,37,47),(54,52,58),(38,55,75),(55,83,106),(77,115,135),(104,101,117)]
    rgba=(*ramp[HAIR_RAMP.get(c,2)],255)
   (back if y>=24 and x<24 else front)[y,x]=rgba
  heads[actor]['hairFront']=Image.fromarray(front);heads[actor]['hairBack']=Image.fromarray(back)
 for actor,head in enumerate(heads):
  for name,im in head.items():banks[name+str(actor)]=spread(im,actions)
 # Shape variants keep the unchanged neck, eyes and shared pose registration.
 for style in ('pony','braid','curly'):
  cell=heads[1]['hairFront'].copy();back=heads[1]['hairBack'].copy();d=ImageDraw.Draw(back)
  if style in ('pony','braid'):
   back=Image.new('RGBA',(48,48));d=ImageDraw.Draw(back)
   if style=='pony':
    d.polygon([(17,17),(14,17),(14,19),(12,20),(11,24),(10,27),(11,30),(14,32),(16,30),(17,26),(16,23),(18,21)],fill='#93464a',outline=INK);d.line([(15,20),(13,23),(12,27),(13,29)],fill='#e38d7c')
   else:
    d.polygon([(16,21),(13,23),(13,26),(14,28),(13,30),(14,32),(16,34),(18,32),(17,30),(18,28),(17,26),(18,23)],fill='#bc6261',outline=INK)
    for y in (24,28,31):d.line([(14,y),(16,y+1)],fill='#6b393d');d.point((16,y),fill='#f0c1ae')
    d.line([(15,33),(17,33)],fill='#548e91')
   d.line([(15,20),(17,20)],fill='#548e91')
  else:
   curl=Image.new('RGBA',(48,48));d=ImageDraw.Draw(curl)
   for x,y in [(19,15),(23,13),(28,14),(32,17),(16,19),(14,23)]:
    d.polygon([(x-1,y-3),(x+1,y-3),(x+3,y-1),(x+3,y+1),(x+1,y+3),(x-1,y+3),(x-3,y+1),(x-3,y-1)],fill='#bc6261',outline=INK)
   curl.alpha_composite(cell);cell=curl;d=ImageDraw.Draw(cell)
   for x,y in [(20,15),(25,14),(30,17),(17,21)]:d.line([(x,y),(x-1,y+1),(x,y+2),(x+2,y+2)],fill='#93464a');d.point((x,y-1),fill='#f0c1ae')
  banks['hairFront-'+style]=spread(cell,actions);banks['hairBack-'+style]=spread(back,actions)
 for name,actor in [('round',1),('small',1),('elder',0)]:
  im=heads[actor]['face'].copy();d=ImageDraw.Draw(im)
  if name=='elder':d.line((23,25,24,25),fill='#b47b5f');d.point((29,26),fill='#b47b5f')
  elif name=='round':d.line((32,25,32,26),fill='#f0c295');d.point((32,27),fill=INK)
  else:d.point((31,25),fill=INK);d.point((30,26),fill=INK)
  banks['face-'+name]=spread(im,actions)
 beard=Image.new('RGBA',(48,48));d=ImageDraw.Draw(beard);d.polygon([(24,26),(26,27),(29,27),(31,26),(31,28),(28,30),(25,29)],fill=INK);d.line([(25,27),(27,29),(29,28),(30,27)],fill='#60443a');banks['beard']=spread(beard,actions)
 for name,im in banks.items():
  a=np.array(im);mask=np.zeros_like(a);group=1 if name.startswith(('face','scalp')) else 2 if name.startswith('hair') or name=='beard' else 3 if name.startswith('shirt') else 4 if name.startswith('coat') else 7 if name.startswith('hat') else 0
  for action,(row,count,_) in actions.items():
   for f in range(count):
    dx,dy=POSES[action][f];cell=a[row*48:(row+1)*48,f*48:(f+1)*48]
    actor=int(name[-1]) if name[-1:].isdigit() else 1
    iris=IRISES[actor] if name.startswith('face') else []
    for y,x in zip(*np.where(cell[:,:,3]>0)):
     c=color(cell[y,x]);g=group;shade=2
     if g==1:
      if (x-dx,y-dy) in iris:g=8;shade=2
      elif c=='#f7f1dc':g=0
      elif c in FACE_RAMP:shade=FACE_RAMP[c]
      else:g=0
     elif g==2:
      if c=='#25252f':
       interior=all(0<=x+xx<48 and 0<=y+yy<48 and cell[y+yy,x+xx,3] for xx,yy in [(1,0),(-1,0),(0,1),(0,-1)])
       if name.startswith('hair') and interior:shade=2 if name.endswith('2') else 0
       else:g=0
      elif c in {'#243f44','#4d7387','#548e91'} and name!='hairFront2':g=0
      else:shade=HAIR_RAMP.get(c,1)
     elif g in (3,4):
      if c in FACE_RAMP and c not in {'#f7f1dc','#f0c1ae'}:g=1;shade=FACE_RAMP[c]
      elif c=='#25252f':g=0
      else:shade=CLOTH_RAMP.get(c,1)
     mask[row*48+y,f*48+x]=(g,shade,0,255)
  path=OUT/(name+'.png');material=OUT/(name+'-material.png');im.save(path);Image.fromarray(mask).save(material)
  records[name]={'file':path.name,'material':material.name,'sha256':hashlib.sha256(path.read_bytes()).hexdigest(),'materialSha256':hashlib.sha256(material.read_bytes()).hexdigest(),'group':group}
 references=[]
 for actor in range(3):
  result=alpha_compose(banks,actor);source=Image.open(SOURCE/f'gardener-{actor+1}.png').convert('RGBA')
  # Standing and walking preserve the artwork; care heads intentionally use the rig.
  for row,count,_ in [actions['idle'],actions['walk']]:
   assert result.crop((0,row*48,count*48,(row+1)*48)).tobytes()==source.crop((0,row*48,count*48,(row+1)*48)).tobytes(),f'Base silhouette changed: {actor}'
  references.append({'name':archive['gardeners'][actor]['name'],'rgbaSha256':hashlib.sha256(result.tobytes()).hexdigest(),'preservedSourceFrames':11,'frames':25,'sourceIdleRgbaSha256':hashlib.sha256(source.crop((0,0,48,48)).tobytes()).hexdigest()})
 manifest={'version':2,'frameSize':48,'origin':[24,44],'actions':{k:{'row':v[0],'frames':v[1],'durationMs':v[2]} for k,v in actions.items()},'headPoses':POSES,'parts':records,'reference':references,'sourceArchive':'archives/default-gardeners-rc11','reconstruction':'authored semantic masks, back/front hair, complete scalp, shared care rig','eyePixels':IRISES,'preservedSourceFrames':33,'careFrames':'42 re-registered care frames; archived originals remain unchanged'}
 (OUT/'manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2),encoding='utf-8')
 (OUT/'CREDITS.md').write_text('# Classic native parts\n\nProject-authored source archive: archives/default-gardeners-rc11. Idle/walk artwork is preserved. Care poses use a shared head rig; face/hair/hat and clothing ownership are explicit. New locks and hidden scalp are edited derivatives. No LPC sprites or AI service are used. Editable projects are in art/classic. LibreSprite is an external build/editor tool, not bundled into the application.\n',encoding='utf-8')
 print('Native parts:',len(records),'; source frames preserved:33; care frames re-registered:42')
 return manifest
if __name__=='__main__':build()
