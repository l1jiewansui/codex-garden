"""Save only the declared font license texts, preserving upstream paths; no archive extraction."""
from pathlib import Path
import urllib.request,zipfile,io
ROOT=Path(__file__).resolve().parents[1]/'assets/pixel-v04/font-licenses'
URL='https://github.com/TakWolf/fusion-pixel-font/releases/download/2026.09.25/fusion-pixel-font-12px-proportional-otf.woff2-v2026.09.25.zip'
ALLOWED=['OFL.txt','LICENSES/ark-pixel/OFL.txt','LICENSES/cubic-11/OFL.txt','LICENSES/galmuri/LICENSE.txt']
def main():
    with urllib.request.urlopen(URL,timeout=60) as r:data=r.read()
    with zipfile.ZipFile(io.BytesIO(data)) as z:
        for name in ALLOWED:
            target=ROOT/name
            if not target.resolve().is_relative_to(ROOT.resolve()):raise ValueError('License path outside destination')
            target.parent.mkdir(parents=True,exist_ok=True)
            target.write_bytes(z.read(name))
    print('Saved 4 upstream font license texts with preserved paths.')
if __name__=='__main__':main()
