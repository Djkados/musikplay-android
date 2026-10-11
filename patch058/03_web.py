from pathlib import Path
root=Path("source/autoresponder-pro")
p=root/"web/app.js"
s=p.read_text()
def change(old,new):
 global s
 n=s.count(old)
 assert n==1, f"Unexpected web panel (found {n}): {old[:85]}"
 s=s.replace(old,new)
change("AutoResponder Pro v0.5.6","AutoResponder Pro v0.5.8")
anchor="  const runtime = {route:'inicio'"
assert anchor in s
s=s.replace(anchor,'''  // Both WhatsApp channels can handle both businesses. Contact-specific
  // exceptions and manual channel changes continue to work after migration.
  const mixedMigration="autoresponder_pro_v058_dual_business";
  if(native && !localStorage.getItem(mixedMigration)){
    for(const ch of ["normal","business"])
      if(state.channel[ch])state.channel[ch].assistant="auto";
    localStorage.setItem(KEY,JSON.stringify(state));
    localStorage.setItem(mixedMigration,"done");
  }
'''+anchor,1)
change("const r=respond(i.channel,i.contact,i.text,!!i.group);return",
'''const r=respond(i.channel,i.contact,i.text,!!i.group);
      // This Android decision includes the remembered business; the browser
      // simulator cannot independently reconstruct the private conversation.
      if(i.routeMethod){
        r.image=null;
        if(i.assistant){r.assistant=i.assistant;r.unit=i.department||null;}
        if(i.preparedText){r.reply=i.preparedText;r.reason=null;}
        else if(i.autoReason){r.reply=null;r.reason=i.autoReason;}
        if(i.autoReason==="Fuera de horario")r.status="closed";
      }
      return''')
change("La app prepara respuestas para todos los contactos que escriban. Con autoenvío activo, responde textos según el negocio y su horario. Las imágenes se revisan.",
"Ambos WhatsApp atienden MoviePlay y Las Tres M. El motor recuerda el negocio hasta 24 horas por conversación; las imágenes siempre requieren revisión.")
change("Un solo panel, tres horarios separados.",
"Dos WhatsApp, dos negocios y tres horarios separados.")
change("Configura cada negocio sin cruzar sus mensajes. Ambos WhatsApp pueden detectar MoviePlay o Las Tres M por la consulta.",
"Los dos WhatsApp identifican MoviePlay y Las Tres M. Si no está claro, preguntan 1 o 2 y recuerdan esa elección durante 24 horas.")
change("Configúralas por WhatsApp; solo para contactos autorizados. Inician apagadas.",
"Activa o pausa cada WhatsApp por separado. También atiende contactos nuevos y guardados sin lista obligatoria.")
change("Primero autoriza un contacto de prueba y utiliza el",
"Primero comprueba MoviePlay y Las Tres M en el")
change("Por seguridad, el texto automático sigue apagado inicialmente y solo responde a contactos autorizados en el WhatsApp elegido.",
"Los contactos nuevos no requieren autorización cuando está apagado el modo restringido. La lista de excepciones asigna un negocio fijo si lo necesitas.")
change("Prueba Netflix, hamburguesa, horario sin indicar negocio o soporte de MoviePlay un domingo a las 6:00 p. m.",
"Prueba Netflix, hamburguesa, horario o soporte un domingo. El contexto de 24 horas se aplica a las notificaciones Android; el simulador evalúa cada mensaje de forma independiente.")
change("i.autoStatus==='throttled'?' · Autoenvío limitado por seguridad'",
       "i.autoStatus==='clarification_waiting'?' · Esperando que el cliente elija el negocio':i.autoStatus==='throttled'?' · Autoenvío limitado por seguridad'")
p.write_text(s)
(root/"android/app/src/main/assets/app.js").write_text(s)
engine=root/"web/schedule-engine.js"
e=engine.read_text()
old="function resolveAssignment(channel,contact,message,channels,exceptions){"
assert e.count(old)==1
e=e.replace(old,"function resolveAssignment(channel,contact,message,channels,exceptions,context={}){")
old="""    if(detected.assistant)return {assistant:detected.assistant,method:'detected',confidence:detected.confidence};
    return {assistant:null,method:'clarify',confidence:detected.confidence,reason:detected.reason};"""
new="""    if(detected.assistant)return {assistant:detected.assistant,method:'detected',confidence:detected.confidence};
    if(detected.confidence==='mixed')return {assistant:null,method:'clarify',confidence:'mixed',reason:detected.reason};
    const answer=normalize(message);
    if(context.awaitingChoice && ['1','opcion 1','la primera','primera'].includes(answer))
      return {assistant:'movieplay',method:'choice'};
    if(context.awaitingChoice && ['2','opcion 2','la segunda','segunda'].includes(answer))
      return {assistant:'tresm',method:'choice'};
    if(['movieplay','tresm'].includes(context.business))
      return {assistant:context.business,method:'context'};
    return {assistant:null,method:'clarify',confidence:detected.confidence,reason:detected.reason};"""
assert e.count(old)==1
e=e.replace(old,new)
engine.write_text(e)
(root/"android/app/src/main/assets/schedule-engine.js").write_text(e)
b=root/"android/app/build.gradle.kts"
g=b.read_text()
assert 'versionCode = 12' in g and 'versionName = "0.5.7"' in g
b.write_text(g.replace('versionCode = 12','versionCode = 13').replace('versionName = "0.5.7"','versionName = "0.5.8"'))
print("v0.5.8 WebView UI, diagnostics, and JS route preview updated")
