import unittest,json,hashlib
from pathlib import Path
from PIL import Image
class CropV07Tests(unittest.TestCase):
 def test_root_contact_animation_and_pixel_contract(self):
  folder=Path(__file__).resolve().parents[1]/'assets/pixel-v07'
  m=json.loads((folder/'manifest.json').read_text());allowed={tuple(bytes.fromhex(c)) for c in m['palette']}
  for name,digest in m['sha256'].items():
   self.assertEqual(hashlib.sha256((folder/name).read_bytes()).hexdigest(),digest)
   for p in Image.open(folder/name).convert('RGBA').getdata():
    self.assertIn(p[3],(0,255))
    if p[3]:self.assertIn(p[:3],allowed)
  atlas=Image.open(folder/'crops.png')
  for variety in range(3):
   for kind in range(3):
    for stage in range(4):
     roots=[]
     for frame in range(3):
      x,y=stage*28,(variety*9+kind*3+frame)*28;im=atlas.crop((x,y,x+28,y+28))
      self.assertEqual(im.getbbox()[3],28);roots.append(im.crop((0,26,28,28)).tobytes())
     self.assertEqual(roots[0],roots[1]);self.assertEqual(roots[1],roots[2])
    y=(variety*9+kind*3)*28
    growing=atlas.crop((56,y,84,y+28));ripe=atlas.crop((84,y,112,y+28))
    self.assertGreater(sum(p[3]>0 for p in ripe.getdata()),sum(p[3]>0 for p in growing.getdata())*1.25)
  for kind in range(3):
   self.assertEqual(len({atlas.crop((84,(v*9+kind*3)*28,112,(v*9+kind*3)*28+28)).tobytes() for v in range(3)}),3)
