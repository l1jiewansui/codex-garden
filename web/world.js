/* Original side-view garden renderer. Phaser is vendored locally (MIT).
 * Scene graphics use an integer pixel grid; studio frames keep their original canvases. */
(function(){
 const THEMES={dusk:{sky:'#686396',haze:'#b28fba',far:'#8c78a4',near:'#685e87',wood:'#66506e',orb:'#f8c98a',night:false},day:{sky:'#83b8c5',haze:'#ced9bc',far:'#91b6af',near:'#649790',wood:'#4a7773',orb:'#f6dfa1',night:false},night:{sky:'#222842',haze:'#495172',far:'#3e4666',near:'#303b58',wood:'#263449',orb:'#eee9bc',night:true}};
 function random(seed){let s=seed>>>0;return()=>{s=(Math.imul(s,1664525)+1013904223)>>>0;return s/4294967296;};}
 function texture(scene,key,w,h,draw){if(scene.textures.exists(key))scene.textures.remove(key);const t=scene.textures.createCanvas(key,w,h);const c=t.context;c.imageSmoothingEnabled=false;draw(c);t.refresh();return key;}
 function box(c,x,y,w,h,col){c.fillStyle=col;c.fillRect(Math.round(x),Math.round(y),Math.round(w),Math.round(h));}
 function ellipse(c,x,y,rx,ry,color){c.fillStyle=color;for(let yy=-ry;yy<=ry;yy++){const xx=Math.round(rx*Math.sqrt(Math.max(0,1-yy*yy/(ry*ry))));c.fillRect(Math.round(x-xx),Math.round(y+yy),xx*2+1,1);}}
 function tree(scene,key,seed){return texture(scene,key,90,170,c=>{const rnd=random(seed);const r=(...a)=>box(c,...a);
   r(42,47,9,123,'#443e3d');r(44,48,5,120,'#956f52');r(44,47,2,122,'#b69164');r(48,48,2,120,'#6a503e');
   r(36,166,22,4,'#443e3d');r(40,161,13,7,'#846849');
   for(let y=72;y<149;y+=23){const left=rnd()>.5;r(left?32:50,y,12,4,'#6d513e');r(left?31:59,y-7,3,9,'#a27a54');ellipse(c,left?28:66,y-11,9,7,'#315444');ellipse(c,left?26:64,y-12,6,5,'#4a7850');}
   const blobs=[[43,23,23,21],[24,34,20,18],[62,35,21,19],[42,43,27,19],[45,10,13,9]];
   for(const [x,y,rx,ry]of blobs){ellipse(c,x,y,rx+2,ry+2,'#284838');ellipse(c,x,y-1,rx,ry,'#3f6943');}
   for(let i=0;i<560;i++){const x=Math.floor(rnd()*86),y=Math.floor(rnd()*66);if(c.getImageData(x,y,1,1).data[3])r(x,y,1+Math.floor(rnd()*3),1+Math.floor(rnd()*2),['#416f47','#4d7d4d','#608b50','#335e41','#739354'][Math.floor(rnd()*5)]);}
   ellipse(c,35,15,10,5,'#638b50');r(30,14,5,2,'#819e5c');
 });}
 function crop(scene,key,kind,stage){texture(scene,key,24,35,c=>{const r=(...a)=>box(c,...a);if(stage===0){r(9,30,5,2,'#bfa078');return;}r(11,18,2,14,'#415634');r(6,18,6,4,'#4b773a');r(13,14,6,4,'#689343');r(14,13,3,2,'#8caf4f');if(stage===1)return;
   r(3,20,8,4,'#527b3a');r(14,20,7,4,'#547c3b');r(10,12,3,12,'#628c40');if(stage===2){r(10,15,3,3,'#9ab65d');return;}
   if(kind===0){r(8,23,9,5,'#e5a142');r(9,28,7,3,'#cd7b30');r(11,31,3,3,'#a75c29');r(9,23,2,5,'#ffd078');r(12,28,4,1,'#a9652c');}
   if(kind===1){ellipse(c,12,25,9,7,'#41613b');ellipse(c,12,23,8,7,'#82a14f');ellipse(c,12,24,5,6,'#acc372');r(11,20,2,8,'#d0d998');r(6,24,2,5,'#658744');}
   if(kind===2){ellipse(c,12,25,8,7,'#733c3b');ellipse(c,12,23,7,6,'#c8664e');r(8,20,3,2,'#f0a175');r(11,17,3,4,'#52783a');r(14,23,2,5,'#a54e44');}
 });}
 window.createGardenWorld=function(options){
  let pending={threads:[],slots:{},filter:'all',hero:0,theme:'dusk'},scene,ready=false;
  class GardenScene extends Phaser.Scene{
   constructor(){super('Garden');this.plots=new Map();this.autoTarget=null;this.follow=true;this.heroIndex=-1;this.loadErrors=[];this.lastSignature='';this.harvestedEffects=0;}
   preload(){this.load.on('loaderror',file=>this.loadErrors.push(file.key));for(const hero of options.heroes)for(const frame of hero.frames)this.load.image(hero.id+'-'+frame.file,'../assets/heroes/'+hero.id+'/'+frame.file);}
   create(){scene=this;this.cameras.main.setRoundPixels(true);this.decor=this.add.group();this.layers=[];
    for(let k=0;k<3;k++)for(let s=0;s<4;s++)crop(this,'crop-'+k+'-'+s,k,s);
    tree(this,'tree-a',147);tree(this,'tree-b',39);
    texture(this,'soil',16,16,c=>{box(c,0,0,16,16,'#655047');const rnd=random(21);for(let i=0;i<26;i++)box(c,rnd()*16,rnd()*16,2,1,['#7e6050','#493f40','#92715a'][i%3]);});
    texture(this,'grass',16,8,c=>{box(c,0,2,16,5,'#374f38');box(c,0,0,16,3,'#688d46');box(c,0,0,16,1,'#9cab62');for(let x=1;x<16;x+=4)box(c,x,3,2,3,'#4c713b');});
    for(const hero of options.heroes)for(const action of ['idle','walk','cast']){const frames=hero.frames.filter(f=>f.action===action);this.anims.create({key:hero.id+'-'+action,frames:frames.map(f=>({key:hero.id+'-'+f.file,duration:Math.max(0,f.durationMs-1)})),frameRate:1000,repeat:-1});}
    this.makeLandscape();this.player=this.physics.add.sprite(190,this.ground,'');this.player.setDepth(15).setCollideWorldBounds(true);this.switchHero(pending.hero);this.physics.add.collider(this.player,this.floor);
    this.keys=this.input.keyboard.addKeys({left:'LEFT',right:'RIGHT',a:'A',d:'D',jump:'SPACE'});this.input.keyboard.disableGlobalCapture();
    this.input.on('pointerdown',p=>{this.drag={x:p.x,scroll:this.cameras.main.scrollX};});
    this.input.on('pointermove',p=>{if(p.isDown&&this.drag&&Math.abs(p.x-this.drag.x)>5){this.follow=false;this.cameras.main.scrollX=Phaser.Math.Clamp(this.drag.scroll+this.drag.x-p.x,0,Math.max(0,this.worldWidth-this.scale.width));}});
    this.input.on('pointerup',p=>{if(this.drag&&Math.abs(p.x-this.drag.x)<5){const point=this.cameras.main.getWorldPoint(p.x,p.y);for(const [id,plot]of this.plots)if(plot.visible&&Math.abs(point.x-plot.x)<90&&point.y>this.ground-76&&point.y<this.ground+43){options.onSelect(id);break;}}this.drag=null;});
    this.input.on('wheel',(_p,_o,dx,dy)=>{this.follow=false;this.cameras.main.scrollX=Phaser.Math.Clamp(this.cameras.main.scrollX+(dx||dy)*.5,0,Math.max(0,this.worldWidth-this.scale.width));});
    this.scale.on('resize',()=>{this.makeLandscape();this.lastSignature='';this.apply(pending);this.player.y=this.ground;});
    ready=true;this.apply(pending);options.onReady?.();
   }
   makeLandscape(){
    const oldFloor=this.floor;this.decor.clear(true,true);this.layers=[];this.ground=this.scale.height-Math.min(64,Math.floor(this.scale.height*.28));const H=this.scale.height,G=this.ground,T=THEMES[pending.theme]||THEMES.dusk;
    this.worldWidth=Math.max(1000,(Math.max(-1,...Object.values(pending.slots))+1)*220+230);
    texture(this,'sky',512,H,c=>{for(let y=0;y<H;y++){const a=Phaser.Display.Color.HexStringToColor(T.sky),b=Phaser.Display.Color.HexStringToColor(T.haze),v=y/H;box(c,0,y,512,1,Phaser.Display.Color.RGBToString(a.red*(1-v)+b.red*v,a.green*(1-v)+b.green*v,a.blue*(1-v)+b.blue*v,255,'#'));}if(T.night){const rnd=random(71);for(let i=0;i<65;i++)box(c,rnd()*512,rnd()*G*.7,1,1,'#c9d0db');}});
    this.decor.add(this.add.tileSprite(0,0,this.scale.width,H,'sky').setOrigin(0).setScrollFactor(0).setDepth(-30));
    const sun=this.add.circle(this.scale.width*.78,Math.max(42,G*.25),T.night?13:19,Phaser.Display.Color.HexStringToColor(T.orb).color).setScrollFactor(0).setDepth(-28);this.decor.add(sun);
    for(let layer=0;layer<3;layer++){
     const key='mountain-'+layer;texture(this,key,768,H,c=>{const rnd=random(50+layer*47),color=[T.far,T.near,T.wood][layer];c.fillStyle=color;c.beginPath();c.moveTo(0,H);let y=G*(.45+layer*.16);c.lineTo(0,y);for(let x=0;x<=768;x+=6){y=G*(.5+layer*.16)+Math.sin(x*.012+layer)*G*.17+Math.sin(x*.033)*G*.04+(rnd()-.5)*5;c.lineTo(x,Math.round(y));}c.lineTo(768,H);c.closePath();c.fill();});
     const image=this.add.tileSprite(0,0,this.scale.width,H,key).setOrigin(0).setScrollFactor(0).setDepth(-25+layer);this.layers.push({image,factor:.08+layer*.12});this.decor.add(image);
    }
    for(let x=25;x<this.worldWidth;x+=72){const rnd=random(x);const h=50+rnd()*48;this.decor.add(this.add.image(x,G+2,'tree-a').setOrigin(.5,1).setScale(h/170).setTint(Phaser.Display.Color.HexStringToColor(T.wood).color).setAlpha(.8).setDepth(-19));}
    // Foreground trees frame plots, leaving plant and title areas readable.
    for(let x=72;x<this.worldWidth;x+=220){const rnd=random(x+5);const image=this.add.image(x,G+3,rnd()>.5?'tree-a':'tree-b').setOrigin(.5,1).setScale((.85+rnd()*.25)*Math.min(1,G/150)).setDepth(-5);if(T.night)image.setTint(0x8c9ca6);this.decor.add(image);}
    this.decor.add(this.add.tileSprite(0,G,this.worldWidth,H-G,'soil').setOrigin(0).setDepth(0));
    this.decor.add(this.add.tileSprite(0,G-2,this.worldWidth,8,'grass').setOrigin(0).setDepth(1));
    const stones=this.add.graphics().setDepth(2);const rnd=random(883);for(let x=0;x<this.worldWidth;x+=9){stones.fillStyle([0x877368,0x514a49,0x9c826b][Math.floor(rnd()*3)]);stones.fillRect(x,G+12+rnd()*38,2+rnd()*3,2);}this.decor.add(stones);
    // A small gardener's hut at the beginning of the path.
    const hut=this.add.graphics().setDepth(-2);hut.fillStyle(0x614b45);hut.fillRect(8,G-50,53,50);hut.fillStyle(0xa3815e);for(let y=G-47;y<G;y+=7)hut.fillRect(10,y,49,4);hut.fillStyle(0x3b3d48);hut.fillTriangle(0,G-48,34,G-80,70,G-48);hut.fillStyle(0x706f68);hut.fillTriangle(6,G-51,34,G-76,61,G-51);hut.fillStyle(0x3c3b37);hut.fillRect(29,G-29,14,29);hut.fillStyle(0xefc582);hut.fillRect(12,G-36,10,12);hut.lineStyle(1,0x725b4b);hut.strokeRect(12,G-36,10,12);const hutScale=Math.min(1,G/95);hut.setScale(hutScale).setPosition(0,G*(1-hutScale));this.decor.add(hut);
    if(oldFloor){oldFloor.setPosition(this.worldWidth/2,G+4).setSize(this.worldWidth,8);this.physics.add.existing(oldFloor,true);oldFloor.body.updateFromGameObject();}
    else {this.floor=this.add.rectangle(this.worldWidth/2,G+4,this.worldWidth,8,0,0);this.physics.add.existing(this.floor,true);}
    this.physics.world.setBounds(0,0,this.worldWidth,H+40);this.cameras.main.setBounds(0,0,this.worldWidth,H);
   }
   switchHero(index){if(!this.player||!options.heroes.length)return;this.heroIndex=index%options.heroes.length;const h=options.heroes[this.heroIndex];this.player.setTexture(h.id+'-idle_000.png');this.player.setOrigin(h.origin[0]/64,h.origin[1]/64);this.player.body.setSize(14,25).setOffset(h.origin[0]-7,h.origin[1]-25);this.player.play(h.id+'-idle');}
   apply(data){
    const oldTheme=this.theme;this.theme=data.theme;
    const width=Math.max(1000,(Math.max(-1,...Object.values(data.slots))+1)*220+230);
    if(width!==this.worldWidth||oldTheme!==this.theme)this.makeLandscape();
    if(this.heroIndex!==data.hero)this.switchHero(data.hero);
    const signature=JSON.stringify([data.filter,data.threads.map(t=>[t.id,t.status,t.title,data.slots[t.id]])]);if(signature===this.lastSignature)return;this.lastSignature=signature;
    for(const p of this.plots.values()){for(const child of p.list)this.tweens.killTweensOf(child);p.destroy(true);}this.plots.clear();
    for(const t of data.threads){const x=180+data.slots[t.id]*220,p=this.add.container(x,this.ground).setDepth(5);p.thread=t;p.visible=GardenModel.matches(t,data.filter);this.plots.set(t.id,p);
     const bed=this.add.graphics();bed.fillStyle(0x443c37);bed.fillRect(-79,-1,158,5);bed.fillStyle(0x93724d);bed.fillRect(-79,4,158,3);bed.fillStyle(0x60513c);for(let xx=-74;xx<78;xx+=9)bed.fillRect(xx,0,6,2);p.add(bed);
     const stage=GardenModel.cropStage(t.status);for(let i=0;i<6;i++){const plant=this.add.image(-63+i*25,1,'crop-'+t.crop+'-'+stage).setOrigin(.5,1);p.add(plant);if(t.status==='growing'&&!matchMedia('(prefers-reduced-motion: reduce)').matches)this.tweens.add({targets:plant,angle:3,duration:1100+i*100,yoyo:true,repeat:-1});}
     const color=t.status==='ripe'?'#f0cd7a':GardenModel.CARE.includes(t.status)?'#d6ac95':'#ccddaf';
     const title=(t.title||'未命名对话');const name=this.add.text(0,20,title.length>15?title.slice(0,14)+'…':title,{fontFamily:'Microsoft YaHei',fontSize:'9px',color:'#e1d5bb',backgroundColor:'#393738',padding:{x:5,y:3}}).setOrigin(.5,0);p.add(name);
     const badge=this.add.text(0,-Math.min(62,this.ground-28),options.labels[t.status]||'状态未知',{fontFamily:'Microsoft YaHei',fontSize:'9px',color,backgroundColor:'#283339',padding:{x:5,y:3}}).setOrigin(.5,1);p.add(badge);
     const post=this.add.graphics();post.fillStyle(0x786449);post.fillRect(-83,-25,3,25);post.fillStyle(0xb49a68);post.fillRect(-88,-28,14,10);post.fillStyle(t.status==='ripe'?0xf5cc69:0x657d56);post.fillRect(-85,-25,8,4);p.add(post);
     if(t.status==='ripe'){const star=this.add.text(61,-40,'✦',{fontSize:'14px',color:'#f4d78c'});p.add(star);if(!matchMedia('(prefers-reduced-motion: reduce)').matches)this.tweens.add({targets:star,alpha:.25,y:-46,duration:1100,yoyo:true,repeat:-1});}
    }
    if(this.autoTarget&&!this.plots.has(this.autoTarget))this.autoTarget=null;
   }
   go(id){const p=this.plots.get(id);if(!p)return;this.autoTarget=id;this.follow=true;if(Math.abs(p.x-this.player.x)>this.scale.width*.85){this.player.x=p.x-100;this.player.y=this.ground;this.player.setVelocity(0,0);this.cameras.main.scrollX=Math.max(0,p.x-this.scale.width*.4);}this.player.x=Phaser.Math.Clamp(this.player.x,16,this.worldWidth-16);}
   pan(fraction){this.follow=false;this.cameras.main.scrollX=Phaser.Math.Clamp(fraction,0,1)*Math.max(0,this.worldWidth-this.scale.width);}
   celebrate(id){const p=this.plots.get(id);if(!p)return;this.harvestedEffects++;for(let i=0;i<9;i++){const dot=this.add.image(p.x+(i-4)*12,this.ground-18,'crop-'+p.thread.crop+'-3').setDepth(20).setScale(.7);this.tweens.add({targets:dot,y:dot.y-60-Math.random()*30,x:dot.x+(Math.random()-.5)*60,alpha:0,duration:900,onComplete:()=>dot.destroy()});}}
   update(time,dt){if(!this.player)return;const blocked=document.getElementById('detail').open||!document.getElementById('drawer').hidden||['INPUT','SELECT','TEXTAREA'].includes(document.activeElement?.tagName);const left=!blocked&&(this.keys.left.isDown||this.keys.a.isDown),right=!blocked&&(this.keys.right.isDown||this.keys.d.isDown);let move=left?-1:right?1:0;
    if(move){this.autoTarget=null;this.follow=true;}
    if(this.autoTarget&&!blocked){const target=this.plots.get(this.autoTarget);if(target){const dx=target.x+76-this.player.x;if(Math.abs(dx)>4)move=Math.sign(dx);else{this.autoTarget=null;this.idleUntil=time+1800;}}}
    this.player.setVelocityX(blocked?0:move*88);if(!blocked&&Phaser.Input.Keyboard.JustDown(this.keys.jump)&&this.player.body.blocked.down)this.player.setVelocityY(-185);
    const hero=options.heroes[this.heroIndex];const nearby=[...this.plots.values()].find(p=>Math.abs(p.x+76-this.player.x)<16&&p.thread.status==='growing');const action=move?'walk':nearby?'cast':'idle';if(hero)this.player.anims.play(hero.id+'-'+action,true);if(move)this.player.setFlipX(move<0);
    if(this.follow){const target=this.player.x-this.scale.width*.42;this.cameras.main.scrollX=Phaser.Math.Clamp(Phaser.Math.Linear(this.cameras.main.scrollX,target,Math.min(1,dt*.005)),0,Math.max(0,this.worldWidth-this.scale.width));}
    for(const l of this.layers)l.image.tilePositionX=Math.floor(this.cameras.main.scrollX*l.factor);
    options.onPosition?.(this.cameras.main.scrollX/Math.max(1,this.worldWidth-this.scale.width));
   }
  }
  const host=document.getElementById('world'),size=()=>({width:Math.max(300,Math.floor(host.clientWidth/2)),height:Math.max(130,Math.floor(host.clientHeight/2))});
  const game=new Phaser.Game({type:Phaser.CANVAS,parent:'world',...size(),pixelArt:true,roundPixels:true,antialias:false,backgroundColor:'#5e5785',physics:{default:'arcade',arcade:{gravity:{y:480},debug:false}},fps:{target:30,forceSetTimeOut:true},scene:GardenScene,audio:{noAudio:true},banner:false});
  new ResizeObserver(()=>{const s=size();if(game.scale&&(game.scale.width!==s.width||game.scale.height!==s.height))game.scale.resize(s.width,s.height);}).observe(host);
  const api={update(data){pending=data;if(ready)scene.apply(data);},focus(id){if(ready)scene.go(id);},pan(f){if(ready)scene.pan(f);},follow(){if(ready)scene.follow=true;},celebrate(id){if(ready)scene.celebrate(id);},inspect(){return ready?{ready:true,plots:scene.plots.size,visible:[...scene.plots.values()].filter(p=>p.visible).length,worldWidth:scene.worldWidth,ground:scene.ground,playerX:scene.player.x,playerY:scene.player.y,grounded:scene.player.body.blocked.down,cameraX:scene.cameras.main.scrollX,theme:scene.theme,hero:scene.heroIndex,target:scene.autoTarget,loadErrors:scene.loadErrors,effects:scene.harvestedEffects,positions:Object.fromEntries([...scene.plots].map(([id,p])=>[id,p.x]))}:{ready:false};},game};return api;
 };
})();
