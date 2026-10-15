"""Import actual studio outputs, preserving frame bytes and animation timing."""
import hashlib, json, shutil
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
STUDIO=ROOT.parent/'XiuXianPixelStudio'

def sync():
    heroes=[]
    for job in sorted((STUDIO/'output').iterdir(),key=lambda p:p.stat().st_mtime,reverse=True):
        source=job/'64x64'; manifest=source/'manifest.json'
        if not manifest.exists(): continue
        data=json.loads(manifest.read_text(encoding='utf-8'))
        if any(h['name']==data['name'] for h in heroes): continue
        if not all((source/(a+'.gif')).exists() for a in ('idle','walk','cast')): continue
        target=ROOT/'assets/heroes'/job.name;target.mkdir(parents=True,exist_ok=True)
        for name in ('idle.gif','walk.gif','cast.gif','manifest.json'):
            shutil.copy2(source/name,target/name)
        for frame in data['frames']:
            if frame['action'] in ('idle','walk','cast'):
                shutil.copy2(source/frame['file'],target/frame['file'])
        heroes.append({'id':job.name,'name':data['name'],'source':str(source),'sha256':hashlib.sha256(manifest.read_bytes()).hexdigest(),'visualApproved':data.get('visualApproved',False),'origin':data['origin'],'frames':[f for f in data['frames'] if f['action'] in ('idle','walk','cast')]})
    if not heroes: raise RuntimeError('没有找到可导入的角色工坊输出')
    (ROOT/'assets/heroes.json').write_text(json.dumps(heroes,ensure_ascii=False,indent=2),encoding='utf-8')
    shutil.copy2(STUDIO/'output'/heroes[0]['id']/'64x64/idle_000.png',ROOT/'assets/tray.png')
    print(f'Imported {len(heroes)} studio characters without modifying source assets.')

if __name__=='__main__':sync()
