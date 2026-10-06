const assert=require('node:assert/strict'),fs=require('node:fs'),vm=require('node:vm');
const source=fs.readFileSync('static/i18n.js','utf8').split("document.addEventListener('change'")[0];
const context={localStorage:{getItem:()=>null}};vm.createContext(context);vm.runInContext('let state=null;'+source,context);
function translate(lang,value){context.value=value;return vm.runInContext(`language='${lang}';translateText(value)`,context)}
assert.equal(translate('lt','График ротаций'),'Rotacijų grafikas');assert.equal(translate('pl','График ротаций'),'Grafik rotacji');
assert.equal(translate('lt','Октябрь 2026'),'Spalis 2026');assert.equal(translate('pl','Неактивные работники'),'Nieaktywni pracownicy');
assert.equal(translate('pl','Время (необязательно)'),'Godzina (opcjonalnie)');assert.equal(translate('lt','Больничный * · Слой 2'),'Nedarbingumas * · Sluoksnis 2');
assert.equal(translate('ru','Работа'),'Работа');assert.equal(translate('pl','Иван Работов'),'Иван Работов');
vm.runInContext("state={projects:[{name:'Работа — Стокгольм'}],employees:[{first_name:'Иван',last_name:'Работник',specialty:'Инженер',notes:'Сменить пароль'}],sites:[],users:[],events:[]}",context);
assert.equal(translate('pl','Работа — Стокгольм'),'Работа — Стокгольм');assert.equal(translate('lt','Иван Работник'),'Иван Работник');
assert.equal(translate('pl','Сменить пароль'),'Сменить пароль');assert.equal(vm.runInContext('state.employees[0].notes',context),'Сменить пароль');
vm.runInContext('state=null',context);assert.equal(translate('pl','Сменить пароль'),'Zmień hasło');
assert.deepEqual(JSON.parse(vm.runInContext('JSON.stringify(UI_TRANSLATIONS)',context)),JSON.parse(fs.readFileSync('static/translations.json')));
console.log('14 translation checks passed');
