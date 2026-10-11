from pathlib import Path
root=Path("source/autoresponder-pro")
p=root/"web/app.js"
s=p.read_text(encoding="utf-8")
def change(a,b):
    global s
    count=s.count(a)
    assert count==1,(a[:100],count)
    s=s.replace(a,b,1)
# Use native business route when selecting promotional media.
change('''      if(i.routeMethod){
        r.image=null;
        if(i.assistant){r.assistant=i.assistant;r.unit=i.department||null;}''',
'''      if(i.routeMethod){
        r.image=(i.imageTag&&i.assistant)?
          pickImage(i.assistant,i.imageTag,SE.bogotaParts().date):null;
        if(i.assistant){r.assistant=i.assistant;r.unit=i.department||null;}''')
change("safe(short(r.reply,400))","safe(short(r.reply,1600))")
change('''    if(button.dataset.reviewInbox){const msg=state.inbox.find(i=>i.id===button.dataset.reviewInbox);if(msg){const result=respond(msg.channel,msg.contact,msg.text,!!msg.group);if(result.image)openReview({imageId:result.image.id,contact:msg.contact,channel:msg.channel,caption:result.reply,inboxId:msg.id,showChannel:false});}return;}''',
'''    if(button.dataset.reviewInbox){
      const msg=state.inbox.find(i=>i.id===button.dataset.reviewInbox);
      if(msg){
        const result=respond(msg.channel,msg.contact,msg.text,!!msg.group);
        const photo=msg.routeMethod?
          (msg.assistant&&msg.imageTag?pickImage(msg.assistant,msg.imageTag,SE.bogotaParts().date):null):
          result.image;
        if(photo)openReview({imageId:photo.id,contact:msg.contact,
          channel:msg.channel,caption:msg.preparedText||result.reply||"",
          inboxId:msg.id,showChannel:false});
        else notify("No hay publicidad vigente para esta consulta.");
      }
      return;
    }''')
# Distinguish delivery request from verified send; counts are local.
anchor="  function renderSettings(){"
assert s.count(anchor)==1
stats='''  function renderActivity(){
    const diag=androidDiagnostics()||{};
    const inbox=state.inbox||[];
    const leads=inbox.filter(i=>i.autoReason==="Catálogo aprobado").length;
    const pending=inbox.filter(i=>!i.autoStatus||i.autoStatus==="skipped"||
      i.autoStatus==="no_quick_reply"||i.routeMethod==="human_pause").length;
    const unknown=inbox.filter(i=>
      ["Consulta sin regla aprobada","Negocio ambiguo: revisión manual","Atención humana pausada"]
      .includes(i.autoReason)).length;
    const cards=[
      ["Consultas en bandeja",inbox.length,"Últimos registros guardados en este dispositivo","✉"],
      ["Respuestas preparadas en Android",Number(diag.submittedCount||0),
        "Android aceptó el intento; no confirma entrega en WhatsApp","↗"],
      ["Consultas de catálogo",Number(diag.catalogReplies||0),
        "Solicitudes de respuesta sobre precios o productos","＄"],
      ["Pausas por atención humana",Number(diag.humanPauses||0),
        "Solo cuando Android detecta una respuesta manual","◉"],
      ["Pendientes por revisar",pending,"En la bandeja local actual","◇"],
      ["Sin regla o en atención humana",unknown,
        "Consultas que conviene resolver o convertir en nuevas reglas","⚙"]
    ];
    return '<div class="home-intro"><div><span class="pill">ACTIVIDAD LOCAL</span>'+
      '<h2>Seguimiento de respuestas y oportunidades</h2>'+
      '<p>Indicadores guardados en el teléfono, sin servidores ni gastos externos.</p>'+
      '</div><div class="row"><button class="btn primary" data-action="refresh-activity">↻ Actualizar</button>'+
      '<button class="btn soft" data-go="bandeja">Ver conversaciones →</button></div></div>'+
      '<div class="grid cols3">'+cards.map(x=>stat(x[0],x[1],x[2],x[3])).join('')+'</div>'+
      '<div class="section card stack"><h2>Oportunidades de atención</h2>'+
      '<p class="small muted">Consultas de catálogo recientes: '+leads+
      '. Para sugerir imágenes, asigna etiquetas al producto y a la publicidad del mismo negocio.</p>'+
      '<p class="small muted">Fallos de respuesta directa: '+Number(diag.noQuickReplyCount||0)+
      ' · Errores registrados: '+Number(diag.failedCount||0)+'.</p>'+
      '<div class="notice">Las cifras de respuesta indican intentos enviados a Android, no confirmaciones de lectura, entrega o compra. Las ventas reales deben verificarse manualmente.</div>'+
      '<div class="row"><button class="btn soft" data-go="catalogo">Editar catálogo y promociones</button>'+
      '<button class="btn soft" data-go="imagenes">Configurar publicidad manual</button></div></div>';
  }
'''
s=s.replace(anchor,stats+anchor,1)
change("ajustes:['SISTEMA / AJUSTES','Configuración']",
       "actividad:['MÉTRICAS / ACTIVIDAD','Actividad'],ajustes:['SISTEMA / AJUSTES','Configuración']")
change("reglas:renderRules,catalogo:renderCatalog,imagenes:renderImages,bandeja:renderInbox,",
       "reglas:renderRules,catalogo:renderCatalog,imagenes:renderImages,actividad:renderActivity,bandeja:renderInbox,")
change("    if(a==='refresh-inbox'){",
       "    if(a==='refresh-activity'){await loadNative();render();notify('Actividad actualizada.');return;}\n    if(a==='refresh-inbox'){")
change("throttled:'Límite de 10 minutos activo'",
       "throttled:'Espera breve para evitar respuestas repetidas',own_notification_skipped:'Mensaje propio ignorado',own_echo_skipped:'Eco de respuesta ignorado',human_reply_paused:'Pausa por atención humana'")
change("Máximo una respuesta por conversación cada 10 minutos. Si la notificación no permite respuesta directa, no se envía nada.",
       "Control de duplicados y pausa breve entre consultas; después de elegir 1 o 2 se atiende la respuesta inmediatamente. Requiere respuesta directa de WhatsApp.")
change('''<div class="notice">Si la bandeja recibe el mensaje, pulsa «Autorizar pruebas» desde ese mismo mensaje: WhatsApp puede mostrar un nombre aunque hayas guardado un número.</div>''',
       '''<div class="notice">Las respuestas automáticas no requieren lista de contactos si desactivaste el modo restringido. Revisa la bandeja si WhatsApp no ofreció respuesta directa.</div>''')
p.write_text(s,encoding="utf-8")
(root/"android/app/src/main/assets/app.js").write_text(s,encoding="utf-8")
p=root/"web/index.html"
html=p.read_text(encoding="utf-8")
anchor='<button class="navbtn" data-route="bandeja">'
assert anchor in html
html=html.replace(anchor,'<button class="navbtn" data-route="actividad"><span>▥</span> Actividad y oportunidades</button>\n        '+anchor,1)
p.write_text(html,encoding="utf-8")
(root/"android/app/src/main/assets/index.html").write_text(html,encoding="utf-8")
print("v0.5.9 activity dashboard and manual advertisement review added")
