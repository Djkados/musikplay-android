from pathlib import Path
root=Path("source/autoresponder-pro")
p=root/"web/app.js";s=p.read_text(encoding="utf-8")
def rep(a,b):
 global s
 assert s.count(a)==1,(a[:85],s.count(a))
 s=s.replace(a,b,1)
rep("  const SE=window.ScheduleEngine;", "  const SE=window.ScheduleEngine;\n  const LE=window.LearningEngine;")
rep("    inbox:[]\n  });","    learningSuggestions:[],inbox:[]\n  });")
rep("  state.payments ||= paymentDefaults();",
    "  state.payments ||= paymentDefaults();\n  state.learningSuggestions ||= [];")
rep("  state.settings.autoReplies ||= {normal:false,business:false};",
    "  state.settings.autoReplies ||= {normal:false,business:false};\n  state.settings.learningEnabled ??= true;")
rep("  const runtime = {catalogEdit:null,",
    "  const runtime = {learningDraft:null,catalogEdit:null,")
rep("const headings = {pagos:",
    "const headings = {aprendizaje:['ASISTENTE / APRENDIZAJE','Centro de aprendizaje'],pagos:")
rep("reglas:renderRules,catalogo:renderCatalog,pagos:renderPayments,",
    "reglas:renderRules,aprendizaje:renderLearning,catalogo:renderCatalog,pagos:renderPayments,")
rep("state.inbox=state.inbox.slice(0,40);save();",
    '''state.inbox=state.inbox.slice(0,40);
       if(LE&&state.settings.learningEnabled!==false)
         state.learningSuggestions=LE.absorb(state.learningSuggestions||[],incoming);
       save();''')
anchor="  function renderRules(){"
ui='''  function renderLearning(){
    const pending=(state.learningSuggestions||[]).filter(x=>x.status==="pending");
    const approved=(state.learningSuggestions||[]).filter(x=>x.status==="approved").length;
    const ignored=(state.learningSuggestions||[]).filter(x=>x.status==="ignored").length;
    const choice=(value,key,label)=>'<option value="'+key+'"'+(value===key?' selected':'')+'>'+label+'</option>';
    const all=state.catalog.slice().sort((a,b)=>a.assistant===b.assistant?
      a.name.localeCompare(b.name,'es'):a.assistant==="movieplay"?-1:1);
    const card=i=>{
      const products='<option value="">Seleccionar producto</option>'+all.map(p=>
        '<option value="'+safe(p.id)+'">'+(p.assistant==="movieplay"?"🎬":"🍔")+
        ' '+safe(p.name)+(p.duration?' · '+safe(p.duration):'')+'</option>').join('');
      return '<article class="card stack"><div class="between"><span class="pill">Consulta por aprender</span>'+
        '<span class="tiny muted">'+i.count+' consulta(s)</span></div>'+
        '<p class="reply" style="white-space:pre-wrap">'+safe(i.phrase)+'</p>'+
        '<div class="grid cols2"><div class="form-control"><label>Negocio correcto</label>'+
        '<select id="learnBusiness_'+safe(i.id)+'">'+
        choice(i.assistant||"none","none","Elegir negocio")+
        choice(i.assistant||"none","movieplay","🎬 MoviePlay")+
        choice(i.assistant||"none","tresm","🍔 Las Tres M")+'</select></div>'+
        '<div class="form-control"><label>Palabra o frase para reconocer</label>'+
        '<input class="field" id="learnAlias_'+safe(i.id)+'" maxlength="45" value="'+
          safe(i.alias||"")+'" placeholder="Ej. flujotv"></div></div>'+
        '<div class="form-control"><label>Producto relacionado</label>'+
        '<select id="learnProduct_'+safe(i.id)+'">'+products+'</select></div>'+
        '<div class="row"><button class="btn primary mini" data-learning-approve="'+safe(i.id)+'">Aprobar asociación</button>'+
        '<button class="btn soft mini" data-learning-rule="'+safe(i.id)+'">Crear respuesta</button>'+
        '<button class="btn danger mini" data-learning-ignore="'+safe(i.id)+'">Ignorar</button></div>'+
        '<p class="tiny muted">Revisa cada sugerencia: nunca se convierte en una respuesta sin tu aprobación.</p></article>';
    };
    return '<div class="home-intro"><div><span class="pill">APRENDIZAJE SUPERVISADO</span>'+
      '<h2>Enseña al asistente</h2><p>Propone nuevas asociaciones cuando no comprende una consulta de texto. '+
      'No procesa imágenes, comprobantes, nombres, números de teléfono ni contraseñas.</p></div></div>'+
      '<div class="grid cols3">'+
      stat("Pendientes",pending.length,"Requieren tu aprobación","◇")+
      stat("Aprobados",approved,"Aprendizajes aplicados","✓")+
      stat("Ignorados",ignored,"Sugerencias descartadas","×")+'</div>'+
      '<div class="card stack top-space"><label class="between"><strong>Detectar nuevas preguntas</strong>'+
      '<input type="checkbox" class="toggle" data-setting="learningEnabled"'+
      (state.settings.learningEnabled!==false?' checked':'')+'></label>'+
      '<p class="small muted">Se guarda solo una frase filtrada, sin datos de los contactos, en este dispositivo.</p>'+
      '<button class="btn soft" data-action="refresh-learning">↻ Revisar consultas</button></div>'+
      '<div class="section stack">'+(pending.length?pending.map(card).join(''):
      '<div class="empty">Todavía no hay nuevas expresiones seguras para revisar.</div>')+'</div>';
  }
'''
assert s.count(anchor)==1
s=s.replace(anchor,ui+anchor,1)
rep("function renderRuleEditor(id){const r=state.rules.find(x=>x.id===id)||{id:'',assistant:'movieplay',keywords:'',response:'',imageTag:'',active:true};",
    "function renderRuleEditor(id){const r=state.rules.find(x=>x.id===id)||runtime.learningDraft||{id:'',assistant:'movieplay',keywords:'',response:'',imageTag:'',active:true};")
