const $=id=>document.getElementById(id),canvas=$('garden'),ctx=canvas.getContext('2d',{willReadFrequently:true});ctx.imageSmoothingEnabled=false;
const labels={growing:'正在回复',ripe:'可收获',harvested:'已收获',paused:'已暂停',failed:'遇到问题',stale:'等待更新',unknown:'等待更新',waiting:'等你处理'};
let art=null,atlases=new Map(),heroes=[],frames=new Map(),threads=[],page=0,heroIndex=0,expanded=false,selected=null,demo=false,busy=false,ready=false,harvesting=new Set(),slots={},timer,lastMask=0,maskData=null,errorText='',toastTimer;
const activating=new Set(),opened=[];
const errors=[];window.addEventListener('error',e=>errors.push(e.message));window.addEventListener('unhandledrejection',e=>errors.push(String(e.reason)));
let walker={x:50,target:50,facing:1,pending:null},lastDraw=0,land=null,sun=null,supplies=null,plantAtlas=null,specialAtlas=null,fantasyAtlas=null,tilled=null,camera=0;
let customRecipe=setting('gardener-recipe-v1',null),customActions=null,customPortrait=null,customSelected=setting('photo-gardener-selected',false),defaultActor=null,customActor=null,generatedDefaults=[];
let connection='loading',lastStorageNotice='';
let storageOpen=false,inventory={},demoInventory={};
let gardenName=GardenModel.gardenName(setting('garden-name',null)),editingName=false;
function orderLabel(id){return String(slots[id]+1).padStart(2,'0');}
function syncName(){document.title=gardenName;$('welcome-title').textContent='欢迎来到'+gardenName;return window.garden.window('name',gardenName);}
async function finishName(commit=false){if(!editingName)return;editingName=false;if(commit){gardenName=GardenModel.gardenName($('garden-name-input').value);save('garden-name',gardenName);await syncName();}$('name-editor').hidden=true;$('panel').classList.remove('naming');await window.garden.window('editing',false);if(expanded)renderPanel();publishGeometry();}
$('rename-garden').onclick=async()=>{editingName=true;$('name-editor').hidden=false;$('panel').classList.add('naming');$('garden-name-input').value=gardenName;publishGeometry();await window.garden.window('editing',true);$('garden-name-input').focus();$('garden-name-input').select();};
$('name-editor').onsubmit=event=>{event.preventDefault();finishName(true);};$('cancel-name').onclick=()=>finishName(false);$('garden-name-input').addEventListener('keydown',event=>{if(event.key==='Escape'){event.preventDefault();finishName(false);}});
let hoverId=null,pinnedInfo=null,hoverTimer,hideTimer;const careEffects=[],careQueue=[],careHistory=[];let activeCare=null;
function hideInfo(force=true){if(pinnedInfo&&!force)return;clearTimeout(hoverTimer);clearTimeout(hideTimer);hoverId=null;pinnedInfo=null;$('plant-info').hidden=true;$('care-tools').hidden=true;}
function showInfo(id){if(expanded)return;const t=threads.find(t=>t.id===id);if(!t)return;hoverId=id;$('info-title').textContent=orderLabel(t.id)+' · '+(t.title||'未命名对话');$('info-status').textContent=userStatus(t);$('plant-info').hidden=false;$('care-tools').hidden=false;publishGeometry();}
function care(kind,id=hoverId){if(!['water','feed'].includes(kind)||!threads.some(t=>t.id===id)||careQueue.length>=4)return;careQueue.push({kind,id});draw();}
let pan=null,suppressClick=false;
$('drag').hidden=true;
let cropChoices=setting('garden-crop-choices',{}),demoChoices={};
const cropNames=['胡萝卜','卷心菜','番茄','南瓜','玉米','茄子','草莓','向日葵','月光花','水晶菇','星灯草','黄金萝卜','月玉卷心菜','星露番茄','琥珀南瓜','豌豆炮手','双荚炮手','火炬辣椒','铃铛蘑菇','捕虫花','星月莲'];
const selectableKinds=[15,16,17,18,19,20,0,1,2,3,4,5,6,7,8,9,10];
const isHiddenKind=kind=>kind>=11&&kind<15;
const hiddenNames=['黄金萝卜','月玉卷心菜','星露番茄','琥珀南瓜'];let discoveries=setting('garden-discoveries',[]);
function secretOf(t){return GardenModel.secretPlant(t.id,t.turn);}
function displayKind(t){const secret=t.status==='ripe'?secretOf(t):null;return secret===null?cropKind(t):11+secret;}
function plantRect(kind,stage,frame=0,variety=0){return kind>=15?{image:fantasyAtlas,y:((kind-15)*6+frame%6)*28}:kind<3?{image:plantAtlas,y:(variety*9+kind*3+frame)*28}:{image:specialAtlas,y:((kind-3)*3+frame)*28};}
function cropKind(t){return (demo?demoChoices:cropChoices)[t.id]??t.crop;}
function walkTo(x,pending=null){walker.target=Math.max(46,x);walker.pending=pending;}
function visit(id){if(!threads.some(t=>t.id===id))return;walkTo(cropX(id)-GardenModel.geometry.interactionOffset,{id});}
function chooseCrop(kind){if(!selected||!Number.isInteger(kind)||!selectableKinds.includes(kind))return;(demo?demoChoices:cropChoices)[selected]=kind;if(!demo)save('garden-crop-choices',cropChoices);renderPanel();draw();}
function setting(key,fallback){try{return JSON.parse(localStorage.getItem(key))??fallback;}catch{return fallback;}}
function save(key,value){localStorage.setItem(key,JSON.stringify(value));}
function atlasDraw(c,imageKey,rect,x,y,w,h){const image=atlases.get(imageKey);if(image)c.drawImage(image,...rect,Math.round(x),Math.round(y),w,h);}
function icon(c,name,x,y,size){if(art){const base=size===24?12:size===32?16:size,variant=art.icons[name].variants[String(base)];if(!variant)throw Error('缺少整数像素图标尺寸 '+size);atlasDraw(c,variant.image,variant.sourceRect,x,y,size,size);}}
function drawChest(){const c=$('chest').getContext('2d');c.clearRect(0,0,28,28);c.fillStyle='#60443a';c.fillRect(2,8,24,16);c.fillRect(4,4,20,6);c.fillStyle='#bb8e5c';c.fillRect(4,10,20,12);c.fillRect(6,6,16,4);c.fillStyle='#895a30';c.fillRect(4,14,20,2);c.fillStyle='#f5c86c';c.fillRect(6,10,2,12);c.fillRect(20,10,2,12);c.fillRect(12,12,4,6);}
function drawMarks(){drawChest();for(const [id,name] of [['app-mark','app'],['mini-mark','app']]){const el=$(id),c=el.getContext('2d');c.imageSmoothingEnabled=false;c.clearRect(0,0,el.width,el.height);icon(c,name,0,0,el.width);}}
const attentionLabels={unread:'有新回复',read:'已读',unknown:'阅读状态待更新'};
function userStatus(t){return [labels[t.status],attentionLabels[t.attention||'unknown']].filter(Boolean).join(' · ');}
function crop(c,x,status,kind,attention='unknown',time=performance.now(),variety=0){
 const stage=GardenModel.cropStage(status),reduce=matchMedia('(prefers-reduced-motion: reduce)').matches,frame=!reduce&&['growing','ripe'].includes(status)?Math.floor((time+x*7)/420)%3:0;
 if(plantAtlas){const spec=plantRect(kind,stage,kind>=15&&!reduce?Math.floor((time+x*7)/160)%6:frame,variety);if(!reduce&&stage>0&&kind<15){const wind=Math.sin(time/650+x*.07)*1.4;for(let row=0;row<28;row++){const offset=Math.round(wind*((27-row)/27)**1.8);c.drawImage(spec.image,stage*28,spec.y+row,28,1,Math.round(x-14)+offset,32+row,28,1);}}else c.drawImage(spec.image,stage*28,spec.y,28,28,Math.round(x-14),32,28,28);}
 if(GardenModel.CARE.includes(status))icon(c,'care',x+9,40,8);
}
const fx=$('plant-fx'),fxc=fx.getContext('2d');
function drawPlantLight(time){
 fxc.clearRect(0,0,420,150);const reduced=matchMedia('(prefers-reduced-motion: reduce)').matches;
 const glow=(x,y,r,alpha,gold=false)=>{const g=fxc.createRadialGradient(x,y,0,x,y,r);g.addColorStop(0,`rgba(235,253,255,${alpha})`);g.addColorStop(.18,gold?`rgba(255,226,133,${alpha*.8})`:`rgba(135,231,255,${alpha*.85})`);g.addColorStop(.48,gold?`rgba(245,184,74,${alpha*.32})`:`rgba(45,159,255,${alpha*.38})`);g.addColorStop(1,'rgba(30,135,255,0)');fxc.fillStyle=g;fxc.beginPath();fxc.arc(x,y,r,0,Math.PI*2);fxc.fill();};
 const star=(x,y,size,alpha)=>{glow(x,y,size*3.4,alpha*.8);fxc.strokeStyle=`rgba(203,248,255,${alpha})`;fxc.lineWidth=1;fxc.beginPath();fxc.moveTo(x-size,y);fxc.lineTo(x+size,y);fxc.moveTo(x,y-size);fxc.lineTo(x,y+size);fxc.stroke();fxc.fillStyle=`rgba(255,255,255,${alpha})`;fxc.fillRect(Math.round(x)-1,Math.round(y)-1,2,2);};
 fxc.save();fxc.globalCompositeOperation='screen';
 for(const t of visible()){
  const unread=t.attention==='unread',rare=isHiddenKind(displayKind(t));if(!unread&&!rare)continue;
  let seed=0;for(const ch of t.id)seed=(Math.imul(seed,31)+ch.charCodeAt(0))>>>0;
  const cx=(cropX(t.id)-camera)*2,pulse=reduced?.7:.5+.5*Math.sin(time/460+seed%17);
  if(unread){
   // A persistent blue aura distinguishes unread plants even between sparkles.
   const aura=fxc.createRadialGradient(cx,101,2,cx,101,31);aura.addColorStop(0,`rgba(60,185,255,${.12+pulse*.12})`);aura.addColorStop(.55,`rgba(40,140,255,${.08+pulse*.06})`);aura.addColorStop(1,'rgba(40,140,255,0)');fxc.fillStyle=aura;fxc.fillRect(cx-31,70,62,62);
   fxc.fillStyle=`rgba(91,201,255,${.12+pulse*.1})`;fxc.beginPath();fxc.ellipse(cx,120,19,2.5,0,0,Math.PI*2);fxc.fill();
   star(cx+Math.sin(reduced?0:time/700)*3,72,2.5+pulse, .72+pulse*.28);
  }
  const count=reduced?(unread?6:3):(unread?13:5);
  for(let i=0;i<count;i++){
   const duration=1900+(seed+i*137)%1600,phase=reduced?.45:((time+(seed%3000)+i*479)%duration)/duration;
   const envelope=Math.sin(Math.PI*phase),drift=Math.sin(phase*5+i*2.1)*(unread?8:5);
   let px=cx+((seed+i*17)%43)-21+drift;const py=119-phase*(unread?52+(i%3)*5:28+(i%3)*8);if(unread&&py>85&&Math.abs(px-cx)<13)px=cx+(px<cx?-1:1)*17;
   const radius=(unread?5:3)+(i%3)*1.4,alpha=(unread?.48:.6)*envelope;
   glow(px,py,radius,alpha,rare&&!unread);
   fxc.fillStyle=`rgba(255,255,255,${envelope})`;fxc.beginPath();fxc.arc(px,py,unread?.65:.55,0,Math.PI*2);fxc.fill();
   if(unread&&i%5===0)star(px,py,1.5+envelope*1.5,envelope*.95);
  }
 }
 fxc.restore();
}
function drawCareLight(time){
 for(let i=careEffects.length-1;i>=0;i--){const e=careEffects[i],age=(time-e.start)/1000;if(age>1.5){careEffects.splice(i,1);continue;}const end=(cropX(e.id)-camera+3)*2,start=(e.emitterX-camera)*2;
  if(e.kind==='water'){
   const wet=Math.max(0,Math.min(1,(age-.35)*3))*(1-Math.max(0,age-1));fxc.fillStyle=`rgba(45,69,66,${wet*.24})`;fxc.beginPath();fxc.ellipse(end,121,7,1.6,0,0,Math.PI*2);fxc.fill();
   if(age<.33||age>.82)continue;const fade=Math.min(1,(age-.33)/.07,(.82-age)/.1);
   fxc.save();fxc.lineCap='round';fxc.strokeStyle=`rgba(147,211,225,${fade*.65})`;fxc.lineWidth=1;fxc.beginPath();fxc.moveTo(start,104);fxc.bezierCurveTo(start+3,103,end-2,110,end,119);fxc.stroke();
   fxc.strokeStyle=`rgba(230,248,248,${fade*.5})`;fxc.lineWidth=.4;fxc.stroke();
   for(let k=0;k<3;k++){const t=(age*2.3+k/3)%1,u=1-t,px=u*u*u*start+3*u*u*t*(start+3)+3*u*t*t*(end-2)+t*t*t*end,py=u*u*u*104+3*u*u*t*103+3*u*t*t*110+t*t*t*119;fxc.fillStyle=`rgba(216,244,246,${fade*.8})`;fxc.beginPath();fxc.ellipse(px,py,.6,1,0,0,Math.PI*2);fxc.fill();}
   const r=1+((age*4)%1)*3;fxc.strokeStyle=`rgba(157,207,212,${fade*.3})`;fxc.lineWidth=.5;fxc.beginPath();fxc.ellipse(end,120,r,r*.28,0,0,Math.PI*2);fxc.stroke();fxc.restore();
  }else{
   for(let k=0;k<3;k++){const t=(age-.32-k*.09)/.42;if(t<0||t>1)continue;const px=start+(end-start)*t+(k-1)*1.3,py=105+15*t*t;fxc.fillStyle=`rgba(187,142,92,${Math.min(1,(1-t)*4)})`;fxc.beginPath();fxc.arc(px,py,.85,0,Math.PI*2);fxc.fill();}
   if(age>.6){const a=Math.max(0,1-(age-.6)/.9)*.25;fxc.fillStyle=`rgba(123,87,64,${a})`;fxc.beginPath();fxc.ellipse(end,121,5,1.2,0,0,Math.PI*2);fxc.fill();}
  }
 }
}
function ordered(){return [...threads].sort((a,b)=>slots[a.id]-slots[b.id]);}
function cropX(id){return 76+slots[id]*36;}
function visible(){return ordered().filter(t=>cropX(t.id)-camera>=-16&&cropX(t.id)-camera<=226);}
function currentFrame(hero,action,time){const list=hero.frames.filter(f=>f.action===action);const duration=list.reduce((n,f)=>n+f.durationMs,0);let t=time%duration;for(const f of list){if(t<f.durationMs)return f;t-=f.durationMs;}return list[0];}
function draw(time=performance.now()){
 ctx.clearRect(0,0,210,75);if(!ready)return;const sc=$('sun').getContext('2d');sc.imageSmoothingEnabled=false;sc.clearRect(0,0,32,32);const sunFrame=matchMedia('(prefers-reduced-motion: reduce)').matches?0:Math.floor(time/240)%6;if(sun)sc.drawImage(sun,sunFrame*16,0,16,16,0,0,32,32);
 if(activeCare?.start!==null&&activeCare&&time-activeCare.start>1200)activeCare=null;
 if(!activeCare&&careQueue.length){activeCare={...careQueue.shift(),start:null};walkTo(cropX(activeCare.id)-18);}
 const previous=walker.x;walker.x=GardenModel.stepWorld(walker.x,walker.target,lastDraw?(time-lastDraw)/1000:0);lastDraw=time;
 const moving=Math.abs(walker.target-walker.x)>.01;if(previous!==walker.x){walker.facing=Math.sign(walker.x-previous);camera=Math.max(0,GardenModel.followCamera(walker.x,camera));}
 if(!moving&&walker.pending)walker.pending=null;
 if(activeCare&&activeCare.start===null&&!moving){activeCare.start=time;walker.facing=1;careEffects.push({...activeCare,emitterX:walker.x+(activeCare.kind==='water'?15:12)});careHistory.push({kind:activeCare.kind,hero:heroIndex});}
 // Terrain, plants and gardener share one scrolling world.

 if(land){for(let x=-((Math.round(camera)%16+16)%16);x<210;x+=16)ctx.drawImage(land,x,GardenModel.geometry.surfaceY,16,14);}
 if(supplies)ctx.drawImage(supplies,Math.round(2-camera),40,36,20);
 const list=visible();list.forEach(t=>{const x=cropX(t.id)-camera;if(tilled)ctx.drawImage(tilled,Math.round(x-18),60,36,14);crop(ctx,x,t.status,displayKind(t),t.attention||'unknown',time,(slots[t.id]||0)%3);const label=orderLabel(t.id),width=label.length*4+3,left=Math.round(x)-Math.floor(width/2);ctx.fillStyle='#60443a';ctx.fillRect(left,65,width,9);ctx.fillStyle='#bb8e5c';ctx.fillRect(left,65,width,1);for(let i=0;i<label.length;i++)atlasDraw(ctx,'digits',[Number(label[i])*3,0,3,5],left+2+i*4,67,3,5);});
 const reduce=matchMedia('(prefers-reduced-motion: reduce)').matches,acting=activeCare&&activeCare.start!==null&&!moving;
 if(defaultActor){ctx.save();ctx.translate(Math.round(walker.x-camera),60);ctx.scale(walker.facing,1);GardenerStudio.draw(ctx,customSelected&&customActor?customActor:heroIndex===3?defaultActor:generatedDefaults[heroIndex],acting?activeCare.kind:moving?'walk':'idle',reduce?0:acting?time-activeCare.start:time,-24,-44);ctx.restore();}

 if(!list.length){icon(ctx,'seeds',92,44,16);icon(ctx,'app',114,44,16);}
 drawPlantLight(time);drawCareLight(time);
 $('page').textContent=(Math.floor(camera/144)+1)+'段';$('prev').disabled=camera<=0;if(time-lastMask>(moving?80:250)){lastMask=time;publishGeometry();}
}
function publishGeometry(){
 const image=ctx.getImageData(0,0,210,75);const bytes=new Uint8Array(210*75);for(let i=0;i<bytes.length;i++)bytes[i]=image.data[i*4+3]>32?1:0;maskData=bytes;
 let binary='';for(const v of bytes)binary+=String.fromCharCode(v);
 const regions=[...document.querySelectorAll('[data-hit]')].filter(e=>!e.hidden&&e.getClientRects().length).map(e=>{const r=e.getBoundingClientRect();return{x:r.x,y:r.y,width:r.width,height:r.height};});
 window.garden.geometry({regions,mask:{x:0,y:innerHeight-150,width:210,height:75,scale:2,data:btoa(binary)}});
}
function toast(text){$('toast').textContent=text;$('toast').hidden=false;clearTimeout(toastTimer);toastTimer=setTimeout(()=>$('toast').hidden=true,2600);}
function make(tag,text){const e=document.createElement(tag);if(text!==undefined)e.textContent=text;return e;}
async function panel(open){if(!open){closeWorkshop();await finishName(false);}hideInfo();expanded=open;if(!open){$('panel').hidden=true;selected=null;$('hint').hidden=true;}await window.garden.window('panel',open);$('panel').hidden=!open;if(open)renderPanel();publishGeometry();}
async function showWelcome(){if(!$('welcome').hidden)return;hideInfo();$('panel').hidden=true;await window.garden.window('panel',true);$('welcome').hidden=false;publishGeometry();}
$('begin').onclick=async()=>{await window.garden.window('start');$('welcome').hidden=true;await panel(false);await refresh();};
function showDetail(id){storageOpen=false;selected=id;panel(true);}
let listScrollPosition=0;$('threads').addEventListener('scroll',()=>{if($('threads').getClientRects().length)listScrollPosition=$('threads').scrollTop;});
function renderPanel(){
 const listScroll=$('threads').getClientRects().length?$('threads').scrollTop:listScrollPosition,choiceScroll=$('crop-choices')?.scrollTop||0;listScrollPosition=listScroll;
 $('panel-title').textContent=!$('gardener-workshop').hidden?'园丁工坊':storageOpen?'储物收藏':selected?'我的菜地':gardenName;$('panel-title').title=gardenName;$('rename-garden').hidden=storageOpen||Boolean(selected);$('back').hidden=!selected;$('list-view').hidden=storageOpen||Boolean(selected);$('detail-view').hidden=storageOpen||!selected;$('storage-view').hidden=!storageOpen;$('settings').hidden=storageOpen;$('error').textContent=errorText?'暂时无法更新，请稍后再试。':'';
 if(storageOpen){const items=demo?demoInventory:inventory;$('storage-items').replaceChildren();const entries=Object.entries(items).filter(([k,n])=>Number(n)>0);$('storage-caption').textContent=entries.length?'你的收获都在这里':'还没有收藏，双击成熟植物收获吧。';for(const [key,count] of entries){const kind=Number(key),tile=make('div'),picture=make('canvas');picture.width=28;picture.height=28;const pc=picture.getContext('2d');pc.imageSmoothingEnabled=false;const spec=plantRect(kind,3);pc.drawImage(spec.image,84,spec.y,28,28,0,0,28,28);tile.className=isHiddenKind(kind)?'stored-plant rare':'stored-plant';tile.append(picture,make('span',isHiddenKind(kind)?hiddenNames[kind-11]:cropNames[kind]),make('small','× '+count));$('storage-items').append(tile);}}
 if(selected&&!storageOpen){const t=threads.find(t=>t.id===selected);if(!t){selected=null;renderPanel();return;}$('status').textContent=orderLabel(t.id)+' · '+userStatus(t);$('title').textContent=t.title||'未命名对话';const secret=t.status==='ripe'?secretOf(t):null;if(secret!==null)$('status').textContent+=' · '+hiddenNames[secret];$('project').textContent='';$('summary').textContent='';$('harvest').hidden=true;$('harvest').disabled=t.status!=='ripe'||harvesting.has(t.id);$('harvest').textContent=harvesting.has(t.id)?'收获中…':'收获';$('open-thread').disabled=demo;}
 else if(!storageOpen){$('threads').replaceChildren();for(const t of ordered()){const b=make('button');b.dataset.thread=t.id;b.dataset.order=String(slots[t.id]+1);const number=make('span',orderLabel(t.id));number.className='thread-number';const thumb=make('canvas');thumb.width=28;thumb.height=28;thumb.className='thread-crop';thumb.dataset.kind=String(displayKind(t));thumb.setAttribute('aria-label',t.title||'未命名对话');const tc=thumb.getContext('2d');tc.imageSmoothingEnabled=false;const spec=plantRect(displayKind(t),GardenModel.cropStage(t.status));tc.drawImage(spec.image,GardenModel.cropStage(t.status)*28,spec.y,28,28,0,0,28,28);const n=make('strong',t.title||'未命名对话'),s=make('small',userStatus(t));s.className=t.status;b.append(number,thumb,n,s);b.onclick=()=>{selected=t.id;visit(t.id);renderPanel();};$('threads').append(b);}if(!threads.length){const message=connection==='loading'?'正在连接本机 Codex…':connection==='missing'?'先打开 Codex，再回来看看。':connection==='error'||errorText?'暂时连接不上，稍后可以重试。':'开始一段 Codex 对话，种下第一颗种子。';$('threads').append(make('p',message));if(connection!=='loading'){const retry=make('button','重新连接');retry.id='retry-sync';retry.onclick=async()=>{retry.disabled=true;retry.textContent='连接中…';await refresh();};$('threads').append(retry);}}}
 let chooser=$('crop-choices');if(!chooser){chooser=make('div');chooser.id='crop-choices';$('summary').before(chooser);}
 chooser.replaceChildren();if(selected){const t=threads.find(t=>t.id===selected);selectableKinds.forEach(i=>{const name=cropNames[i];const b=make('button');b.className=cropKind(t)===i?'selected':'';b.setAttribute('aria-pressed',String(cropKind(t)===i));const c=make('canvas');c.width=32;c.height=32;const pc=c.getContext('2d');pc.imageSmoothingEnabled=false;const spec=plantRect(i,3);pc.drawImage(spec.image,84,spec.y,28,28,2,2,28,28);b.append(c,make('span',name));b.onclick=()=>chooseCrop(i);chooser.append(b);});let note=$('collection-note');if(!note){note=make('p');note.id='collection-note';chooser.after(note);}note.textContent=discoveries.length?'已发现：'+discoveries.map(i=>hiddenNames[i]).join('、'):'成熟时，偶尔会遇见隐藏品种。';}
 $('threads').scrollTop=listScroll;if($('crop-choices'))$('crop-choices').scrollTop=choiceScroll;
 $('demo').textContent=demo?'返回真实':'演示';$('heroes').replaceChildren();heroes.forEach((h,i)=>{const b=make('button');b.className=!customSelected&&i===heroIndex?'selected':'';b.title=h.name;b.setAttribute('aria-label','选择园丁 '+h.name);const portrait=make('canvas');portrait.width=32;portrait.height=32;portrait.setAttribute('aria-label',h.name);const pc=portrait.getContext('2d');pc.imageSmoothingEnabled=false;if(defaultActor)pc.drawImage(i===3?defaultActor.portrait:generatedDefaults[i].portrait,0,0);else atlasDraw(pc,h.portrait.image,h.portrait.sourceRect,0,0,32,32);b.append(portrait);b.onclick=()=>{customSelected=false;save('photo-gardener-selected',false);heroIndex=i;save('art04-hero',i);renderPanel();draw();};$('heroes').append(b);});if(customPortrait){const b=make('button');b.title='我的园丁 · 右键移除';b.oncontextmenu=e=>{e.preventDefault();customRecipe=null;customActor=null;customActions=null;customPortrait=null;customSelected=false;save('gardener-recipe-v1',null);save('photo-gardener-selected',false);renderPanel();draw();toast('自定义园丁已移除');};b.setAttribute('aria-label','选择我的园丁');b.className=customSelected?'selected':'';const c=make('canvas');c.width=32;c.height=32;c.getContext('2d').drawImage(customPortrait,0,0);b.append(c);b.onclick=()=>{customSelected=true;save('photo-gardener-selected',true);renderPanel();draw();};$('heroes').append(b);}
}
function render(){const previousSlots=slots;slots=GardenModel.sequentialSlots(threads);if(walker.pending){if(slots[walker.pending.id]===undefined){walker.pending=null;walker.target=walker.x;}else walker.target=cropX(walker.pending.id)-GardenModel.geometry.interactionOffset;}if(activeCare&&(slots[activeCare.id]===undefined||slots[activeCare.id]!==previousSlots[activeCare.id])){careEffects.length=0;if(slots[activeCare.id]===undefined)activeCare=null;else{activeCare.start=null;walker.target=cropX(activeCare.id)-18;}}for(let i=careQueue.length-1;i>=0;i--)if(slots[careQueue[i].id]===undefined)careQueue.splice(i,1);page=Math.min(page,Math.max(0,Math.ceil(threads.length/4)-1));$('growing').textContent=threads.filter(t=>t.status==='growing').length;$('ripe').textContent=threads.filter(t=>t.attention==='unread').length;$('page').textContent=(page+1)+'/'+Math.max(1,Math.ceil(threads.length/4));$('prev').disabled=false;$('next').disabled=false;if(!demo&&connection!=='ready')$('ripe').textContent='—';$('overview').title=!demo&&connection!=='ready'?'连接暂不可用，请先打开 Codex':'查看全部对话';if(expanded)renderPanel();if(hoverId&&!$('plant-info').hidden){if(threads.some(t=>t.id===hoverId))showInfo(hoverId);else hideInfo();}draw();}
async function refresh(){if(busy||demo)return;busy=true;try{const s=await window.garden.snapshot();if(demo)return;connection=s.connection||'ready';if(connection==='welcome'){await showWelcome();return;}if(!s.error)threads=s.threads;inventory=s.inventory||inventory;errorText=s.error||'';if(s.storageNotice&&lastStorageNotice!==s.storageNotice){lastStorageNotice=s.storageNotice;toast(s.storageNotice);}$('sync').textContent='本地只读 · '+new Date().toLocaleTimeString('zh-CN')+' 同步';render();}catch(e){connection='error';errorText='同步中断：'+e.message;$('sync').textContent='本地同步中断';if(expanded)renderPanel();}finally{busy=false;}}
async function harvest(id){const t=threads.find(t=>t.id===id);if(!t||t.status!=='ripe'||harvesting.has(id))return false;harvesting.add(id);if(expanded)renderPanel();try{const harvestedKind=displayKind(t);if(!demo){const result=await window.garden.harvest(id,harvestedKind);inventory=result.inventory||inventory;}else demoInventory[harvestedKind]=(demoInventory[harvestedKind]||0)+1;const secret=secretOf(t);if(secret!==null&&!demo&&!discoveries.includes(secret)){discoveries.push(secret);save('garden-discoveries',discoveries);}t.status='harvested';toast(secret===null?'收获成功':'发现隐藏款 · '+hiddenNames[secret]);render();return true;}catch(e){errorText=e.message;toast('收获失败，请稍后重试');return false;}finally{harvesting.delete(id);if(expanded)renderPanel();}}
async function activatePlant(id){if(!demo&&connection!=='ready'){toast('连接恢复后再试');return;}if(activating.has(id))return;const t=threads.find(t=>t.id===id);if(!t)return;activating.add(id);walker.pending=null;try{if(t.status==='ripe'&&!await harvest(id))return;if(demo)opened.push(id);else await window.garden.open(id);}catch(e){errorText=e.message;toast('暂时无法打开对话，请稍后重试');}finally{activating.delete(id);}}
function pick(event){const r=canvas.getBoundingClientRect(),x=(event.clientX-r.left)/2,y=(event.clientY-r.top)/2;if(y<30||y>74)return null;return visible().find((_t,i)=>Math.abs(x-(cropX(_t.id)-camera))<16)||null;}
canvas.addEventListener('click',event=>{if(suppressClick){suppressClick=false;return;}const r=canvas.getBoundingClientRect(),x=(event.clientX-r.left)/2,y=(event.clientY-r.top)/2;if(x+camera<40)return;const t=y<60?pick(event):null;if(t){visit(t.id);if(event.detail<2){if(pinnedInfo===t.id)hideInfo();else{pinnedInfo=t.id;clearTimeout(hoverTimer);clearTimeout(hideTimer);showInfo(t.id);}}}else if(y>=60&&y<=74)walkTo(x+camera);});canvas.addEventListener('dblclick',event=>{event.preventDefault();const r=canvas.getBoundingClientRect();if((event.clientY-r.top)/2>=60)return;const t=pick(event);if(t){hideInfo();activatePlant(t.id);}});canvas.addEventListener('contextmenu',event=>{event.preventDefault();const t=pick(event);if(t)showDetail(t.id);});
canvas.addEventListener('mousemove',event=>{if(expanded||pinnedInfo)return;clearTimeout(hideTimer);const t=pick(event);if(!t){clearTimeout(hoverTimer);if($('plant-info').hidden)hoverId=null;hideTimer=setTimeout(()=>hideInfo(false),450);return;}if(hoverId===t.id)return;clearTimeout(hoverTimer);hoverId=t.id;hoverTimer=setTimeout(()=>showInfo(t.id),420);});
canvas.addEventListener('mouseleave',()=>{clearTimeout(hoverTimer);if($('plant-info').hidden)hoverId=null;hideTimer=setTimeout(()=>hideInfo(false),450);});
for(const el of [$('plant-info'),$('care-tools')]){el.addEventListener('mouseenter',()=>{clearTimeout(hideTimer);});el.addEventListener('mouseleave',()=>{hideTimer=setTimeout(()=>hideInfo(false),350);});}$('change-plant').onclick=()=>{if(hoverId)showDetail(hoverId);};$('water').onclick=()=>care('water');$('feed').onclick=()=>care('feed');
canvas.addEventListener('pointerdown',e=>{if(e.button!==0)return;pan={x:e.clientX,camera,moved:false};canvas.setPointerCapture(e.pointerId);});
canvas.addEventListener('pointermove',e=>{if(pan&&Math.abs(e.clientX-pan.x)>6)pan.moved=true;});
canvas.addEventListener('pointerup',e=>{if(pan?.moved)suppressClick=true;pan=null;canvas.style.cursor='pointer';if(canvas.hasPointerCapture(e.pointerId))canvas.releasePointerCapture(e.pointerId);});
canvas.addEventListener('pointercancel',()=>{pan=null;suppressClick=false;canvas.style.cursor='pointer';});
function changePage(delta){hideInfo();careQueue.length=0;activeCare=null;walker.pending=null;walker.target=walker.x;camera=GardenModel.panCamera(camera,delta,threads.length);page=Math.floor(camera/144);$('hint').hidden=true;render();}
$('prev').onclick=()=>changePage(-1);$('next').onclick=()=>changePage(1);$('pet').addEventListener('wheel',e=>{if(!e.deltaY&&!e.deltaX)return;e.preventDefault();changePage((e.deltaY||e.deltaX)>0?1:-1);},{passive:false});
$('storage').onclick=()=>{if(connection==='welcome'){showWelcome();return;}storageOpen=true;selected=null;panel(true);};$('overview').onclick=()=>{if(connection==='welcome'){showWelcome();return;}storageOpen=false;selected=null;panel(!expanded);};$('menu').onclick=()=>{storageOpen=false;selected=null;panel(!expanded);};$('close').onclick=()=>panel(false);$('back').onclick=()=>{selected=null;renderPanel();};$('harvest').onclick=()=>{};$('open-thread').onclick=()=>window.garden.open(selected).catch(e=>{errorText=e.message;renderPanel();});
$('pass').onclick=async()=>{await panel(false);await window.garden.window('pass');};
function toggleDemo(){if(harvesting.size)return;demo=!demo;careQueue.length=0;activeCare=null;walker.pending=null;walker.x=50;walker.target=50;camera=0;selected=null;page=0;if(demo){threads=['growing','ripe','paused','growing','harvested','ripe','unknown','failed'].map((status,i)=>({id:'demo-'+i,title:['为新功能播下一颗种子','文档整理完成','等你照料的菜田','人物动画制作中','收下的上一茬','代码检查已完成','状态待确认','这一茬遇到问题'][i],cwd:'演示菜园 / 示例项目',status,attention:['read','unread','unknown','read','read','unread','unknown','read'][i],crop:[15,16,17,18,19,20,7,9][i],summary:'演示数据。点击草沿可走动；点作物走过去操作，右键查看与选菜。真实模式仅根据本地记录变化。'}));$('sync').textContent='演示模式 · 示例数据';errorText='';toast('演示菜园 · 示例数据');render();}else{slots=setting('pet-slots',{});refresh();}}
$('demo').onclick=toggleDemo;window.garden.onCommand(command=>{if(command==='help')showWelcome();if(command==='collapse')panel(false);if(command==='cancel-name')finishName(false);});window.addEventListener('resize',()=>{draw();publishGeometry();});
async function init(){try{await syncName();art=await(await fetch('../assets/pixel-v04/manifest.json')).json();await GardenerStudio.init(art.pixelContract.paletteHex);defaultActor=GardenerStudio.build(GardenerStudio.fourthPreset.recipe);generatedDefaults=GardenerStudio.defaultPresets.map(p=>GardenerStudio.build(p.recipe));heroes=art.heroes;GardenerStudio.defaultPresets.forEach((p,i)=>heroes[i].name=p.name);heroes[3].name='栗辫 · 围裙园丁';heroIndex=Math.max(0,setting('art04-hero',0))%heroes.length;slots=setting('pet-slots',{});await Promise.all(Object.entries(art.images).map(([key,file])=>new Promise((resolve,reject)=>{const img=new Image();img.onload=()=>{atlases.set(key,img);resolve();};img.onerror=()=>reject(Error('像素图集无法加载：'+file));img.src='../assets/pixel-v04/'+file;})));for(const h of heroes)for(const f of h.frames)frames.set(h.id+'/'+f.file,atlases.get(h.image));land=await new Promise((resolve,reject)=>{const img=new Image();img.onload=()=>resolve(img);img.onerror=()=>reject(Error('土地纹理加载失败'));img.src='../assets/pixel-v05/land.png';});sun=await new Promise((resolve,reject)=>{const img=new Image();img.onload=()=>resolve(img);img.onerror=()=>reject(Error('太阳动画加载失败'));img.src='../assets/pixel-v05/sun.png';});supplies=await new Promise((resolve,reject)=>{const img=new Image();img.onload=()=>resolve(img);img.onerror=()=>reject(Error('农具角加载失败'));img.src='../assets/pixel-v05/farm-supplies.png';});for(const [name,file] of [['plantAtlas','crops.png'],['tilled','tilled.png'],['specialAtlas','specials.png'],['fantasyAtlas','../pixel-fantasy/plants.png']]){const img=await new Promise((resolve,reject)=>{const v=new Image();v.onload=()=>resolve(v);v.onerror=()=>reject(Error(file+' 加载失败'));v.src='../assets/pixel-v07/'+file;});if(name==='plantAtlas')plantAtlas=img;else if(name==='specialAtlas')specialAtlas=img;else if(name==='fantasyAtlas')fantasyAtlas=img;else tilled=img;}rebuildPhotoGardener();drawMarks();await document.fonts.ready;ready=true;await refresh();timer=setInterval(()=>draw(),40);}catch(e){errorText=e.message;errors.push(e.message);$('overview').textContent='暂时无法更新';}publishGeometry();}
window.petApp={inspect:()=>({ready,studioReady:Boolean(defaultActor),gardenerPipeline:ready?GardenerStudio.source():null,defaultSources:generatedDefaults.map(a=>a.source),studioActions:defaultActor?GardenerStudio.actions():null,demo,gardenName,editingName,sequence:ordered().map(t=>({id:t.id,number:slots[t.id]+1,kind:displayKind(t)})),expanded,pinnedInfo,customGardener:Boolean(customActions),customSelected,page,camera,connection,storageOpen,inventory:{...(demo?demoInventory:inventory)},opened:[...opened],hoverId,careEffects:careEffects.length,careQueued:careQueue.length,careHistory:[...careHistory],activeCare:activeCare?.kind||null,walker:{...walker},cropChoices:{...(demo?demoChoices:cropChoices)},suppliesLoaded:Boolean(supplies),suppliesWorldX:2,attentionCounts:Object.fromEntries(['read','unread','unknown'].map(k=>[k,threads.filter(t=>(t.attention||'unknown')===k).length])),plantOptions:selectableKinds.length,discoveries:[...discoveries],independentActions:Boolean(defaultActor),specialArt:Boolean(specialAtlas),cropArtV07:Boolean(plantAtlas&&tilled),sunLoaded:Boolean(sun),groundLoaded:Boolean(land),threads:threads.length,visible:visible().map(t=>({id:t.id,status:t.status,attention:t.attention})),loadedFrames:frames.size,artVersion:art?.version,loadedAtlases:atlases.size,errors,hero:heroIndex,error:errorText,maskOpaque:maskData?maskData.reduce((a,b)=>a+b,0):0}),panel,detail:showDetail,harvest,toggleDemo,walkTo,visit,chooseCrop,care};setInterval(refresh,4000);init();

