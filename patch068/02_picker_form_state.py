from pathlib import Path
root=Path("source/autoresponder-pro")
p=root/"web/app.js"
s=p.read_text(encoding="utf-8")
def rep(a,b,reason):
 global s
 n=s.count(a)
 assert n==1,(reason,n,a[:105])
 s=s.replace(a,b,1)

rep("const runtime = {learningDraft:null,catalogEdit:null,route:'inicio'",
    "const runtime = {contactDraft:null,contactPickSettings:null,contactLastId:null,learningDraft:null,catalogEdit:null,route:'inicio'",
    "private short-lived contact form draft")

# Keep the Android-selected values after every render (visibilitychange,
# async loadNative(), browser focus, route changes). Do not save the contact
# as a vendor until the owner chooses Guardar vendedor.
helper='''  function restoreSelectedContact(){
    const info=runtime.contactDraft;
    if(!info)return;
    if(Date.now()-info.pickedAt>600000){
      runtime.contactDraft=null;return;
    }
    const field=(id,value)=>{
      const node=document.getElementById(id);
      if(node)node.value=value;
    };
    if(runtime.route==="vendedores"){
      field("vendorName",info.name);
      field("vendorPhone",info.phone);
      field("vendorChannel",info.channel||"both");
      field("vendorBusiness",info.assistant||"movieplay");
      const box=document.getElementById("vendorSaveFeedback");
      if(box)box.textContent=runtime.vendorFeedback||
        "✅ Contacto recuperado. Revisa y pulsa Guardar vendedor.";
    }else if(runtime.route==="contactos"){
      field("ctName",info.name);
      field("ctPhone",info.phone);
      if(info.contactType)field("ctType",info.contactType);
      if(info.channel)field("ctChannel",info.channel);
      if(info.assistant)field("ctAssistant",info.assistant);
      const row=document.getElementById("ctAssistantRow");
      if(row&&info.contactType)row.hidden=
        !["exceptions","sellerContacts"].includes(info.contactType);
    }
  }
  function recoverAndroidSelectedContact(){
    if(!native || !window.AndroidBridge ||
       typeof window.AndroidBridge.takeSelectedPhoneContact!=="function")return;
    try{
      const data=window.AndroidBridge.takeSelectedPhoneContact();
      if(data)window.onAndroidContactSelected(data);
    }catch(e){console.warn("No se pudo recuperar el contacto seleccionado",e);}
  }
'''
anchor="  function render(){"
assert s.count(anchor)==1
s=s.replace(anchor,helper+anchor,1)
rep("$('#screen').innerHTML=h();putEditorBesideSelectedProduct();",
    "$('#screen').innerHTML=h();putEditorBesideSelectedProduct();restoreSelectedContact();",
    "restore values following every redraw")
rep("""(runtime.vendorFeedback||'Escribe el nombre, el número o ambos y pulsa Guardar.')+""",
    """safe(runtime.vendorFeedback||'Escribe el nombre, el número o ambos y pulsa Guardar.')+""",
    "escape selected contact notice before markup injection")

start=s.index("  // Receives ONLY the contact explicitly chosen through Android ACTION_PICK.")
end=s.index("  // Global delegated interactions.",start)
callback='''  // Android Contact Picker. Returning to the app triggers visibilitychange,
  // which redraws the form. Keep the chosen data in an in-memory draft and
  // restore it on every render. The native one-shot result survives WebView
  // reloads for 10 minutes, then is discarded.
  window.onAndroidContactSelected=(selection)=>{
    let result;
    try{result=typeof selection==="string"?JSON.parse(selection):selection;}
    catch(_){return notify("No pude leer el contacto seleccionado.");}
    const rawPhone=String(result?.phone||"").trim();
    const normalizedPhone=phoneKey(rawPhone);
    const name=String(result?.name||"").trim().slice(0,140);
    if(!name&&!normalizedPhone)
      return notify("Este contacto no tiene un nombre ni teléfono válido.");
    const pickedAt=Number(result?.pickedAt)||Date.now();
    const lastId=pickedAt+"|"+normalizedPhone+"|"+name;
    if(runtime.contactLastId===lastId){
      restoreSelectedContact();return;
    }
    runtime.contactLastId=lastId;
    const settings=runtime.contactPickSettings||{};
    runtime.contactDraft={
      name,phone:normalizedPhone||"",pickedAt:Date.now(),
      channel:settings.channel||"both",
      assistant:settings.assistant||"movieplay",
      contactType:settings.contactType||"sellerContacts"
    };
    // Discard the temporary native copy as soon as the JS in-memory
    // draft safely owns the user's explicit selection.
    if(native && typeof window.AndroidBridge.takeSelectedPhoneContact==="function"){
      try{window.AndroidBridge.takeSelectedPhoneContact();}catch(_){}
    }
    runtime.vendorFeedback="✅ Contacto seleccionado: "+(name||"número terminado en "+
      normalizedPhone.slice(-4))+(normalizedPhone?" · Celular terminado en "+
      normalizedPhone.slice(-4):" · Sin teléfono válido")+
      ". Revisa los datos y pulsa Guardar vendedor.";
    if(["vendedores","contactos"].includes(runtime.route)){
      render();
      const editor=document.getElementById(runtime.route==="vendedores"?
        "vendorEditor":"ctName");
      editor?.scrollIntoView?.({block:"nearest"});
    }
    notify("Contacto seleccionado. Ahora pulsa Guardar vendedor.");
  };
'''
s=s[:start]+callback+s[end:]

