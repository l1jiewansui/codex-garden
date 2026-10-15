const $=id=>document.getElementById(id);
const labels={growing:'生长中',ripe:'成熟 · 可收菜',harvested:'已收获',paused:'已暂停',failed:'本轮出错',stale:'状态待确认',unknown:'状态未知',waiting:'等你照料'};
let threads=[],heroes=[],filter='all',selected=null,demo=false,busy=false,world=null,heroIndex=0,theme='dusk',liveSlots={},demoSlots={},pendingHarvest=false,toastTimer;
const errors=[];window.addEventListener('error',e=>errors.push(e.message));window.addEventListener('unhandledrejection',e=>errors.push(String(e.reason)));
function readSetting(name,fallback){try{return JSON.parse(localStorage.getItem(name))??fallback;}catch{return fallback;}}
function saveSetting(name,value){localStorage.setItem(name,JSON.stringify(value));}
function notice(t){$('notice').textContent=t;}
function toast(t){$('toast').textContent=t;$('toast').classList.add('visible');clearTimeout(toastTimer);toastTimer=setTimeout(()=>$('toast').classList.remove('visible'),2800);}
function make(tag,cls,text){const e=document.createElement(tag);if(cls)e.className=cls;if(text!==undefined)e.textContent=text;return e;}
function project(t){return t.cwd.split(/[\\/]/).filter(Boolean).pop()||'未命名项目';}
function render(){
 const previous=demo?demoSlots:liveSlots,slots=GardenModel.slots(previous,threads);if(demo)demoSlots=slots;else{liveSlots=slots;saveSetting('world-slots',slots);}
 $('growing').textContent=threads.filter(t=>t.status==='growing').length;$('ripe').textContent=threads.filter(t=>t.status==='ripe').length;$('care').textContent=threads.filter(t=>GardenModel.CARE.includes(t.status)).length;
 const visible=threads.filter(t=>GardenModel.matches(t,filter));$('plot-count').textContent=visible.length+' 块田';$('world-empty').hidden=threads.length>0;$('next-ripe').disabled=!visible.some(t=>t.status==='ripe');
 world?.update({threads,slots,filter,hero:heroIndex,theme});
 $('markers').replaceChildren();const count=Math.max(4,...Object.values(slots))+1;
 for(const t of threads){const marker=make('span','marker '+t.status);marker.style.left=((slots[t.id]+.5)/count*100)+'%';marker.title=t.title;$('markers').append(marker);}
 $('thread-list').replaceChildren();for(const t of visible.sort((a,b)=>slots[a.id]-slots[b.id])){const b=make('button');b.dataset.thread=t.id;b.append(make('b','',t.title||'未命名对话'),make('small','',(slots[t.id]+1)+' 号田 · '+labels[t.status]+' · '+project(t)));b.onclick=()=>{world?.focus(t.id);$('drawer').hidden=true;document.activeElement?.blur();toast('前往 '+(slots[t.id]+1)+' 号菜田，点击田里的作物查看对话。');};$('thread-list').append(b);}
 if(selected){const t=threads.find(t=>t.id===selected);if(t)updateDetail(t);else{$('detail').close();selected=null;toast('这段对话已不在最近菜田中。');}}
}
function updateDetail(t){$('detail-title').textContent=t.title;$('detail-state').textContent=labels[t.status]||'状态未知';$('detail-project').textContent=t.cwd;$('detail-summary').textContent=t.summary||'这一轮尚无可显示的完成摘要。';$('harvest').disabled=t.status!=='ripe'||pendingHarvest;$('harvest').textContent=pendingHarvest?'正在收下…':t.status==='harvested'?'这一茬已收获':'收下这一茬';$('open-thread').disabled=demo;}
function select(id){const t=threads.find(t=>t.id===id);if(!t)return;selected=id;updateDetail(t);if(!$('detail').open)$('detail').showModal();}
async function refresh(){if(busy||demo)return;busy=true;try{const s=await window.garden.snapshot();if(demo)return;threads=s.threads;$('harvests').textContent=s.harvestCount||0;notice(s.error||'');$('sync').textContent='● 本地只读同步 · '+new Date().toLocaleTimeString('zh-CN');render();}catch(e){notice('同步中断：'+e.message);$('sync').textContent='○ 同步中断';}finally{busy=false;}}
async function harvest(){if(pendingHarvest)return;const id=selected,t=threads.find(t=>t.id===id);if(!t||t.status!=='ripe')return;pendingHarvest=true;updateDetail(t);try{
 if(demo){t.status='harvested';$('harvests').textContent=Number($('harvests').textContent)+1;}else{await window.garden.harvest(id);t.status='harvested';$('harvests').textContent=Number($('harvests').textContent)+1;}
 world?.celebrate(id);$('detail').close();toast('这一茬已收下。下次对话，会在这里重新发芽。');render();
 }catch(e){notice('收获失败：'+e.message);}finally{pendingHarvest=false;if(selected)updateDetail(threads.find(t=>t.id===selected));}}
