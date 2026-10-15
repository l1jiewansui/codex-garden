import json,hashlib,unittest
from pathlib import Path
from PIL import Image
class SpecialPlantTests(unittest.TestCase):
 def test_palette_contact_and_manifest(self):
  folder=Path(__file__).resolve().parents[1]/'assets/pixel-v07'
  m=json.loads((folder/'specials.json').read_text(encoding='utf-8'));im=Image.open(folder/'specials.png').convert('RGBA')
  self.assertEqual(m['sha256'],hashlib.sha256((folder/'specials.png').read_bytes()).hexdigest())
  allowed={tuple(bytes.fromhex(v)) for v in m['palette']}
  for p in im.getdata():
   self.assertIn(p[3],(0,255))
   if p[3]:self.assertIn(p[:3],allowed)
  for kind in range(12):
   for stage in range(4):
    for frame in range(3):
     x,y=stage*28,(kind*3+frame)*28
     self.assertEqual(im.crop((x,y,x+28,y+28)).getbbox()[3],28)
