"""Compile pinned LPC layers into registered garden pixels and material masks.

Rebuild: python tools/import_lpc_gardeners.py && python tools/build_gardener_layers.py
No network or AI. Coordinates are shared across all layers and action frames.
"""
import hashlib,json,math,shutil
from pathlib import Path
from PIL import Image
ROOT=Path(__file__).resolve().parents[1]
SOURCE=ROOT/'assets/lpc-gardeners'
OUT=ROOT/'assets/pixel-lpc'

def build():
    OUT.mkdir(exist_ok=True)
    source=json.loads((SOURCE/'manifest.json').read_text(encoding='utf-8'))
    art=json.loads((ROOT/'assets/pixel-v04/manifest.json').read_text(encoding='utf-8'))
    palette=art['pixelContract']['paletteHex'] if 'pixelContract' in art else art['paletteHex']
    colors=[tuple(bytes.fromhex(v.lstrip('#'))) for v in palette]
    nearest=lambda rgb:min(range(len(colors)),key=lambda i:sum((rgb[c]-colors[i][c])**2*(2,3,1)[c] for c in range(3)))
    skin={tuple(bytes.fromhex(v.lstrip('#'))) for v in source['palettes']['body']['light']}
    records={}
    material={'body':1,'curly':2,'pixie':2,'pony':2,'ponyBack':2,'braid':2,'braidBack':2,'beard':2,'shirt':3,'overalls':4,'pants':5,'boots':6,'hat':7}
    eye_colors={(42,60,73):0,(86,134,174):3,(87,206,228):5}
    for name,part in source['parts'].items():
        skin_part=name=='body' or name.startswith(('head','nose'))
        if skin_part:material[name]=1
        path=SOURCE/part['file']
        if hashlib.sha256(path.read_bytes()).hexdigest()!=part['sha256']:raise ValueError('LPC source hash mismatch: '+name)
        im=Image.open(path).convert('RGBA')
        ramp=sorted({p[:3] for p in im.getdata() if p[3] and (not skin_part or p[:3] in skin)},key=lambda p:sum(p[c]*(2,3,1)[c] for c in range(3)))
        ranks={rgb:round(i*5/max(1,len(ramp)-1)) for i,rgb in enumerate(ramp)}
        out=Image.new('RGBA',(432,192));pix=out.load()
        for action,a in source['actions'].items():
            for frame in range(a['frames']):
                for y in range(48):
                    # Bigger head, compact torso, fixed source foot y=62 -> garden y=44.
                    sy=math.floor(14+(y-12)*20/17) if y<29 else math.floor(34+(y-29)*28/15)
                    if not 0<=sy<64:continue
                    scale=1.10 if y<29 else 1.05
                    for x in range(48):
                        sx=math.floor(32+(x-24)/scale)
                        if not 0<=sx<64:continue
                        p=im.getpixel((frame*64+sx,a['row']*64+sy))
                        if p[3]<128:continue
                        rgb=p[:3]
                        if name.startswith('head') and rgb in eye_colors:encoded=(8,eye_colors[rgb],0,255)
                        else:encoded=(material[name],ranks[rgb],0,255) if name in material and rgb in ranks else (0,nearest(rgb),0,255)
                        pix[frame*48+x,a['row']*48+y]=encoded
        target=OUT/(name+'.png');out.save(target)
        records[name]={'file':target.name,'sha256':hashlib.sha256(target.read_bytes()).hexdigest(),'sourceSha256':part['sha256'],'source':part['source'],'creditId':part['definition'],'material':material.get(name,0)}
    shutil.copy2(ROOT/'assets/gardener-recipes.json',OUT/'recipes.json')
    manifest={'version':2,'recipeSha256':hashlib.sha256((OUT/'recipes.json').read_bytes()).hexdigest(),'repository':source['repository'],'commit':source['commit'],'frameSize':48,'origin':[24,44],'palette':palette,'actions':source['actions'],'parts':records,'encoding':'R=material (0=literal palette, 8=iris), G=ramp or palette index; binary alpha','transform':'shared fixed mesh; enlarged head, compact body; no per-frame recentering'}
    (OUT/'manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2),encoding='utf-8')
    for name in ['CREDITS.json','CREDITS.md','OGA-BY-3.0.txt','CC-BY-SA-3.0.txt','CC-BY-SA-4.0.txt']:shutil.copy2(SOURCE/name,OUT/name)
    print('Compiled LPC material layers:',len(records))

if __name__=='__main__':build()
