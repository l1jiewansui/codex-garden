"""Candidate gardener compiler: shared grid, palette, scale and ground anchor.

The input is a complete 4x4 sprite sheet, never a recolored existing actor.
Rows: idle / walk / water / feed. Technical success requires visual approval.
"""
import hashlib,json,os,tempfile,shutil
from pathlib import Path
from collections import deque
import numpy as np
from PIL import Image
try:
    from pixel_pipeline.pixelate_core import _downsample_proper
except ModuleNotFoundError:
    from backend.pixel_pipeline.pixelate_core import _downsample_proper

ACTIONS=('idle','walk','water','feed')

def remove_matte(frame):
    """Flood only corner-connected magenta; white hair is never color-keyed."""
    a=np.array(frame.convert('RGBA'));h,w=a.shape[:2]
    keyed=(a[:,:,0]>200)&(a[:,:,1]<80)&(a[:,:,2]>200)
    q=deque((x,y) for x,y in ((0,0),(w-1,0),(0,h-1),(w-1,h-1)) if keyed[y,x])
    seen=np.zeros((h,w),bool)
    while q:
        x,y=q.popleft()
        if seen[y,x] or not keyed[y,x]:continue
        seen[y,x]=True
        for xx,yy in ((x-1,y),(x+1,y),(x,y-1),(x,y+1)):
            if 0<=xx<w and 0<=yy<h and not seen[yy,xx]:q.append((xx,yy))
    a[seen]=0;a[:,:,3]=np.where(a[:,:,3]>=128,255,0);a[a[:,:,3]==0]=0
    return Image.fromarray(a)

def compile_sheet(source,destination,palette,name='我的园丁'):
    source=Path(source);destination=Path(destination)
    if destination.exists():raise ValueError('候选目录已存在，不覆盖已有园丁')
    if source.stat().st_size>20*1024*1024:raise ValueError('精灵表需小于20MB')
    with Image.open(source) as raw:
        if raw.width%4 or raw.height%4 or not 128<=raw.width<=4096 or not 128<=raw.height<=4096:raise ValueError('需要4行4列等分精灵表，每格至少32像素，整图不超过4096像素')
        sheet=raw.convert('RGBA')
    sw,sh=sheet.width//4,sheet.height//4
    frames=[remove_matte(sheet.crop((c*sw,r*sh,(c+1)*sw,(r+1)*sh))) for r in range(4) for c in range(4)]
    boxes=[im.getbbox() for im in frames]
    if any(b is None for b in boxes):raise ValueError('存在空白动作帧')
    if any(b[0]<1 or b[1]<1 or b[2]>=sw or b[3]>=sh for b in boxes):raise ValueError('角色触碰分格边界，可能截肢或串格，请重新生成')
    for row in range(4):
        if len({im.tobytes() for im in frames[row*4:row*4+4]})<2:raise ValueError(f'{ACTIONS[row]}动作没有逐帧变化')
    bounds=(min(b[0] for b in boxes),min(b[1] for b in boxes),max(b[2] for b in boxes),max(b[3] for b in boxes))
    heights=[b[3]-b[1] for b in boxes]
    if max(heights)>min(heights)*1.5:raise ValueError('动作间体型变化过大，请重新生成')
    w,h=bounds[2]-bounds[0],bounds[3]-bounds[1];scale=min(40/w,40/h)
    tw,th=max(1,round(w*scale)),max(1,round(h*scale))
    if (max(b[3] for b in boxes)-min(b[3] for b in boxes))*scale>4:raise ValueError('脚底基线漂移超过4像素，请重新生成')
    colors=np.array([tuple(bytes.fromhex(v.lstrip('#'))) for v in palette],dtype=np.int32)
    if not 8<=len(colors)<=64:raise ValueError('调色板需要8–64色')
    atlas=Image.new('RGBA',(192,192));records=[]
    for i,frame in enumerate(frames):
        a=np.array(frame.crop(bounds));rgb,inv=np.unique(a[:,:,:3].reshape(-1,3),axis=0,return_inverse=True)
        mapped=[]
        for start in range(0,len(rgb),1024):
            delta=rgb[start:start+1024,None,:].astype(np.int32)-colors[None,:,:]
            mapped.extend(colors[np.argmin((delta*delta*np.array([2,3,1])).sum(2),axis=1)])
        a[:,:,:3]=np.array(mapped,dtype=np.uint8)[inv].reshape(a.shape[:2]+(3,))
        mesh=(np.rint(np.linspace(0,w,tw+1)).astype(int).tolist(),np.rint(np.linspace(0,h,th+1)).astype(int).tolist())
        small=Image.fromarray(_downsample_proper(a[:,:,:3],a[:,:,3],mesh));cell=Image.new('RGBA',(48,48));cell.paste(small,((48-tw)//2,44-th))
        if not cell.getbbox():raise ValueError('像素化后动作帧为空')
        atlas.paste(cell,((i%4)*48,(i//4)*48));records.append({'action':ACTIONS[i//4],'index':i%4,'rect':[(i%4)*48,(i//4)*48,48,48],'durationMs':180 if i//4==0 else 140})
    destination.parent.mkdir(parents=True,exist_ok=True);staging=Path(tempfile.mkdtemp(prefix='gardener-',dir=destination.parent))
    try:
        atlas.save(staging/'sheet.png');atlas.crop((0,0,48,48)).resize((32,32),Image.Resampling.NEAREST).save(staging/'portrait.png')
        manifest={'schemaVersion':1,'name':str(name)[:24],'frameSize':[48,48],'origin':[24,44],'grid':[4,4],'frames':records,'palette':list(palette),'sourceSha256':hashlib.sha256(source.read_bytes()).hexdigest(),'sheetSha256':hashlib.sha256((staging/'sheet.png').read_bytes()).hexdigest(),'technicalPassed':True,'visualApproved':False,'pipeline':'pinned FrameRonin majority reducer; global scale and origin; no per-frame recentering'}
        (staging/'manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2),encoding='utf-8');os.rename(staging,destination)
    except Exception:
        shutil.rmtree(staging);raise
    return manifest
