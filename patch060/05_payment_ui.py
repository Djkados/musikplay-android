from pathlib import Path
root=Path("source/autoresponder-pro")
p=root/"web/app.js";s=p.read_text(encoding="utf-8")
def change(a,b):
 global s
 assert s.count(a)==1,(a[:85],s.count(a))
 s=s.replace(a,b,1)
seed='''  const paymentDefaults=()=>({
    movieplay:{holder:"Cristian Castaño",
      nequi:{number:"3045214937",key:"@3045214937"},
      bancolombia:{number:"912 752309 23",key:"@castano454"},
      daviplata:{number:"3045214937",key:"@PLATA3045214937"}},
    tresm:{holder:"",nequi:{number:"",key:""},
      bancolombia:{number:"",key:""},daviplata:{number:"",key:""}}
  });
'''
change("  const defaults = () => ({",seed+"  const defaults = () => ({")
change("],images:[],catalog:catalogDefaults(),schedules:SE.defaultSchedules()",
       "],images:[],catalog:catalogDefaults(),payments:paymentDefaults(),schedules:SE.defaultSchedules()")
change("  state.catalog ||= catalogDefaults();",
       "  state.catalog ||= catalogDefaults();\n  state.payments ||= paymentDefaults();")
change("migrateScheduleConfig();state.catalog ||= catalogDefaults();save();setRoute",
       "migrateScheduleConfig();state.catalog ||= catalogDefaults();state.payments ||= paymentDefaults();save();setRoute")
change("const {channel,assistants,exceptions,allowlist,blocked,paused,rules,catalog,schedules,scheduleOverrides,settings}=state;",
       "const {channel,assistants,exceptions,allowlist,blocked,paused,rules,catalog,payments,schedules,scheduleOverrides,settings}=state;")
change("JSON.stringify({version:1,channel,assistants,exceptions,allowlist,blocked,paused,rules,catalog,schedules,scheduleOverrides,settings})",
       "JSON.stringify({version:1,channel,assistants,exceptions,allowlist,blocked,paused,rules,catalog,payments,schedules,scheduleOverrides,settings})")
change("const headings = {catalogo:", "const headings = {pagos:['COBROS / MEDIOS DE PAGO','Medios de pago'],catalogo:")
change("reglas:renderRules,catalogo:renderCatalog,imagenes:renderImages,",
       "reglas:renderRules,catalogo:renderCatalog,pagos:renderPayments,imagenes:renderImages,")

anchor="  function renderRules(){"
paymentForm='''  function renderPayments(){
    const f=(business,key,label,initial="")=>
      '<div class="form-control"><label>'+safe(label)+'</label>'+
      '<input class="field" id="pay_'+business+'_'+key+'" value="'+
        safe(initial)+'" autocomplete="off"></div>';
    const card=business=>{
      const pay=state.payments[business]||paymentDefaults()[business];
      const title=business==="movieplay"?"🎬 MoviePlay":"🍔 Las Tres M";
      return '<article class="card stack"><div class="between"><h2>'+title+
        '</h2><span class="pill">Configuración independiente</span></div>'+
        '<p class="small muted">Esta información solo se ofrece a consultas de este negocio. '+
        'Si no configuras una cuenta, no enviaremos números de otro negocio.</p>'+
        f(business,"holder","Titular",pay.holder||"")+
        ["nequi","bancolombia","daviplata"].map(k=>{
          const label=k==="nequi"?"Nequi":k==="daviplata"?"DaviPlata":"Bancolombia";
          const obj=pay[k]||{};
          return '<div class="form-control"><h3>'+label+'</h3></div><div class="grid cols2">'+
            f(business,k+"_number",k==="bancolombia"?"Cuenta de ahorros":"Número",obj.number||"")+
            f(business,k+"_key","Llave",obj.key||"")+'</div>';
        }).join("")+
        '<div class="notice">La información se envía solo después de identificar el negocio. '+
        'Una consulta por Nequi entrega solo Nequi; “medios de pago” muestra el menú para escoger.</div>'+
        '<button class="btn primary" data-payment-save="'+business+'">Guardar medios de pago</button>'+
        '</article>';
    };
    return '<div class="home-intro"><div><span class="pill">PAGOS · DATOS LOCALES</span>'+
      '<h2>Respuestas de pago separadas por negocio</h2><p>Un mismo WhatsApp puede contestar por los dos negocios, '+
      'pero nunca comparte las cuentas de uno con clientes del otro. Las llaves y números son editables.</p>'+
      '</div></div><div class="grid cols2">'+card("movieplay")+card("tresm")+'</div>';
  }
'''
assert s.count(anchor)==1
s=s.replace(anchor,paymentForm+anchor,1)
anchor="    if(a==='catalog-save'){"
action='''    if(button.dataset.paymentSave){
      const business=button.dataset.paymentSave;
      if(!["movieplay","tresm"].includes(business))return;
      const value=k=>($("#pay_"+business+"_"+k)?.value||"").trim();
      const next={holder:value("holder").slice(0,120)};
      for(const method of ["nequi","bancolombia","daviplata"]){
        next[method]={number:value(method+"_number").slice(0,80),
          key:value(method+"_key").slice(0,80)};
      }
      state.payments[business]=next;save();render();
      notify("Medios de pago actualizados para "+(business==="movieplay"?"MoviePlay":"Las Tres M"));
      return;
    }
'''
assert s.count(anchor)==1
s=s.replace(anchor,action+anchor,1)

