"""Preserve the pre-redesign default gardeners. Never overwrite an archive."""
import hashlib,json,shutil,zipfile
from pathlib import Path
from PIL import Image
ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'archives/default-gardeners-rc11'

def main():
    if OUT.exists():raise RuntimeError('Archive already exists; refusing to overwrite')
    OUT.mkdir(parents=True)
    for source,name in [('assets/pixel-v091/actions.png','original-actions.png'),('assets/pixel-v04/gardeners.png','original-gardeners.png'),('assets/pixel-v04/portraits.png','original-portraits.png'),('assets/pixel-v04/manifest.json','original-art-manifest.json'),('web/gardener-studio.js','studio-rc11.js')]:
        shutil.copy2(ROOT/source,OUT/name)
    art=json.loads((OUT/'original-art-manifest.json').read_text(encoding='utf-8'))
    source=Image.open(OUT/'original-actions.png').convert('RGBA')
    actions={'idle':(0,2,520),'walk':(1,9,140),'water':(2,8,150),'feed':(3,6,190)}
    recipes=[]
    for index,name in enumerate(['麦穗','桃桃','夜蓝']):
        sheet=Image.new('RGBA',(432,192))
        for action,(row,count,duration) in actions.items():
            for frame in range(count):
                col=[2,2,3,3,4,4,3,2][frame] if action=='water' else [5,6,7,7,6,5][frame] if action=='feed' else 2
                cell=source.crop((col*48,index*48,(col+1)*48,(index+1)*48))
                if action=='walk':
                    left,right=cell.crop((0,36,24,48)),cell.crop((24,36,48,48))
                    cell.paste((0,0,0,0),(0,36,48,48));offset=[-1,0,1,0,0,-1,0,1,0][frame]
                    cell.paste(left,(offset,36));cell.paste(right,(24-offset,36))
                sheet.paste(cell,(frame*48,row*48))
        sheet.save(OUT/f'gardener-{index+1}.png')
        recipes.append({'name':name,'originalHero':art['heroes'][index],'legacyRecipe':{'template':f'original{index}'},'sheet':f'gardener-{index+1}.png'})
    (OUT/'manifest.json').write_text(json.dumps({'archiveVersion':1,'sourceVersion':'0.10.0-rc.11','frameSize':48,'origin':[24,44],'actions':actions,'gardeners':recipes},ensure_ascii=False,indent=2),encoding='utf-8')
    (OUT/'README.md').write_text('# 默认三角色存档\n\n此目录保存 rc.11 的三位旧默认角色，未被新版生成角色覆盖。\n\noriginal-* 为原始图集与元数据的逐字节副本；gardener-1/2/3.png 为按旧版动作顺序导出的独立精灵表，4 行依次为站立、走路、浇水、施肥，每格 48×48 像素，脚底原点 (24,44)。studio-rc11.js 保留旧版构建逻辑。manifest.json 保留角色信息与旧预设标识。\n\nSHA256.json 可校验全部文件。此存档独立于新版默认角色，不会随新版构建改写。原始素材沿用项目原有许可。\n',encoding='utf-8')
    hashes={str(p.relative_to(OUT)).replace('\\','/'):hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(OUT.iterdir()) if p.is_file()}
    (OUT/'SHA256.json').write_text(json.dumps(hashes,indent=2),encoding='utf-8')
    target=ROOT/'dist/default-gardeners-rc11-archive.zip'
    with zipfile.ZipFile(target,'w',zipfile.ZIP_DEFLATED) as z:
        for p in sorted(OUT.iterdir()):z.write(p,p.relative_to(OUT.parent))
    print(OUT);print(target)

if __name__=='__main__':main()
