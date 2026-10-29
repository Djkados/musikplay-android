from pathlib import Path
root=Path("source/autoresponder-pro")
web=root/"web"
def change(path,old,new,label):
 s=path.read_text(encoding="utf-8")
 assert s.count(old)==1,(label,s.count(old))
 path.write_text(s.replace(old,new,1),encoding="utf-8")

(web/"sales-360.js").write_text(r'''/* AutoResponder Pro · Ventas 360 · no external services or automated follow-ups. */
(function(root,factory){const api=factory();
if(typeof module==='object'&&module.exports)module.exports=api;
if(root)root.Sales360Helper=api;})(typeof window!=='undefined'?window:null,function(){
'use strict';
const stages={
  quote_prepared:'Cotización preparada',
  quoted:'Cotización enviada (sin confirmar entrega)',
  payment_prepared:'Pago preparado (sin envío)',
  payment_requested:'Medios de pago enviados (sin confirmar entrega)',
  review:'Comprobante o archivo por revisar',
  confirmed:'Venta confirmada manualmente',
  lost:'No concretada',
  opt_out:'No contactar'
};
const closed=new Set(['confirmed','lost','opt_out']);
const metrics=items=>{
  const rows=Array.isArray(items)?items:[];
  return {
    quoted:rows.filter(x=>x.quote).length,
    payment:rows.filter(x=>['payment_prepared','payment_requested','review'].includes(x.stage)).length,
    review:rows.filter(x=>x.stage==='review').length,
    confirmed:rows.filter(x=>x.stage==='confirmed').length,
    pending:rows.filter(x=>!closed.has(x.stage)).length
  };
};
const followup=lead=>{
  if(!lead || closed.has(lead.stage)||lead.stage==='review')return null;
  if(['payment_requested','payment_prepared'].includes(lead.stage))
    return '¡Hola! 😊 Soy de MoviePlay. ¿Pudiste revisar los medios de pago de tu pedido? Si tienes alguna duda, con gusto te ayudo. Si prefieres no recibir más seguimientos, dímelo y lo respetamos.';
  return '¡Hola! 😊 Soy de MoviePlay. ¿Te puedo ayudar con alguna duda sobre la cotización que te compartimos? Si ya no la necesitas, me dices y no te volvemos a escribir sobre ella. 💚';
};
return {stages,closed,metrics,followup};
});
''',encoding="utf-8")
change(web/"index.html",'''  <script src="netflix-international.js"></script>
  <script src="app.js"></script>''','''  <script src="netflix-international.js"></script>
  <script src="sales-360.js"></script>
  <script src="app.js"></script>''',"Sales360 scripts")
change(web/"index.html",'''        <button class="navbtn" data-route="ventas"><span>💚</span> Asistente de ventas</button>''',
'''        <button class="navbtn" data-route="ventas"><span>💚</span> Asistente de ventas</button>
        <button class="navbtn" data-route="ventas360"><span>🛒</span> Ventas 360 · Seguimiento</button>''',"Sales360 menu")
change(web/"index.html",'''Versión 0.6.11 · Autotexto opcional''',
'''Versión 0.6.12 · Ventas 360''',"Sales360 version footer")
p=web/"app.js"
change(p,'''  const runtime = {comboSimulation:new Map(),''',
'''  let sales360Rows=[];
  const runtime = {sales360Filter:"pending",comboSimulation:new Map(),''',"Sales360 state")
