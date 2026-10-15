const WIDTH=420,HEIGHT=150,EXPANDED=470;
function bounded(rect,area){return {x:Math.max(area.x,Math.min(Math.round(rect.x),area.x+Math.max(0,area.width-rect.width))),y:Math.max(area.y,Math.min(Math.round(rect.y),area.y+Math.max(0,area.height-rect.height))),width:rect.width,height:rect.height};}
function hitTest(point,regions,mask){
 if(regions.some(r=>point.x>=r.x&&point.x<r.x+r.width&&point.y>=r.y&&point.y<r.y+r.height))return true;
 if(!mask)return false;const x=Math.floor((point.x-mask.x)/mask.scale),y=Math.floor((point.y-mask.y)/mask.scale);
 return x>=0&&y>=0&&x<mask.width&&y<mask.height&&mask.pixels[y*mask.width+x]>0;
}
module.exports={WIDTH,HEIGHT,EXPANDED,bounded,hitTest};
