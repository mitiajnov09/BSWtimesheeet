// Isolated render checks with a minimal document stub. No browser or network access.
const assert=require('node:assert/strict'),fs=require('node:fs'),vm=require('node:vm');
const nodes=new Map();function node(selector){if(!nodes.has(selector))nodes.set(selector,{innerHTML:'',textContent:'',value:['[name=project_id]','[name=registration_project]'].includes(selector)?'1':'',scrollLeft:0,scrollTop:0,style:{},classList:{add(){},remove(){}},querySelector(){return node('child')},querySelectorAll(){return[]},addEventListener(){},setAttribute(){},focus(){}});return nodes.get(selector)}
const doc={querySelector:node,querySelectorAll:()=>[],addEventListener(){},activeElement:null,documentElement:{dataset:{},style:{}},body:{classList:{remove(){}}}};
const fixture={user:{id:1,name:'Администратор',role:'admin'},csrf:'test',projects:[{id:1,name:'Тестовый проект',status:'active',city:'Стокгольм',country:'Швеция',timezone:'Europe/Stockholm',start:'2026-01-01',end:'2027-12-31'}],employees:[{id:1,first_name:'Иван',last_name:'Петров',specialty:'Монтажник',status:'active',schedule_version:1}],assignments:[{id:1,employee_id:1,project_id:1,start:'2026-01-01',end:'2027-12-31'}],periods:[],events:[],managers:[],users:[],sites:[],teams:[{id:1,project_id:1,name:'Монтажная команда'}],team_members:[{id:1,project_id:1,employee_id:1,team_id:1,version:1}]};
const context={localStorage:{getItem:()=>null},document:doc,Intl,Date,setTimeout(){},clearTimeout(){},languageSelect:()=>'<select>Language</select>',translateText:x=>x,fixture};vm.createContext(context);
const source=fs.readFileSync('static/app.js','utf8').replace(/^load\(\)\.catch\(.*$/m,'');vm.runInContext(source,context);
vm.runInContext("state=fixture;projectId=1;anchor='2026-10-01';render()",context);
assert.match(node('#content').innerHTML,/Создать учётную запись/);assert.match(node('#calendar').innerHTML,/Монтажная команда/);
vm.runInContext('openEmployee(undefined,1)',context);assert.match(node('#modal-root').innerHTML,/registration_project/);assert.match(node('#registration-assignment').innerHTML,/Начало назначения/);
vm.runInContext('openUser()',context);assert.match(node('#modal-root').innerHTML,/value="secretary"/);
vm.runInContext("state.user.role='secretary';render()",context);
assert.doesNotMatch(node('#content').innerHTML,/Создать учётную запись/);assert.match(node('#content').innerHTML,/data-palette="work"/);assert.match(node('#content').innerHTML,/data-palette="sick"/);assert.doesNotMatch(node('#content').innerHTML,/data-palette="vacation"/);assert.doesNotMatch(node('#app').innerHTML,/data-id="users"/);
vm.runInContext('openTools(1)',context);assert.doesNotMatch(node('#modal-root').innerHTML,/data-act="tool-cycle"/);assert.doesNotMatch(node('#modal-root').innerHTML,/data-act="tool-deactivate"/);
vm.runInContext('openPeriod(1)',context);assert.doesNotMatch(node('#modal-root').innerHTML,/value="vacation"/);assert.match(node('#modal-root').innerHTML,/value="sick"/);
console.log('14 registration, role and team render checks passed');
fixture.teams.push({id:2,project_id:1,name:'Пустая команда',status:'active',version:1});
vm.runInContext("state.user.role='admin';render()",context);
assert.match(node('#calendar').innerHTML,/Пустая команда/);assert.match(node('#calendar').innerHTML,/data-act="team-add" data-id="2"/);assert.match(node('#calendar').innerHTML,/data-act="team-delete" data-id="2"/);
vm.runInContext('openTeam(2)',context);assert.doesNotMatch(node('#modal-root').innerHTML,/<select name="project_id"/);
fixture.periods=[{id:1,project_id:1,employee_id:1,start:'2026-10-01',end:'2026-10-03',kind:'work',layer:0},{id:2,project_id:1,employee_id:1,start:'2026-10-02',end:'2026-10-02',kind:'sick',layer:1}];
assert.equal(vm.runInContext("dailyOnSiteCount('2026-10-01')",context),1);assert.equal(vm.runInContext("dailyOnSiteCount('2026-10-02')",context),0);assert.equal(vm.runInContext("dailyOnSiteCount('2026-10-03')",context),1);
fixture.employees[0].leadership='team_leader';vm.runInContext('render()',context);assert.match(node('#calendar').innerHTML,/leadership-badge tl/);
vm.runInContext("view='projects';render()",context);assert.doesNotMatch(node('#content').innerHTML,/data-act="assign-project"/);
vm.runInContext('toggleTheme()',context);assert.equal(doc.documentElement.dataset.theme,'dark');vm.runInContext('toggleTheme()',context);assert.equal(doc.documentElement.dataset.theme,'light');
console.log('11 empty-team, daily count, badge and theme checks passed');

vm.runInContext("view='employees';render()",context);
assert.match(node('#content').innerHTML,/id="employees-search"/);
assert.equal(vm.runInContext("employeeNameMatches({first_name:'Ąžuolas',last_name:'Žukauskas'},'zuk azu')",context),true);
assert.equal(vm.runInContext("employeeNameMatches({first_name:'Ąžuolas',last_name:'Žukauskas'},'Mantas')",context),false);
vm.runInContext('openTeam(2)',context);assert.match(node('#modal-root').innerHTML,/data-act="delete-current-team">Удалить команду/);
vm.runInContext("view='schedule';render()",context);assert.match(node('#calendar').innerHTML,/class="icon team-delete-button"/);
console.log('Worker name search and visible team deletion checks passed');