function rebuildPhotoGardener(){if(GardenerStudio.valid(customRecipe)){customActor=GardenerStudio.build(customRecipe);customRecipe={...customActor.recipe};save('gardener-recipe-v1',customRecipe);customActions=customActor.sheet;customPortrait=customActor.portrait;}else{customSelected=false;save('photo-gardener-selected',false);}}
let workshopActor=null,workshopRecipe=null,previewAction='idle',workshopTimer=null,workshopSession=0,photoBusy=false,workshopInitial=null;
let workshopHistory=[],workshopFuture=[];
const sameRecipe=(a,b)=>JSON.stringify(a)===JSON.stringify(b);
function closePicker(){$('workshop-picker').hidden=true;document.querySelectorAll('#workshop-fields button').forEach(b=>b.setAttribute('aria-expanded','false'));}
function workshopHistoryState(){$('workshop-undo').disabled=!workshopHistory.length;$('workshop-redo').disabled=!workshopFuture.length;$('workshop-reset').disabled=sameRecipe(workshopRecipe,workshopInitial);}
function setPhotoBusy(value){photoBusy=value;$('workshop-photo').disabled=value;$('workshop-photo').textContent=value?'处理中…':'照片参考';$('workshop-apply').disabled=value;}

function closeWorkshop(){workshopSession++;setPhotoBusy(false);closePicker();clearInterval(workshopTimer);workshopTimer=null;$('gardener-workshop').hidden=true;$('panel').classList.remove('workshopping');$('reference-photo').getContext('2d').clearRect(0,0,80,80);$('reference-photo').hidden=true;workshopActor=null;}
function updateWorkshop(){workshopRecipe={schemaVersion:3};for(const k of Object.keys(GardenerStudio.choices))workshopRecipe[k]=$('recipe-'+k).dataset.value;workshopRecipe.beard=$('recipe-beard').checked;workshopActor=GardenerStudio.build(workshopRecipe);$('recipe-body').closest('label').hidden=workshopRecipe.library==='lpc';}
const workshopLabels={library:'画风',body:'衣型',face:'脸型',nose:'鼻型',eyes:'瞳色',style:'发型',hat:'帽子',skin:'肤色',hair:'发色',shirt:'上衣',coat:'围裙'};
const workshopNames={classic:'原作像素',lpc:'冒险像素',field:'麦穗款',petal:'桃桃款',night:'夜蓝款',source:'原色',balanced:'标准脸',soft:'柔和脸',round:'圆润脸',angular:'棱角脸',elder:'长者脸',small:'小脸',natural:'原生',button:'圆鼻',straight:'直鼻',large:'宽鼻',ocean:'湖蓝',moss:'苔绿',honey:'琥珀',amethyst:'紫灰',crop:'蓬松短发',bob:'齐耳短发',shag:'碎发',curly:'卷发',pony:'马尾',braid:'编辫',straw:'草帽',none:'不戴帽',bald:'光头',light:'浅色',amber:'暖色',olive:'橄榄',bronze:'古铜',brown:'棕色',black:'黑色',ginger:'姜红',blonde:'金色',dark_brown:'深棕',white:'米白',pink:'粉色',sky:'浅蓝',yellow:'黄',rose:'玫瑰',slate:'灰蓝',forest:'森林绿',blue:'蓝色',maroon:'酒红',teal:'青绿'};
function setWorkshopFields(recipe,{record=true}={}){
 const r=GardenerStudio.normalize(recipe);if(record&&workshopRecipe&&!sameRecipe(workshopRecipe,r)){workshopHistory.push({...workshopRecipe});if(workshopHistory.length>30)workshopHistory.shift();workshopFuture=[];}
 for(const k of Object.keys(GardenerStudio.choices)){const b=$('recipe-'+k);b.dataset.value=r[k];b.textContent=workshopNames[r[k]]+' ▾';b.setAttribute('aria-label',workshopLabels[k]+'：'+workshopNames[r[k]]);}
 $('recipe-beard').checked=r.beard;updateWorkshop();workshopHistoryState();
 [...$('workshop-presets').children].forEach((b,i)=>{const selected=sameRecipe(workshopRecipe,GardenerStudio.normalize(GardenerStudio.presets[i].recipe));b.classList.toggle('selected',selected);b.setAttribute('aria-pressed',String(selected));});
}
function showWorkshopOptions(key){
 const holder=$('picker-options');holder.replaceChildren();$('picker-title').textContent='选择'+workshopLabels[key];
 for(const value of GardenerStudio.optionsFor(workshopRecipe,key)){const b=make('button',workshopNames[value]);b.type='button';b.dataset.option=value;b.classList.toggle('selected',value===workshopRecipe[key]);b.setAttribute('aria-pressed',String(value===workshopRecipe[key]));b.onclick=()=>{setWorkshopFields({...workshopRecipe,[key]:value});closePicker();};holder.append(b);}
 $('workshop-picker').hidden=false;$('recipe-'+key).setAttribute('aria-expanded','true');
}
$('picker-close').onclick=closePicker;
$('workshop-undo').onclick=()=>{if(!workshopHistory.length)return;workshopFuture.push({...workshopRecipe});setWorkshopFields(workshopHistory.pop(),{record:false});closePicker();};
$('workshop-redo').onclick=()=>{if(!workshopFuture.length)return;workshopHistory.push({...workshopRecipe});setWorkshopFields(workshopFuture.pop(),{record:false});closePicker();};
$('workshop-reset').onclick=()=>{setWorkshopFields(workshopInitial);closePicker();};
function openWorkshop(){
 closeWorkshop();const current=customSelected&&GardenerStudio.valid(customRecipe)?customRecipe:(heroIndex===3?GardenerStudio.fourthPreset.recipe:GardenerStudio.defaultPresets[heroIndex]?.recipe)||GardenerStudio.defaults;workshopInitial=GardenerStudio.normalize(current);workshopRecipe=null;workshopHistory=[];workshopFuture=[];
 $('workshop-presets').replaceChildren();
 for(const preset of GardenerStudio.presets){
  const b=make('button'),c=document.createElement('canvas');c.width=32;c.height=32;b.type='button';b.title=preset.name;b.setAttribute('aria-label',preset.name+'样式');c.getContext('2d').drawImage(GardenerStudio.build(preset.recipe).portrait,0,0);b.append(c,document.createTextNode(preset.name));
  b.onclick=()=>{setWorkshopFields(preset.recipe);closePicker();};$('workshop-presets').append(b);
 }
 $('workshop-fields').replaceChildren();
 for(const [k,values] of Object.entries(GardenerStudio.choices)){
  const l=make('label');l.textContent=workshopLabels[k];const b=make('button');b.type='button';b.id='recipe-'+k;
  b.setAttribute('aria-haspopup','true');b.setAttribute('aria-expanded','false');b.onclick=()=>showWorkshopOptions(k);l.append(b);$('workshop-fields').append(l);
 }
 $('recipe-beard').onchange=()=>setWorkshopFields({...workshopRecipe,beard:$('recipe-beard').checked});setWorkshopFields(workshopInitial,{record:false});previewAction='idle';document.querySelectorAll('[data-preview-action]').forEach(b=>{const active=b.dataset.previewAction==='idle';b.classList.toggle('selected',active);b.setAttribute('aria-pressed',String(active));});$('panel-title').textContent='园丁工坊';$('workshop-status').textContent='修改只在预览中生效，点“应用园丁”保存。';$('gardener-workshop').hidden=false;$('panel').classList.add('workshopping');
 const paint=()=>{if(!workshopActor)return;const c=$('workshop-preview'),x=c.getContext('2d');x.clearRect(0,0,c.width,c.height);x.imageSmoothingEnabled=false;GardenerStudio.draw(x,workshopActor,previewAction,performance.now(),0,0,96);};paint();workshopTimer=setInterval(paint,80);publishGeometry();
}
$('photo-gardener').onclick=openWorkshop;
$('workshop-cancel').onclick=()=>{closeWorkshop();renderPanel();};
$('workshop-apply').onclick=()=>{if(!workshopActor)return;customRecipe={...workshopRecipe};save('gardener-recipe-v1',customRecipe);customSelected=true;save('photo-gardener-selected',true);rebuildPhotoGardener();closeWorkshop();renderPanel();draw();toast('园丁已加入菜园');};
$('workshop-photo').onclick=async()=>{
 if(photoBusy)return;const session=workshopSession;setPhotoBusy(true);closePicker();$('workshop-status').textContent='选择照片后会在本机参考配色，不上传。';
 try{const data=await window.garden.photo();if(session!==workshopSession||$('gardener-workshop').hidden)return;if(!data){$('workshop-status').textContent='已取消，外观没有改变。';return;}
 $('workshop-status').textContent='正在参考照片配色…';const img=new Image();await new Promise((ok,fail)=>{img.onload=ok;img.onerror=()=>fail(Error('照片无法读取，请换一张'));img.src=data;});if(session!==workshopSession||$('gardener-workshop').hidden)return;applyPhoto(img);
 }catch(e){if(session===workshopSession)$('workshop-status').textContent=e.message||'照片无法读取，请换一张';}finally{if(session===workshopSession)setPhotoBusy(false);}
};
document.querySelectorAll('[data-preview-action]').forEach(b=>b.onclick=()=>{previewAction=b.dataset.previewAction;document.querySelectorAll('[data-preview-action]').forEach(v=>{v.classList.toggle('selected',v===b);v.setAttribute('aria-pressed',String(v===b));});});
function applyPhoto(bitmap){if(bitmap.width*bitmap.height>40000000)throw Error('照片过大，请缩小后重试');if($('gardener-workshop').hidden)return;setWorkshopFields(GardenerStudio.fromPhoto(bitmap,workshopRecipe));$('reference-photo').hidden=false;const x=$('reference-photo').getContext('2d');x.clearRect(0,0,80,80);const scale=Math.min(80/bitmap.width,80/bitmap.height);x.drawImage(bitmap,(80-bitmap.width*scale)/2,(80-bitmap.height*scale)/2,bitmap.width*scale,bitmap.height*scale);$('workshop-status').textContent='已参考照片搭配配色和发型，可继续调整。';}
$('gardener-photo-file').onchange=async event=>{const file=event.target.files[0];if(!file)return;if($('gardener-workshop').hidden)openWorkshop();const session=workshopSession;try{if(!['image/png','image/jpeg','image/webp'].includes(file.type)||file.size>10*1024*1024)throw Error('请选择10MB以内的 PNG、JPEG 或 WebP 照片');const bitmap=await createImageBitmap(file);try{if(session===workshopSession)applyPhoto(bitmap);}finally{bitmap.close();}}catch(e){$('workshop-status').textContent=e.message||'照片无法读取，请换一张';}finally{event.target.value='';}};
