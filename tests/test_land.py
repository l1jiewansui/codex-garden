import unittest,json,hashlib
from pathlib import Path
from PIL import Image
ROOT=Path(__file__).resolve().parents[1]
class LandTests(unittest.TestCase):
    def test_plant_and_foot_contact_anchors(self):
        folder=ROOT/'assets/pixel-v04'
        manifest=json.loads((folder/'manifest.json').read_text(encoding='utf-8'))
        plants=Image.open(folder/'garden-kit.png')
        # Every crop stage reaches the retained root row; no transparent gap to y=60.
        for stages in manifest['crops']:
            for crop in stages:
                x,y,_,_=crop['sourceRect']
                self.assertEqual(plants.crop((x,y,x+32,y+20)).getbbox()[3],20)
        heroes=Image.open(folder/'gardeners.png')
        # The idle atlas used for standing and articulated walking has a stable sole.
        for hero in manifest['heroes']:
            for frame in hero['frames']:
                if frame['action']!='idle':continue
                x,y,_,_=frame['sourceRect']
                self.assertEqual(heroes.crop((x,y,x+48,y+48)).getbbox()[3],hero['origin'][1])
    def test_ground_is_processed_and_palette_bound(self):
        folder=ROOT/'assets/pixel-v05'
        proof=json.loads((folder/'pixel-checks.json').read_text())
        self.assertEqual(proof['sha256'],hashlib.sha256((folder/'land.png').read_bytes()).hexdigest())
        palette=json.loads((ROOT/'assets/pixel-v04/manifest.json').read_text(encoding='utf-8'))['pixelContract']['paletteHex']
        allowed={tuple(bytes.fromhex(c[1:])) for c in palette}
        im=Image.open(folder/'land.png').convert('RGBA')
        self.assertEqual(im.size,(16,14))
        for pixel in im.getdata():
            self.assertIn(pixel[3],(0,255))
            if pixel[3]:self.assertIn(pixel[:3],allowed)
        supplies=Image.open(folder/'farm-supplies.png').convert('RGBA')
        self.assertEqual(supplies.size,(36,20))
        self.assertEqual(supplies.getbbox()[3],20)
        self.assertIn('fixed-left-farm-supplies',[r['name'] for r in proof['records']])
        for pixel in supplies.getdata():
            self.assertIn(pixel[3],(0,255))
            if pixel[3]:self.assertIn(pixel[:3],allowed)
