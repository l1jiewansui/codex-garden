"""Fetch the pinned official portable LibreSprite editor for local art builds."""
import hashlib,urllib.request,zipfile
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
URL='https://github.com/LibreSprite/LibreSprite/releases/download/v1.3/libresprite-v1.3-windows-x86_64.zip'
SHA256='8408d2f962121948e9fbee053756b5e1e7e88d6d645120574d13fca66d475874'

if __name__=='__main__':
    target=ROOT/'.work/libresprite-v1.3';target.mkdir(parents=True,exist_ok=True)
    archive=target/'libresprite-v1.3-windows-x86_64.zip'
    if not archive.exists():urllib.request.urlretrieve(URL,archive)
    if hashlib.sha256(archive.read_bytes()).hexdigest()!=SHA256:raise ValueError('LibreSprite archive checksum mismatch')
    with zipfile.ZipFile(archive) as z:
        for name in z.namelist():
            if not (target/name).resolve().is_relative_to(target.resolve()):raise ValueError('Invalid editor archive path')
        z.extractall(target)
    print(target/'libresprite.exe')
