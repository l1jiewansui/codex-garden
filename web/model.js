(function(root){
 'use strict';
 const CARE=['paused','failed','stale','unknown','waiting'];
 function gardenName(value){return typeof value==='string'?Array.from(value.replace(/[\u0000-\u001f\u007f-\u009f\u200b-\u200f\u202a-\u202e\u2066-\u2069]/g,'').trim()).slice(0,24).join('')||'我的菜园':'我的菜园';}
 function orderedThreads(threads){return threads.map((thread,index)=>({thread,index})).sort((a,b)=>{const x=Number(a.thread.updated_at),y=Number(b.thread.updated_at),xf=Number.isFinite(x),yf=Number.isFinite(y);if(xf!==yf)return xf?-1:1;if(xf&&x!==y)return y-x;if(xf)return String(a.thread.id).localeCompare(String(b.thread.id),'en');return a.index-b.index;}).map(v=>v.thread);}
 function sequentialSlots(threads){return Object.fromEntries(orderedThreads(threads).map((t,index)=>[t.id,index]));}
 function slots(previous,threads){
   const result={},used=new Set();
   for(const t of threads){const n=previous[t.id];if(Number.isInteger(n)&&n>=0&&n<48&&!used.has(n)){result[t.id]=n;used.add(n);}}
   for(const t of threads)if(result[t.id]===undefined){let n=0;while(used.has(n))n++;result[t.id]=n;used.add(n);}
   return result;
 }
 function matches(t,filter){return filter==='all'||(filter==='care'?CARE.includes(t.status):t.status===filter);}
 function cropStage(status){return status==='ripe'?3:status==='growing'?2:status==='harvested'?0:1;}
 function stepWalker(x,target,seconds){const goal=Math.max(22,Math.min(194,target)),distance=goal-x,step=48*Math.max(0,Math.min(seconds,.1));return Math.abs(distance)<=step?goal:x+Math.sign(distance)*step;}
 const geometry=Object.freeze({surfaceY:60,cropHeight:20,cropY:40,soilBottom:74,interactionOffset:18});
 function stepWorld(x,target,seconds){const d=target-x,step=48*Math.max(0,Math.min(seconds,.1));return Math.abs(d)<=step?target:x+Math.sign(d)*step;}
 function followCamera(x,camera){return x-camera>150?x-150:x-camera<50?x-50:camera;}
 function secretPlant(id,turn){let h=2166136261;for(const c of id+'|'+(turn||'initial'))h=Math.imul(h^c.charCodeAt(0),16777619)>>>0;return h%16===0?(h>>>4)%4:null;}
 const api={slots,sequentialSlots,orderedThreads,gardenName,matches,cropStage,CARE,stepWalker,stepWorld,followCamera,geometry,secretPlant};
 if(typeof module!=='undefined')module.exports=api;else root.GardenModel=api;
})(globalThis);
