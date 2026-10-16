const fs=require('node:fs'),path=require('node:path');
exports.pick=async({win,dialog,restore,fileSystem=fs})=>{
 win.setFocusable(true);win.focus();
 try{
  const result=await dialog.showOpenDialog(win,{title:'选择照片生成园丁',properties:['openFile'],filters:[{name:'人物照片',extensions:['png','jpg','jpeg','webp']}]});
  if(result.canceled||!result.filePaths?.[0])return null;
  const file=result.filePaths[0],mime={'.png':'image/png','.jpg':'image/jpeg','.jpeg':'image/jpeg','.webp':'image/webp'}[path.extname(file).toLowerCase()];
  if(!mime||fileSystem.statSync(file).size>10*1024*1024)throw Error('请选择10MB以内的 PNG、JPEG 或 WebP 照片');
  const data=fileSystem.readFileSync(file);if(data.length>10*1024*1024)throw Error('照片过大，请缩小后重试');
  return 'data:'+mime+';base64,'+data.toString('base64');
 }catch(error){if(error.message?.startsWith('请选择')||error.message?.startsWith('照片过大'))throw error;throw Error('照片无法读取，请换一张重试');}finally{restore();}
};
