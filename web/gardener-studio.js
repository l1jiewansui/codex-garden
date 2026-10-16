/* Native pixel parts and optional LPC assets share recipes and action timing. */
(()=>{
 const canvas=(w,h)=>Object.assign(document.createElement('canvas'),{width:w,height:h});
 const rgb=h=>[1,3,5].map(i=>parseInt(h.slice(i,i+2),16));
 const WIDTH=432,HEIGHT=192,ink=rgb('#25252f');
 let manifest,classicManifest,layerManifest,recipeBook,allowed=[];
 const classic={},parts={},tinted=new Map();
 const choices={style:['crop','bob','shag','pony','braid','curly','bald'],hat:['none','straw','blue'],face:['balanced','soft','round','angular','elder','small'],nose:['natural','button','straight','large'],eyes:['source','ocean','moss','honey','amethyst'],skin:['source','light','amber','olive','bronze','brown','black'],hair:['source','ginger','blonde','dark_brown','black','white','pink'],shirt:['source','white','sky','yellow','rose','slate'],coat:['source','forest','blue','brown','maroon','teal'],body:['field','petal','night'],library:['classic','lpc']};
 const defaults={schemaVersion:3,library:'classic',body:'field',face:'balanced',nose:'natural',eyes:'source',style:'crop',hat:'straw',skin:'source',hair:'source',shirt:'source',coat:'source',beard:false};
 function normalize(recipe){
  if(!recipe||typeof recipe!=='object')throw Error('园丁配置无效');
  let r={...recipe};
  if(/^original[0-2]$/.test(r.template||'')){
   if(!recipeBook)throw Error('园丁样式尚未加载');
   r={...recipeBook.defaults[Number(r.template.slice(-1))].recipe};
  }else if(r.template&&r.template!=='custom')throw Error('不支持的园丁配置');
  // Preserve existing LPC avatars; new drafts use native pixels.
  if(r.schemaVersion===2||r.template==='custom')r.library??='lpc';
  if(r.style==='straw'){r.style='crop';r.hat='straw';}
  if(r.style==='pixie')r.style='shag';
  if(r.library==='lpc')r.hat??='none';
  if(r.library==='lpc'){if(r.style==='shag')r.style='crop';if(r.style==='bob')r.style='curly';for(const [k,value] of Object.entries({skin:'light',hair:'dark_brown',shirt:'white',coat:'forest',eyes:'ocean'}))if(r[k]==='source')r[k]=value;}
  const result={schemaVersion:3};
  for(const [k,values] of Object.entries(choices)){
   const value=r[k]??defaults[k];
   if(!values.includes(value))throw Error('无效园丁选项：'+k);
   result[k]=value;
  }
  if(typeof r.beard!=='boolean')throw Error('无效胡须选项');
  result.beard=r.beard;return result;
 }
 function optionsFor(r,key){const all=choices[key];if(r.library!=='lpc')return all;return key==='style'?all.filter(v=>!['bob','shag'].includes(v)):all.filter(v=>v!=='source');}
 function valid(r){try{normalize(r);return true;}catch{return false;}}
 async function readPixels(url){
  const image=new Image();await new Promise((ok,fail)=>{image.onload=ok;image.onerror=()=>fail(Error('园丁部件加载失败'));image.src=url;});
  if(image.width!==WIDTH||image.height!==HEIGHT)throw Error('园丁部件尺寸无效');
  const c=canvas(WIDTH,HEIGHT),x=c.getContext('2d',{willReadFrequently:true});x.drawImage(image,0,0);return x.getImageData(0,0,WIDTH,HEIGHT);
 }
 async function init(palette){
  allowed=palette.map(rgb);
  [classicManifest,layerManifest,recipeBook]=await Promise.all(['../assets/pixel-classic/manifest.json','../assets/pixel-lpc/manifest.json','../assets/pixel-lpc/recipes.json'].map(async url=>{const r=await fetch(url);if(!r.ok)throw Error('园丁资源读取失败');return r.json();}));
  if(recipeBook.schemaVersion!==3||recipeBook.defaults.length!==3)throw Error('园丁样式版本不匹配');
  manifest={actions:classicManifest.actions,palettes:{body:{},hair:{},cloth:{},eyes:{}}};
  const ramps={light:['#60443a','#b47b5f','#d99d73','#f0c295','#f5d7ad','#f7f1dc'],amber:['#4b3936','#9b6c47','#b47b5f','#d99d73','#f0c295','#f5d7ad'],olive:['#4b3936','#7b5740','#9b6c47','#bb8e5c','#d99d73','#f0c295'],bronze:['#36343a','#60443a','#7b5740','#9b6c47','#bb8e5c','#d99d73'],brown:['#25252f','#4b3936','#60443a','#7b5740','#9b6c47','#bb8e5c'],black:['#25252f','#36343a','#4b3936','#60443a','#7b5740','#9b6c47'],ginger:['#4b3936','#895a30','#b57b35','#dca04a','#f5c86c','#ffe3a3'],blonde:['#60443a','#9b6c47','#bb8e5c','#dca04a','#f5c86c','#ffe3a3'],dark_brown:['#25252f','#4b3936','#60443a','#7b5740','#9b6c47','#bb8e5c'],white:['#686575','#90879d','#b8a7bb','#e3d5a9','#f6eac3','#f7f1dc'],pink:['#6b393d','#93464a','#bc6261','#e38d7c','#d49b9c','#f0c1ae'],sky:['#26374b','#37536a','#4d7387','#77a0ae','#b0c9c7','#f7f1dc'],yellow:['#60443a','#895a30','#b57b35','#dca04a','#f5c86c','#ffe3a3'],rose:['#4b3936','#6b393d','#93464a','#bc6261','#d49b9c','#f0c1ae'],slate:['#25252f','#36343a','#686575','#90879d','#b8a7bb','#f7f1dc'],forest:['#25252f','#263f35','#35553b','#4c6f3e','#6a8b48','#91ac58'],blue:['#25252f','#26374b','#37536a','#4d7387','#77a0ae','#b0c9c7'],maroon:['#25252f','#4b3936','#6b393d','#93464a','#bc6261','#e38d7c'],teal:['#25252f','#243f44','#34636b','#548e91','#8cb6ad','#b0c9c7']};
  manifest.palettes.eyes={ocean:ramps.sky,moss:ramps.forest,honey:ramps.ginger,amethyst:ramps.slate};
  for(const [group,keys] of [['body',choices.skin],['hair',choices.hair],['cloth',[...choices.shirt,...choices.coat]]])for(const k of keys)if(k!=='source')manifest.palettes[group][k]=ramps[k];
  manifest.palettes.hair.black=['#25252f','#36343a','#26374b','#37536a','#4d7387','#686575'];
  for(const p of [...recipeBook.defaults,...recipeBook.extras])normalize(p.recipe);
  await Promise.all([
   ...Object.entries(layerManifest.parts).map(async([name,p])=>{parts[name]=await readPixels('../assets/pixel-lpc/'+p.file);}),
   ...Object.entries(classicManifest.parts).map(async([name,p])=>{const [image,material]=await Promise.all([readPixels('../assets/pixel-classic/'+p.file),readPixels('../assets/pixel-classic/'+p.material)]);classic[name]={image,material};})
  ]);
 }
 function rampsFor(r){return [null,manifest.palettes.body[r.skin],manifest.palettes.hair[r.hair],manifest.palettes.cloth[r.shirt],manifest.palettes.cloth[r.coat],manifest.palettes.cloth.slate,manifest.palettes.hair.dark_brown,null,manifest.palettes.eyes[r.eyes]].map(v=>v&&v.map(rgb));}
 function cache(key,render){let image=tinted.get(key);if(!image){image=render();if(tinted.size>=160)tinted.clear();tinted.set(key,image);}return image;}
 function classicPart(name,r){
  return cache('classic:'+name+'|'+JSON.stringify([r.skin,r.hair,r.shirt,r.coat,r.eyes,r.face,r.hat]),()=>{
   const image=canvas(WIDTH,HEIGHT),x=image.getContext('2d'),im=x.createImageData(WIDTH,HEIGHT),src=classic[name].image.data,mask=classic[name].material.data,ramps=rampsFor(r);
   im.data.set(src);
   for(let i=0;i<src.length;i+=4){if(!src[i+3])continue;const group=mask[i],ramp=ramps[group];if(!ramp)continue;const c=ramp[mask[i+1]];im.data[i]=c[0];im.data[i+1]=c[1];im.data[i+2]=c[2];}
   if(name.startsWith('hair')){
    const faceIndex={balanced:0,soft:1,angular:2,round:1,small:1,elder:0}[r.face],iris=classicManifest.eyePixels[faceIndex];
    const hat=r.hat==='none'?null:classic[r.hat==='straw'?'hat0':'hat2'].image.data;
    const faceKey={balanced:'face0',soft:'face1',angular:'face2',round:'face-round',small:'face-small',elder:'face-elder'}[r.face],face=classic[faceKey].image.data;
    for(const [action,a] of Object.entries(manifest.actions))for(let f=0;f<a.frames;f++){
     const [dx,dy]=classicManifest.headPoses[action][f];
     for(const [xx,yy] of iris){const i=((a.row*48+yy+dy)*WIDTH+f*48+xx+dx)*4;im.data.fill(0,i,i+4);}
     if(name.startsWith('hairFront'))for(let yy=25+dy;yy<29+dy;yy++)for(let xx=24+dx;xx<36+dx;xx++){const i=((a.row*48+yy)*WIDTH+f*48+xx)*4;if(face[i+3])im.data.fill(0,i,i+4);}
     // Hair beneath a crown stays inside it. Keep the visible fringe below it.
     if(hat)for(let y=0;y<18+dy;y++)for(let xx=0;xx<48;xx++){
      const i=((a.row*48+y)*WIDTH+f*48+xx)*4;if(!hat[i+3])im.data.fill(0,i,i+4);
     }
    }
   }
   x.putImageData(im,0,0);return image;
  });
 }
 function composeClassic(out,r){
  const body={field:0,petal:1,night:2}[r.body],faceIndex={balanced:0,soft:1,angular:2,round:1,small:1,elder:0}[r.face];
  const face={balanced:'face0',soft:'face1',angular:'face2',round:'face-round',small:'face-small',elder:'face-elder'}[r.face];
  const hair={crop:'0',bob:'1',shag:'2',pony:'-pony',braid:'-braid',curly:'-curly'}[r.style];
  const layers=['scalp'+faceIndex,...(hair===undefined?[]:['hairBack'+hair]),'boots'+body,'coat'+body,'shirt'+body,face,...(hair===undefined?[]:['hairFront'+hair])];
  for(const name of layers)out.drawImage(classicPart(name,r),0,0);
  // Nose profiles use a small registered skin/outline overlay, never arbitrary
  // rightmost pixels (which could be hair or an eye in the previous version).
  if(r.nose!=='natural'){
   const skin=r.skin==='source'?'#f0c295':manifest.palettes.body[r.skin][3];
   for(const [action,a] of Object.entries(manifest.actions))for(let f=0;f<a.frames;f++){
    const [dx,dy]=classicManifest.headPoses[action][f],xx=f*48+dx,yy=a.row*48+dy;
    out.fillStyle=skin;
    if(r.nose==='button'){out.fillRect(xx+31,yy+24,1,1);out.fillStyle='#25252f';out.fillRect(xx+32,yy+24,1,1);}
    if(r.nose==='straight'){out.fillRect(xx+32,yy+24,1,2);out.fillStyle='#25252f';out.fillRect(xx+33,yy+24,1,2);}
    if(r.nose==='large'){out.fillRect(xx+32,yy+24,1,3);out.fillRect(xx+33,yy+25,1,1);out.fillStyle='#25252f';out.fillRect(xx+34,yy+25,1,1);out.fillRect(xx+33,yy+26,1,1);}
   }
  }
  const front=[...(r.beard?['beard']:[]),...(r.hat==='none'?[]:[r.hat==='straw'?'hat0':'hat2']),'tools'+body];
  for(const name of front)out.drawImage(classicPart(name,r),0,0);
  return [...layers,...front];
 }
 function composeLpc(out,recipe){
  const r={...recipe,skin:recipe.skin==='source'?'light':recipe.skin,hair:recipe.hair==='source'?'dark_brown':recipe.hair,shirt:recipe.shirt==='source'?'white':recipe.shirt,coat:recipe.coat==='source'?'forest':recipe.coat,eyes:recipe.eyes==='source'?'ocean':recipe.eyes};
  const ramps=rampsFor(r);ramps[7]=manifest.palettes.cloth[r.hat==='blue'?'blue':'yellow'].map(rgb);
  const hair={crop:'pixie',bob:'curly',shag:'pixie'}[r.style]||r.style;
  const head={balanced:'head',soft:'headSoft',round:'headRound',angular:'headAngular',elder:'headElder',small:'headSmall'}[r.face];
  const layers=[...(hair==='pony'?['ponyBack']:hair==='braid'?['braidBack']:[]),'canBack','body','pants','boots','shirt','overalls',head,...(r.nose==='natural'?[]:[{button:'noseButton',straight:'noseStraight',large:'noseLarge'}[r.nose]]),...(r.beard?['beard']:[]),...(hair==='bald'?[]:[hair]),...(r.hat==='none'?[]:['hat']),'can'];
  for(const name of layers){
   const image=cache('lpc:'+name+'|'+JSON.stringify(r),()=>{
    const c=canvas(WIDTH,HEIGHT),x=c.getContext('2d'),im=x.createImageData(WIDTH,HEIGHT),src=parts[name].data;
    for(let i=0;i<src.length;i+=4){if(!src[i+3])continue;const color=src[i]===0?allowed[src[i+1]]:src[i+1]===0?ink:ramps[src[i]][src[i+1]];im.data.set([...color,255],i);}
    x.putImageData(im,0,0);return c;
   });out.drawImage(image,0,0);
  }return layers;
 }
 function build(recipe){
  const r=normalize(recipe),sheet=canvas(WIDTH,HEIGHT),out=sheet.getContext('2d',{willReadFrequently:true});out.imageSmoothingEnabled=false;
  const layers=r.library==='classic'?composeClassic(out,r):composeLpc(out,r);
  const portrait=canvas(32,32),pc=portrait.getContext('2d');pc.imageSmoothingEnabled=false;pc.drawImage(sheet,0,0,48,48,0,0,32,32);
  return {sheet,portrait,recipe:r,source:r.library==='classic'?'classic-parts':'lpc',parts:layers};
 }
 function draw(ctx,actor,action,time,dx,dy,size=48){const a=manifest.actions[action],f=Math.floor(Math.max(0,time)/a.durationMs)%a.frames;ctx.drawImage(actor.sheet,f*48,a.row*48,48,48,dx,dy,size,size);}
 function fromPhoto(image,base=defaults){
  const c=canvas(64,64),x=c.getContext('2d',{willReadFrequently:true}),side=Math.min(image.width,image.height);x.drawImage(image,(image.width-side)/2,(image.height-side)/2,side,side,0,0,64,64);const p=x.getImageData(0,0,64,64).data;
  const skin=v=>v[0]>70&&v[0]>v[2]*1.15&&v[0]>v[1]*1.03&&v[0]-Math.min(v[1],v[2])>12;
  function sample(box,predicate){const bins=new Map();for(let yy=box[1];yy<box[3];yy++)for(let xx=box[0];xx<box[2];xx++){const i=(yy*64+xx)*4,v=[p[i],p[i+1],p[i+2]];if(p[i+3]<128||predicate&&!predicate(v))continue;const key=v.map(t=>Math.min(255,Math.round(t/24)*24)).join(',');bins.set(key,(bins.get(key)||0)+1);}return bins.size?[...bins].sort((a,b)=>b[1]-a[1])[0][0].split(',').map(Number):null;}
  const hair=sample([19,5,45,22],v=>!skin(v)),face=sample([22,16,43,39],skin),coat=sample([12,42,52,63]);
  const nearest=(color,group,key)=>{let best={skin:'light',hair:'dark_brown',shirt:'white',coat:'forest'}[key],distance=Infinity;if(!color)return best;for(const name of choices[key]){if(name==='source')continue;const ramp=manifest.palettes[group][name].map(rgb),target=ramp[group==='body'?3:4],d=target.reduce((n,v,i)=>n+(v-color[i])**2,0);if(d<distance){distance=d;best=name;}}return best;};
  const dark=v=>!skin(v)&&v.reduce((a,b)=>a+b,0)<360;let sideDark=0,top=0,skinTop=0,texture=0;
  for(let y=6;y<40;y++)for(let xx=12;xx<52;xx++){const i=(y*64+xx)*4,v=[p[i],p[i+1],p[i+2]];if(y>=24&&(xx<22||xx>=42)&&dark(v))sideDark++;if(y<22&&xx>=20&&xx<44){if(dark(v))top++;if(skin(v))skinTop++;if(xx>20&&Math.abs(v.reduce((a,b)=>a+b,0)-p[i-4]-p[i-3]-p[i-2])>110)texture++;}}
  const style=skinTop>260?'bald':sideDark>130?'pony':texture>65&&top>120?'curly':'crop';
  return {...normalize(base),hat:'none',style,skin:nearest(face,'body','skin'),hair:nearest(hair,'hair','hair'),shirt:nearest(coat,'cloth','shirt'),coat:nearest(coat,'cloth','coat'),beard:false};
 }
 window.GardenerStudio={init,build,draw,valid,normalize,fromPhoto,optionsFor,choices,defaults,get presets(){return [...recipeBook.defaults,...recipeBook.extras];},get defaultPresets(){return recipeBook.defaults;},get fourthPreset(){return recipeBook.extras[0];},references:()=>classicManifest.reference,source:()=>({nativeParts:Object.keys(classic).length,loadedParts:Object.keys(parts).length,repository:layerManifest.repository,commit:layerManifest.commit,faceOptions:choices.face.length,recipeVersion:recipeBook.schemaVersion,defaultLibrary:'classic',reconstruction:classicManifest.reconstruction,rigVersion:classicManifest.version,preservedSourceFrames:classicManifest.preservedSourceFrames,editor:'LibreSprite'}),actions:()=>manifest.actions};
})();