change(p,'''  const headings = {ventas:['VENTAS / MÁS AHORRO','Asistente de ventas'],''',
'''  const headings = {ventas360:['VENTAS / SEGUIMIENTO','Ventas 360'],ventas:['VENTAS / MÁS AHORRO','Asistente de ventas'],''',"Sales360 header")
fn=r'''
  function refreshSales360(){
    if(!native || typeof window.AndroidBridge.getSales360!=='function')return;
    try{
      const parsed=JSON.parse(window.AndroidBridge.getSales360());
      if(Array.isArray(parsed))sales360Rows=parsed.slice(0,120);
    }catch(error){console.warn('Ventas 360 sin datos',error);}
  }
  function renderSales360(){
    refreshSales360();
    const h=window.Sales360Helper,m=h.metrics(sales360Rows);
    const filter=runtime.sales360Filter;
    const rows=sales360Rows.filter(x=>filter==='all'||
      (filter==='pending'&&!h.closed.has(x.stage))||x.stage===filter);
    const actions=x=>{
      const id=safe(x.id);
      const basic='<button class="btn mini soft" data-sales-action="followup:'+id+'">Seguimiento manual</button>';
      if(x.stage==='opt_out')return '<button class="btn mini soft" data-sales-action="delete:'+id+'">Eliminar</button>';
      if(x.stage==='confirmed'||x.stage==='lost')
        return '<button class="btn mini soft" data-sales-action="reopen:'+id+'">Reabrir</button>'+
          '<button class="btn mini danger" data-sales-action="delete:'+id+'">Eliminar</button>';
      return (x.stage!=='review'?basic:'')+
        '<button class="btn mini primary" data-sales-action="confirmed:'+id+'">✓ Venta confirmada</button>'+
        '<button class="btn mini soft" data-sales-action="lost:'+id+'">No concretada</button>'+
        '<button class="btn mini danger" data-sales-action="opt_out:'+id+'">No contactar</button>';
    };
    return '<div class="home-intro"><div><span class="pill">MOVIEPLAY · VENTAS 360</span>'+
      '<h2>Oportunidades y pagos pendientes</h2>'+
      '<p>Registro local de los últimos 30 días. Los envíos desde Android no prueban entrega '+
      'y los pagos se verifican manualmente. No enviamos seguimientos sin tu acción.</p></div></div>'+
      '<div class="grid cols3">'+
      stat('Cotizaciones',m.quoted,'Con resumen preparado o enviado','📋')+
      stat('Solicitaron pago',m.payment,'Incluye comprobantes por verificar','💳')+
      stat('Por revisar',m.review,'Nunca se confirma automáticamente','🔎')+
      stat('Ventas confirmadas',m.confirmed,'Solo confirmación manual','✓')+
      stat('Oportunidades abiertas',m.pending,'Pendientes en el dispositivo','🛒')+'</div>'+
      '<div class="section"><div class="card stack"><div class="between">'+
      '<div><h2>Bandeja de oportunidades</h2><p class="small muted">Cada registro corresponde a un chat, '+
      'no a una venta contable. El historial se elimina automáticamente a los 30 días.</p></div>'+
      '<button class="btn mini soft" data-action="refresh-sales360">↻ Actualizar</button></div>'+
      '<div class="form-control"><label>Filtrar</label><select id="sales360Filter">'+
      [['pending','Pendientes'],['all','Todas'],['review','Comprobantes'],['confirmed','Confirmadas'],['lost','No concretadas'],['opt_out','No contactar']]
        .map(option=>'<option value="'+option[0]+'"'+(filter===option[0]?' selected':'')+'>'+option[1]+'</option>').join('')+
      '</select></div>'+
      (native?rows.length?rows.map(x=>'<article class="card sales-lead">'+
        '<div class="between"><strong>'+safe(x.contact||'Cliente')+'</strong><span class="pill">'+
          safe(h.stages[x.stage]||'En seguimiento')+'</span></div>'+
        '<p class="tiny muted">'+safe(channelNames[x.channel]||x.channel)+
          ' · '+(Number(x.updatedAt)>0?new Date(x.updatedAt).toLocaleString('es-CO'):'Sin fecha')+
          (Number(x.total)>0?' · Combo $'+Number(x.total).toLocaleString('es-CO'):'')+'</p>'+
        (x.quote?'<details><summary>Ver cotización / pedido preparado</summary>'+
          '<p class="message" style="white-space:pre-wrap">'+safe(x.quote)+'</p></details>':'')+
        (x.stage==='review'?'<p class="notice">⚠️ Archivo recibido: revisar pago y titular en WhatsApp antes de entregar.</p>':'')+
        '<div class="row top-space">'+actions(x)+'</div></article>').join(''):
        '<div class="empty">No hay oportunidades en este filtro todavía.</div>':
        '<div class="empty">La bandeja de seguimiento funciona dentro de la aplicación Android. '+
        'El simulador web no registra ventas reales.</div>')+
      '<p class="tiny muted">El botón de seguimiento abre WhatsApp para que elijas destinatario y confirmes el envío. '+
      'Respeta solicitudes de no contacto. No se envían mensajes automáticos a clientes inactivos.</p>'+
      '</div></div>';
  }
'''
change(p,'''  function renderPayments(){''',fn+'''  function renderPayments(){''',"Ventas360 renderer")
change(p,'''const h=({ventas:renderSales,inicio:renderHome''',
'''const h=({ventas360:renderSales360,ventas:renderSales,inicio:renderHome''',"Ventas360 render switch")
change(p,'''  async function loadNative(){if(!native)return;try{const json=window.AndroidBridge.getInbox();''',
'''  async function loadNative(){if(!native)return;refreshSales360();try{const json=window.AndroidBridge.getInbox();''',"Ventas360 data reload")
change(p,'''    const button=e.target.closest('button');if(!button)return;''',
'''    const button=e.target.closest('button');if(!button)return;
    if(button.dataset.salesAction){
      const [action,id]=button.dataset.salesAction.split(':');
      const lead=sales360Rows.find(x=>x.id===id);
      if(!lead || !native || !window.AndroidBridge.setSales360Status)return notify('Registro no disponible.');
      if(action==='followup'){
        const msg=window.Sales360Helper.followup(lead);
        if(!msg)return notify('No es apropiado contactar este registro.');
        if(!confirm('Verifica consentimiento y destinatario de '+lead.contact+
           '. La aplicación no enviará el mensaje sin tu confirmación en WhatsApp. ¿Continuar?'))return;
        shareText(msg,lead.channel);return;
      }
      const prompts={
        confirmed:'¿Verificaste el pago y la entrega por tu cuenta? Este botón NO comprueba pagos.',
        lost:'¿Marcar esta oportunidad como no concretada?',
        opt_out:'¿Marcar como NO CONTACTAR? No se sugerirá seguimiento.',
        reopen:'¿Reabrir este seguimiento?',
        delete:'¿Eliminar definitivamente este registro local?'
      };
      if(!prompts[action]||!confirm(prompts[action]))return;
      if(!window.AndroidBridge.setSales360Status(id,action))
        return notify('No se pudo guardar el estado.');
      refreshSales360();render();notify('Estado actualizado en Ventas 360.');return;
    }
''',"Ventas360 interactions")
change(p,'''    if(a==='refresh-inbox'){''',
'''    if(a==='refresh-sales360'){refreshSales360();render();notify('Seguimiento actualizado.');return;}
    if(a==='refresh-inbox'){''',"Ventas360 refresh")
