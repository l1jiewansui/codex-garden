"""Editable native projects and real LibreSprite batch compilation.

seed creates layered projects once. compile reads those projects with LibreSprite,
not with the extraction heuristic. Runtime needs only the resulting PNGs.
"""
import argparse,hashlib,json,struct,subprocess,tempfile,zlib
from pathlib import Path
from PIL import Image
ROOT=Path(__file__).resolve().parents[1]
ASSETS=ROOT/'assets/pixel-classic';ART=ROOT/'art/classic'
H=lambda data:hashlib.sha256(data).hexdigest()
def chunk(kind,data):return struct.pack('<IH',len(data)+6,kind)+data
def string(s):
 b=s.encode('utf-8');return struct.pack('<H',len(b))+b

def write_project(path,manifest,material=False):
 names=list(manifest['parts']);default={'scalp0','hairBack0','boots0','coat0','shirt0','face0','hairFront0','hat0','tools0'}
 frames=[];sequence=[(action,a,f) for action,a in manifest['actions'].items() for f in range(a['frames'])]
 images={name:Image.open(ASSETS/p['material' if material else 'file']).convert('RGBA') for name,p in manifest['parts'].items()}
 for number,(action,a,f) in enumerate(sequence):
  chunks=[]
  if number==0:
   for name in names:
    visible=name in default if not material else name=='face0'
    chunks.append(chunk(0x2004,struct.pack('<HHHHHHB3x',3 if visible else 2,0,0,0,0,0,255)+string(name)))
   tags=struct.pack('<H8x',len(manifest['actions']));offset=0
   for label,v in manifest['actions'].items():tags+=struct.pack('<HHB8xBBBB',offset,offset+v['frames']-1,0,106,139,72,0)+string(label);offset+=v['frames']
   chunks.append(chunk(0x2018,tags))
  for index,name in enumerate(names):
   head=name.startswith(('scalp','face','hair','hat')) or name=='beard'
   dx,dy=manifest['headPoses'][action][f] if head else (0,0)
   if head and number>0:payload=struct.pack('<HhhBH7xH',index,dx,dy,255,1,0)
   else:
    im=images[name].crop((f*48,a['row']*48,(f+1)*48,(a['row']+1)*48));payload=struct.pack('<HhhBH7xHH',index,0,0,255,2,48,48)+zlib.compress(im.tobytes(),9)
   chunks.append(chunk(0x2005,payload))
  body=b''.join(chunks);frames.append(struct.pack('<IHHH6x',len(body)+16,0xF1FA,len(chunks),a['durationMs'])+body)
 header=bytearray(128);struct.pack_into('<IHHHHHIH',header,0,128+sum(map(len,frames)),0xA5E0,len(frames),48,48,32,1,100);header[34:36]=bytes([1,1]);path.write_bytes(header+b''.join(frames))

def compile_projects(editor):
 manifest=json.loads((ASSETS/'manifest.json').read_text(encoding='utf-8'));editor=Path(editor).resolve()
 if not editor.is_file():raise ValueError('LibreSprite executable not found; run tools/setup_classic_editor.py')
 results={};provenance=[]
 with tempfile.TemporaryDirectory(prefix='classic-editor-',dir=ROOT/'.work') as tmp:
  tmp=Path(tmp)
  for material in (False,True):
   source=ART/('native-materials.aseprite' if material else 'native-parts.aseprite')
   for name,part in manifest['parts'].items():
    sheet=tmp/(name+('-material' if material else '')+'.png')
    command=[str(editor),'--batch','--all-layers','--layer',name,str(source),'--sheet-width','1200','--sheet-height','48','--sheet',str(sheet),'--data',str(sheet.with_suffix('.json'))]
    process=subprocess.run(command,cwd=ROOT,timeout=30,creationflags=getattr(subprocess,'CREATE_NO_WINDOW',0),capture_output=True)
    if process.returncode or not sheet.is_file():raise ValueError('LibreSprite failed to export '+name)
    exported=Image.open(sheet).convert('RGBA')
    if exported.size!=(1200,48):raise ValueError('Editor resized or trimmed the frame canvas: '+name+str(exported.size))
    metadata=json.loads(sheet.with_suffix('.json').read_text(encoding='utf-8'));frames=list(metadata['frames'].values());assert len(frames)==25
    atlas=Image.new('RGBA',(432,192));offset=0
    for a in manifest['actions'].values():
     for f in range(a['frames']):
      frame=frames[offset];rect=frame['frame'];assert not frame['rotated'] and not frame['trimmed'] and frame['duration']==a['durationMs']
      assert frame['sourceSize']=={'w':48,'h':48} and rect['w']==48 and rect['h']==48
      atlas.paste(exported.crop((rect['x'],rect['y'],rect['x']+48,rect['y']+48)),(f*48,a['row']*48));offset+=1
    results[(name,material)]=atlas
   provenance.append({'file':source.relative_to(ROOT).as_posix(),'sha256':H(source.read_bytes())})
  for name in manifest['parts']:
   if results[name,False].getchannel('A').tobytes()!=results[name,True].getchannel('A').tobytes():raise ValueError('Art/material coverage mismatch: '+name)
  # Commit only after every layer exported and semantic masks matched.
  for (name,material),im in results.items():
   key='material' if material else 'file';im.save(ASSETS/manifest['parts'][name][key]);manifest['parts'][name]['materialSha256' if material else 'sha256']=H((ASSETS/manifest['parts'][name][key]).read_bytes())
 manifest['editor']={'repository':'https://github.com/LibreSprite/LibreSprite','version':'v1.3','commit':'cdb12a323ce5ec4fce3512bc6590a90228f15bb9','binarySha256':H(editor.read_bytes()),'sources':provenance,'exportedLayers':len(results),'linkedHeadCels':True,'canvas':[48,48],'frameCount':25}
 (ASSETS/'manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2),encoding='utf-8')
 (ROOT/'verification/classic-editor-roundtrip.json').write_text(json.dumps({'passed':True,**manifest['editor']},indent=2),encoding='utf-8')
 print('LibreSprite compiled layers:',len(results),'; linked head cels and masks verified')

if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('action',choices=['seed','compile']);p.add_argument('--editor',default=str(ROOT/'.work/libresprite-v1.3/libresprite.exe'));args=p.parse_args()
 if args.action=='seed':
  ART.mkdir(parents=True,exist_ok=True);m=json.loads((ASSETS/'manifest.json').read_text(encoding='utf-8'))
  for name in ['native-parts.aseprite','native-materials.aseprite']:
   if (ART/name).exists():raise ValueError('Preserve the existing authored project before seeding again')
  write_project(ART/'native-parts.aseprite',m);write_project(ART/'native-materials.aseprite',m,True);print('Created editable projects with linked head cels and four action tags')
 else:compile_projects(args.editor)
