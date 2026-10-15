import json,hashlib,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]/'assets/art-v04'

class ArtManifestTests(unittest.TestCase):
    def test_original_atlases_and_complete_assets(self):
        m=json.loads((ROOT/'manifest.json').read_text(encoding='utf-8'))
        self.assertEqual(len(m['heroes']),4)
        self.assertEqual(sum(len(h['frames']) for h in m['heroes']),32)
        self.assertEqual(sum(len(row) for row in m['crops']),12)
        self.assertEqual(set(m['icons']),{'sparkle','care','seeds','app'})
        for key,name in m['images'].items():
            self.assertEqual(hashlib.sha256((ROOT/name).read_bytes()).hexdigest(),m['sourceSha256'][key])
    def test_animation_crops_do_not_touch_edges(self):
        checks=json.loads((ROOT/'atlas-checks.json').read_text(encoding='utf-8'))
        self.assertEqual(checks['edgeTouches'],0)
        self.assertEqual(len(checks['frames']),32)
