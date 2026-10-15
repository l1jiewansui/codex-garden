"""Embed application identity; preserve crisp palette pixels in ICO conversion."""
import json
from pathlib import Path
from PIL import Image
from PyInstaller.utils.win32 import icon,versioninfo as v
from PyInstaller import config
ROOT=Path(__file__).resolve().parents[1]

def brand(executable):
    asset=ROOT/'assets/pixel-v04/tray-icon.png'
    source=Image.open(asset).convert('RGBA');sizes=(16,32,48,64,128,256)
    images=[source.resize((n,n),Image.Resampling.NEAREST) for n in sizes]
    target=ROOT/'release/garden.ico'
    images[-1].save(target,format='ICO',sizes=[(n,n) for n in sizes],append_images=images[:-1])
    with Image.open(target) as check:
        palette=set(source.getdata())
        for size in check.ico.sizes():
            if not set(check.ico.getimage(size).convert('RGBA').getdata())<=palette:raise RuntimeError('ICO palette changed')
    version=json.loads((ROOT/'package.json').read_text(encoding='utf-8'))['version']
    fields={'CompanyName':'risu1','FileDescription':'Qingyun Desktop Garden','FileVersion':version,'InternalName':'CodexGarden','OriginalFilename':'CodexGarden.exe','ProductName':'Qingyun Garden','ProductVersion':version,'LegalCopyright':'Copyright (c) 2026 risu1. Third-party notices included.'}
    numbers=tuple(map(int,version.split('-')[0].split('.')))+(int(version.rsplit('.',1)[-1]) if '-' in version and version.rsplit('.',1)[-1].isdigit() else 0,)
    info=v.VSVersionInfo(ffi=v.FixedFileInfo(filevers=numbers,prodvers=numbers,flags=2),kids=[v.StringFileInfo([v.StringTable('040904b0',[v.StringStruct(k,value) for k,value in fields.items()])]),v.VarFileInfo([v.VarStruct('Translation',[1033,1200])])])
    config.CONF['workpath']=str(ROOT/'.work')
    icon.CopyIcons(str(executable),str(target));v.write_version_info_to_executable(str(executable),info)
