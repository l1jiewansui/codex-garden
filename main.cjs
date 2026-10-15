const {app,BrowserWindow,ipcMain,shell,Tray,Menu,nativeImage,screen,dialog}=require('electron');
const {spawn}=require('node:child_process');const path=require('node:path'),fs=require('node:fs'),readline=require('node:readline');
const {gardenName:normalizeGardenName}=require('./web/model.js');
const {WIDTH,HEIGHT,EXPANDED,bounded,hitTest}=require('./desktop-model.cjs');
app.setName('codex-garden-pet-v06');app.setPath('userData',path.join(app.getPath('appData'),'codex-garden-pet-v06'));
const VERSION=require('./package.json').version,{upgradeExecutable}=require('./update-policy.cjs');
const qa=process.argv.includes('--qa');if(qa)app.setPath('userData',path.join(app.getPath('temp'),'codex-garden-pet-qa-'+process.pid));
const ownsLock=app.requestSingleInstanceLock({version:VERSION,executable:process.execPath});if(!ownsLock)app.quit();
const qaWelcome=process.argv.includes('--qa-welcome');let readRequests=0;
let accepted=qa&&!qaWelcome;try{if(!qaWelcome)accepted=accepted||JSON.parse(fs.readFileSync(path.join(app.getPath('userData'),'welcome.json'),'utf8')).accepted===true;}catch{}
let win,bridge,tray,quitting=false,seq=0,regions=[],mask=null,ignoring=true,manualPass=false,pointerTimer,saveTimer,desiredHeight=HEIGHT;const pending=new Map();
const settingsPath=()=>path.join(app.getPath('userData'),'widget-position.json');
function savePosition(){if(!win||win.isDestroyed())return;fs.mkdirSync(app.getPath('userData'),{recursive:true});const b=win.getBounds();fs.writeFileSync(settingsPath(),JSON.stringify({x:b.x,y:b.y+b.height-HEIGHT}));}
function setIgnore(ignore){if(!win||win.isDestroyed()||ignoring===ignore)return;win.setIgnoreMouseEvents(ignore,{forward:true});ignoring=ignore;}
function updatePointer(){if(!win||win.isDestroyed()||!win.isVisible())return;const cursor=screen.getCursorScreenPoint(),b=win.getBounds();setIgnore(manualPass||!hitTest({x:cursor.x-b.x,y:cursor.y-b.y},regions,mask));}
function moveBounded(bounds){const area=screen.getDisplayMatching(bounds).workArea,b=bounded({...bounds,width:WIDTH,height:desiredHeight},area),now=win.getBounds();if(now.x!==b.x||now.y!==b.y||Math.abs(now.width-b.width)>2||Math.abs(now.height-b.height)>2)win.setBounds(b);}
function corner(){const a=screen.getPrimaryDisplay().workArea;moveBounded({x:a.x+a.width-WIDTH-20,y:a.y+a.height-win.getBounds().height-10,width:WIDTH,height:win.getBounds().height});}
function resizePanel(expanded){const b=win.getBounds(),height=expanded?EXPANDED:HEIGHT;desiredHeight=height;regions=[];mask=null;setIgnore(true);moveBounded({x:b.x,y:b.y+b.height-height,width:WIDTH,height});return {height};}
function rpc(method,extra={}){return new Promise((resolve,reject)=>{if(!bridge||bridge.killed||!bridge.stdin.writable)return reject(Error('本地读取程序不可用'));const id=++seq,timer=setTimeout(()=>{pending.delete(id);reject(Error('本地对话读取超时'));},15000);pending.set(id,{resolve,reject,timer});bridge.stdin.write(JSON.stringify({id,method,...extra})+'\n');});}
function rejectPending(error){for(const p of pending.values()){clearTimeout(p.timer);p.reject(error);}pending.clear();}
function artIcon(){return nativeImage.createFromPath(path.join(__dirname,'assets/pixel-v04/tray-icon.png'));}
function createWindow(){
 const area=screen.getPrimaryDisplay().workArea;let pos={x:area.x+area.width-WIDTH-20,y:area.y+area.height-HEIGHT-10};try{pos={...pos,...JSON.parse(fs.readFileSync(settingsPath(),'utf8'))};}catch{}
 pos={x:Number.isFinite(pos.x)?Math.round(pos.x):area.x,y:Number.isFinite(pos.y)?Math.round(pos.y):area.y};
 const bounds=bounded({...pos,width:WIDTH,height:HEIGHT},screen.getDisplayNearestPoint(pos).workArea);
 win=new BrowserWindow({...bounds,frame:false,thickFrame:false,transparent:true,backgroundColor:'#00000000',hasShadow:false,resizable:false,focusable:false,skipTaskbar:true,alwaysOnTop:true,show:false,minimizable:false,maximizable:false,fullscreenable:false,webPreferences:{preload:path.join(__dirname,'preload.cjs'),contextIsolation:true,nodeIntegration:false,sandbox:true}});
 win.on('blur',()=>{if(win.isFocusable()){win.setFocusable(false);win.webContents.send('garden:command','cancel-name');}});win.on('hide',()=>{win.setFocusable(false);win.webContents.send('garden:command','cancel-name');});
 win.setBounds(bounds);win.setIgnoreMouseEvents(true,{forward:true});win.setMenu(null);win.loadFile(path.join(__dirname,'web/pet.html'));win.once('ready-to-show',()=>win.showInactive());
 win.on('close',e=>{if(!quitting){e.preventDefault();win.hide();}});win.on('moved',()=>{clearTimeout(saveTimer);saveTimer=setTimeout(()=>{moveBounded(win.getBounds());savePosition();},250);});
 win.webContents.setWindowOpenHandler(()=>({action:'deny'}));win.webContents.on('will-navigate',e=>e.preventDefault());pointerTimer=setInterval(updatePointer,50);
}
async function exportCollection(){try{const result=await dialog.showSaveDialog({title:'导出收藏备份',defaultPath:path.join(app.getPath('documents'),'菜园收藏备份.json'),filters:[{name:'收藏备份',extensions:['json']}]});if(result.canceled||!result.filePath)return;const data=await rpc('export');fs.writeFileSync(result.filePath,JSON.stringify(data,null,2),'utf8');}catch{dialog.showMessageBox({type:'error',message:'备份暂时无法导出，请稍后重试。'});}}
function trayMenu(){traying();function traying(){tray.setContextMenu(Menu.buildFromTemplate([
 {label:'显示桌面菜园',click:()=>{manualPass=false;win.showInactive();updatePointer();trayMenu();}},
 {label:'全部鼠标穿透',type:'checkbox',checked:manualPass,click:item=>{manualPass=item.checked;updatePointer();}},
 {label:'置顶显示',type:'checkbox',checked:win.isAlwaysOnTop(),click:item=>win.setAlwaysOnTop(item.checked)},
 {label:'移回屏幕右下角',click:()=>{corner();win.showInactive();}},
 {label:'使用说明',click:()=>win.webContents.send('garden:command','help')},
 {label:'导出收藏备份',click:exportCollection},
 {label:'打开收藏文件夹',click:()=>{const folder=process.env.CODEX_GARDEN_DATA||path.join(app.getPath('home'),'.codex-garden');fs.mkdirSync(folder,{recursive:true});shell.openPath(folder);}},
 {label:'收起详情',click:()=>win.webContents.send('garden:command','collapse')},
 {label:'隐藏',click:()=>win.hide()},{type:'separator'},{label:'退出',click:()=>app.quit()}
 ]));}}