function nextRipe(){const slots=demo?demoSlots:liveSlots;const list=threads.filter(t=>t.status==='ripe'&&GardenModel.matches(t,filter)).sort((a,b)=>slots[a.id]-slots[b.id]);if(!list.length){toast('这片菜园暂时没有成熟作物。');return;}const x=world?.inspect().playerX||0;const target=list.find(t=>180+slots[t.id]*220>x+8)||list[0];world?.focus(target.id);document.activeElement?.blur();toast('园丁正走向成熟的 '+(slots[target.id]+1)+' 号田。');}
function toggleDemo(){if(pendingHarvest)return;demo=!demo;$('demo').textContent=demo?'返回真实菜园':'体验演示';$('world-label').textContent=demo?'青云林地 · 演示菜园':'青云林地 · 本地菜园';if(demo){threads=['growing','ripe','paused','growing','harvested','ripe','unknown','failed'].map((status,i)=>({id:'demo-'+i,title:['为新功能播下一颗种子','文档已整理，等你收菜','需要你照料的菜田','给新角色画一段动画','已经收下的一茬','代码检查完成','等待新的活动记录','这一茬遇到点问题'][i],cwd:'演示菜园 / 示例项目',status,crop:i%3,updated_at:Date.now()/1000,summary:'这是演示数据，用于体验横版菜园、人物移动和收获交互。真实模式只根据本地 Codex 记录更新。'}));notice('演示模式 · 以下为示例状态，不代表真实聊天');$('sync').textContent='演示菜园';$('harvests').textContent=0;filter='all';document.querySelectorAll('[data-filter]').forEach(b=>b.classList.toggle('active',b.dataset.filter===filter));render();world?.pan(0);}else refresh();}
$('harvest').onclick=harvest;$('open-thread').onclick=async()=>{try{await window.garden.open(selected);}catch(e){notice('无法打开 Codex：'+e.message);}};
$('close-detail').onclick=()=>$('detail').close();$('detail').addEventListener('close',()=>selected=null);
for(const action of ['pin','compact','minimize','hide'])$(action).onclick=async()=>{const value=await window.garden.window(action);if(action==='pin')$('pin').textContent=value?'已置顶':'置顶';if(action==='compact')$('compact').textContent=value?'展开':'小窗';};
document.querySelectorAll('[data-filter]').forEach(b=>b.onclick=()=>{filter=b.dataset.filter;document.querySelectorAll('[data-filter]').forEach(x=>x.classList.toggle('active',x===b));render();const first=threads.find(t=>GardenModel.matches(t,filter));if(first)world?.focus(first.id);document.activeElement?.blur();});
$('hero').onchange=()=>{heroIndex=Number($('hero').value);saveSetting('hero-v2',heroIndex);render();$('hero').blur();};$('theme').onchange=()=>{theme=$('theme').value;saveSetting('world-theme',theme);render();$('theme').blur();};
$('position').oninput=()=>world?.pan(Number($('position').value)/1000);$('west').onclick=()=>{const s=world?.inspect();if(s?.ready)world.pan((s.cameraX-200)/Math.max(1,s.worldWidth-world.game.scale.width));};$('east').onclick=()=>{const s=world?.inspect();if(s?.ready)world.pan((s.cameraX+200)/Math.max(1,s.worldWidth-world.game.scale.width));};
$('next-ripe').onclick=nextRipe;$('follow').onclick=()=>{world?.follow();document.activeElement?.blur();};$('list-toggle').onclick=()=>$('drawer').hidden=!$('drawer').hidden;$('list-close').onclick=()=>$('drawer').hidden=true;$('refresh').onclick=refresh;$('demo').onclick=toggleDemo;
async function init(){try{heroes=await(await fetch('../assets/heroes.json')).json();heroIndex=Math.max(0,readSetting('hero-v2',0))%heroes.length;liveSlots=readSetting('world-slots',{});theme=readSetting('world-theme','dusk');if(!['day','dusk','night'].includes(theme))theme='dusk';
 heroes.forEach((h,i)=>{const o=make('option','',h.name);o.value=i;$('hero').append(o);});$('hero').value=heroIndex;$('theme').value=theme;
 world=createGardenWorld({heroes,labels,onSelect:select,onPosition:f=>{if(document.activeElement!==$('position'))$('position').value=Math.round(f*1000);},onReady:()=>render()});await refresh();
 }catch(e){notice('菜园启动失败：'+e.message);errors.push(e.message);}}
setInterval(refresh,4000);setInterval(()=>{$('clock').textContent=new Date().toLocaleDateString('zh-CN',{month:'long',day:'numeric',weekday:'short'});},1000);
window.gardenApp={inspect:()=>({demo,filter,threads:threads.length,errors:[...errors],world:world?.inspect()}),select,harvest,nextRipe,focus:id=>world?.focus(id),pan:f=>world?.pan(f)};init();
