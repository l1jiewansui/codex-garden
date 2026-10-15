"""Run all active bitmap artwork through the existing studio's pinned FrameRonin reducer.
Original ImageGen source art is preserved. Outputs are actual low-resolution palette PNGs.
"""
import sys,json,hashlib,shutil
from pathlib import Path
import numpy as np
from PIL import Image
ROOT=Path(__file__).resolve().parents[1]
STUDIO=ROOT.parent/'XiuXianPixelStudio'
sys.path.insert(0,str(STUDIO/'vendor'))
sys.path.insert(0,str(STUDIO/'app'))
from frame_ronin_mcp.lib.pixelate_core import _downsample_proper
from pipeline import map_palette
SOURCE=ROOT/'assets/art-v04'
OUT=ROOT/'assets/pixel-v04'
COLORS=['25252f','36343a','4b3936','60443a','7b5740','9b6c47','bb8e5c','b47b5f','d99d73','f0c295','f5d7ad','706c55','9b9874','c3ba8b','e3d5a9','f6eac3','263f35','35553b','4c6f3e','6a8b48','91ac58','bdd078','26374b','37536a','4d7387','77a0ae','b0c9c7','243f44','34636b','548e91','8cb6ad','6b393d','93464a','bc6261','e38d7c','895a30','b57b35','dca04a','f5c86c','ffe3a3','686575','90879d','b8a7bb','ae7683','d49b9c','f0c1ae','f7f1dc']
PALETTE=[tuple(bytes.fromhex(c)) for c in COLORS]
records=[]
def convert(source,rect,size,name):
    x,y,w,h=rect
    a=map_palette(source.crop((x,y,x+w,y+h)),PALETTE)
    tw,th=size
    mesh=(np.rint(np.linspace(0,w,tw+1)).astype(int).tolist(),np.rint(np.linspace(0,h,th+1)).astype(int).tolist())
    pixels=_downsample_proper(a[:,:,:3],a[:,:,3],mesh)
    pixels[pixels[:,:,3]==0]=0
    opaque=pixels[:,:,3]>0
    if not opaque.any():raise ValueError('Empty pixel asset: '+name)
    alpha=sorted(int(v) for v in np.unique(pixels[:,:,3]))
    colors=np.unique(pixels[:,:,:3][opaque],axis=0)
    if not set(alpha)<={0,255} or len(colors)>len(PALETTE):raise ValueError('Pixel contract violation: '+name)
    records.append({'name':name,'size':list(size),'sourceRect':rect,'alphaValues':alpha,'opaqueColors':len(colors),'opaquePixels':int(opaque.sum())})
    return Image.fromarray(pixels)

def main():
    OUT.mkdir(parents=True,exist_ok=True)
    m=json.loads((SOURCE/'manifest.json').read_text(encoding='utf-8'))
    chars=Image.open(SOURCE/m['images']['gardeners']).convert('RGBA')
    kit=Image.open(SOURCE/m['images']['gardenKit']).convert('RGBA')
    images={'gardeners':'gardeners.png','gardenKit':'garden-kit.png','portraits':'portraits.png'}
    char_atlas=Image.new('RGBA',(48*4,48*8))
    portraits=Image.new('RGBA',(32*4,32))
    for hi,hero in enumerate(m['heroes']):
        hero['origin']=[24,44]
        hero['frameSize']=[48,48]
        hero['portrait']={'image':'portraits','sourceRect':[hi*32,0,32,32]}
        for f in hero['frames']:
            row=hi*2+(f['action']=='cast');col=f['index'];rect=f['sourceRect']
            frame=convert(chars,rect,(48,48),hero['id']+'/'+f['file'])
            char_atlas.paste(frame,(col*48,row*48))
            if f['action']=='idle' and col==0:
                portraits.paste(convert(chars,rect,(32,32),hero['id']+'/portrait'),(hi*32,0))
            f['sourceRect']=[col*48,row*48,48,48]
    char_atlas.save(OUT/'gardeners.png');portraits.save(OUT/'portraits.png')
    crop_atlas=Image.new('RGBA',(32*4,32*3))
    for row,stages in enumerate(m['crops']):
        for col,item in enumerate(stages):
            crop_atlas.paste(convert(kit,item['sourceRect'],(32,32),f'crop-{row}-stage-{col}'),(col*32,row*32))
            item['sourceRect']=[col*32,row*32,32,32]
    crop_atlas.save(OUT/'garden-kit.png')
    icons={name:{'variants':{}} for name in m['icons']}
    for size in [8,9,10,12,16]:
        key='icons'+str(size);images[key]=f'icons-{size}.png'
        atlas=Image.new('RGBA',(size*4,size))
        for i,(name,item) in enumerate(m['icons'].items()):
            icon=convert(kit,item['sourceRect'],(size,size),f'icon-{name}-{size}')
            atlas.paste(icon,(i*size,0));icons[name]['variants'][str(size)]={'image':key,'sourceRect':[i*size,0,size,size]}
            if name=='app' and size==16:icon.save(OUT/'tray-icon.png')
        atlas.save(OUT/images[key])
    glyphs=['111101101101111','010110010010111','111001111100111','111001111001111','101101111001001','111100111001111','111100111101111','111001010010010','111101111101111','111101111001111']
    digits=Image.new('RGBA',(30,5))
    for i,glyph in enumerate(glyphs):
        a=np.zeros((5,3,4),np.uint8)
        for j,v in enumerate(glyph):
            if v=='1':a[j//3,j%3]=[227,213,169,255]
        digits.paste(convert(Image.fromarray(a),[0,0,3,5],(3,5),'digit-'+str(i)),(i*3,0))
    digits.save(OUT/'digits.png');images['digits']='digits.png'
    m.update(version='0.4.1-pixel',images=images,icons=icons,pixelContract={'style':'Terraria-inspired side-view pixel art','characterCanvas':[48,48],'cropCanvas':[32,32],'paletteHex':['#'+x for x in COLORS],'alpha':'binary-0-or-255','filter':'nearest','displayScale':2,'reducer':'pinned FrameRonin _downsample_proper','perFrameCrop':False,'sourceArt':'../art-v04/manifest.json'},notes=['All active artwork is processed PNG pixel art. Source ImageGen atlases are not loaded by the app.','Character actions share fixed-size frames and fixed origins; no per-frame body scaling or recentering.'])
    m['sourceSha256']={k:hashlib.sha256((OUT/file).read_bytes()).hexdigest() for k,file in images.items()}
    (OUT/'manifest.json').write_text(json.dumps(m,ensure_ascii=False,indent=2),encoding='utf-8')
    shutil.copy2(STUDIO/'vendor/FrameRonin-MCP-LICENSE.txt',OUT/'FrameRonin-LICENSE.txt')
    shutil.copy2(STUDIO/'vendor/provenance.json',OUT/'FrameRonin-provenance.json')
    proof={'processed':len(records),'paletteSize':len(PALETTE),'binaryAlpha':True,'frameSizeFixed':True,'sourcesPreserved':True,'records':records,'reducerSha256':hashlib.sha256((STUDIO/'vendor/frame_ronin_mcp/lib/pixelate_core.py').read_bytes()).hexdigest()}
    (OUT/'pixel-checks.json').write_text(json.dumps(proof,indent=2),encoding='utf-8')
    print(f"Processed {len(records)} artwork items with FrameRonin; {len(PALETTE)} shared palette colors; hard alpha.")
if __name__=='__main__':main()