if(ownsLock)app.whenReady().then(()=>{
 app.setAppUserModelId('org.qingyun.codexgarden');
 const bundled=path.join(__dirname,'runtime/garden-bridge.exe'),useBundled=fs.existsSync(bundled)&&!process.env.CODEX_GARDEN_PYTHON;
 bridge=spawn(useBundled?bundled:(process.env.CODEX_GARDEN_PYTHON||'python'),useBundled?[]:['-u',path.join(__dirname,'backend/bridge.py')],{windowsHide:true,env:{...process.env,PYTHONIOENCODING:'utf-8'}});
 readline.createInterface({input:bridge.stdout}).on('line',line=>{try{const m=JSON.parse(line),p=pending.get(m.id);if(p){clearTimeout(p.timer);pending.delete(m.id);m.error?p.reject(Error(m.error)):p.resolve(m.result);}}catch{}});
 bridge.on('error',rejectPending);bridge.stdin.on('error',rejectPending);bridge.on('exit',()=>rejectPending(Error('本地读取程序已退出，请重启菜园。')));
 ipcMain.handle('garden:snapshot',()=>{if(!accepted)return {threads:[],inventory:{},error:null,connection:'welcome'};readRequests++;return rpc('snapshot');});ipcMain.handle('garden:harvest',(_,threadId,plantKind)=>{if(!accepted)throw Error('请先完成欢迎说明');return rpc('harvest',{threadId,plantKind});});
 ipcMain.handle('garden:window',(_,action,value)=>{if(action==='editing'){if(value===true){manualPass=false;setIgnore(false);win.setFocusable(true);win.focus();}else{win.hide();win.setFocusable(false);win.showInactive();updatePointer();}return;}if(action==='name'){const name=normalizeGardenName(value);win.setTitle(name);tray?.setToolTip(name+' · 双击恢复交互');return;}if(action==='drag'&&value&&Number.isFinite(value.dx)&&Number.isFinite(value.dy)&&Math.abs(value.dx)<1000&&Math.abs(value.dy)<1000){const b=win.getBounds();moveBounded({...b,x:b.x+Math.round(value.dx),y:b.y+Math.round(value.dy)});return;}if(action==='start'){fs.mkdirSync(app.getPath('userData'),{recursive:true});fs.writeFileSync(path.join(app.getPath('userData'),'welcome.json'),JSON.stringify({accepted:true,version:VERSION}));accepted=true;return true;}if(action==='panel')return resizePanel(Boolean(value));if(action==='hide')win.hide();if(action==='pass'){manualPass=true;updatePointer();trayMenu();}if(action==='quit')app.quit();});
 ipcMain.handle('garden:open',async(_,id)=>{if(!/^[a-zA-Z0-9-]{1,80}$/.test(id))throw Error('无效聊天ID');await shell.openExternal('codex://threads/'+id);});
 ipcMain.on('garden:geometry',(_,data)=>{
  if(!data||!Array.isArray(data.regions)||data.regions.length>20)return;
  regions=data.regions.filter(r=>['x','y','width','height'].every(k=>Number.isFinite(r[k]))&&r.width>0&&r.height>0&&r.x>=0&&r.y>=0&&r.x+r.width<=WIDTH+1&&r.y+r.height<=EXPANDED+1);
  const m=data.mask;if(m&&m.width===210&&m.height===75&&m.scale===2&&m.x===0&&Number.isFinite(m.y)&&m.y>=0&&m.y<=EXPANDED&&typeof m.data==='string'&&m.data.length<22000){const pixels=Buffer.from(m.data,'base64');if(pixels.length===m.width*m.height)mask={...m,pixels};}updatePointer();
 });
 createWindow();tray=new Tray(artIcon());tray.setToolTip('青云桌面菜园 · 双击恢复交互');trayMenu();tray.on('double-click',()=>{manualPass=false;win.showInactive();trayMenu();updatePointer();});
 screen.on('display-metrics-changed',()=>moveBounded(win.getBounds()));
 if(qa)require('./qa.cjs').run({win,app,root:__dirname,hitTest:(p)=>hitTest(p,regions,mask),state:()=>({bounds:win.getBounds(),focusable:win.isFocusable(),focused:win.isFocused(),background:win.getBackgroundColor(),top:win.isAlwaysOnTop(),regions,maskReady:Boolean(mask),ignoring,manualPass,readRequests}),testIgnore:value=>{setIgnore(value);return ignoring;}});
});
app.on('before-quit',()=>{quitting=true;clearInterval(pointerTimer);clearTimeout(saveTimer);savePosition();bridge?.kill();});app.on('window-all-closed',()=>{});
app.on('second-instance',(_event,_argv,_cwd,data)=>{const executable=upgradeExecutable(data,VERSION);if(executable){app.relaunch({execPath:executable,args:[]});app.quit();return;}manualPass=false;win?.showInactive();});
