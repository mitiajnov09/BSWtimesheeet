// Pointer interaction logic in an isolated VM, without browser automation.
const assert=require('node:assert/strict'),fs=require('node:fs'),vm=require('node:vm');
const source=fs.readFileSync('static/app.js','utf8');
function setup(){
 const listeners={},timers=new Map(),calls=[],errors=[],opened=[];let next=0,loads=0;
 const period={id:9,employee_id:7,project_id:1,start:'2026-10-10',end:'2026-10-15',kind:'work',version:3,layer:1};
 const employee={id:7,status:'active',schedule_version:8},calendar={scrollLeft:0};
 const bar={dataset:{period:'9'},style:{left:'254px',width:'164px'},classList:{add(){},remove(){}},setPointerCapture(){},hasPointerCapture:()=>true,releasePointerCapture(){},addEventListener:(k,f)=>listeners[k]=f,removeEventListener:k=>delete listeners[k]};
 const context={state:{periods:[period],employees:[employee]},currentProject:()=>({status:'active'}),isSecretary:()=>false,$:()=>calendar,dt:d=>new Date(d+'T00:00:00Z'),add:(d,n)=>new Date(new Date(d+'T00:00:00Z').getTime()+n*86400000).toISOString().slice(0,10),setTimeout:(f,ms)=>{timers.set(++next,{f,ms});return next},clearTimeout:id=>timers.delete(id),api:async(path,payload)=>calls.push({path,payload}),load:async()=>loads++,toast:(message,error)=>errors.push({message,error}),translateText:x=>x,modalActions:{},openPeriod:(...args)=>opened.push(args)};
 vm.createContext(context);vm.runInContext(source.slice(source.indexOf('let suppressClick=false'),source.indexOf('function modal(')),context);
 vm.runInContext(source.slice(source.indexOf('async function action('),source.indexOf("document.addEventListener('click'")),context);
 function down(mode='move'){context.ev={button:0,pointerId:1,clientX:100,target:{dataset:mode==='move'?{}:{resize:mode}}};context.bar=bar;vm.runInContext('startDrag(ev,bar,28)',context)}
 return{context,period,employee,calendar,bar,listeners,timers,calls,errors,opened,down,loads:()=>loads};
}
(async()=>{
 let t=setup();t.down();await t.listeners.pointerup();await vm.runInContext("action('period','9')",t.context);assert.equal(t.opened.length,1);assert.equal(t.calls.length,0);
 t=setup();t.down();t.listeners.pointermove({clientX:156});await t.listeners.pointerup();await vm.runInContext("action('period','9')",t.context);assert.equal(t.opened.length,0);assert.equal(t.calls[0].payload.start,'2026-10-12');assert.equal(t.calls[0].payload.end,'2026-10-17');assert.equal(t.calls[0].payload.schedule_version,8);assert.equal(t.calls[0].payload.version,3);assert.equal(t.calls[0].payload.scope,'single');
 for(const [mode,x,start,end] of [['start',128,'2026-10-11','2026-10-15'],['end',72,'2026-10-10','2026-10-14'],['start',-100,'2026-10-03','2026-10-15'],['end',156,'2026-10-10','2026-10-17']]){t=setup();t.down(mode);t.listeners.pointermove({clientX:x});await t.listeners.pointerup();assert.equal(t.calls[0].payload.start,start);assert.equal(t.calls[0].payload.end,end);assert.equal(t.opened.length,0)}
 t=setup();t.down();[...t.timers.values()].find(x=>x.ms===220).f();await t.listeners.pointerup();await vm.runInContext("action('period','9')",t.context);assert.equal(t.opened.length,0);assert.equal(t.calls.length,0);
 t=setup();t.down();t.listeners.pointermove({clientX:105});await t.listeners.pointerup();assert.equal(t.calls.length,0);await vm.runInContext("action('period','9')",t.context);assert.equal(t.opened.length,0);
 t=setup();t.down();t.listeners.pointermove({clientX:156});t.listeners.pointercancel();assert.equal(t.bar.style.left,'254px');assert.equal(t.calls.length,0);
 t=setup();t.down('start');t.listeners.pointermove({clientX:600});await t.listeners.pointerup();assert.equal(t.calls[0].payload.start,t.calls[0].payload.end);
 t=setup();t.down();t.calendar.scrollLeft=28;t.listeners.pointermove({clientX:128});await t.listeners.pointerup();assert.equal(t.calls[0].payload.start,'2026-10-12');
 t=setup();t.context.api=async()=>{throw Object.assign(new Error('Конфликт'),{status:409})};t.down();t.listeners.pointermove({clientX:156});await t.listeners.pointerup();assert.equal(t.loads(),1);assert.equal(t.errors[0].error,true);assert.equal(t.bar.style.left,'254px');assert.equal(t.opened.length,0);
 t=setup();t.context.isSecretary=()=>true;t.period.kind='rest';t.down();assert.equal(t.listeners.pointermove,undefined);
 console.log('Click, hold, move, both resize directions, minimum duration, cancel, scroll and conflict checks passed');
})().catch(e=>{console.error(e);process.exitCode=1});
