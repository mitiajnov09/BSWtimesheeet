const assert=require('node:assert/strict'),fs=require('node:fs'),vm=require('node:vm');
const source=fs.readFileSync('static/i18n.js','utf8').split("document.addEventListener('change'")[0];
const context={localStorage:{getItem:()=>null}};vm.createContext(context);vm.runInContext('let state=null;'+source,context);
assert.equal(vm.runInContext('language',context),'lt');
for(const [saved,expected] of [['en','en'],['pl','pl'],['ru','ru'],['invalid','lt']]){
 const fresh={localStorage:{getItem:()=>saved}};vm.createContext(fresh);vm.runInContext('let state=null;'+source,fresh);
 assert.equal(vm.runInContext('language',fresh),expected);
}
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
assert.equal(translate('en','График ротаций'),'Rotation schedule');
assert.equal(translate('en','Октябрь 2026'),'October 2026');
assert.equal(translate('en','Больничный * · Слой 2'),'Sick leave * · Layer 2');
assert.equal(translate('en','Свернуть меню'),'Collapse menu');
vm.runInContext("state={projects:[{name:'Работа — Стокгольм'}],employees:[{first_name:'Иван',last_name:'Работник'}],sites:[],users:[],events:[]}",context);
assert.equal(translate('en','Работа — Стокгольм'),'Работа — Стокгольм');
assert.equal(translate('en','Иван Работник'),'Иван Работник');
vm.runInContext('state=null',context);
const dictionary=JSON.parse(vm.runInContext('JSON.stringify(UI_TRANSLATIONS)',context));
for(const [key,values] of Object.entries(dictionary)){
 assert.equal(values.length,3,key);
 assert.ok(values[2].trim(),key);
 assert.doesNotMatch(translate('en',key),/[А-Яа-яЁё]/,key);
}
const selector=vm.runInContext('languageSelect()',context);
for(const label of ['🇱🇹 LT','🇵🇱 PL','🇬🇧 EN','🇷🇺 RU'])assert.ok(selector.includes(label),label);
assert.match(selector,/<option value="en" selected>/);
console.log('LT, PL, RU and EN translations, protected names, full English dictionary and flag selector checks passed');
