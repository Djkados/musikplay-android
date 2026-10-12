from pathlib import Path
root=Path("source/autoresponder-pro")
p=root/"web/app.js";s=p.read_text(encoding="utf-8")
a=s.index("  function renderLearning(){")
b=s.index("  function renderRules(){",a)
replacement='''  function renderLearning(){
    const pending=(state.learningSuggestions||[]).filter(x=>x.status==="pending");
    const approved=(state.learningSuggestions||[]).filter(x=>x.status==="approved").length;
    const ignored=(state.learningSuggestions||[]).filter(x=>x.status==="ignored").length;
    const aliases=state.intentAliases||[];
    const choices=[
      ["catalog","📺 Precio o producto del catálogo"],
      ["rule","💬 Asociar a respuesta ya configurada"],
      ["payment","💳 Medios de pago (preguntar cuál prefiere)"],
      ["payment_nequi","💳 Nequi (solo sus datos)"],
      ["payment_bancolombia","🏦 Bancolombia (solo sus datos)"],
      ["payment_daviplata","💳 DaviPlata (solo sus datos)"],
      ["payment_llave","🔑 Pago con llave"],
      ["courtesy","🙌 Agradecimiento"],
      ["renewal","🔄 Solicitud de renovación"],
      ["human","✋ Atención humana, sin respuesta automática"],
      ["custom","✏️ Crear respuesta personalizada"]
    ];
    const optionList=(selected)=>choices.map(([key,label])=>
      '<option value="'+key+'"'+(selected===key?' selected':'')+'>'+
      safe(label)+'</option>').join("");
    const businessOptions=(selected)=>'<option value="none"'+(selected==="none"?' selected':'')+
      '>Elegir negocio</option>'+
      '<option value="movieplay"'+(selected==="movieplay"?' selected':'')+
      '>🎬 MoviePlay</option>'+
      '<option value="tresm"'+(selected==="tresm"?' selected':'')+'>🍔 Las Tres M</option>';
    const products=state.catalog.slice().sort((a,b)=>a.assistant===b.assistant?
      a.name.localeCompare(b.name,"es"):a.assistant==="movieplay"?-1:1);
    const productOptions='<option value="">— Seleccionar producto —</option>'+
      products.map(x=>'<option value="'+safe(x.id)+'">'+
        (x.assistant==="movieplay"?"🎬 ":"🍔 ")+safe(x.name)+
        (x.duration?' · '+safe(x.duration):'')+'</option>').join("");
    const ruleOptions='<option value="">— Seleccionar respuesta —</option>'+
      state.rules.map(x=>'<option value="'+safe(x.id)+'">'+
        safe(labelFor(x.assistant))+' · '+safe(short(x.keywords,50))+'</option>').join("");
    const form=(id,phrase,business,manual)=>{
      const custom=manual?'':'<span class="pill">Sugerencia para aprobar</span>';
      return '<div class="stack" data-learning-box="'+safe(id)+'">'+
        '<div class="between"><strong>'+(manual?'Nueva expresión':'Expresión detectada')+
        '</strong>'+custom+'</div>'+
        '<div class="form-control"><label>Frase que escribe el cliente</label>'+
        '<input class="field" id="learnAlias_'+safe(id)+'" maxlength="100" value="'+
        safe(phrase||'')+'" placeholder="Ej. ¿Me pasas tus datos?"></div>'+
        '<div class="form-control"><label>¿Qué debe hacer el asistente?</label>'+
        '<select class="field" id="learnTarget_'+safe(id)+'" data-learn-kind="'+
        safe(id)+'">'+optionList("catalog")+'</select></div>'+
        '<div class="form-control" data-learn-business-row>'+
        '<label>Negocio de la respuesta</label><select class="field" id="learnBusiness_'+
        safe(id)+'">'+businessOptions(business||"none")+'</select></div>'+
        '<div class="form-control" data-learn-product-row><label>Producto relacionado</label>'+
        '<select class="field" id="learnProduct_'+safe(id)+'">'+productOptions+'</select></div>'+
        '<div class="form-control" data-learn-rule-row style="display:none">'+
        '<label>Respuesta existente</label><select class="field" id="learnRule_'+
        safe(id)+'">'+ruleOptions+'</select></div>'+
        '<p class="small muted" data-learn-hint>'+
        'Puedes vincular la expresión a un producto, una respuesta existente o elegir otro tipo arriba.</p>'+
        '</div>';
    };
    const card=x=>'<article class="card stack">'+
      '<div class="between"><span class="pill">Consulta por aprender</span>'+
      '<span class="tiny muted">'+Number(x.count||1)+' consulta(s)</span></div>'+
      '<div class="notice">'+safe(x.phrase)+'</div>'+
      form(x.id,x.alias||x.phrase,x.assistant||"none",false)+
      '<div class="row"><button class="btn primary mini" data-learning-approve="'+
      safe(x.id)+'">Aprobar aprendizaje</button>'+
      '<button class="btn danger mini" data-learning-ignore="'+safe(x.id)+'">Ignorar</button></div>'+
      '</article>';
    const learned=aliases.length?aliases.map(x=>
      '<div class="contact-line"><div class="contact-meta"><strong>'+
      safe(x.phrase)+'</strong><small>'+
      safe(choices.find(k=>k[0]===x.intent)?.[1]||x.intent)+
      '</small></div><div class="row">'+
      '<input type="checkbox" class="toggle" aria-label="Activar asociación" '+
      'data-intent-active="'+safe(x.id)+'"'+(x.active?' checked':'')+'>'+
      '<button class="btn danger mini" data-intent-delete="'+safe(x.id)+'">Eliminar</button>'+
      '</div></div>').join(''):'<div class="empty">Aún no has enseñado otras respuestas.</div>';
    return '<div class="home-intro"><div><span class="pill">APRENDIZAJE SUPERVISADO</span>'+
      '<h2>🧠 Enseña respuestas al asistente</h2>'+
      '<p>Además de productos, puedes enseñar otras formas de pedir pagos, agradecer, '+
      'renovar o solicitar atención humana. Todo requiere tu aprobación; no se aprende de comprobantes.</p>'+
      '</div></div>'+
      '<div class="grid cols3">'+
      stat("Pendientes",pending.length,"Para revisar","◇")+
      stat("Aprobados",approved+aliases.length,"Asociaciones guardadas","✓")+
      stat("Ignorados",ignored,"Sugerencias descartadas","×")+'</div>'+
      '<div class="card stack top-space"><div class="between"><h2>➕ Enseñar una frase manualmente</h2>'+
      '<span class="pill">También sin mensajes previos</span></div>'+
      form("manual","","none",true)+
      '<button class="btn primary" data-action="learning-manual-add">Guardar aprendizaje</button>'+
      '<div class="notice">Los datos de Nequi, Bancolombia y DaviPlata se consultan desde '+
      'Medios de pago. No se guardan números ni comprobantes como aprendizajes.</div></div>'+
      '<div class="section stack"><div class="between"><h2>Preguntas que no entendió</h2>'+
      '<button class="btn soft mini" data-action="refresh-learning">↻ Revisar</button></div>'+
      '<label class="between"><span>Detectar expresiones nuevas</span>'+
      '<input type="checkbox" class="toggle" data-setting="learningEnabled"'+
      (state.settings.learningEnabled!==false?' checked':'')+'></label>'+
      (pending.length?pending.map(card).join(''):
      '<div class="empty">Aún no hay preguntas nuevas pendientes.</div>')+
      '</div><div class="section card stack"><h2>Respuestas especiales aprendidas ('+
      aliases.length+')</h2>'+learned+'</div>';
  }
'''
s=s[:a]+replacement+s[b:]
p.write_text(s,encoding="utf-8")
(root/"android/app/src/main/assets/app.js").write_text(s,encoding="utf-8")
print("Learning page supports catalog, existing responses, all bank methods, gratitude, renewal, human and manually entered new phrases")
