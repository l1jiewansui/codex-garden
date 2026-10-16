"""Replace the fourth gardener's hat silhouette with white hair and goggles.
Edits existing pixel atlases only, preserving action registration and watercan.
"""
from pathlib import Path
import json,hashlib,subprocess,io
from PIL import Image,ImageDraw
ROOT=Path(__file__).resolve().parents[1]
def head(cell):
    box=cell.getbbox()
    if not box:return cell
    x0,y0,x1,y1=box
    # The head is replaced above the torso; hands/tools and feet remain registered.
    d=ImageDraw.Draw(cell);d.rectangle((x0,y0,x1-1,y0+14),fill=(0,0,0,0))
    cx=24
    d.rectangle((cx-6,y0+5,cx+5,y0+13),fill='#36343a')
    d.rectangle((cx-5,y0+4,cx+3,y0+9),fill='#90879d')
    d.rectangle((cx-4,y0+4,cx+3,y0+8),fill='#f7f1dc')
    for x,y in [(-4,3),(-1,2),(2,3),(-5,6),(4,5)]:d.point((cx+x,y0+y),fill='#e3d5a9')
    d.rectangle((cx-4,y0+9,cx+4,y0+13),fill='#d99d73')
    d.rectangle((cx-5,y0+10,cx+5,y0+11),fill='#36343a')
    d.rectangle((cx-3,y0+10,cx-1,y0+11),fill='#b0c9c7');d.rectangle((cx+2,y0+10,cx+4,y0+11),fill='#b0c9c7')
    d.rectangle((cx-2,y0+14,cx+2,y0+15),fill='#e3d5a9')
    return cell
def recolor(cell):
    colors={'37536a':'686575','4d7387':'90879d','26374b':'36343a','35553b':'6b393d','4c6f3e':'93464a','6a8b48':'ae7683'}
    p=cell.load()
    for y in range(cell.height):
        for x in range(cell.width):
            r,g,b,a=p[x,y];key=f'{r:02x}{g:02x}{b:02x}'
            if a and key in colors:p[x,y]=(*bytes.fromhex(colors[key]),a)
    return cell
def main():
    path=ROOT/'assets/pixel-v091/actions.png';im=Image.open(io.BytesIO(subprocess.check_output(['git','show','ec0ab98:assets/pixel-v091/actions.png'],cwd=ROOT))).convert('RGBA')
    for col in range(8):
        cell=im.crop((col*48,144,col*48+48,192));im.paste(head(recolor(cell)),(col*48,144))
    im.save(path)
    mpath=path.with_name('manifest.json');m=json.loads(mpath.read_text());m['sha256']=hashlib.sha256(path.read_bytes()).hexdigest();m['fourthGardener']='white hair, goggles, plum workwear; existing action alignment preserved';mpath.write_text(json.dumps(m,ensure_ascii=False,indent=2),encoding='utf-8')
    mpath=ROOT/'assets/pixel-v04/manifest.json';m=json.loads(mpath.read_text(encoding='utf-8'));m['heroes'][3]['name']='白发工匠';mpath.write_text(json.dumps(m,ensure_ascii=False,indent=2),encoding='utf-8')
    portraits=Image.open(ROOT/'assets/pixel-v04/portraits.png').convert('RGBA');frame=im.crop((96,144,144,192));frame=frame.resize((32,32),Image.Resampling.NEAREST);portraits.paste(frame,(96,0));portraits.save(ROOT/'assets/pixel-v04/portraits.png')
    m['sourceSha256']['portraits']=hashlib.sha256((ROOT/'assets/pixel-v04/portraits.png').read_bytes()).hexdigest()
    mpath.write_text(json.dumps(m,ensure_ascii=False,indent=2),encoding='utf-8')
if __name__=='__main__':main()