rep("if(a==='new-rule'){runtime.route='rule-edit';",
    "if(a==='new-rule'){runtime.learningDraft=null;runtime.route='rule-edit';")
rep("if(a==='cancel-rule'){setRoute('reglas');return;}",
    "if(a==='cancel-rule'){runtime.learningDraft=null;setRoute('reglas');return;}")
rep("if(a==='export'){const data=new Blob([JSON.stringify({...state,inbox:[]},null,2)]",
    "if(a==='export'){const data=new Blob([JSON.stringify({...state,inbox:[],learningSuggestions:[]},null,2)]")
rep("navigator.clipboard?.writeText(JSON.stringify({...state,inbox:[]},null,2))",
    "navigator.clipboard?.writeText(JSON.stringify({...state,inbox:[],learningSuggestions:[]},null,2))")
rep("const r=respond(i.channel,i.contact,i.text,!!i.group);",
    '''const r=respond(i.channel,i.contact,i.text,!!i.group);
      if(i.autoStatus==="manual_review" || i.routeMethod==="manual_review"){
        r.reply=null;r.image=null;
        r.reason=i.autoReason||"Comprobante o adjunto: revisar manualmente.";
      }''')
rep("i.autoStatus==='skipped'?' · Respuesta bloqueada por una regla':''",
    "i.autoStatus==='manual_review'?' · 📎 Pendiente de revisión; respuesta automática bloqueada':i.autoStatus==='skipped'?' · Respuesta bloqueada por una regla':''")
rep('''["Pendientes por revisar",pending,"En la bandeja local actual","◇"],''',
    '''["Pendientes por revisar",pending,"En la bandeja local actual","◇"],
      ["Aprendizajes por aprobar",(state.learningSuggestions||[]).filter(x=>x.status==="pending").length,
        "Solo expresiones de texto y con aprobación","♧"],''')
rep('''<button class="btn soft" data-go="catalogo">Editar catálogo y promociones</button>''',
    '''<button class="btn soft" data-go="aprendizaje">Centro de aprendizaje</button>
      <button class="btn soft" data-go="catalogo">Editar catálogo y promociones</button>''')
p.write_text(s,encoding="utf-8")
(root/"android/app/src/main/assets/app.js").write_text(s,encoding="utf-8")
for fn in ["web/index.html","android/app/src/main/assets/index.html"]:
    p=root/fn;h=p.read_text(encoding="utf-8")
    anchor='<button class="navbtn" data-route="actividad">'
    assert h.count(anchor)==1
    h=h.replace(anchor,'<button class="navbtn" data-route="aprendizaje"><span>✦</span> Centro de aprendizaje</button>\n        '+anchor,1)
    h=h.replace('</button>\\\\n        <button','</button>\n        <button')
    p.write_text(h,encoding="utf-8")
print("Learning suggestions, review interface and safe inbox behavior added")
