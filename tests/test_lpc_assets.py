import hashlib,json,unittest
from pathlib import Path
from PIL import Image

class LpcArtworkTests(unittest.TestCase):
    def test_pinned_layers_complete_real_motion_and_credits(self):
        root=Path(__file__).resolve().parents[1]/'assets/lpc-gardeners'
        m=json.loads((root/'manifest.json').read_text(encoding='utf-8'))
        self.assertEqual(m['commit'],'9bf06be193b053db256b2536824af426de046aa2')
        self.assertEqual(m['origin'],[24,44])
        credits=json.loads((root/'CREDITS.json').read_text(encoding='utf-8'))
        for key,part in m['parts'].items():
            p=root/part['file'];self.assertEqual(hashlib.sha256(p.read_bytes()).hexdigest(),part['sha256'])
            self.assertIn(part['definition'],credits)
            im=Image.open(p).convert('RGBA');self.assertEqual(im.size,(576,256))
            for action,a in m['actions'].items():
                samples=[im.crop((f*64,a['row']*64,(f+1)*64,(a['row']+1)*64)) for f in range(a['frames'])]
                if key in ('can','canBack'):continue
                self.assertTrue(all(f.getbbox() for f in samples),(key,action))
                if action!='idle':self.assertGreater(len({f.tobytes() for f in samples}),1,(key,action))
        can=Image.alpha_composite(Image.open(root/'canBack.png').convert('RGBA'),Image.open(root/'can.png').convert('RGBA'))
        for a in ('idle','walk','water'):
            row=m['actions'][a]['row']
            for f in range(m['actions'][a]['frames']):
                self.assertIsNotNone(can.crop((f*64,row*64,(f+1)*64,(row+1)*64)).getbbox(),(a,f))
        for name in ['OGA-BY-3.0.txt','CC-BY-SA-3.0.txt','CC-BY-SA-4.0.txt']:
            self.assertGreater((root/name).stat().st_size,10000)
