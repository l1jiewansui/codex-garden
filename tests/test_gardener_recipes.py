import hashlib,json,unittest
from pathlib import Path
from PIL import Image

ROOT=Path(__file__).resolve().parents[1]

class GardenerRecipeTests(unittest.TestCase):
    def test_original_archive_is_complete_and_unchanged(self):
        root=ROOT/'archives/default-gardeners-rc11'
        checks=json.loads((root/'SHA256.json').read_text(encoding='utf-8'))
        for name,digest in checks.items():
            self.assertEqual(hashlib.sha256((root/name).read_bytes()).hexdigest(),digest,name)
        self.assertEqual((root/'original-actions.png').read_bytes(),(ROOT/'assets/pixel-v091/actions.png').read_bytes())
        manifest=json.loads((root/'manifest.json').read_text(encoding='utf-8'))
        self.assertEqual(len(manifest['gardeners']),3)
        for gardener in manifest['gardeners']:
            im=Image.open(root/gardener['sheet']).convert('RGBA')
            self.assertEqual(im.size,(432,192))
            for row,count,_ in manifest['actions'].values():
                for i in range(count):self.assertIsNotNone(im.crop((i*48,row*48,(i+1)*48,(row+1)*48)).getbbox())

    def test_shipped_recipes_and_face_layers_have_source_provenance(self):
        root=ROOT/'assets/pixel-lpc'
        m=json.loads((root/'manifest.json').read_text(encoding='utf-8'))
        self.assertEqual(m['version'],2)
        self.assertEqual(hashlib.sha256((root/'recipes.json').read_bytes()).hexdigest(),m['recipeSha256'])
        self.assertEqual((root/'recipes.json').read_bytes(),(ROOT/'assets/gardener-recipes.json').read_bytes())
        recipes=json.loads((root/'recipes.json').read_text(encoding='utf-8'))
        self.assertEqual(len(recipes['defaults']),3)
        self.assertEqual(len({p['recipe']['face'] for p in recipes['defaults']}),3)
        self.assertTrue(all('template' not in p['recipe'] for p in recipes['defaults']+recipes['extras']))
        source=json.loads((ROOT/'assets/lpc-gardeners/manifest.json').read_text(encoding='utf-8'))
        faces=[]
        for key,part in m['parts'].items():
            raw=(root/part['file']).read_bytes()
            self.assertEqual(hashlib.sha256(raw).hexdigest(),part['sha256'],key)
            self.assertEqual(part['sourceSha256'],source['parts'][key]['sha256'])
            if key.startswith('head'):faces.append(part['sha256'])
            im=Image.open(root/part['file']).convert('RGBA')
            for r,g,b,a in im.getdata():
                self.assertIn(a,(0,255))
                if a:
                    self.assertLessEqual(r,8)
                    self.assertLess(g,len(m['palette']) if r==0 else 6)
        self.assertEqual(len(set(faces)),6)

if __name__=='__main__':unittest.main()
