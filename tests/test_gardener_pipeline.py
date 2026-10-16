import hashlib,json,tempfile,unittest
from pathlib import Path
from PIL import Image,ImageDraw
from backend.gardener_pipeline import compile_sheet,remove_matte

PALETTE=['25252f','36343a','d99d73','f7f1dc','37536a','4d7387','b0c9c7','9b6c47']

def source_sheet(path,empty=False,static=False):
    im=Image.new('RGBA',(256,256),(255,0,255,255));d=ImageDraw.Draw(im)
    for r in range(4):
        for c in range(4):
            if empty and (r,c)==(3,3):continue
            x,y=c*64,r*64
            d.rectangle((x+24,y+12,x+38,y+48),fill='#37536a')
            d.rectangle((x+25,y+13,x+37,y+23),fill='#f7f1dc')
            offset=0 if static else c
            d.rectangle((x+39,y+30-offset,x+43,y+36-offset),fill='#d99d73')
    im.save(path)

class GardenerPipelineTests(unittest.TestCase):
    def test_complete_candidate_preserves_anchor_palette_and_review_gate(self):
        with tempfile.TemporaryDirectory() as tmp:
            src=Path(tmp)/'source.png';out=Path(tmp)/'candidate';source_sheet(src)
            m=compile_sheet(src,out,PALETTE)
            self.assertEqual(len(m['frames']),16);self.assertEqual(m['origin'],[24,44])
            self.assertFalse(m['visualApproved']);self.assertTrue(m['technicalPassed'])
            self.assertEqual(m['sheetSha256'],hashlib.sha256((out/'sheet.png').read_bytes()).hexdigest())
            im=Image.open(out/'sheet.png').convert('RGBA');pixels=list(im.getdata())
            self.assertLessEqual({p[3] for p in pixels},{0,255})
            self.assertLessEqual({p[:3] for p in pixels if p[3]},{tuple(bytes.fromhex(c)) for c in PALETTE})
            self.assertTrue(any(p[:3]==(247,241,220) and p[3] for p in pixels),'white hair must survive matte removal')
            with self.assertRaises(ValueError):compile_sheet(src,out,PALETTE)

    def test_empty_or_static_action_does_not_install_candidate(self):
        with tempfile.TemporaryDirectory() as tmp:
            for mode in ('empty','static'):
                src=Path(tmp)/(mode+'.png');out=Path(tmp)/mode
                source_sheet(src,empty=mode=='empty',static=mode=='static')
                with self.assertRaises(ValueError):compile_sheet(src,out,PALETTE)
                self.assertFalse(out.exists())

    def test_color_key_only_removes_exterior(self):
        im=Image.new('RGBA',(12,12),'magenta');d=ImageDraw.Draw(im)
        d.rectangle((2,2,9,9),fill='#36343a');d.rectangle((4,4,7,7),fill='magenta')
        out=remove_matte(im)
        self.assertEqual(out.getpixel((0,0))[3],0);self.assertEqual(out.getpixel((5,5))[3],255)
