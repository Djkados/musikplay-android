from pathlib import Path
root=Path("source/autoresponder-pro")
p=root/"web/app.js";s=p.read_text(encoding="utf-8")
def rep(a,b,why):
 global s
 assert s.count(a)==1,(why,s.count(a),a[:95])
 s=s.replace(a,b,1)

rep("    learningSuggestions:[],inbox:[]",
    "    learningSuggestions:[],intentAliases:[],inbox:[]",
    "default approved aliases")
rep("  state.learningSuggestions ||= [];",
    "  state.learningSuggestions ||= [];\n  state.intentAliases ||= [];",
    "migrate older installs")
rep("const {channel,assistants,exceptions,sellerContacts,allowlist,blocked,paused,rules,catalog,payments,schedules,scheduleOverrides,settings}=state;",
    "const {channel,assistants,exceptions,sellerContacts,allowlist,blocked,paused,rules,catalog,payments,schedules,scheduleOverrides,settings,intentAliases}=state;",
    "native sync properties")
rep("JSON.stringify({version:1,channel,assistants,exceptions,sellerContacts,allowlist,blocked,paused,rules,catalog,payments,schedules,scheduleOverrides,settings})",
    "JSON.stringify({version:1,channel,assistants,exceptions,sellerContacts,allowlist,blocked,paused,rules,catalog,payments,schedules,scheduleOverrides,settings,intentAliases})",
    "sync approved aliases to native")
# Learn only after owner approves, with a normalized whole-phrase match so a
# refund proof or mixed sentence cannot be accidentally classified.
anchor="  function respond(channel,contact,text,group=false,at=new Date()){"
helper='''  function learnedIntent(text){
    const clean=s=>normalize(s).replace(/[^a-z0-9 ]+/g," ")
      .replace(/\\s+/g," ").trim();
    const n=clean(text),possibilities=[n];
    for(const prefix of ["hola ","buenas ","buenos dias ","buenas tardes ",
      "buenas noches ","oye ","oe ","porfa ","por favor "]){
      if(n.startsWith(prefix))possibilities.push(n.slice(prefix.length).trim());
    }
    return (state.intentAliases||[]).find(x=>x.active&&
      LE?.safeIntentAlias(x.phrase,x.intent) &&
      possibilities.includes(clean(x.phrase)))||null;
  }
  function learnedIntentResponse(intent){
    if(!intent)return null;
    const kind=intent.intent;
    if(kind==="human")return {reason:"Has solicitado atención humana: revisar personalmente.",
      method:"manual_review"};
    if(kind==="courtesy")return {reply:COURTESY_RESPONSE,method:"courtesy",image:null};
    if(kind==="renewal")return {reply:RENEWAL_ACK,method:"renewal",image:null};
    const names={payment:"medios de pago",payment_nequi:"Nequi",
      payment_bancolombia:"Bancolombia",payment_daviplata:"DaviPlata",
      payment_llave:"Llave"};
    if(!Object.hasOwn(names,kind))return null;
    const payment=paymentAnswer("movieplay",names[kind],true);
    return payment?{reply:payment,method:"payment_specific",image:null}:null;
  }
'''
assert s.count(anchor)==1
s=s.replace(anchor,helper+anchor,1)
rep('''    const sellerMarked=sellerFor(channel,contact);''',
'''    const approved=learnedIntentResponse(learnedIntent(text));
    if(approved)return {...approved,status:approved.reason?"review":"open",
      assistant:null,unit:null};
    const sellerMarked=sellerFor(channel,contact);''',
    "approved aliases before seller and business selection but after receipt/blocked")
# Expose in the local test adapter; it does not bypass Android rules.
rep("window.AutoResponderTest={respond,assistantFor,assignmentFor,departmentStatus,normalize,phoneKey,sameContact,pickImage,isImageValid,getConfig:",
    "window.AutoResponderTest={respond,assistantFor,assignmentFor,departmentStatus,normalize,learnedIntent,phoneKey,sameContact,pickImage,isImageValid,getConfig:",
    "test seam")
