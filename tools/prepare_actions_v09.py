"""Process the independent ImageGen atlas using fixed row anchors and FrameRonin."""
import sys,json,shutil,hashlib
from pathlib import Path
from PIL import Image
from pixelize_art_v04 import convert,ROOT,records,COLORS
source=Path(sys.argv[1]);version=sys.argv[2] if len(sys.argv)>2 else 'v09';out=ROOT/('assets/pixel-'+version);out.mkdir(exist_ok=True)
raw=ROOT/('assets/art-'+version);raw.mkdir(exist_ok=True);shutil.copy2(source,raw/'independent-actions.png')
im=Image.open(source).convert('RGBA');atlas=Image.new('RGBA',(48*8,48*4));frames=[]
feet=[223,438,657,861];tops=[22,253,464,674];bottoms=[245,456,673,886]
for hero in range(4):
 for col in range(8):
  left=round(col*im.width/8);right=round((col+1)*im.width/8)
  canvas=Image.new('RGBA',(240,240));region=im.crop((left,tops[hero],right,bottoms[hero]+1))
  canvas.paste(region,((240-region.width)//2,tops[hero]-(feet[hero]-221)))
  processed=convert(canvas,[0,0,240,240],(44,44),f'hero-{hero}-frame-{col}')
  cell=Image.new('RGBA',(48,48));cell.paste(processed,(2,3));atlas.paste(cell,(col*48,hero*48))
  frames.append({'hero':hero,'action':'idle' if col<2 else 'water' if col<5 else 'feed','rect':[col*48,hero*48,48,48]})
atlas.save(out/'actions.png')
(out/'manifest.json').write_text(json.dumps({'origin':[24,44],'frames':frames,'palette':COLORS,'records':records,'sha256':hashlib.sha256((out/'actions.png').read_bytes()).hexdigest()},indent=2))
(raw/'prompt.txt').write_text('Reference: assets/pixel-v04/gardeners.png. Built-in ImageGen: four gardeners, empty-handed idle columns1-2, independent watering columns3-5, independent fertilizing columns6-8. Transparent8x4 sheet, single tool per action, stable feet. See conversation for complete prompt.',encoding='utf-8')
print('32 independent frames processed; fixed per-row feet anchors; 47-color palette.')
