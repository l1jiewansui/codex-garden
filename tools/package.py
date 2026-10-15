"""Build a Windows portable folder from the installed Electron runtime."""
import json, shutil, hashlib, tempfile, time
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'dist/desktop-pet-rc010'
def build():
    if not (ROOT/'runtime/garden-bridge.exe').exists():raise RuntimeError('先构建 runtime/garden-bridge.exe，见 README')
    (ROOT/'.work').mkdir(exist_ok=True)
    staging=Path(tempfile.mkdtemp(prefix='garden-package-',dir=ROOT/'.work'))
    shutil.copytree(ROOT/'node_modules/electron/dist',staging,dirs_exist_ok=True)
    executable=staging/'electron.exe'
    executable.replace(staging/'CodexGarden.exe')
    from windows_branding import brand
    brand(staging/'CodexGarden.exe')
    app=staging/'resources/app';app.mkdir(parents=True,exist_ok=True)
    for name in ('main.cjs','update-policy.cjs','PRIVACY.md','preload.cjs','desktop-model.cjs','qa.cjs','package.json','README-PET.md'):
        shutil.copy2(ROOT/name,app/name)
    (app/'runtime').mkdir();shutil.copy2(ROOT/'runtime/garden-bridge.exe',app/'runtime/garden-bridge.exe')
    # Publish only processed art and the active desktop view. Raw originals remain in the authoring workspace.
    shutil.copytree(ROOT/'assets/pixel-v04',app/'assets/pixel-v04')
    shutil.copytree(ROOT/'assets/pixel-v05',app/'assets/pixel-v05',ignore=shutil.ignore_patterns('signpost.png'))
    shutil.copytree(ROOT/'assets/pixel-v07',app/'assets/pixel-v07')
    shutil.copytree(ROOT/'assets/pixel-v091',app/'assets/pixel-v091')
    (app/'web').mkdir(exist_ok=True)
    for name in ('pet.html','pet.js','pet.css','art-v04.css','pixel-v04.css','model.js'):
        shutil.copy2(ROOT/'web'/name,app/'web'/name)
    for name in ('Install.ps1','Uninstall.ps1','Install.cmd'):
        shutil.copy2(ROOT/'tools'/name,staging/name)
    shutil.copy2(ROOT/'README-PET.md',staging/'READ-ME.md')
    shutil.copy2(ROOT/'PRIVACY.md',staging/'PRIVACY.md')
    shutil.copy2(ROOT/'release/THIRD-PARTY-NOTICES.md',staging/'THIRD-PARTY-NOTICES.md')
    for name in ('dependencies.json','build-toolchain.json'):
        shutil.copy2(ROOT/'release'/name,staging/name)
    shutil.copytree(ROOT/'release/licenses',staging/'licenses')
    records={str(p.relative_to(staging)):hashlib.sha256(p.read_bytes()).hexdigest() for p in staging.rglob('*') if p.is_file() and p.name!='SHA256.json'}
    (staging/'SHA256.json').write_text(json.dumps(records,indent=2),encoding='utf-8')
    OUT.parent.mkdir(exist_ok=True)
    backup=ROOT/'.work'/('previous-package-'+str(time.time_ns()))
    # Windows directory moves: verify all resolved targets stay in this workspace.
    for target in (staging,OUT,backup):
        if not target.resolve().is_relative_to(ROOT.resolve()):raise RuntimeError('打包路径越界')
    if OUT.exists():OUT.rename(backup)
    staging.rename(OUT)
    print(f'Portable application ready: {OUT}/CodexGarden.exe ({len(records)} files)')
if __name__=='__main__':build()
