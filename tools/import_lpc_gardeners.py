"""Vendor a small, pinned set of LPC artwork; no generator code or AI service.
All source artwork keeps its own credits/license. Runtime composes real frames.
"""
import json,hashlib,shutil,subprocess
from pathlib import Path
from PIL import Image
ROOT=Path(__file__).resolve().parents[1];SRC=ROOT/'.work/lpc-generator';OUT=ROOT/'assets/lpc-gardeners'
PARTS={
 'body':('body/bodies/male','body/body'),
 'head':('head/heads/human/male','head/heads/human/heads_human_male'),
 'headSoft':('head/heads/human/female','head/heads/human/heads_human_female'),
 'headRound':('head/heads/human/male_plump','head/heads/human/heads_human_male_plump'),
 'headAngular':('head/heads/human/male_gaunt','head/heads/human/heads_human_male_gaunt'),
 'headElder':('head/heads/human/male_elderly','head/heads/human/heads_human_male_elderly'),
 'headSmall':('head/heads/human/male_small','head/heads/human/heads_human_male_small'),
 'noseButton':('head/nose/button/adult','head/nose/head_nose_button'),
 'noseLarge':('head/nose/large/adult','head/nose/head_nose_large'),
 'noseStraight':('head/nose/straight/adult','head/nose/head_nose_straight'),
 'curly':('hair/curly_short/adult','hair/curly/hair_curly_short'),
 'pixie':('hair/pixie/adult','hair/short/hair_pixie'),
 'ponyBack':('hair/ponytail/adult/bg','hair/braids/hair_ponytail'),
 'pony':('hair/ponytail/adult/fg','hair/braids/hair_ponytail'),
 'braidBack':('hair/braid/adult/bg','hair/braids/hair_braid'),
 'braid':('hair/braid/adult/fg','hair/braids/hair_braid'),
 'hat':(json.loads((SRC/'sheet_definitions/headwear/hats/caps/hat_cap_bonnie.json').read_text(encoding='utf-8'))['layer_1']['male'].rstrip('/'),'headwear/hats/caps/hat_cap_bonnie'),
 'beard':('beards/beard/basic','hair/beards/beards_beard'),
 'shirt':('torso/clothes/longsleeve/longsleeve/male','torso/shirts/longsleeve/torso_clothes_longsleeve'),
 'overalls':('torso/aprons/overalls/male','torso/aprons/torso_aprons_overalls'),
 'pants':('legs/pants/male','legs/pants/legs_pants'),
 'boots':('feet/boots/basic/male','feet/boots/feet_boots_basic'),
 'canBack':('tools/watering_can/bg','tools/tool_watering_can'),
 'can':('tools/watering_can/fg','tools/tool_watering_can')}
ACTIONS=[('idle','walk',2),('walk','walk',9),('water','thrust',8),('feed','slash',6)]
def main():
 OUT.mkdir(parents=True,exist_ok=True);credits={};records={}
 for key,(folder,definition) in PARTS.items():
  definition_data=json.loads((SRC/'sheet_definitions'/f'{definition}.json').read_text(encoding='utf-8'));credits[definition]=definition_data['credits']
  atlas=Image.new('RGBA',(64*9,64*4))
  for row,(action,source,count) in enumerate(ACTIONS):
   tool=key in ('can','canBack');actual=source if action=='water' else 'walk'
   if tool and action=='feed':continue
   src=SRC/'spritesheets'/folder/(actual+'.png' if tool else source+'.png')
   im=Image.open(src).convert('RGBA')
   for col in range(count):
    # Idle holds the can in the walking neutral pose; one consistent east view.
    index=col if action!='idle' else 0
    # Watering-can source only supplies thrust poses 0,1,4,5. Replay those
    # matching full-body poses forwards and back rather than losing the tool.
    if action=='water':index=[0,1,4,5,5,4,1,0][col]
    if tool and action not in ('water','walk'):index=0
    frame=im.crop((index*64,3*64,(index+1)*64,4*64));atlas.paste(frame,(col*64,row*64))
  atlas.save(OUT/(key+'.png'));records[key]={'file':key+'.png','source':folder,'definition':definition,'sha256':hashlib.sha256((OUT/(key+'.png')).read_bytes()).hexdigest()}
 palettes={}
 for material in ('body','hair','cloth'):
  palettes[material]=json.loads((SRC/f'palette_definitions/{material}/{material}_ulpc.json').read_text(encoding='utf-8'))
 manifest={'schemaVersion':1,'repository':'https://github.com/LiberatedPixelCup/Universal-LPC-Spritesheet-Character-Generator','commit':subprocess.check_output(['git','rev-parse','HEAD'],cwd=SRC,text=True).strip(),'sourceFrameSize':64,'frameSize':48,'origin':[24,44],'actions':{a:{'row':r,'frames':n,'durationMs':140 if a=='walk' else 180} for r,(a,s,n) in enumerate(ACTIONS)},'parts':records,'palettes':palettes,'artLicense':'per part, selected OGA-BY-3.0 or CC-BY-SA-3.0; derived combined sprites CC-BY-SA-4.0','adaptation':'east-facing frames extracted without recentering; original source pixels retained; runtime layered composition and fixed mesh pixel reduction'}
 (OUT/'manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2),encoding='utf-8')
 (OUT/'CREDITS.json').write_text(json.dumps(credits,ensure_ascii=False,indent=2),encoding='utf-8')
 text='# LPC artwork attribution\n\nUpstream: '+manifest['repository']+'\nPinned commit: '+manifest['commit']+'\n\n'
 for definition,entries in credits.items():
  text+='## '+definition+'\n'
  for e in entries:text+='- '+', '.join(e['authors'])+'; '+', '.join(e['licenses'])+'\n  '+', '.join(e['urls'])+'\n'
 text+='\nChanges: extracted east-facing source frames, rearranged action rows, composited layers, optional palette selection, fixed-grid downsampling. No AI generation.\n\nCurly/pixie/ponytail/beard and clothing remain available as separate credited source layers. Derived combined sprites are provided under CC-BY-SA 4.0. See license files.\n'
 (OUT/'CREDITS.md').write_text(text,encoding='utf-8');print('Pinned LPC layers prepared:',len(records))
if __name__=='__main__':main()
