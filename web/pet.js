const $=id=>document.getElementById(id),canvas=$('garden'),ctx=canvas.getContext('2d',{willReadFrequently:true});ctx.imageSmoothingEnabled=false;
const labels={growing:'正在回复',ripe:'可收获',harvested:'已收获',paused:'已暂停',failed:'遇到问题',stale:'等待更新',unknown:'等待更新',waiting:'等你处理'};
let art=null,atlases=new Map(),heroes=[],frames=new Map(),threads=[],page=0,heroIndex=0,expanded=false,selected=null,demo=false,busy=false,ready=false,harvesting=new Set(),slots={},timer,lastMask=0,maskData=null,errorText='',toastTimer;
const activating=new Set(),opened=[];
const errors=[];window.addEventListener('error',e=>errors.push(e.message));window.addEventListener('unhandledrejection',e=>errors.push(String(e.reason)));
let walker={x:50,target:50,facing:1,pending:null},lastDraw=0,land=null,sun=null,supplies=null,plantAtlas=null,actionAtlas=null,specialAtlas=null,tilled=null,camera=0;
let connection='loading',lastStorageNotice='';
let storageOpen=false,inventory={},demoInventory={};
let gardenName=GardenModel.gardenName(setting('garden-name',null)),editingName=false;
function orderLabel(id){return String(slots[id]+1).padStart(2,'0');}
function syncName(){document.title=gardenName;$('welcome-title').textContent='欢迎来到'+gardenName;return window.garden.window('name',gardenName);}
async function finishName(commit=false){if(!editingName)return;editingName=false;if(commit){gardenName=GardenModel.gardenName($('garden-name-input').value);save('garden-name',gardenName);await syncName();}$('name-editor').hidden=true;$('panel').classList.remove('naming');await window.garden.window('editing',false);if(expanded)renderPanel();publishGeometry();}
$('rename-garden').onclick=async()=>{editingName=true;$('name-editor').hidden=false;$('panel').classList.add('naming');$('garden-name-input').value=gardenName;publishGeometry();await window.garden.window('editing',true);$('garden-name-input').focus();$('garden-name-input').select();};
$('name-editor').onsubmit=event=>{event.preventDefault();finishName(true);};$('cancel-name').onclick=()=>finishName(false);$('garden-name-input').addEventListener('keydown',event=>{if(event.key==='Escape'){event.preventDefault();finishName(false);}});
let hoverId=null,hoverTimer,hideTimer;const careEffects=[],careQueue=[],careHistory=[];let activeCare=null;
function hideInfo(){clearTimeout(hoverTimer);clearTimeout(hideTimer);hoverId=null;$('plant-info').hidden=true;$('care-tools').hidden=true;}
function showInfo(id){if(expanded)return;const t=threads.find(t=>t.id===id);if(!t)return;hoverId=id;$('info-title').textContent=orderLabel(t.id)+' · '+(t.title||'未命名对话');$('info-status').textContent=userStatus(t);$('plant-info').hidden=false;$('care-tools').hidden=false;publishGeometry();}
function care(kind,id=hoverId){if(!['water','feed'].includes(kind)||!threads.some(t=>t.id===id)||careQueue.length>=4)return;careQueue.push({kind,id});draw();}
let pan=null,suppressClick=false;
$('drag').hidden=true;
let cropChoices=setting('garden-crop-choices',{}),demoChoices={};
const cropNames=['胡萝卜','卷心菜','番茄','南瓜','玉米','茄子','草莓','向日葵','月光花','水晶菇','星灯草'];
const hiddenNames=['黄金萝卜','月玉卷心菜','星露番茄','琥珀南瓜'];let discoveries=setting('garden-discoveries',[]);
function secretOf(t){return GardenModel.secretPlant(t.id,t.turn);}
function displayKind(t){const secret=t.status==='ripe'?secretOf(t):null;return secret===null?cropKind(t):11+secret;}
function plantRect(kind,stage,frame=0,variety=0){return kind<3?{image:plantAtlas,y:(variety*9+kind*3+frame)*28}:{image:specialAtlas,y:((kind-3)*3+frame)*28};}
function cropKind(t){return (demo?demoChoices:cropChoices)[t.id]??t.crop;}
function walkTo(x,pending=null){walker.target=Math.max(46,x);walker.pending=pending;}
function visit(id){if(!threads.some(t=>t.id===id))return;walkTo(cropX(id)-GardenModel.geometry.interactionOffset,{id});}
function chooseCrop(kind){if(!selected||!Number.isInteger(kind)||kind<0||kind>=cropNames.length)return;(demo?demoChoices:cropChoices)[selected]=kind;if(!demo)save('garden-crop-choices',cropChoices);renderPanel();draw();}
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
 if(plantAtlas){const spec=plantRect(kind,stage,frame,variety);c.drawImage(spec.image,stage*28,spec.y,28,28,Math.round(x-14),32,28,28);}
 if(GardenModel.CARE.includes(status))icon(c,'care',x+9,40,8);
}
const fx=$('plant-fx'),fxc=fx.getContext('2d');
function drawPlantLight(time){
 fxc.clearRect(0,0,420,150);const reduced=matchMedia('(prefers-reduced-motion: reduce)').matches;
 for(const t of visible()){
  const rare=displayKind(t)>=11;if(t.attention!=='unread'&&!rare)continue;
  let seed=0;for(const ch of t.id)seed=(Math.imul(seed,31)+ch.charCodeAt(0))>>>0;
  const cx=(cropX(t.id)-camera)*2,count=reduced?3:7;
  for(let i=0;i<count;i++){
   const duration=2200+(seed+i*137)%1400,phase=reduced?.45:((time+(seed%3000)+i*479)%duration)/duration;
   const envelope=Math.sin(Math.PI*phase),drift=Math.sin(phase*5+i*2.1)*5;
   const px=cx+((seed+i*17)%33)-16+drift,py=114-phase*(28+(i%3)*8);
   const radius=3+(i%3)*1.2,alpha=.65*envelope;
   const light=fxc.createRadialGradient(px,py,0,px,py,radius);
   light.addColorStop(0,`rgba(248,255,255,${alpha})`);
   light.addColorStop(.18,rare?`rgba(255,234,160,${alpha*.85})`:`rgba(176,232,255,${alpha*.85})`);
   light.addColorStop(.48,rare?`rgba(245,184,74,${alpha*.26})`:`rgba(100,188,255,${alpha*.26})`);
   light.addColorStop(1,'rgba(100,188,255,0)');fxc.fillStyle=light;fxc.beginPath();fxc.arc(px,py,radius,0,Math.PI*2);fxc.fill();
   fxc.fillStyle=`rgba(255,255,245,${envelope*.88})`;fxc.beginPath();fxc.arc(px,py,.55+(i%2)*.15,0,Math.PI*2);fxc.fill();
  }
 }
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
 let actionColumn=2;
 if(acting)actionColumn=(activeCare.kind==='water'?2:5)+(reduce?1:Math.min(2,Math.floor((time-activeCare.start)/400)));
 if(actionAtlas){const sx=actionColumn*48,sy=heroIndex*48;ctx.save();ctx.translate(Math.round(walker.x-camera),60);ctx.scale(walker.facing,1);
  if(moving&&!reduce){const phase=Math.floor(time/140)%4,offset=[-1,0,1,0][phase];ctx.drawImage(actionAtlas,sx,sy,48,36,-24,-44,48,36);ctx.drawImage(actionAtlas,sx,sy+36,24,12,-24+offset,-8,24,12);ctx.drawImage(actionAtlas,sx+24,sy+36,24,12,-offset,-8,24,12);}
  else ctx.drawImage(actionAtlas,sx,sy,48,48,-24,-44,48,48);
  ctx.restore();}
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
async function panel(open){if(!open)await finishName(false);hideInfo();expanded=open;if(!open){$('panel').hidden=true;selected=null;$('hint').hidden=true;}await window.garden.window('panel',open);$('panel').hidden=!open;if(open)renderPanel();publishGeometry();}
async function showWelcome(){if(!$('welcome').hidden)return;hideInfo();$('panel').hidden=true;await window.garden.window('panel',true);$('welcome').hidden=false;publishGeometry();}
$('begin').onclick=async()=>{await window.garden.window('start');$('welcome').hidden=true;await panel(false);await refresh();};
function showDetail(id){storageOpen=false;selected=id;panel(true);}
function renderPanel(){
 $('panel-title').textContent=storageOpen?'储物收藏':selected?'我的菜地':gardenName;$('panel-title').title=gardenName;$('rename-garden').hidden=storageOpen||Boolean(selected);$('back').hidden=!selected;$('list-view').hidden=storageOpen||Boolean(selected);$('detail-view').hidden=storageOpen||!selected;$('storage-view').hidden=!storageOpen;$('settings').hidden=storageOpen;$('error').textContent=errorText?'暂时无法更新，请稍后再试。':'';
 if(storageOpen){const items=demo?demoInventory:inventory;$('storage-items').replaceChildren();const entries=Object.entries(items).filter(([k,n])=>Number(n)>0);$('storage-caption').textContent=entries.length?'你的收获都在这里':'还没有收藏，双击成熟植物收获吧。';for(const [key,count] of entries){const kind=Number(key),tile=make('div'),picture=make('canvas');picture.width=28;picture.height=28;const pc=picture.getContext('2d');pc.imageSmoothingEnabled=false;const spec=plantRect(kind,3);pc.drawImage(spec.image,84,spec.y,28,28,0,0,28,28);tile.className=kind>=11?'stored-plant rare':'stored-plant';tile.append(picture,make('span',kind>=11?hiddenNames[kind-11]:cropNames[kind]),make('small','× '+count));$('storage-items').append(tile);}}
 if(selected&&!storageOpen){const t=threads.find(t=>t.id===selected);if(!t){selected=null;renderPanel();return;}$('status').textContent=orderLabel(t.id)+' · '+userStatus(t);$('title').textContent=t.title||'未命名对话';const secret=t.status==='ripe'?secretOf(t):null;if(secret!==null)$('status').textContent+=' · '+hiddenNames[secret];$('project').textContent='';$('summary').textContent='';$('harvest').hidden=true;$('harvest').disabled=t.status!=='ripe'||harvesting.has(t.id);$('harvest').textContent=harvesting.has(t.id)?'收获中…':'收获';$('open-thread').disabled=demo;}
 else if(!storageOpen){$('threads').replaceChildren();for(const t of ordered()){const b=make('button');b.dataset.thread=t.id;b.dataset.order=String(slots[t.id]+1);const number=make('span',orderLabel(t.id));number.className='thread-number';const thumb=make('canvas');thumb.width=28;thumb.height=28;thumb.className='thread-crop';thumb.dataset.kind=String(displayKind(t));thumb.setAttribute('aria-label',displayKind(t)>=11?hiddenNames[displayKind(t)-11]:cropNames[displayKind(t)]);const tc=thumb.getContext('2d');tc.imageSmoothingEnabled=false;const spec=plantRect(displayKind(t),GardenModel.cropStage(t.status));tc.drawImage(spec.image,GardenModel.cropStage(t.status)*28,spec.y,28,28,0,0,28,28);const n=make('strong',t.title||'未命名对话'),s=make('small',userStatus(t));s.className=t.status;b.append(number,thumb,n,s);b.onclick=()=>{selected=t.id;visit(t.id);renderPanel();};$('threads').append(b);}if(!threads.length)$('threads').append(make('p','开始一段 Codex 对话，种下第一颗种子。'));}
 let chooser=$('crop-choices');if(!chooser){chooser=make('div');chooser.id='crop-choices';$('summary').before(chooser);}
 chooser.replaceChildren();if(selected){const t=threads.find(t=>t.id===selected);cropNames.forEach((name,i)=>{const b=make('button');b.className=cropKind(t)===i?'selected':'';b.setAttribute('aria-pressed',String(cropKind(t)===i));const c=make('canvas');c.width=32;c.height=32;const pc=c.getContext('2d');pc.imageSmoothingEnabled=false;const spec=plantRect(i,3);pc.drawImage(spec.image,84,spec.y,28,28,2,2,28,28);b.append(c,make('span',name));b.onclick=()=>chooseCrop(i);chooser.append(b);});let note=$('collection-note');if(!note){note=make('p');note.id='collection-note';chooser.after(note);}note.textContent=discoveries.length?'已发现：'+discoveries.map(i=>hiddenNames[i]).join('、'):'成熟时，偶尔会遇见隐藏品种。';}
 $('demo').textContent=demo?'返回真实':'演示';$('heroes').replaceChildren();heroes.forEach((h,i)=>{const b=make('button');b.className=i===heroIndex?'selected':'';b.title=h.name;b.setAttribute('aria-label','选择园丁 '+h.name);const portrait=make('canvas');portrait.width=32;portrait.height=32;portrait.setAttribute('aria-label',h.name);const pc=portrait.getContext('2d');pc.imageSmoothingEnabled=false;atlasDraw(pc,h.portrait.image,h.portrait.sourceRect,0,0,32,32);b.append(portrait);b.onclick=()=>{heroIndex=i;save('art04-hero',i);renderPanel();draw();};$('heroes').append(b);});
}
function render(){const previousSlots=slots;slots=GardenModel.sequentialSlots(threads);if(walker.pending){if(slots[walker.pending.id]===undefined){walker.pending=null;walker.target=walker.x;}else walker.target=cropX(walker.pending.id)-GardenModel.geometry.interactionOffset;}if(activeCare&&(slots[activeCare.id]===undefined||slots[activeCare.id]!==previousSlots[activeCare.id])){careEffects.length=0;if(slots[activeCare.id]===undefined)activeCare=null;else{activeCare.start=null;walker.target=cropX(activeCare.id)-18;}}for(let i=careQueue.length-1;i>=0;i--)if(slots[careQueue[i].id]===undefined)careQueue.splice(i,1);page=Math.min(page,Math.max(0,Math.ceil(threads.length/4)-1));$('growing').textContent=threads.filter(t=>t.status==='growing').length;$('ripe').textContent=threads.filter(t=>t.attention==='unread').length;$('page').textContent=(page+1)+'/'+Math.max(1,Math.ceil(threads.length/4));$('prev').disabled=false;$('next').disabled=false;if(!demo&&connection!=='ready')$('ripe').textContent='—';$('overview').title=!demo&&connection!=='ready'?'连接暂不可用，请先打开 Codex':'查看全部对话';if(expanded)renderPanel();draw();}
async function refresh(){if(busy||demo)return;busy=true;try{const s=await window.garden.snapshot();if(demo)return;connection=s.connection||'ready';if(connection==='welcome'){await showWelcome();return;}if(!s.error)threads=s.threads;inventory=s.inventory||inventory;errorText=s.error||'';if(s.storageNotice&&lastStorageNotice!==s.storageNotice){lastStorageNotice=s.storageNotice;toast(s.storageNotice);}$('sync').textContent='本地只读 · '+new Date().toLocaleTimeString('zh-CN')+' 同步';render();}catch(e){connection='error';errorText='同步中断：'+e.message;$('sync').textContent='本地同步中断';if(expanded)renderPanel();}finally{busy=false;}}
async function harvest(id){const t=threads.find(t=>t.id===id);if(!t||t.status!=='ripe'||harvesting.has(id))return false;harvesting.add(id);if(expanded)renderPanel();try{const harvestedKind=displayKind(t);if(!demo){const result=await window.garden.harvest(id,harvestedKind);inventory=result.inventory||inventory;}else demoInventory[harvestedKind]=(demoInventory[harvestedKind]||0)+1;const secret=secretOf(t);if(secret!==null&&!demo&&!discoveries.includes(secret)){discoveries.push(secret);save('garden-discoveries',discoveries);}t.status='harvested';toast(secret===null?'收获成功':'发现隐藏款 · '+hiddenNames[secret]);render();return true;}catch(e){errorText=e.message;toast('收获失败，请稍后重试');return false;}finally{harvesting.delete(id);if(expanded)renderPanel();}}
async function activatePlant(id){if(!demo&&connection!=='ready'){toast('连接恢复后再试');return;}if(activating.has(id))return;const t=threads.find(t=>t.id===id);if(!t)return;activating.add(id);walker.pending=null;try{if(t.status==='ripe'&&!await harvest(id))return;if(demo)opened.push(id);else await window.garden.open(id);}catch(e){errorText=e.message;toast('暂时无法打开对话，请稍后重试');}finally{activating.delete(id);}}
function pick(event){const r=canvas.getBoundingClientRect(),x=(event.clientX-r.left)/2,y=(event.clientY-r.top)/2;if(y<30||y>74)return null;return visible().find((_t,i)=>Math.abs(x-(cropX(_t.id)-camera))<16)||null;}
canvas.addEventListener('click',event=>{if(suppressClick){suppressClick=false;return;}const r=canvas.getBoundingClientRect(),x=(event.clientX-r.left)/2,y=(event.clientY-r.top)/2;if(x+camera<40)return;const t=y<60?pick(event):null;if(t)visit(t.id);else if(y>=60&&y<=74)walkTo(x+camera);});canvas.addEventListener('dblclick',event=>{event.preventDefault();const r=canvas.getBoundingClientRect();if((event.clientY-r.top)/2>=60)return;const t=pick(event);if(t)activatePlant(t.id);});canvas.addEventListener('contextmenu',event=>{event.preventDefault();const t=pick(event);if(t)showDetail(t.id);});
canvas.addEventListener('mousemove',event=>{if(expanded)return;clearTimeout(hideTimer);const t=pick(event);if(!t){clearTimeout(hoverTimer);if($('plant-info').hidden)hoverId=null;hideTimer=setTimeout(hideInfo,450);return;}if(hoverId===t.id)return;clearTimeout(hoverTimer);hoverId=t.id;hoverTimer=setTimeout(()=>showInfo(t.id),420);});
canvas.addEventListener('mouseleave',()=>{clearTimeout(hoverTimer);if($('plant-info').hidden)hoverId=null;hideTimer=setTimeout(hideInfo,450);});
for(const el of [$('plant-info'),$('care-tools')]){el.addEventListener('mouseenter',()=>{clearTimeout(hideTimer);});el.addEventListener('mouseleave',()=>{hideTimer=setTimeout(hideInfo,350);});}$('water').onclick=()=>care('water');$('feed').onclick=()=>care('feed');
canvas.addEventListener('pointerdown',e=>{if(e.button!==0)return;pan={x:e.clientX,camera,moved:false};canvas.setPointerCapture(e.pointerId);});
canvas.addEventListener('pointermove',e=>{if(pan&&Math.abs(e.clientX-pan.x)>6)pan.moved=true;});
canvas.addEventListener('pointerup',e=>{if(pan?.moved)suppressClick=true;pan=null;canvas.style.cursor='pointer';if(canvas.hasPointerCapture(e.pointerId))canvas.releasePointerCapture(e.pointerId);});
canvas.addEventListener('pointercancel',()=>{pan=null;suppressClick=false;canvas.style.cursor='pointer';});
function changePage(delta){hideInfo();careQueue.length=0;activeCare=null;walker.pending=null;walker.target=walker.x;camera=Math.max(0,camera+delta*144);page=Math.floor(camera/144);$('hint').hidden=true;render();}
$('prev').onclick=()=>changePage(-1);$('next').onclick=()=>changePage(1);$('pet').addEventListener('wheel',e=>{e.preventDefault();changePage(e.deltaY>0?1:-1);},{passive:false});
$('storage').onclick=()=>{if(connection==='welcome'){showWelcome();return;}storageOpen=true;selected=null;panel(true);};$('overview').onclick=()=>{if(connection==='welcome'){showWelcome();return;}storageOpen=false;selected=null;panel(!expanded);};$('menu').onclick=()=>{storageOpen=false;selected=null;panel(!expanded);};$('close').onclick=()=>panel(false);$('back').onclick=()=>{selected=null;renderPanel();};$('harvest').onclick=()=>{};$('open-thread').onclick=()=>window.garden.open(selected).catch(e=>{errorText=e.message;renderPanel();});
$('pass').onclick=async()=>{await panel(false);await window.garden.window('pass');};
function toggleDemo(){if(harvesting.size)return;demo=!demo;careQueue.length=0;activeCare=null;walker.pending=null;walker.x=50;walker.target=50;camera=0;selected=null;page=0;if(demo){threads=['growing','ripe','paused','growing','harvested','ripe','unknown','failed'].map((status,i)=>({id:'demo-'+i,title:['为新功能播下一颗种子','文档整理完成','等你照料的菜田','人物动画制作中','收下的上一茬','代码检查已完成','状态待确认','这一茬遇到问题'][i],cwd:'演示菜园 / 示例项目',status,attention:['read','unread','unknown','read','read','unread','unknown','read'][i],crop:i%3,summary:'演示数据。点击草沿可走动；点作物走过去操作，右键查看与选菜。真实模式仅根据本地记录变化。'}));$('sync').textContent='演示模式 · 示例数据';errorText='';toast('演示菜园 · 示例数据');render();}else{slots=setting('pet-slots',{});refresh();}}
$('demo').onclick=toggleDemo;window.garden.onCommand(command=>{if(command==='help')showWelcome();if(command==='collapse')panel(false);if(command==='cancel-name')finishName(false);});window.addEventListener('resize',()=>{draw();publishGeometry();});
async function init(){try{await syncName();art=await(await fetch('../assets/pixel-v04/manifest.json')).json();heroes=art.heroes;heroIndex=Math.max(0,setting('art04-hero',0))%heroes.length;slots=setting('pet-slots',{});await Promise.all(Object.entries(art.images).map(([key,file])=>new Promise((resolve,reject)=>{const img=new Image();img.onload=()=>{atlases.set(key,img);resolve();};img.onerror=()=>reject(Error('像素图集无法加载：'+file));img.src='../assets/pixel-v04/'+file;})));for(const h of heroes)for(const f of h.frames)frames.set(h.id+'/'+f.file,atlases.get(h.image));land=await new Promise((resolve,reject)=>{const img=new Image();img.onload=()=>resolve(img);img.onerror=()=>reject(Error('土地纹理加载失败'));img.src='../assets/pixel-v05/land.png';});sun=await new Promise((resolve,reject)=>{const img=new Image();img.onload=()=>resolve(img);img.onerror=()=>reject(Error('太阳动画加载失败'));img.src='../assets/pixel-v05/sun.png';});supplies=await new Promise((resolve,reject)=>{const img=new Image();img.onload=()=>resolve(img);img.onerror=()=>reject(Error('农具角加载失败'));img.src='../assets/pixel-v05/farm-supplies.png';});for(const [name,file] of [['plantAtlas','crops.png'],['tilled','tilled.png'],['specialAtlas','specials.png']]){const img=await new Promise((resolve,reject)=>{const v=new Image();v.onload=()=>resolve(v);v.onerror=()=>reject(Error(file+' 加载失败'));v.src='../assets/pixel-v07/'+file;});if(name==='plantAtlas')plantAtlas=img;else if(name==='specialAtlas')specialAtlas=img;else tilled=img;}actionAtlas=await new Promise((resolve,reject)=>{const img=new Image();img.onload=()=>resolve(img);img.onerror=()=>reject(Error('人物动作加载失败'));img.src='../assets/pixel-v091/actions.png';});drawMarks();await document.fonts.ready;ready=true;await refresh();timer=setInterval(()=>draw(),40);}catch(e){errorText=e.message;errors.push(e.message);$('overview').textContent='暂时无法更新';}publishGeometry();}
window.petApp={inspect:()=>({ready,demo,gardenName,editingName,sequence:ordered().map(t=>({id:t.id,number:slots[t.id]+1,kind:displayKind(t)})),expanded,page,camera,connection,storageOpen,inventory:{...(demo?demoInventory:inventory)},opened:[...opened],hoverId,careEffects:careEffects.length,careQueued:careQueue.length,careHistory:[...careHistory],activeCare:activeCare?.kind||null,walker:{...walker},cropChoices:{...(demo?demoChoices:cropChoices)},suppliesLoaded:Boolean(supplies),suppliesWorldX:2,attentionCounts:Object.fromEntries(['read','unread','unknown'].map(k=>[k,threads.filter(t=>(t.attention||'unknown')===k).length])),plantOptions:cropNames.length,discoveries:[...discoveries],independentActions:Boolean(actionAtlas),specialArt:Boolean(specialAtlas),cropArtV07:Boolean(plantAtlas&&tilled),sunLoaded:Boolean(sun),groundLoaded:Boolean(land),threads:threads.length,visible:visible().map(t=>({id:t.id,status:t.status,attention:t.attention})),loadedFrames:frames.size,artVersion:art?.version,loadedAtlases:atlases.size,errors,hero:heroIndex,error:errorText,maskOpaque:maskData?maskData.reduce((a,b)=>a+b,0):0}),panel,detail:showDetail,harvest,toggleDemo,walkTo,visit,chooseCrop,care};setInterval(refresh,4000);init();
