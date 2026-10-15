"""Format existing processed pixels for listing; no new source art."""
from pathlib import Path
from PIL import Image
import shutil
ROOT=Path(__file__).resolve().parents[1];out=ROOT/'plugin/assets';out.mkdir(exist_ok=True)
source=Image.open(ROOT/'assets/pixel-v04/tray-icon.png').convert('RGBA')
palette=set(source.getdata())
for name,size in (('icon',64),('logo',256)):
    image=source.resize((size,size),Image.Resampling.NEAREST)
    assert set(image.getdata())<=palette
    image.save(out/(name+'.png'))
shutil.copy2(ROOT/'verification/garden-v091.png',out/'garden.png')
print('Listing icons retain source palette and hard alpha; screenshot uses demo data.')
