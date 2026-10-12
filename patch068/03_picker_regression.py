from pathlib import Path
root=Path("source/autoresponder-pro")
p=root/"tests/contact_picker_068.test.cjs"
p.write_text(r'''const assert=require('node:assert/strict');
const fs=require('node:fs');
const vm=require('node:vm');
const schedule=require('../web/schedule-engine.js');
const learning=require('../web/learning-engine.js');
const script=fs.readFileSync(__dirname+'/../web/app.js','utf8');

const sleep=(ms=20)=>new Promise(done=>setTimeout(done,ms));
async function main(){
  const store=new Map(),handlers={},events={},nodes=new Map();
  let pending="",picked=0,latestSync=null;
  const fieldNames=['vendorName','vendorPhone','vendorChannel','vendorBusiness',
    'vendorSaveFeedback','ctName','ctPhone','ctChannel','ctType','ctAssistant',
    'ctAssistantRow','vendorEditor'];
  const node=()=>({
    value:'',textContent:'',checked:false,hidden:false,innerHTML:'',
    classList:{add(){},remove(){},toggle(){}},
    addEventListener(){},focus(){},scrollIntoView(){},
    querySelectorAll(){return[]},appendChild(){}
  });
  const screen=node();
  // Simulate actual browser behavior: a complete innerHTML redraw destroys
  // input nodes, including fields filled immediately after ACTION_PICK.
  Object.defineProperty(screen,'innerHTML',{
    get(){return this._html||''},
    set(value){
      this._html=String(value);
      for(const name of fieldNames)nodes.delete('#'+name);
    }
  });
  nodes.set('#screen',screen);
  function find(key){
    if(key==='#screen')return screen;
    if(key[0]==='#'){
      const name=key.slice(1);
      if(fieldNames.includes(name) &&
          !screen.innerHTML.includes('id="'+name+'"'))return null;
    }
    if(!nodes.has(key)){
      const n=node();
      if(key==='#vendorChannel')n.value='both';
      if(key==='#vendorBusiness')n.value='movieplay';
      if(key==='#ctChannel')n.value='normal';
      if(key==='#ctType')n.value='allowlist';
      if(key==='#ctAssistant')n.value='movieplay';
      nodes.set(key,n);
    }
    return nodes.get(key);
  }
  const document={
    hidden:false,
    querySelector:find,
    getElementById(id){return find('#'+id)},
    querySelectorAll(){return[]},
    addEventListener(type,fn){(handlers[type]??=[]).push(fn)},
    createElement(){return node()}
  };
  const bridge={
    shareText(){},syncAutomationConfig(raw){latestSync=JSON.parse(raw)},
    setCaptureChannels(){},getInbox(){return '[]'},clearInbox(){},
    pickPhoneContact(){picked++},
    takeSelectedPhoneContact(){const result=pending;pending='';return result;}
  };
  const window={
    ScheduleEngine:schedule,LearningEngine:learning,
    AndroidBridge:bridge,
    addEventListener(type,fn){(events[type]??=[]).push(fn)}
  };
  const context={document,window,console,setTimeout,clearTimeout,URL,Blob,
    FileReader:function(){},Date,Math,navigator:{},confirm:()=>true,prompt:()=>null,
    localStorage:{
      getItem(key){return store.get(key)||null},
      setItem(key,value){store.set(key,String(value))}
    }
  };
  vm.runInNewContext(script,context,{filename:'app.js'});
  await sleep();
  async function click(dataset){
    const button={dataset,id:'',closest(){return this}};
    const event={target:{closest(){return button}}};
    for(const callback of handlers.click||[])await callback(event);
  }
  const read=(key)=>find('#'+key)?.value;
  async function resume(){
    for(const callback of handlers.visibilitychange||[])callback();
    for(const callback of events.focus||[])callback();
    await sleep();
  }

  await click({route:'vendedores'});
  assert.ok(screen.innerHTML.includes('id="vendorPhone"'));
  assert.equal(read('vendorName'),'');
  await click({action:'pick-contact'});
  assert.equal(picked,1);
  // The ActivityResult callback arrived before visibilitychange.
  window.onAndroidContactSelected({
    name:'Luisa Vendedora',
    phone:'+57 300 234 5678',
    pickedAt:Date.now()
  });
  assert.equal(read('vendorName'),'Luisa Vendedora');
  assert.equal(read('vendorPhone'),'3002345678');
  assert.equal(read('vendorChannel'),'both');
  await resume();
  // In v0.6.7 this assertion failed because visibilitychange->render()
  // wiped both fields, exactly as the owner's video demonstrated.
  assert.equal(read('vendorName'),'Luisa Vendedora',
    'Selected name must survive WebView foreground redraw');
  assert.equal(read('vendorPhone'),'3002345678',
    'Selected phone must survive WebView foreground redraw');
  assert.match(find('#vendorSaveFeedback').textContent,/Contacto seleccionado/);

  await click({action:'save-vendor'});
  const saved=window.AutoResponderTest.getConfig();
  assert.equal(saved.sellerContacts.length,1);
  assert.equal(saved.sellerContacts[0].contact,'Luisa Vendedora');
  assert.equal(saved.sellerContacts[0].phone,'3002345678');
  assert.equal(saved.sellerContacts[0].channel,'both');
  assert.equal(latestSync.sellerContacts[0].phone,'3002345678',
    'Android native policy must receive saved seller');
  assert.match(screen.innerHTML,/Registrados \(1\)/);
  assert.equal(read('vendorName'),'',
    'Fields should clear AFTER saving, not after selecting');

  // WebView can be recreated while Android Contacts is foregrounded.
  // The temporary one-shot native value must repopulate fields when it returns.
  await click({route:'vendedores'});
  pending=JSON.stringify({
    name:'Vendedor Recuperado',phone:'301 333 2244',pickedAt:Date.now()
  });
  await resume();
  assert.equal(read('vendorName'),'Vendedor Recuperado');
  assert.equal(read('vendorPhone'),'3013332244');
  assert.equal(pending,'','Native cache must be consumed once');
  await resume();
  assert.equal(read('vendorName'),'Vendedor Recuperado');
  assert.equal(read('vendorPhone'),'3013332244');

  // Choosing Las Tres M before opening the picker is preserved, even after
  // the browser screen redraw that previously lost the contact.
  find('#vendorBusiness').value='tresm';
  await click({action:'pick-contact'});
  window.onAndroidContactSelected({
    name:'María Tres M',phone:'302 111 2233',pickedAt:Date.now()+1
  });
  await resume();
  assert.equal(read('vendorBusiness'),'tresm');
  assert.equal(read('vendorName'),'María Tres M');
  await click({action:'save-vendor'});
  const updated=window.AutoResponderTest.getConfig();
  assert.equal(updated.sellerContacts.length,2);
  const last=updated.sellerContacts.at(-1);
  assert.equal(last.assistant,'tresm');
  assert.equal(last.channel,'both');

  // Owner can still register by name if Android Contacts returns a
  // display name but the phone field cannot be normalized.
  await click({route:'vendedores'});
  window.onAndroidContactSelected({name:'Nombre Guardado',phone:'no disponible',
    pickedAt:Date.now()+2});
  await resume();
  assert.equal(read('vendorName'),'Nombre Guardado');
  assert.equal(read('vendorPhone'),'');
  await click({action:'save-vendor'});
  assert.equal(window.AutoResponderTest.getConfig().sellerContacts.length,3);

  console.log('OK — Android contact survives resume, is visible, saves both WhatsApp, recovers after WebView reload and preserves chosen business.');
}
main().catch(err=>{console.error(err);process.exitCode=1;});
''',encoding="utf-8")
print("Regression test simulates actual DOM destruction on Android resume, native one-shot delivery, seller save, re-render and user edits")