# Snapshot form selections before opening Android Contacts; do not force
# the business back to MoviePlay if owner already selected Las Tres M.
rep("""    if(a==='pick-contact'){
      if(!native || typeof window.AndroidBridge.pickPhoneContact!=='function')return notify('El selector de contactos requiere la APK 0.5.1.');
      try{window.AndroidBridge.pickPhoneContact();}catch(_){notify('No se pudo abrir la agenda. Puedes escribir el número.');}
      return;
    }""",
"""    if(a==='pick-contact'){
      if(!native || typeof window.AndroidBridge.pickPhoneContact!=='function')
        return notify('El selector de contactos requiere la APK Android.');
      runtime.contactPickSettings={
        channel:runtime.route==='vendedores'?($('#vendorChannel')?.value||'both'):
          ($('#ctChannel')?.value||'normal'),
        assistant:runtime.route==='vendedores'?($('#vendorBusiness')?.value||'movieplay'):
          ($('#ctAssistant')?.value||'movieplay'),
        contactType:runtime.route==='vendedores'?'sellerContacts':
          ($('#ctType')?.value||'allowlist')
      };
      try{window.AndroidBridge.pickPhoneContact();}
      catch(_){notify('No se pudo abrir la agenda. Puedes escribir el número.');}
      return;
    }""",
    "retain selected channel, business and contact type when launching Android picker")

# If user manually edits a selected name/phone after choosing a contact, its
# changes also persist across a subsequent WebView render.
anchor="  document.addEventListener('change',e=>{"
handler='''  document.addEventListener("input",e=>{
    const draft=runtime.contactDraft;
    if(!draft)return;
    const id=e.target?.id;
    if(id==="vendorName"||id==="ctName")draft.name=String(e.target.value||"").slice(0,140);
    if(id==="vendorPhone"||id==="ctPhone")draft.phone=String(e.target.value||"");
  });
'''
assert s.count(anchor)==1
s=s.replace(anchor,handler+anchor,1)
anchor="    if(e.target?.dataset.vendorBusiness){"
handler='''    if(runtime.contactDraft){
      const control=e.target?.id;
      if(control==="vendorChannel"||control==="ctChannel")
        runtime.contactDraft.channel=e.target.value;
      if(control==="vendorBusiness"||control==="ctAssistant")
        runtime.contactDraft.assistant=e.target.value;
      if(control==="ctType")runtime.contactDraft.contactType=e.target.value;
    }
'''
assert s.count(anchor)==1
s=s.replace(anchor,handler+anchor,1)

# A deliberately changed, now-saved record should not be repopulated after
# save() triggers another dashboard render.
anchor='''        runtime.vendorFeedback="✅ Vendedor guardado correctamente. Protegido en "+'''
assert s.count(anchor)==1
s=s.replace(anchor,'''        runtime.contactDraft=null;
        runtime.contactPickSettings=null;
        runtime.contactLastId=null;
        runtime.vendorFeedback="✅ Vendedor guardado correctamente. Protegido en "+''',1)

# Clear the local draft when the contacts/exceptions form was successfully
# saved as well. Leave the draft untouched on validation errors.
anchor="save();render();notify('Contacto guardado en '+channelNames[channel]+'.');return;"
assert s.count(anchor)==1
s=s.replace(anchor,"runtime.contactDraft=null;runtime.contactPickSettings=null;runtime.contactLastId=null;\n      "+anchor,1)

# Async notification-refresh is exactly what previously erased picked data.
# Recover from the native one-time cache, and restore after its render.
rep("""  document.addEventListener('visibilitychange',()=>{if(!document.hidden&&native){loadNative().then(()=>render());}});
  window.addEventListener('focus',()=>{if(native&&runtime.route==='automatizacion'){loadNative().then(()=>render());}});""",
"""  document.addEventListener('visibilitychange',()=>{
    if(!document.hidden&&native){
      recoverAndroidSelectedContact();
      loadNative().then(()=>{render();recoverAndroidSelectedContact();});
    }
  });
  window.addEventListener('focus',()=>{
    if(native)recoverAndroidSelectedContact();
    if(native&&runtime.route==='automatizacion')loadNative().then(()=>render());
  });""",
"consume temporary native selection on resume, preserve draft on redraw")
rep("  syncNativeCapture();loadNative().then(()=>render());",
    "  syncNativeCapture();loadNative().then(()=>{render();recoverAndroidSelectedContact();});",
    "recover after startup or process-recreated WebView")

p.write_text(s,encoding="utf-8")
(root/"android/app/src/main/assets/app.js").write_text(s,encoding="utf-8")
print("Selected Android contact stays visible through visibilitychange, render and Android WebView recreation; both vendor and contacts forms preserve name/phone and selections, no auto-save.")
