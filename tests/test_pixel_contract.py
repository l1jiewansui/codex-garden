import json,hashlib,unittest
from pathlib import Path
from PIL import Image
ROOT=Path(__file__).resolve().parents[1]
ART=ROOT/'assets/pixel-v04'

class PixelContractTests(unittest.TestCase):
    def test_every_published_bitmap_uses_palette_and_binary_alpha(self):
        m=json.loads((ART/'manifest.json').read_text(encoding='utf-8'))
        palette={tuple(bytes.fromhex(c[1:])) for c in m['pixelContract']['paletteHex']}
        self.assertEqual(len(palette),47)
        for path in ART.glob('*.png'):
            with self.subTest(image=path.name),Image.open(path) as im:
                pixels=list(im.convert('RGBA').getdata())
                self.assertLessEqual({p[3] for p in pixels},{0,255})
                self.assertLessEqual({p[:3] for p in pixels if p[3]},palette)
                self.assertGreater(sum(p[3]>0 for p in pixels),0)
        for key,file in m['images'].items():
            self.assertEqual(hashlib.sha256((ART/file).read_bytes()).hexdigest(),m['sourceSha256'][key])
    def test_actions_keep_fixed_canvas_and_original_timing(self):
        m=json.loads((ART/'manifest.json').read_text(encoding='utf-8'))
        raw=json.loads((ROOT/'assets/art-v04/manifest.json').read_text(encoding='utf-8'))
        for hero,source in zip(m['heroes'],raw['heroes']):
            self.assertEqual(hero['frameSize'],[48,48])
            self.assertEqual(hero['origin'],[24,44])
            self.assertEqual([f['durationMs'] for f in hero['frames']],[f['durationMs'] for f in source['frames']])
            self.assertTrue(all(f['sourceRect'][2:]==[48,48] for f in hero['frames']))
        self.assertEqual(len(m['images']),9)
        self.assertTrue((ART/'fusion-pixel-12px.woff2').exists())
        self.assertTrue((ART/'font-licenses/OFL.txt').exists())
