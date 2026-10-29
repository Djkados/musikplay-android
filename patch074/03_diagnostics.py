from pathlib import Path
root=Path("source/autoresponder-pro")
native=root/"android/app/src/main/java/com/autoresponder/pro"
web=root/"web"
assets=root/"android/app/src/main/assets"

def change(path,old,new,label):
 s=path.read_text(encoding="utf-8")
 assert s.count(old)==1,(label,s.count(old),str(path))
 path.write_text(s.replace(old,new,1),encoding="utf-8")

activity=native/"MainActivity.kt"
change(activity,'''                .put("lastEventAt", status.getLong("lastEventAt", 0))''',
'''                .put("lastEventAt", status.getLong("lastEventAt", 0))
                // Recent events contain only a status code, channel and
                // timestamp. Never include message, contact or credentials.
                .put("recentEvents",runCatching {
                    org.json.JSONArray(status.getString("recentEvents","[]") ?: "[]")
                }.getOrDefault(org.json.JSONArray()))''',
"expose metadata-only diagnostic history")
(web/"diagnostics-074.js").write_text(r'''/* Safe, local diagnosis of notification responses. No chat transcript. */
(function(root,factory){const api=factory();if(typeof module==='object'&&module.exports)module.exports=api;
if(root)root.Diagnostics074=api;})(typeof window!=='undefined'?window:null,function(){
'use strict';
const labels={
 capture_off:['Captura apagada','Activa la captura del WhatsApp correspondiente en Respuestas automáticas.'],
 no_rules_config:['Falta configuración','Abre Respuestas automáticas y guarda los ajustes para sincronizar Android.'],
 skipped:['Respuesta omitida','Consulta la bandeja: puede faltar autorización, una regla aprobada o el negocio correcto.'],
 no_quick_reply:['WhatsApp no permite respuesta directa','Abre WhatsApp y contesta manualmente; revisa las notificaciones.'],
 failed_canceled:['WhatsApp canceló la respuesta','Revisa permisos y notificaciones; vuelve a probar desde otro teléfono.'],
 failed_permission:['Permiso de respuesta rechazado','Verifica el acceso a notificaciones y los ajustes restringidos de Android.'],
 failed_storage:['Error guardando control temporal','Verifica que el dispositivo tenga almacenamiento disponible.'],
 failed_config:['Configuración no válida','Revisa las reglas; exporta una copia antes de hacer cambios.'],
 failed:['Error al responder','Revisa WhatsApp y prueba otra vez con un mensaje nuevo.'],
 submitted_unverified:['Respuesta preparada en Android','No confirma entrega ni lectura. Comprueba el resultado en WhatsApp.'],
 throttled:['Pausa antirrepetición','La aplicación evitó responder muy rápido en el mismo chat.'],
 repeat_answer_suppressed:['Respuesta repetida evitada','Ya se intentó esa respuesta recientemente.'],
 duplicate_notification_skipped:['Notificación duplicada','Android volvió a publicar el mismo aviso; no se respondió dos veces.'],
 rapid_duplicate_skipped:['Aviso duplicado inmediato','Se evitó una respuesta repetida en pocos segundos.'],
 human_reply_paused:['Atención humana prioritaria','El asistente permanece en pausa para ese chat.'],
 own_echo_skipped:['Eco de mensaje propio','La aplicación descartó una notificación del propio envío.'],
 media_skipped:['Archivo o foto recibidos','El adjunto requiere revisión humana.'],
 manual_review:['Comprobante en revisión','Comprueba manualmente el pago; nunca se confirma de forma automática.'],
 sensitive_skipped:['Contenido sensible','No se responde automáticamente a solicitudes con datos sensibles.'],
 group_skipped:['Mensaje de grupo omitido','Por seguridad, el bot no responde a grupos.'],
 notification_summary:['Resumen de notificaciones','Android no proporcionó un mensaje individual verificable.']
};
const trouble=new Set(['no_quick_reply','failed','failed_permission','failed_canceled',
  'failed_storage','failed_config','no_rules_config','capture_off']);
const review=new Set(['skipped','manual_review','sensitive_skipped','media_skipped',
  'human_reply_paused']);
const explain=code=>({
  label:labels[code]?.[0]||String(code||'Sin clasificar').replace(/_/g,' '),
  advice:labels[code]?.[1]||'Consulta el historial local o prueba desde otro teléfono.',
  type:trouble.has(code)?'error':review.has(code)?'review':
    code==='submitted_unverified'?'submitted':'normal'
});
const entries=(rows,filter)=> (Array.isArray(rows)?rows:[])
  .filter(x=>x && typeof x.reason==='string' &&
    ['business','normal'].includes(x.channel) && Number.isFinite(Number(x.at)))
  .filter(x=>filter==='all'||explain(x.reason).type===filter)
  .sort((a,b)=>Number(b.at)-Number(a.at)).slice(0,20);
const metrics=rows=>{
  const all=entries(rows,'all');
  return {total:all.length,errors:entries(all,'error').length,
    review:entries(all,'review').length,submitted:entries(all,'submitted').length};
};
return {explain,entries,metrics};
});
''',encoding="utf-8")
change(web/"index.html",'''        <button class="navbtn" data-route="actividad"><span>▥</span> Actividad y oportunidades</button>''',
'''        <button class="navbtn" data-route="actividad"><span>▥</span> Actividad y oportunidades</button>
        <button class="navbtn" data-route="diagnostico074"><span>🛠</span> Diagnóstico de respuestas</button>''',"diagnostic route nav")
