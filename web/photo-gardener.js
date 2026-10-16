/* Local photo palette extraction. No network calls or retained source photo. */
(()=>{
 let allowed=[];
 const canvas=(w,h)=>Object.assign(document.createElement('canvas'),{width:w,height:h});
 function colors(image){
  const c=canvas(32,32),x=c.getContext('2d');x.drawImage(image,0,0,32,32);const p=x.getImageData(0,0,32,32).data;
  function sample(x0,y0,x1,y1,fallback){const bins=new Map();for(let y=y0;y<y1;y++)for(let x=x0;x<x1;x++){const i=(y*32+x)*4;if(p[i+3]<128)continue;const v=[p[i],p[i+1],p[i+2]].map(n=>Math.round(n/32)*32).map(n=>Math.min(255,n));const key=v.join(',');bins.set(key,(bins.get(key)||0)+1);}return bins.size?[...bins].sort((a,b)=>b[1]-a[1])[0][0].split(',').map(Number):fallback;}
  return {hair:sample(10,3,22,10,[75,57,54]),skin:sample(12,11,20,18,[217,157,115]),coat:sample(8,21,24,30,[77,115,135])};
 }
 const near=(a,b)=>Math.hypot(...a.map((v,i)=>v-b[i]))<32;
 function paint(source,palette,portrait=false){
  const c=canvas(portrait?32:384,portrait?32:48),x=c.getContext('2d');x.imageSmoothingEnabled=false;
  if(portrait)x.drawImage(source,0,0,32,32,0,0,32,32);else x.drawImage(source,0,0,384,48,0,0,384,48);
  const im=x.getImageData(0,0,c.width,c.height),p=im.data;
  for(let i=0;i<p.length;i+=4){if(!p[i+3])continue;const rgb=[p[i],p[i+1],p[i+2]];let target=null,shade=1;
   if(near(rgb,[217,157,115])||near(rgb,[240,194,149])||near(rgb,[245,215,173])){target=palette.skin;shade=(rgb[0]+rgb[1]+rgb[2])/560;}
   else if(near(rgb,[77,115,135])||near(rgb,[55,83,106])||near(rgb,[38,55,75])){target=palette.coat;shade=(rgb[0]+rgb[1]+rgb[2])/327;}
   else if(near(rgb,[155,108,71])||near(rgb,[187,142,92])||near(rgb,[181,123,53])||near(rgb,[220,160,74])){target=palette.hair;shade=(rgb[0]+rgb[1]+rgb[2])/390;}
   if(target){let out=target.map(v=>Math.max(0,Math.min(255,Math.round(v*shade))));if(allowed.length)out=allowed.reduce((best,c)=>c.reduce((n,v,k)=>n+(v-out[k])**2,0)<best.reduce((n,v,k)=>n+(v-out[k])**2,0)?c:best);for(let k=0;k<3;k++)p[i+k]=out[k];}p[i+3]=255;
  }x.putImageData(im,0,0);return c;
 }
 window.PhotoGardener={colors,paint,setPalette:hex=>{allowed=hex.map(s=>s.replace('#','')).map(s=>[0,2,4].map(i=>parseInt(s.slice(i,i+2),16)));},valid:p=>p&&['skin','hair','coat'].every(k=>Array.isArray(p[k])&&p[k].length===3&&p[k].every(v=>Number.isFinite(v)&&v>=0&&v<=255))};
})();
