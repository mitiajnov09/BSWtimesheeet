// Generate the server/PDF dictionary from the frontend source, without executing UI code.
const fs=require('node:fs'),vm=require('node:vm'),path=require('node:path');
const root=path.resolve(__dirname,'..');
const source=fs.readFileSync(path.join(root,'static/i18n.js'),'utf8').split('const translationKeys=')[0];
const context={localStorage:{getItem:()=>null}};vm.createContext(context);
const result=vm.runInContext(source+'; JSON.stringify(UI_TRANSLATIONS)',context);
fs.writeFileSync(path.join(root,'static/translations.json'),result);
