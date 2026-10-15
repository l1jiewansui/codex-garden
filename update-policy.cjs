const fs=require('node:fs'),path=require('node:path');
function compare(a,b){
 const parse=v=>{const m=/^(\d+)\.(\d+)\.(\d+)(?:-([\w.-]+))?$/.exec(v||'');return m?{parts:m.slice(1,4).map(Number),pre:m[4]}:null;},x=parse(a),y=parse(b);
 if(!x||!y)return 0;
 for(let i=0;i<3;i++)if(x.parts[i]!==y.parts[i])return Math.sign(x.parts[i]-y.parts[i]);
 if(Boolean(x.pre)!==Boolean(y.pre))return x.pre?-1:1;
 return x.pre&&y.pre?x.pre.localeCompare(y.pre,undefined,{numeric:true}):0;
}
function upgradeExecutable(data,current){
 if(!data||typeof data.executable!=='string'||!path.isAbsolute(data.executable)||path.basename(data.executable).toLowerCase()!=='codexgarden.exe'||compare(data.version,current)<=0)return null;
 try{const manifest=JSON.parse(fs.readFileSync(path.join(path.dirname(data.executable),'resources/app/package.json'),'utf8'));return manifest.name==='codex-garden'&&manifest.version===data.version&&fs.statSync(data.executable).isFile()?data.executable:null;}catch{return null;}
}
module.exports={compare,upgradeExecutable};
