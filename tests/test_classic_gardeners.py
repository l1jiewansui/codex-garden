import hashlib,json,unittest
from pathlib import Path
from PIL import Image

ROOT=Path(__file__).resolve().parents[1]

class NativeGardenerTests(unittest.TestCase):
    def test_original_idle_walk_and_registered_action_hashes(self):
        root=ROOT/'assets/pixel-classic'
        m=json.loads((root/'manifest.json').read_text(encoding='utf-8'))
        archive=ROOT/m['sourceArchive']
        self.assertEqual(len(m['parts']),37)
        frames=0
        for actor,reference in enumerate(m['reference']):
            restored=Image.new('RGBA',(432,192))
            for part in ('scalp','hairBack','boots','coat','shirt','face','hairFront','hat','tools'):
                restored.alpha_composite(Image.open(root/m['parts'][part+str(actor)]['file']).convert('RGBA'))
            original=Image.open(archive/f'gardener-{actor+1}.png').convert('RGBA')
            for row,count in [(0,2),(1,9)]:
                box=(0,row*48,count*48,(row+1)*48)
                self.assertEqual(restored.crop(box).tobytes(),original.crop(box).tobytes(),reference['name'])
            self.assertEqual(hashlib.sha256(restored.tobytes()).hexdigest(),reference['rgbaSha256'])
            frames+=sum(a['frames'] for a in m['actions'].values())
        self.assertEqual(frames,75)

    def test_linked_head_pose_registration_and_editor_sources(self):
        root=ROOT/'assets/pixel-classic'
        m=json.loads((root/'manifest.json').read_text(encoding='utf-8'))
        self.assertEqual(m['editor']['repository'],'https://github.com/LibreSprite/LibreSprite')
        self.assertEqual(m['editor']['exportedLayers'],74)
        for source in m['editor']['sources']:
            self.assertEqual(hashlib.sha256((ROOT/source['file']).read_bytes()).hexdigest(),source['sha256'])
        for name,part in m['parts'].items():
            if not (name.startswith(('scalp','face','hair','hat')) or name=='beard'):continue
            for key in ('file','material'):
                atlas=Image.open(root/part[key]).convert('RGBA');first=atlas.crop((0,0,48,48))
                for action,a in m['actions'].items():
                    for f,(dx,dy) in enumerate(m['headPoses'][action]):
                        expected=Image.new('RGBA',(48,48));expected.paste(first,(dx,dy))
                        actual=atlas.crop((f*48,a['row']*48,(f+1)*48,(a['row']+1)*48))
                        self.assertEqual(actual.tobytes(),expected.tobytes(),name+key+action)

    def test_iris_masks_only_cover_registered_eye_pixels(self):
        root=ROOT/'assets/pixel-classic';m=json.loads((root/'manifest.json').read_text(encoding='utf-8'))
        for actor in range(3):
            im=Image.open(root/m['parts']['face'+str(actor)]['material']).convert('RGBA')
            for action,a in m['actions'].items():
                for f,(dx,dy) in enumerate(m['headPoses'][action]):
                    points=[]
                    for y in range(48):
                        for x in range(48):
                            r,g,b,alpha=im.getpixel((f*48+x,a['row']*48+y))
                            if alpha and r==8:points.append([x-dx,y-dy])
                    self.assertEqual(sorted(points),sorted(m['eyePixels'][actor]))

    def test_materials_and_drawn_variants_are_real_parts(self):
        root=ROOT/'assets/pixel-classic';m=json.loads((root/'manifest.json').read_text(encoding='utf-8'))
        for name,part in m['parts'].items():
            for key,checksum in [('file','sha256'),('material','materialSha256')]:
                self.assertEqual(hashlib.sha256((root/part[key]).read_bytes()).hexdigest(),part[checksum],name)
            image=Image.open(root/part['file']).convert('RGBA')
            mask=Image.open(root/part['material']).convert('RGBA')
            self.assertEqual(image.size,(432,192))
            self.assertEqual(image.getchannel('A').tobytes(),mask.getchannel('A').tobytes())
            self.assertLess(sum(a>0 for a in image.getchannel('A').get_flattened_data()),20000)
        for group in [('hairFront0','hairFront1','hairFront2','hairFront-curly','hairBack-pony','hairBack-braid'),('face0','face1','face2','face-round','face-small','face-elder')]:
            self.assertEqual(len({m['parts'][name]['sha256'] for name in group}),len(group))

if __name__=='__main__':unittest.main()