# The existing approval path only accepted a product. Replace it with a
# central action that can append to a product, append to an existing rule,
# or create a typed, safe built-in response mapping.
anchor="    if(button.dataset.learningApprove){"
start=s.index(anchor);end=s.index("    if(button.dataset.learningRule){",start)
s=s[:start]+'''    if(a==="learning-manual-add" || button.dataset.learningApprove){
      const id=a==="learning-manual-add"?"manual":button.dataset.learningApprove;
      const proposal=id==="manual"?null:
        (state.learningSuggestions||[]).find(x=>x.id===id && x.status==="pending");
      if(id!=="manual"&&!proposal)return notify("La sugerencia ya fue revisada.");
      const field=(name)=>document.getElementById(name+"_"+id);
      const phrase=(field("learnAlias")?.value||"").trim();
      const intent=field("learnTarget")?.value;
      const business=field("learnBusiness")?.value;
      const productId=field("learnProduct")?.value;
      const ruleId=field("learnRule")?.value;
      if(!phrase)return notify("Escribe la frase que diría el cliente.");
      if(intent==="custom"){
        if(!["movieplay","tresm"].includes(business))
          return notify("Escoge el negocio de la respuesta personalizada.");
        if(!LE?.safeAlias(phrase))
          return notify("La frase es insegura o demasiado general.");
        runtime.learningDraft={id:"",assistant:business,keywords:phrase,
          response:"",imageTag:"",active:true,sourceId:proposal?.id||null};
        runtime.route="rule-edit";
        $('#screen').innerHTML=renderRuleEditor("");
        notify("Escribe el mensaje y guárdalo para aprobarlo.");return;
      }
      if(intent==="catalog"||intent==="rule"){
        if(!LE?.safeAlias(phrase))
          return notify("La frase no es segura para una regla de productos.");
        if(!["movieplay","tresm"].includes(business))
          return notify("Selecciona MoviePlay o Las Tres M.");
        const record=intent==="catalog"?
          state.catalog.find(x=>x.id===productId):
          state.rules.find(x=>x.id===ruleId);
        if(!record||record.assistant!==business)
          return notify("Elige un producto o respuesta del mismo negocio.");
        const old=String(record.keywords||"").split(",").map(x=>LE.normalize(x));
        if(!old.includes(LE.normalize(phrase))){
          if((record.keywords||"").length+phrase.length+1>300)
            return notify("No caben más palabras clave. Edita primero las anteriores.");
          record.keywords=(record.keywords?record.keywords+",":"")+phrase;
        }
      } else {
        if(!LE?.safeIntentAlias(phrase,intent))
          return notify("La frase puede confundirse con un pago o comprobante, o incluye datos sensibles.");
        const canonical=LE.normalize(phrase);
        const found=state.intentAliases.find(x=>LE.normalize(x.phrase)===canonical);
        if(found && found.intent!==intent)
          return notify("Esta frase ya se usa para otra respuesta. Edita la asociación anterior.");
        if(found)found.active=true;
        else state.intentAliases.push({id:token(),phrase,active:true,intent});
      }
      if(proposal){proposal.status="approved";proposal.alias=phrase;
        if(["movieplay","tresm"].includes(business))proposal.assistant=business;}
      save();render();notify("Aprendizaje aprobado y sincronizado con Android.");
      return;
    }
''' + s[end:]
# Style field selectors based on selected type on the same card. Remove inert
# controls instead of requiring a page refresh.
anchor="    if(e.target?.id==='ctType'){"
handler='''    if(e.target?.dataset.learnKind){
      const box=e.target.closest("[data-learning-box]");
      if(!box)return;
      const intent=e.target.value;
      const productRow=box.querySelector("[data-learn-product-row]");
      const ruleRow=box.querySelector("[data-learn-rule-row]");
      const businessRow=box.querySelector("[data-learn-business-row]");
      const hint=box.querySelector("[data-learn-hint]");
      if(productRow)productRow.style.display=intent==="catalog"?"":"none";
      if(ruleRow)ruleRow.style.display=intent==="rule"?"":"none";
      if(businessRow)businessRow.style.display=["catalog","rule","custom"].includes(intent)?"":"none";
      if(hint)hint.textContent=({
        catalog:"Vincula una expresión al producto local que ya administras.",
        rule:"Utiliza una respuesta que tú ya aprobaste en Respuestas y reglas.",
        payment:"Mostrará las opciones de pago compartidas y preguntará cuál prefiere.",
        payment_nequi:"Compartirá solo los datos Nequi configurados, sin copiarlos.",
        payment_bancolombia:"Compartirá solo los datos Bancolombia configurados.",
        payment_daviplata:"Compartirá solo los datos DaviPlata configurados.",
        payment_llave:"Compartirá las llaves de pago configuradas.",
        courtesy:"Usará exactamente tu mensaje de agradecimiento.",
        renewal:"Avisará que revisarás la renovación. Nunca la confirma automáticamente.",
        human:"No responderá; dejará la consulta para atención personal.",
        custom:"Te abrirá el editor para escribir y aprobar el mensaje."
      })[intent]||"Selecciona el tipo de respuesta.";
      return;
    }
'''
assert s.count(anchor)==1
s=s.replace(anchor,handler+anchor,1)
anchor="    if(button.dataset.learningIgnore){"
handlers='''    if(button.dataset.intentDelete){
      if(!confirm("¿Eliminar esta frase aprendida?"))return;
      state.intentAliases=state.intentAliases.filter(x=>x.id!==button.dataset.intentDelete);
      save();render();notify("Asociación eliminada.");return;
    }
'''
assert s.count(anchor)==1
s=s.replace(anchor,handlers+anchor,1)
anchor="    if(t.dataset.catalogToggle){"
toggle='''    if(t.dataset.intentActive){
      const item=state.intentAliases.find(x=>x.id===t.dataset.intentActive);
      if(item){item.active=t.checked;save();render();}
      return;
    }
'''
assert s.count(anchor)==1
s=s.replace(anchor,toggle+anchor,1)
p.write_text(s,encoding="utf-8")
(root/"android/app/src/main/assets/app.js").write_text(s,encoding="utf-8")
print("Learning now stores approved built-in intent aliases separately from products; manual creation and existing-rule linking are wired and synchronized.")
