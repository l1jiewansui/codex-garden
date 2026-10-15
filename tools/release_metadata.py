"""Capture pinned dependencies, upstream license texts and official schemas."""
import hashlib,importlib.metadata as metadata,json,shutil,sys,urllib.request
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
out=ROOT/'release';licenses=out/'licenses';licenses.mkdir(exist_ok=True)
records=[]
if not (ROOT/'.work/mcp-deps').is_dir():raise RuntimeError('Install release/mcp-requirements.lock into .work/mcp-deps before capturing metadata')
for dist in sorted(metadata.distributions(path=[str(ROOT/'.work/mcp-deps')]),key=lambda d:d.metadata['Name'].lower()):
    name=dist.metadata['Name'];record={'name':name,'version':dist.version,'license':dist.metadata.get('License-Expression') or dist.metadata.get('License',''),'files':[]}
    for file in dist.files or []:
        if any(token in str(file).lower() for token in ('license','copying','notice')) and not str(file).endswith(('.py','.pyc')):
            source=Path(dist.locate_file(file));target=licenses/'python'/name/str(file)
            if source.is_file() and target.resolve().is_relative_to(licenses.resolve()):
                target.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(source,target);record['files'].append(target.relative_to(out).as_posix())
    records.append(record)
(out/'dependencies.json').write_text(json.dumps(records,ensure_ascii=False,indent=2),encoding='utf-8')
(out/'mcp-requirements.lock').write_text('\n'.join(f"{r['name']}=={r['version']}" for r in records)+'\n',encoding='ascii')
for name in ('pyinstaller','pyinstaller-hooks-contrib'):
    dist=metadata.distribution(name)
    for file in dist.files or []:
        if any(token in str(file).lower() for token in ('license','copying')):
            source=Path(dist.locate_file(file));target=licenses/'build-tools'/name/str(file)
            if source.is_file() and target.resolve().is_relative_to(licenses.resolve()):target.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(source,target)
source=next((p for p in (Path(sys.base_prefix)/'LICENSE.txt',Path(sys.base_prefix)/'LICENSE_PYTHON.txt') if p.is_file()),Path(sys.base_prefix)/'LICENSE.txt')
if not source.is_file():raise RuntimeError('Python license not found')
shutil.copy2(source,licenses/'Python-LICENSE.txt')
schemas=out/'schemas';schemas.mkdir(exist_ok=True)
for name in ('plugin','mcp'):
    url=f'https://agent-plugins.org/schemas/1.0.0/{name}.schema.json'
    data=urllib.request.urlopen(url,timeout=30).read();json.loads(data)
    (schemas/f'{name}.schema.json').write_bytes(data)
    print(name,hashlib.sha256(data).hexdigest())
print(f'{len(records)} pinned MCP runtime dependencies; license texts preserved')
