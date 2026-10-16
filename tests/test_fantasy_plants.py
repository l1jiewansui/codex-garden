from pathlib import Path
import unittest,json,hashlib
from PIL import Image
class FantasyPlantTests(unittest.TestCase):
 def test_rooted_animation_palette_and_distinct_silhouettes(self):
  root=Path(__file__).resolve().parents[1];folder=root/'assets/pixel-fantasy'
  m=json.loads((folder/'manifest.json').read_text(encoding='utf-8'));im=Image.open(folder/'plants.png').convert('RGBA')
  self.assertEqual(hashlib.sha256((folder/'plants.png').read_bytes()).hexdigest(),m['sha256'])
  palette={tuple(bytes.fromhex(v[1:])) for v in json.loads((root/'assets/pixel-v04/manifest.json').read_text(encoding='utf-8'))['pixelContract']['paletteHex']}
  for p in im.getdata():
   self.assertIn(p[3],(0,255))
   if p[3]:self.assertIn(p[:3],palette)
  silhouettes=[]
  for kind in range(6):
   poses=[]
   for frame in range(6):
    cell=im.crop((84,(kind*6+frame)*28,112,(kind*6+frame+1)*28))
    self.assertEqual(cell.getbbox()[3],28);poses.append(cell.tobytes())
    self.assertEqual(cell.crop((0,27,28,28)).tobytes(),im.crop((84,kind*6*28+27,112,kind*6*28+28)).tobytes())
   self.assertGreater(len(set(poses)),2);silhouettes.append(poses[0])
  self.assertEqual(len(set(silhouettes)),6)
