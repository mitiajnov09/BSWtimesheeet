const assert=require('node:assert/strict'),fs=require('node:fs'),vm=require('node:vm');
const source=fs.readFileSync('static/app.js','utf8');
const functions=source.slice(source.indexOf('function dropPosition('),source.indexOf('function setupPalette('));
let project={status:'active',timezone:'Europe/Stockholm'},employee={id:7,status:'active',schedule_version:4};
let track={dataset:{employee:'7'},getBoundingClientRect:()=>({left:-250})},calls=[],loads=0;
const days=Array.from({length:31},(_,i)=>`2026-10-${String(i+1).padStart(2,'0')}`);
const context={document:{elementsFromPoint:()=>[{closest:()=>track}]},state:{employees:[employee]},scale:'month',projectId:1,paletteBusy:false,periodRange:()=>({days}),currentProject:()=>project,api:async(...args)=>{calls.push(args)},load:async()=>{loads++},toast:()=>{},translateText:x=>x};
vm.createContext(context);vm.runInContext(functions,context);
function position(x){context.x=x;return vm.runInContext('dropPosition(x,100)',context)}
assert.equal(position(-250).date,'2026-10-01');assert.equal(position(-250+28*30+27).date,'2026-10-31');
assert.equal(position(-251),null);assert.equal(position(-250+28*31),null);
project.status='archived';assert.equal(position(0),null);project.status='active';employee.status='archived';assert.equal(position(0),null);employee.status='active';
context.position=position(-250+28*11);
(async()=>{
 await vm.runInContext("addPaletteItem(position,'sick')",context);
 assert.equal(calls[0][0],'periods');assert.equal(calls[0][1].start,'2026-10-12');assert.equal(calls[0][1].end,'2026-10-12');assert.equal(calls[0][1].schedule_version,4);
 await vm.runInContext("addPaletteItem(position,'outbound')",context);
 assert.equal(calls[1][1].transport,'unknown');assert.equal(calls[1][1].ticket_bought,0);assert.equal(calls[1][0],'events');assert.equal(Object.hasOwn(calls[1][1],'timezone'),false);assert.equal(calls[1][1].date,'2026-10-12');assert.equal(loads,2);
 context.paletteBusy=true;await vm.runInContext("addPaletteItem(position,'work')",context);assert.equal(calls.length,2);
 console.log('14 palette coordinate and save checks passed');
})().catch(error=>{console.error(error);process.exitCode=1});
