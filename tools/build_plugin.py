"""Assemble local-test plugin. Public eligibility is checked separately."""
import hashlib,json,shutil,zipfile
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
from release_paths import APP,PLUGIN,PLUGIN_ZIP

def build():
    app=APP;server=ROOT/'runtime/garden-mcp.exe'
    if not app.is_dir() or not server.is_file():raise RuntimeError('Build application and MCP executable first')
    target=PLUGIN
    if target.exists():raise RuntimeError('Plugin output already exists; preserve it before rebuilding')
    shutil.copytree(ROOT/'plugin',target)
    publisher=json.loads((ROOT/'release/PUBLISHER.json').read_text(encoding='utf-8'))
    manifest=json.loads((target/'plugin.json').read_text(encoding='utf-8'))
    for field in ('websiteURL','supportURL','privacyPolicyURL','termsOfServiceURL'):
        if publisher.get(field):manifest['extensions']['com.openai']['interface'][field]=publisher[field]
    (target/'plugin.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2),encoding='utf-8')
    shutil.copytree(app,target/'app')
    (target/'server').mkdir();shutil.copy2(server,target/'server/garden-mcp.exe')
    shutil.copytree(ROOT/'release/licenses',target/'licenses')
    shutil.copy2(ROOT/'release/dependencies.json',target/'dependencies.json')
    for source,destination in [('PRIVACY.md','PRIVACY.md'),('release/PLUGIN-INSTALL.md','README.md'),('release/THIRD-PARTY-NOTICES.md','THIRD-PARTY-NOTICES.md')]:shutil.copy2(ROOT/source,target/destination)
    records={p.relative_to(target).as_posix():hashlib.sha256(p.read_bytes()).hexdigest() for p in target.rglob('*') if p.is_file()}
    (target/'SHA256.json').write_text(json.dumps(records,indent=2),encoding='utf-8')
    archive=PLUGIN_ZIP
    with zipfile.ZipFile(archive,'w',zipfile.ZIP_DEFLATED,compresslevel=6) as z:
        for p in target.rglob('*'):
            if p.is_file():z.write(p,p.relative_to(target).as_posix())
    archive.with_suffix('.zip.sha256').write_text(hashlib.sha256(archive.read_bytes()).hexdigest()+'  '+archive.name+'\n',encoding='ascii')
    print(target)
if __name__=='__main__':build()
