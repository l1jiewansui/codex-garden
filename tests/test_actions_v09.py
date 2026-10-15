import unittest,json,hashlib
from pathlib import Path
from PIL import Image
class IndependentActionsTests(unittest.TestCase):
 def test_complete_palette_bound_actions(self):
  folder=Path(__file__).resolve().parents[1]/'assets/pixel-v091'
  m=json.loads((folder/'manifest.json').read_text());im=Image.open(folder/'actions.png').convert('RGBA')
  self.assertEqual(hashlib.sha256((folder/'actions.png').read_bytes()).hexdigest(),m['sha256'])
  allowed={tuple(bytes.fromhex(v)) for v in m['palette']}
  for p in im.getdata():
   self.assertIn(p[3],(0,255))
   if p[3]:self.assertIn(p[:3],allowed)
  for hero in range(4):
   frames=[v for v in m['frames'] if v['hero']==hero]
   self.assertEqual([v['action'] for v in frames],['idle']*2+['water']*3+['feed']*3)
   samples=[]
   for f in frames:
    x,y,w,h=f['rect'];cell=im.crop((x,y,x+w,y+h));self.assertIsNotNone(cell.getbbox());samples.append(cell.tobytes())
   self.assertNotEqual(samples[0],samples[3]);self.assertNotEqual(samples[3],samples[6])
