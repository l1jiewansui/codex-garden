"""Describe generated atlases without resampling, editing or overwriting source PNGs.
Read alpha only for atlas validation. The app crops source rectangles at draw time.
"""
from pathlib import Path
import json, hashlib
from PIL import Image
ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'assets/art-v04'

def prepare():
    # Actual generated layout, reviewed against source alpha bands; no invented 4x8 equal grid.
    xs=[31,239,446,652]
    ys=[54,258,471,681,897,1105,1313,1526]
    names=['苔芽 · 草帽园丁','桃枝 · 围巾园丁','雨青 · 蓝帽园丁','栗果 · 栗发园丁']
    heroes=[]
    for h,name in enumerate(names):
        frames=[]
        for action,row in [('idle',h*2),('cast',h*2+1)]:
            for col in range(4):
                frames.append({'action':action,'index':col,'file':f'{action}_{col:03}.png','sourceRect':[xs[col],ys[row],208,208],'durationMs':[520,260,160,480][col] if action=='idle' else [260,220,240,300][col]})
        heroes.append({'id':f'gardener-{h}','name':name,'origin':[32,59.08],'image':'gardeners','frames':frames,'visualApproved':False})
    cols=[(0,314),(314,313),(627,313),(940,314)]
    rows=[(0,314),(316,314),(638,314),(969,285)]
    crops=[[{'sourceRect':[x,rows[row][0],w,rows[row][1]]} for x,w in cols] for row in range(3)]
    icons={name:{'sourceRect':[cols[i][0],rows[3][0],cols[i][1],rows[3][1]]} for i,name in enumerate(['sparkle','care','seeds','app'])}
    manifest={'version':'0.4.0','backend':'built-in ImageGen','images':{'gardeners':'gardeners.png','gardenKit':'garden-kit.png'},'heroes':heroes,'crops':crops,'icons':icons,'notes':['Original generated PNGs preserved. Runtime atlas source rectangles account for the actual nonuniform layout.','No per-frame recentering, body scaling or Python image edits.','Original action identity and watercan/feet continuity remain subject to visual review at actual desktop size.']}
    checks=[]
    with Image.open(OUT/'gardeners.png') as im:
        for hero in heroes:
            for frame in hero['frames']:
                x,y,w,h=frame['sourceRect'];assert x>=0 and y>=0 and x+w<=im.width and y+h<=im.height
                bbox=im.crop((x,y,x+w,y+h)).getchannel('A').point(lambda a:255 if a>128 else 0).getbbox()
                if not bbox:raise ValueError('Empty frame: '+hero['id']+'/'+frame['file'])
                checks.append({'id':hero['id']+'/'+frame['file'],'bounds':list(bbox),'edgeTouch':bbox[0]==0 or bbox[1]==0 or bbox[2]==w or bbox[3]==h})
    with Image.open(OUT/'garden-kit.png') as im:
        for item in [s for row in crops for s in row]+list(icons.values()):
            x,y,w,h=item['sourceRect'];assert x>=0 and y>=0 and x+w<=im.width and y+h<=im.height
    manifest['sourceSha256']={name:hashlib.sha256((OUT/file).read_bytes()).hexdigest() for name,file in manifest['images'].items()}
    (OUT/'manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2),encoding='utf-8')
    (OUT/'atlas-checks.json').write_text(json.dumps({'frames':checks,'edgeTouches':sum(c['edgeTouch'] for c in checks),'validation':'Technical alpha/rect checks, not a substitute for visual animation review'},indent=2),encoding='utf-8')
    print(f"32 new animation frames, 12 crop stages, 4 icons; edge touches: {sum(c['edgeTouch'] for c in checks)}")
if __name__=='__main__':prepare()
