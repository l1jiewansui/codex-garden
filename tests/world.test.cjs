const assert=require('node:assert/strict');const {slots,matches,cropStage}=require('../web/model.js');
const initial=slots({},[{id:'a'},{id:'b'},{id:'c'}]);
assert.deepEqual(slots(initial,[{id:'c'},{id:'a'},{id:'b'}]),{c:2,a:0,b:1});
assert.deepEqual(slots(initial,[{id:'b'},{id:'d'}]),{b:1,d:0});
assert.equal(new Set(Object.values(slots({a:1,b:1,c:-3},[{id:'a'},{id:'b'},{id:'c'}]))).size,3);
assert.equal(matches({status:'stale'},'care'),true);assert.equal(matches({status:'growing'},'care'),false);
assert.equal(cropStage('ripe'),3);assert.equal(cropStage('failed'),1);assert.equal(cropStage('harvested'),0);
console.log('World model: slot stability, slot reuse, invalid slots, filtering and crop states passed.');
