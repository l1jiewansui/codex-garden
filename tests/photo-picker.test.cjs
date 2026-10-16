const assert=require('node:assert/strict'),{pick}=require('../photo-picker.cjs');
(async()=>{
 for(const mode of ['photo','cancel','oversize','dialogError']){
  const events=[],win={setFocusable:v=>events.push(['focusable',v]),focus:()=>events.push(['focus'])};
  const dialog={showOpenDialog:async(w,options)=>{assert.equal(w,win);assert(options.filters[0].extensions.includes('webp'));if(mode==='dialogError')throw Error('dialog failed');return {canceled:mode==='cancel',filePaths:['C:/private/photo.PNG']};}};
  const fileSystem={statSync:()=>({size:mode==='oversize'?11*1024*1024:3}),readFileSync:()=>Buffer.from('png')};
  const promise=pick({win,dialog,fileSystem,restore:()=>events.push(['restore'])});
  if(['oversize','dialogError'].includes(mode))await assert.rejects(promise);else assert.equal(await promise,mode==='cancel'?null:'data:image/png;base64,cG5n');
  assert.deepEqual(events,[['focusable',true],['focus'],['restore']]);
 }
 console.log('Photo picker: owned native dialog, local-only image read, size limit, cancel/error focus restoration passed.');
})().catch(e=>{console.error(e);process.exitCode=1;});