# Browser simulator mirrors native payment menu while respecting merchant choice.
anchor="  function respond(channel,contact,text,group=false,at=new Date()){"
paymentEngine='''  function paymentAnswer(assistant,text){
    const n=normalize(text).trim();
    const hitNequi=/\\bnequi\\b/.test(n);
    const hitBanco=/\\bbancolombia\\b|\\bbanco colombia\\b/.test(n);
    const hitDavi=/\\bdaviplata\\b|\\bdavi plata\\b/.test(n);
    const hitKeys=/\\bllaves?\\b|\\bbre ?b\\b/.test(n);
    const generic=/\\bmedios? de pago\\b|\\bformas? de pago\\b|\\bcomo pago\\b|\\bdonde (puedo )?pago\\b|\\ba donde pago\\b|\\bdatos (de|para) pago\\b|\\bcuentas? (bancarias?|para pagar|de pago)\\b|\\bdame (las? )?cuentas?\\b|\\bnumero de cuenta\\b|\\bpara transferir\\b|\\bcomo te pago\\b|\\ba donde transfiero\\b|\\bpagar el servicio\\b/.test(n);
    const choices=[hitNequi,hitBanco,hitDavi].filter(Boolean).length;
    const type=choices>1?"menu":hitNequi?"nequi":hitBanco?"bancolombia":
      hitDavi?"daviplata":hitKeys?"llaves":generic?"menu":null;
    if(!type)return null;
    const pay=state.payments[assistant]||paymentDefaults()[assistant];
    const title=assistant==="movieplay"?"🎬 *MOVIEPLAY*":"🍔 *LAS TRES M*";
    const names=["nequi","bancolombia","daviplata"];
    if(!names.some(k=>pay[k]?.number||pay[k]?.key))
      return title+"\\n\\n💳 Los datos de pago de este negocio se confirman directamente con nuestro equipo.\\n\\nEscríbenos cuando estés listo para pagar. 😊";
    const holder=pay.holder?"👤 *Titular:* "+pay.holder+"\\n\\n":"";
    if(type==="menu")return title+"\\n\\n💳 *MEDIOS DE PAGO*\\n\\n"+holder+
      "1️⃣ *Nequi*\\n2️⃣ *Bancolombia*\\n3️⃣ *DaviPlata*\\n4️⃣ *Pago con llave*\\n\\n"+
      "✍️ *Responde 1, 2, 3 o 4; también puedes escribir el nombre del medio que prefieras.*";
    let body="";
    if(type==="llaves"){
      body="🔑 *PAGO CON LLAVE*\\n\\n"+names.map(k=>
        pay[k]?.key?"*"+(k==="bancolombia"?"Bancolombia":k==="daviplata"?"DaviPlata":"Nequi")+":* "+pay[k].key:"").filter(Boolean).join("\\n");
    }else{
      const detail=pay[type]||{},label=type==="nequi"?"NEQUI":type==="bancolombia"?"BANCOLOMBIA":"DAVIPLATA";
      body="💳 *"+label+"*\\n\\n"+
        (detail.number?(type==="bancolombia"?"🏦 *Cuenta de ahorros:* ":"📲 *Número:* ")+detail.number+"\\n":"")+
        (detail.key?"🔑 *Llave:* "+detail.key:"");
    }
    return title+"\\n\\n"+holder+body+"\\n\\n📩 *Después de pagar, envíanos el comprobante* para verificar tu pago.";
  }
'''
assert s.count(anchor)==1
s=s.replace(anchor,paymentEngine+anchor,1)
needle='''    const unit=SE.determineUnit(assistant,text);
    if(unit){'''
replacement='''    const unit=SE.determineUnit(assistant,text);
    const payment=paymentAnswer(assistant,text);
    if(payment)return {reply:payment,assistant,unit,method:assign.method,status:"open",image:null};
    if(unit){'''
assert s.count(needle)==1
s=s.replace(needle,replacement,1)
p.write_text(s,encoding="utf-8")
(root/"android/app/src/main/assets/app.js").write_text(s,encoding="utf-8")
p=root/"web/index.html";html=p.read_text(encoding="utf-8")
needle='<button class="navbtn" data-route="catalogo">'
assert html.count(needle)==1
html=html.replace(needle,'<button class="navbtn" data-route="pagos"><span>💳</span> Medios de pago</button>\\n        '+needle,1)
p.write_text(html,encoding="utf-8")
(root/"android/app/src/main/assets/index.html").write_text(html,encoding="utf-8")
print("Separate editable merchant payment settings and targeted reply simulation added")
