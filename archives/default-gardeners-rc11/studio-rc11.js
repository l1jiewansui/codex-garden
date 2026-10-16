/* Native gardener studio: derives every pose from the original gardener atlas. */
(()=>{
 const canvas=(w,h)=>Object.assign(document.createElement('canvas'),{width:w,height:h});
 const rgb=h=>[1,3,5].map(i=>parseInt(h.slice(i,i+2),16));
 let manifest,parts={},allowed=[],layerManifest;const tinted=new Map();
 const choices={style:['curly','pixie','pony','braid','straw','bald'],skin:['light','amber','olive','bronze','brown','black'],hair:['ginger','blonde','dark_brown','black','white','pink'],shirt:['white','sky','yellow','rose','slate'],coat:['forest','blue','brown','maroon','teal']};
 const defaults={template:'custom',style:'pony',skin:'light',hair:'dark_brown',shirt:'white',coat:'forest',beard:false};
 function valid(r){return r&&Object.entries(choices).every(([k,v])=>v.includes(r[k]))&&typeof r.beard==='boolean'&&(!r.template||['custom','original0','original1','original2'].includes(r.template));}
 let nativeAtlas;
 async function init(palette){allowed=palette.map(rgb);manifest={actions:{idle:{row:0,frames:2,durationMs:520},walk:{row:1,frames:9,durationMs:140},water:{row:2,frames:8,durationMs:150},feed:{row:3,frames:6,durationMs:190}},palettes:{body:{},hair:{},cloth:{}}};
 const ramps={light:['#60443a','#b47b5f','#d99d73','#f0c295','#f5d7ad','#f7f1dc'],amber:['#4b3936','#9b6c47','#b47b5f','#d99d73','#f0c295','#f5d7ad'],olive:['#4b3936','#7b5740','#9b6c47','#bb8e5c','#d99d73','#f0c295'],bronze:['#36343a','#60443a','#7b5740','#9b6c47','#bb8e5c','#d99d73'],brown:['#25252f','#4b3936','#60443a','#7b5740','#9b6c47','#bb8e5c'],black:['#25252f','#36343a','#4b3936','#60443a','#7b5740','#9b6c47'],ginger:['#4b3936','#895a30','#b57b35','#dca04a','#f5c86c','#ffe3a3'],blonde:['#60443a','#9b6c47','#bb8e5c','#dca04a','#f5c86c','#ffe3a3'],dark_brown:['#25252f','#4b3936','#60443a','#7b5740','#9b6c47','#bb8e5c'],white:['#686575','#90879d','#b8a7bb','#e3d5a9','#f6eac3','#f7f1dc'],pink:['#6b393d','#93464a','#bc6261','#e38d7c','#d49b9c','#f0c1ae'],sky:['#26374b','#37536a','#4d7387','#77a0ae','#b0c9c7','#f7f1dc'],yellow:['#60443a','#895a30','#b57b35','#dca04a','#f5c86c','#ffe3a3'],rose:['#4b3936','#6b393d','#93464a','#bc6261','#d49b9c','#f0c1ae'],slate:['#25252f','#36343a','#686575','#90879d','#b8a7bb','#f7f1dc'],forest:['#25252f','#263f35','#35553b','#4c6f3e','#6a8b48','#91ac58'],blue:['#25252f','#26374b','#37536a','#4d7387','#77a0ae','#b0c9c7'],maroon:['#25252f','#4b3936','#6b393d','#93464a','#bc6261','#e38d7c'],teal:['#25252f','#243f44','#34636b','#548e91','#8cb6ad','#b0c9c7']};
 for(const [group,keys] of [['body',choices.skin],['hair',choices.hair],['cloth',[...choices.shirt,...choices.coat]]])for(const k of keys)manifest.palettes[group][k]=ramps[k];
 nativeAtlas=new Image();await new Promise((ok,fail)=>{nativeAtlas.onload=ok;nativeAtlas.onerror=fail;nativeAtlas.src='../assets/pixel-v091/actions.png';});layerManifest=await(await fetch('../assets/pixel-lpc/manifest.json')).json();await Promise.all(Object.entries(layerManifest.parts).map(async([name,part])=>{const image=new Image();await new Promise((ok,fail)=>{image.onload=ok;image.onerror=()=>fail(Error('园丁部件加载失败：'+name));image.src='../assets/pixel-lpc/'+part.file;});const c=canvas(432,192),x=c.getContext('2d',{willReadFrequently:true});x.drawImage(image,0,0);parts[name]=x.getImageData(0,0,432,192);}));}
 function build(recipe){if(!valid(recipe))throw Error('园丁配置无效');const r={...defaults,...recipe},sheet=canvas(432,192),out=sheet.getContext('2d',{willReadFrequently:true});out.imageSmoothingEnabled=false;
 if(r.template.startsWith('original')){
  const row=Number(r.template.slice(-1));
  for(const [action,a] of Object.entries(manifest.actions))for(let f=0;f<a.frames;f++){
   const cell=canvas(48,48),x=cell.getContext('2d',{willReadFrequently:true});x.imageSmoothingEnabled=false;
   const col=action==='water'?[2,2,3,3,4,4,3,2][f]:action==='feed'?[5,6,7,7,6,5][f]:2;
   x.drawImage(nativeAtlas,col*48,row*48,48,48,0,0,48,48);
   if(action==='walk'){const legs=x.getImageData(0,36,48,12),offset=[-1,0,1,0,0,-1,0,1,0][f];x.clearRect(0,36,48,12);x.putImageData(legs,offset,36,0,0,24,12);x.putImageData(legs,-offset,36,24,0,24,12);}
   out.drawImage(cell,f*48,a.row*48);
  }
 }else{
  const ramps=[null,manifest.palettes.body[r.skin],manifest.palettes.hair[r.hair],manifest.palettes.cloth[r.shirt],manifest.palettes.cloth[r.coat],manifest.palettes.cloth.slate,manifest.palettes.hair.dark_brown,manifest.palettes.cloth.yellow].map(v=>v&&v.map(rgb));
  const hair=r.style==='straw'?'pixie':r.style;
  const layers=[...(hair==='pony'?['ponyBack']:hair==='braid'?['braidBack']:[]),'canBack','body','pants','boots','shirt','overalls','head',...(r.beard?['beard']:[]),...(hair==='bald'?[]:[hair]),...(r.style==='straw'?['hat']:[]),'can'];
  for(const name of layers){const key=name+'|'+JSON.stringify(r);let image=tinted.get(key);if(!image){image=canvas(432,192);const x=image.getContext('2d'),im=x.createImageData(432,192),src=parts[name].data,dst=im.data;for(let i=0;i<src.length;i+=4){if(!src[i+3])continue;const c=src[i]===0?allowed[src[i+1]]:src[i+1]===0?rgb('#25252f'):ramps[src[i]][src[i+1]];dst[i]=c[0];dst[i+1]=c[1];dst[i+2]=c[2];dst[i+3]=255;}x.putImageData(im,0,0);if(tinted.size>160)tinted.clear();tinted.set(key,image);}out.drawImage(image,0,0);}
 }
 const portrait=canvas(32,32),pc=portrait.getContext('2d');pc.imageSmoothingEnabled=false;pc.drawImage(sheet,0,0,48,48,0,0,32,32);return {sheet,portrait,recipe:r,source:r.template==='custom'?'lpc':r.template};}
 function draw(ctx,actor,action,time,dx,dy,size=48){const a=manifest.actions[action],f=Math.floor(Math.max(0,time)/a.durationMs)%a.frames;ctx.drawImage(actor.sheet,f*48,a.row*48,48,48,dx,dy,size,size);}
 function fromPhoto(image){const c=canvas(64,64),x=c.getContext('2d',{willReadFrequently:true});const side=Math.min(image.width,image.height);x.drawImage(image,(image.width-side)/2,(image.height-side)/2,side,side,0,0,64,64);const p=x.getImageData(0,0,64,64).data;
 const skin=v=>v[0]>70&&v[0]>v[2]*1.15&&v[0]>v[1]*1.03&&v[0]-Math.min(v[1],v[2])>12;
 function sample(box,predicate){const bins=new Map();for(let yy=box[1];yy<box[3];yy++)for(let xx=box[0];xx<box[2];xx++){const i=(yy*64+xx)*4,v=[p[i],p[i+1],p[i+2]];if(p[i+3]<128||predicate&&!predicate(v))continue;const key=v.map(t=>Math.min(255,Math.round(t/24)*24)).join(',');bins.set(key,(bins.get(key)||0)+1);}return bins.size?[...bins].sort((a,b)=>b[1]-a[1])[0][0].split(',').map(Number):null;}
 const hair=sample([19,5,45,22],v=>!skin(v)),face=sample([22,16,43,39],skin),coat=sample([12,42,52,63]);
 const nearest=(color,group,key)=>{if(!color)return defaults[key];let best=defaults[key],distance=Infinity;for(const name of choices[key]){const ramp=manifest.palettes[group][name].map(rgb);const target=ramp[group==='body'?3:4],d=target.reduce((n,v,i)=>n+(v-color[i])**2,0);if(d<distance){distance=d;best=name;}}return best;};
 const dark=v=>!skin(v)&&v.reduce((a,b)=>a+b,0)<360;let sideDark=0,top=0,skinTop=0,texture=0;for(let y=6;y<40;y++)for(let xx=12;xx<52;xx++){const i=(y*64+xx)*4,v=[p[i],p[i+1],p[i+2]];if(y>=24&&(xx<22||xx>=42)&&dark(v))sideDark++;if(y<22&&xx>=20&&xx<44){if(dark(v))top++;if(skin(v))skinTop++;if(xx>20&&Math.abs(v.reduce((a,b)=>a+b,0)-p[i-4]-p[i-3]-p[i-2])>110)texture++;}}const style=skinTop>260?'bald':sideDark>130?'pony':texture>65&&top>120?'curly':'pixie';
 return {...defaults,style,skin:nearest(face,'body','skin'),hair:nearest(hair,'hair','hair'),shirt:nearest(coat,'cloth','shirt'),coat:nearest(coat,'cloth','coat'),beard:false};}
 const originals=[{name:'麦穗',recipe:{...defaults,template:'original0',style:'straw',hair:'ginger',coat:'teal'}},{name:'桃桃',recipe:{...defaults,template:'original1',style:'pony',hair:'pink',coat:'teal'}},{name:'夜蓝',recipe:{...defaults,template:'original2',style:'pixie',hair:'black',coat:'teal'}}];
 const presets=[...originals,
 {name:'栗辫',recipe:{...defaults,style:'braid'}},
 {name:'麦田帽',recipe:{...defaults,style:'straw',hair:'ginger',shirt:'yellow',coat:'brown'}},
 {name:'薄荷',recipe:{...defaults,style:'pixie',hair:'black',shirt:'sky',coat:'teal'}},
 {name:'莓卷',recipe:{...defaults,style:'curly',hair:'pink',shirt:'white',coat:'maroon'}},
 {name:'银尾',recipe:{...defaults,style:'pony',hair:'white',shirt:'slate',coat:'blue'}},
 {name:'老乔',recipe:{...defaults,style:'bald',hair:'dark_brown',skin:'bronze',shirt:'yellow',coat:'forest',beard:true}}
 ];
 window.GardenerStudio={init,build,draw,valid,fromPhoto,choices,defaults,presets,originals,source:()=>({repository:layerManifest.repository,commit:layerManifest.commit,loadedParts:Object.keys(parts).length}),actions:()=>manifest.actions};
})();
