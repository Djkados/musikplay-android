from pathlib import Path
p=Path("source/autoresponder-pro/web/app.js")
s=p.read_text(encoding="utf-8")
def rep(a,b):
 global s
 assert s.count(a)==1,(a[:100],s.count(a))
 s=s.replace(a,b,1)
anchor="    if(a==='new-rule'){"
handlers='''    if(a==='refresh-learning'){
      await loadNative();render();notify("Consultas revisadas.");return;
    }
    if(button.dataset.learningIgnore){
      const item=state.learningSuggestions.find(x=>x.id===button.dataset.learningIgnore);
      if(item){item.status="ignored";save();render();}return;
    }
    if(button.dataset.learningApprove){
      const item=state.learningSuggestions.find(x=>x.id===button.dataset.learningApprove);
      if(!item)return;
      const business=document.getElementById("learnBusiness_"+item.id)?.value;
      const alias=document.getElementById("learnAlias_"+item.id)?.value.trim();
      const productId=document.getElementById("learnProduct_"+item.id)?.value;
      const product=state.catalog.find(x=>x.id===productId);
      if(!["movieplay","tresm"].includes(business))
        return notify("Selecciona el negocio correcto.");
      if(!product || product.assistant!==business)
        return notify("Selecciona un producto del mismo negocio.");
      if(!LE?.safeAlias(alias))
        return notify("La expresión es demasiado general o contiene datos sensibles.");
      const terms=String(product.keywords||"").split(",").map(x=>LE.normalize(x));
      if(!terms.includes(LE.normalize(alias))){
        const next=(product.keywords?product.keywords+",":"")+alias;
        if(next.length>300)return notify("Este producto ya tiene demasiadas palabras.");
        product.keywords=next;
      }
      item.status="approved";item.alias=LE.normalize(alias);item.assistant=business;
      save();render();
      notify("Asociación aprobada y sincronizada con el motor Android.");return;
    }
    if(button.dataset.learningRule){
      const item=state.learningSuggestions.find(x=>x.id===button.dataset.learningRule);
      if(!item)return;
      const business=document.getElementById("learnBusiness_"+item.id)?.value;
      const alias=document.getElementById("learnAlias_"+item.id)?.value.trim();
      if(!["movieplay","tresm"].includes(business)||!LE?.safeAlias(alias))
        return notify("Selecciona el negocio y una frase específica.");
      runtime.learningDraft={id:"",assistant:business,keywords:alias,response:"",
        imageTag:"",active:true,sourceId:item.id};
      runtime.route="rule-edit";
      document.querySelector("#screen").innerHTML=renderRuleEditor("");
      notify("Redacta y revisa la respuesta antes de aprobarla.");return;
    }
'''
assert s.count(anchor)==1
s=s.replace(anchor,handlers+anchor,1)
rep("}else state.rules.push(r);save();setRoute('reglas');notify('Regla guardada.');return;}",
''' }else state.rules.push(r);
      if(runtime.learningDraft?.sourceId){
        const suggestion=state.learningSuggestions.find(x=>x.id===runtime.learningDraft.sourceId);
        if(suggestion)suggestion.status="approved";
      }
      runtime.learningDraft=null;save();setRoute('reglas');
      notify('Regla revisada y guardada.');return;}''')
rep('''if(button.dataset.useInbox){const msg=state.inbox.find(i=>i.id===button.dataset.useInbox);if(msg){runtime.selectedInbox=msg.id;''',
'''if(button.dataset.useInbox){const msg=state.inbox.find(i=>i.id===button.dataset.useInbox);
      if(msg?.autoStatus==="manual_review")return notify("Adjunto o comprobante: revísalo directamente en WhatsApp.");
      if(msg){runtime.selectedInbox=msg.id;''')
rep('''i.autoStatus==="no_quick_reply"||i.routeMethod==="human_pause"''',
    '''i.autoStatus==="no_quick_reply"||i.autoStatus==="manual_review"||
      i.routeMethod==="human_pause"||i.routeMethod==="manual_review"''')
# Use a distinct operational label for manual review; avoid outdated claims.
rep('''La pausa cuando respondes tú es manual por ahora.''',
    '''Si el teléfono identifica una respuesta manual tuya, intenta pausar ese chat 1 hora; revisa las pruebas en tu dispositivo.''')
p.write_text(s,encoding="utf-8")
Path("source/autoresponder-pro/android/app/src/main/assets/app.js").write_text(s,encoding="utf-8")
print("Learning approve/new rule/dismiss actions connected and manual-review inbox protected")
