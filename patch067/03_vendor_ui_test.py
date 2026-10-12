from pathlib import Path
root=Path("source/autoresponder-pro")
p=root/"tests/vendor_form_067.test.cjs"
p.write_text(r'''const assert=require('node:assert/strict');
const fs=require('node:fs');
const vm=require('node:vm');
const schedule=require('../web/schedule-engine.js');
const learning=require('../web/learning-engine.js');
const js=fs.readFileSync(__dirname+'/../web/app.js','utf8');

async function run(){
 const store=new Map(), sent=[];
 const handlers={};
 const elements=new Map();
 const node=()=>({
  value:'',textContent:'',innerHTML:'',checked:false,
  classList:{add(){},remove(){},toggle(){}},
  addEventListener(){},focus(){},scrollIntoView(){},
  querySelectorAll(){return[]},appendChild(){}
 });
 const document={
   querySelector(key){
     if(!elements.has(key))elements.set(key,node());
     return elements.get(key);
   },
   querySelectorAll(){return[]},
   addEventListener(type,fn){(handlers[type]??=[]).push(fn)},
   createElement(){return node()}
 };
 const window={
   ScheduleEngine:schedule,LearningEngine:learning,addEventListener(){},
   AndroidBridge:{
     shareText(){},
     setCaptureChannels(){},
     syncAutomationConfig(json){sent.push(JSON.parse(json))},
     getInbox(){return '[]'},clearInbox(){}
   }
 };
 const context={document,window,console,
   localStorage:{
     getItem(k){return store.get(k)||null},
     setItem(k,value){store.set(k,value)}
   },
   setTimeout,clearTimeout,URL,Blob,FileReader:function(){},
   indexedDB:{open(){throw Error('Unexpected IndexedDB in vendor setup test')}},
   Date,Math,navigator:{},confirm:()=>true,prompt:()=>null
 };
 vm.runInNewContext(js,context,{filename:'app.js'});
 async function click(dataset){
   const button={dataset,id:'',closest(){return this}};
   const event={target:{closest(){return button}}};
   for(const fn of handlers.click??[])await fn(event);
 }
 const val=(id,v)=>{document.querySelector('#'+id).value=v};
 await click({route:'vendedores'});
 assert.match(document.querySelector('#screen').innerHTML,
     /value="both" selected[^>]*>✅ Ambos WhatsApp/);
 assert.match(document.querySelector('#screen').innerHTML,/Guardar vendedor/);

 val('vendorName','Carlos Prueba');
 val('vendorPhone','');
 val('vendorChannel','both');
 val('vendorBusiness','movieplay');
 await click({action:'save-vendor'});
 const config=window.AutoResponderTest.getConfig();
 assert.equal(config.sellerContacts.length,1,'New vendor must persist');
 assert.equal(config.sellerContacts[0].contact,'Carlos Prueba');
 assert.equal(config.sellerContacts[0].channel,'both');
 assert.equal(sent.at(-1).sellerContacts[0].channel,'both',
    'Native Android receives the saved both-channel role');
 assert.match(document.querySelector('#screen').innerHTML,
     /✅ Vendedor guardado correctamente/);
 assert.match(document.querySelector('#screen').innerHTML,/Registrados \(1\)/);

 // Resaving an existing record MUST change its channel: this was one
 // possible hidden reason that owners saw no effective result.
 val('vendorName','Carlos Prueba');
 val('vendorPhone','');
 val('vendorChannel','normal');
 val('vendorBusiness','movieplay');
 await click({action:'save-vendor'});
 const updated=window.AutoResponderTest.getConfig();
 assert.equal(updated.sellerContacts.length,1);
 assert.equal(updated.sellerContacts[0].channel,'normal');

 val('vendorName','Carlos Prueba');
 val('vendorPhone','');
 val('vendorChannel','both');
 val('vendorBusiness','movieplay');
 await click({action:'save-vendor'});
 assert.equal(window.AutoResponderTest.getConfig().sellerContacts[0].channel,'both');

 // Saving ONLY a valid phone is also allowed, with no name.
 val('vendorName','');
 val('vendorPhone','+57 301 123 4567');
 val('vendorChannel','both');
 val('vendorBusiness','movieplay');
 await click({action:'save-vendor'});
 assert.equal(window.AutoResponderTest.getConfig().sellerContacts.length,2);
 assert.equal(window.AutoResponderTest.getConfig().sellerContacts[1].phone,
   '3011234567');

 // Validation failures remain visible below the button, unlike a short
 // toast that can be hidden by the Android keyboard.
 val('vendorName','');
 val('vendorPhone','123');
 await click({action:'save-vendor'});
 assert.equal(window.AutoResponderTest.getConfig().sellerContacts.length,2);
 assert.match(document.querySelector('#vendorSaveFeedback').textContent,/Número inválido/);

 assert.match(document.querySelector('#screen').innerHTML,/Ambos WhatsApp/);
 console.log('OK — Save vendor: both channels by default, persistent UI confirmation, phone-only, update, visible errors and native sync.');
}
run().catch(err=>{console.error(err);process.exitCode=1});
''',encoding="utf-8")
print("Browser-based VM click test exercises real save button, localStorage and AndroidBridge config sync")
