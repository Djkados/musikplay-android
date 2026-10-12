from pathlib import Path
root=Path("source/autoresponder-pro")
p=root/"web/learning-engine.js"
s=p.read_text(encoding="utf-8")
old='''      const existing=all.find(x=>x.id===id);
      if(existing){existing.count=Math.min(99,(existing.count||1)+1);continue;}
      all.unshift({id,phrase,alias:aliasFromPhrase(phrase),assistant:business,'''
new='''      const alias=aliasFromPhrase(phrase);
      // Group only safe pending expressions that target the SAME business
      // and the SAME non-generic alias. Never cross-approve or auto-learn.
      const existing=all.find(x=>x.id===id || (alias && x.status==="pending" &&
        x.assistant===business && x.alias===alias && safePhrase(x.phrase)));
      if(existing){existing.count=Math.min(99,(existing.count||1)+1);continue;}
      all.unshift({id,phrase,alias,assistant:business,'''
assert s.count(old)==1
p.write_text(s.replace(old,new,1),encoding="utf-8")
(root/"android/app/src/main/assets/learning-engine.js").write_text(p.read_text(encoding="utf-8"),encoding="utf-8")

p=root/"web/app.js";s=p.read_text(encoding="utf-8")
old='''    const rows=['normal','business'].map(ch=>{'''
new='''    const extraDiagnostic=diag?'<div class="card stack top-space">'+
      '<h2>🔧 Autodiagnóstico sin enviar mensajes</h2>'+
      '<p class="small muted">Verifica estado, último intento de respuesta y batería. '+
      'No inicia conversaciones ni envía datos.</p>'+
      '<div class="meta-line"><span class="chip">Versión: '+
      safe(diag.appVersion||"Android")+'</span>'+
      '<span class="chip">Batería: '+(diag.batteryOptimizationIgnored?
      'Sin restricción conocida':'Revisar optimización')+'</span></div>'+
      '<p class="small muted">Último intento de respuesta: '+
      (diag.lastSubmittedAt?new Date(diag.lastSubmittedAt).toLocaleString("es-CO"):
      'Aún sin registro')+'</p>'+
      '<p class="small muted">Acciones manuales: '+Number(diag.manualControlCount||0)+'</p>'+
      '<div class="row"><button class="btn soft" data-action="battery-settings">'+
      'Revisar ahorro de batería</button>'+
      '<button class="btn soft" data-action="refresh-diagnostics">Actualizar diagnóstico</button></div>'+
      '<div class="notice">Android acepta el intento de respuesta; no confirma entrega, lectura ni pago.</div></div>':"";
    const rows=['normal','business'].map(ch=>{'''
assert s.count(old)==1
s=s.replace(old,new,1)
marker='$'+'{rows}</div>'+'$'+'{diagnostic}'
assert s.count(marker)==1
s=s.replace(marker,marker+'$'+'{extraDiagnostic}',1)
old='''    if(a==='app-settings'){if(native&&window.AndroidBridge.openApplicationSettings)window.AndroidBridge.openApplicationSettings();return;}'''
new=old+'''
    if(a==='battery-settings'){
      if(native && window.AndroidBridge.openBatteryOptimizationSettings)
        window.AndroidBridge.openBatteryOptimizationSettings();
      else notify("Requiere Android con acceso a ajustes de batería.");
      return;
    }'''
assert s.count(old)==1
s=s.replace(old,new,1)
# Interface copy accurately describes supervised local learning.
old='''<h2>Enseña al asistente</h2><p>Propone nuevas asociaciones cuando no comprende una consulta de texto. '''
new='''<h2>Enseña al asistente</h2><p>Agrupa preguntas parecidas de un mismo negocio y propone asociaciones cuando no comprende una consulta de texto. '''
assert s.count(old)==1
s=s.replace(old,new,1)
p.write_text(s,encoding="utf-8")
(root/"android/app/src/main/assets/app.js").write_text(s,encoding="utf-8")
print("Supervised learning groups same-topic safe phrases and adds passive battery, app version, last-reply diagnostics")