change(p,'''    if(t.id==='ovMode'){''',
'''    if(t.id==='sales360Filter'){runtime.sales360Filter=t.value;render();return;}
    if(t.id==='ovMode'){''',"Ventas360 filter")
styles=web/"styles.css"
styles.write_text(styles.read_text(encoding="utf-8")+"""
/* Ventas 360: mobile-first cards and actions without horizontal clipping. */
.sales-lead .between{flex-wrap:wrap;align-items:flex-start}
.sales-lead .between strong{min-width:0;overflow-wrap:anywhere;flex:1}
.sales-lead .pill{white-space:normal;max-width:100%;line-height:1.4}
.sales-lead .row{flex-wrap:wrap;align-items:stretch}
.sales-lead .row .btn{min-height:42px;white-space:normal;text-align:center}
.sales-lead summary{cursor:pointer;font-size:12px;color:#8eeaba;margin:8px 0}
.sales-lead details[open] .message{max-height:270px;overflow:auto}
@media(max-width:700px){.sales-lead .row .btn{flex:1 1 135px}}
""",encoding="utf-8")
for name in ["index.html","app.js","sales-360.js"]:
    (root/"android/app/src/main/assets"/name).write_text(
        (web/name).read_text(encoding="utf-8"),encoding="utf-8")
(root/"android/app/src/main/assets/styles.css").write_text(styles.read_text(encoding="utf-8"),encoding="utf-8")
print("0.6.12 sales dashboard: isolated native leads, manual WhatsApp follow-up and statuses.")
