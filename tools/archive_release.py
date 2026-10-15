"""Verify the release folder and create a distributable archive with checksums."""
import hashlib,json,zipfile
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
source=ROOT/'dist/desktop-pet-rc010'
target=ROOT/'dist/QingyunGarden-0.10.0-rc.1-Windows.zip'
partial=target.with_suffix('.zip.part')
for path in (source,target,partial):
    if not path.resolve().is_relative_to((ROOT/'dist').resolve()):raise ValueError('Release path outside dist')
manifest=json.loads((source/'SHA256.json').read_text(encoding='utf-8'))
for relative,digest in manifest.items():
    path=(source/relative).resolve()
    if not path.is_relative_to(source.resolve()):raise ValueError('Invalid release manifest path')
    if hashlib.sha256(path.read_bytes()).hexdigest()!=digest:raise ValueError('Release checksum mismatch: '+relative)
with zipfile.ZipFile(partial,'w',zipfile.ZIP_DEFLATED,compresslevel=6) as archive:
    for path in source.rglob('*'):
        if path.is_file():archive.write(path,'QingyunGarden/'+path.relative_to(source).as_posix())
partial.replace(target)
digest=hashlib.sha256(target.read_bytes()).hexdigest()
target.with_suffix('.zip.sha256').write_text(digest+'  '+target.name+'\n',encoding='ascii')
print(f'{target} ({target.stat().st_size//1024//1024} MiB), {len(manifest)} files verified')