change(web/"index.html",'''  <script src="sales-360.js"></script>''',
'''  <script src="sales-360.js"></script>
  <script src="diagnostics-074.js"></script>''',"diagnostic helper script")
change(web/"index.html",'''Versión 0.6.13 · Ventas 360''',
'''Versión 0.6.14 · Ventas 360''',"version visible")
app=web/"app.js"
change(app,'''sales360Filter:"pending",comboSimulation''',
'''sales360Filter:"pending",diagnostics074Filter:"all",comboSimulation''',"diagnostic filter state")
change(app,'''  const headings = {ventas360:''',
'''  const headings = {diagnostico074:['CALIDAD / DIAGNÓSTICO','Diagnóstico de respuestas'],ventas360:''',
"diagnostics title")
render=r'''
  function renderDiagnostics074(){
    const h=window.Diagnostics074;
    const device=androidDiagnostics();
    const all=device?.recentEvents||[];
    const counts=h.metrics(all);
    const filter=runtime.diagnostics074Filter||'all';
    const recent=h.entries(all,filter);
    const labels=[['all','Todo'],['error','Fallos'],['review','Revisión humana'],
      ['submitted','Enviadas a Android'],['normal','Descartes seguros']];
    const cards=[
      ['Eventos recientes',counts.total,'Últimos 20 registros locales','◉'],
      ['Fallos detectados',counts.errors,'Permisos, envío directo o configuración','⚠'],
      ['Para revisión',counts.review,'Mensajes que requieren una persona','◇'],
      ['Enviadas a Android',counts.submitted,'No confirma entrega ni lectura','↗']
    ];
    return '<div class="home-intro"><div><span class="pill">DIAGNÓSTICO DE RESPUESTAS · 0.6.14</span>'+
      '<h2>Descubre por qué el bot respondió o se detuvo</h2>'+
      '<p>Solo metadatos locales: fecha, WhatsApp y motivo. No se guardan aquí contraseñas, '+
      'comprobantes ni el contenido de las conversaciones.</p></div>'+
      '<div class="row"><button class="btn primary" data-action="refresh-diagnostics">↻ Actualizar</button>'+
      '<button class="btn soft" data-go="pruebas">Probar una frase</button>'+
      '<button class="btn danger" data-action="stop-auto">Detener autoenvío</button></div></div>'+
      '<div class="grid cols3">'+cards.map(x=>stat(x[0],x[1],x[2],x[3])).join('')+'</div>'+
      '<div class="section card stack">'+
      '<h2>Estado de conexión</h2>'+
      (!device?'<div class="notice">Esta pantalla necesita la APK Android para leer el diagnóstico real.</div>':
      '<div class="meta-line"><span class="chip">Permiso: '+(device.permissionGranted?'Sí':'Falta')+
      '</span><span class="chip">Servicio: '+(device.listenerConnected?'Conectado':'Desconectado')+
      '</span><span class="chip">Reglas: '+(device.rulesSynchronized?'Sincronizadas':'Pendientes')+
      '</span></div><p class="small muted">WhatsApp: '+Number(device.eventsNormal||0)+
      ' avisos · Business: '+Number(device.eventsBusiness||0)+
      ' avisos. Son notificaciones, no mensajes únicos.</p>')+
      '<div class="row"><button class="btn soft" data-action="test-connection">Revisar conexión</button>'+
      '<button class="btn soft" data-action="notification-settings">Permisos Android</button>'+
      '<button class="btn soft" data-go="bandeja">Ver bandeja</button></div></div>'+
      '<div class="section card stack"><div class="between"><h2>Últimos eventos</h2>'+
      '<span class="pill">Sin datos personales</span></div>'+
      '<label for="diag074Filter">Filtrar eventos</label><select id="diag074Filter">'+
      labels.map(([v,name])=>'<option value="'+v+'"'+(v===filter?' selected':'')+'>'+name+'</option>').join('')+
      '</select>'+
      (recent.length?recent.map(x=>{
        const info=h.explain(x.reason),when=new Date(Number(x.at));
        const date=Number.isFinite(when.getTime())?when.toLocaleString('es-CO'):'Fecha desconocida';
        return '<article class="diagnostic-line"><div class="between">'+
          '<strong>'+safe(info.label)+'</strong><span class="pill">'+
          safe(channelNames[x.channel]||x.channel)+'</span></div>'+
          '<p class="small muted">'+safe(date)+'</p>'+
          '<p class="small">'+safe(info.advice)+'</p></article>';
      }).join(''):'<div class="empty">No hay eventos en este filtro. Envía una prueba desde otro teléfono.</div>')+
      '<p class="tiny muted">No se envía ningún mensaje desde este panel. Una respuesta '+
      'enviada a Android no demuestra que WhatsApp la haya entregado.</p></div>';
  }
'''
change(app,'''  function renderActivity(){''',render+'''  function renderActivity(){''',
"diagnostic page function")
change(app,'''const h=({ventas360:renderSales360''',
'''const h=({diagnostico074:renderDiagnostics074,ventas360:renderSales360''',
"render diagnostic route")
change(app,'''    if(t.id==='sales360Filter'){runtime.sales360Filter=t.value;render();return;}''',
'''    if(t.id==='diag074Filter'){runtime.diagnostics074Filter=t.value;render();return;}
    if(t.id==='sales360Filter'){runtime.sales360Filter=t.value;render();return;}''',
"diagnostic filtering")
change(app,'''      '<button class="btn soft" data-go="aprendizaje">Centro de aprendizaje</button>''',
'''      '<button class="btn soft" data-go="diagnostico074">🛠 Diagnóstico de respuestas</button>'+
      '<button class="btn soft" data-go="aprendizaje">Centro de aprendizaje</button>''',
"activity links diagnostics")
change(app,'''AutoResponder Pro v0.6.13''','''AutoResponder Pro v0.6.14''',
"app version marker")
style=web/"styles.css"
style.write_text(style.read_text(encoding="utf-8")+r'''
/* Diagnóstico de respuestas · adaptado a móvil, sin tablas horizontales. */
.diagnostic-line{padding:13px 0;border-bottom:1px solid var(--line, #293436);
 overflow-wrap:anywhere}
.diagnostic-line:last-of-type{border-bottom:0}
.diagnostic-line .between{flex-wrap:wrap;align-items:flex-start;gap:8px}
.diagnostic-line .pill{white-space:normal;line-height:1.35;max-width:100%}
.diagnostic-line p{margin:7px 0 0}
''',encoding="utf-8")
for name in ["index.html","app.js","diagnostics-074.js","styles.css"]:
    (assets/name).write_text((web/name).read_text(encoding="utf-8"),encoding="utf-8")
print("0.6.14 diagnostics page: safe local events, reasons, suggested actions and filters.")
