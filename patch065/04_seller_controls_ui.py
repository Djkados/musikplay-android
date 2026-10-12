from pathlib import Path
root=Path("source/autoresponder-pro")
p=root/"web/app.js"
s=p.read_text(encoding="utf-8")
def rep(old,new):
 global s
 assert s.count(old)==1,("web UI mismatch",old[:85],s.count(old))
 s=s.replace(old,new,1)

rep('''  function humanBadge(entry){''',
'''  function sellerBadge(entry){
    const seller=sellerFor(entry.channel,entry.contact);
    return seller?'<div class="notice">👤 *Vendedor / revendedor* · '+
      safe(labelFor(seller.assistant))+
      '. Solo agradecimientos y medios de pago; el resto lo atiendes tú.</div>':'';
  }
  function humanBadge(entry){''')
rep('''${humanBadge(i)}<div class="row">''',
'''${sellerBadge(i)}${humanBadge(i)}<div class="row">''')
rep('''<button class="btn mini soft" data-pause-inbox="${safe(i.id)}">✋ Atender personalmente</button>''',
'''<button class="btn mini soft" data-seller-inbox="${safe(i.id)}">${sellerFor(i.channel,i.contact)?'Quitar modo vendedor':'👤 Marcar vendedor'}</button>
    <button class="btn mini soft" data-pause-inbox="${safe(i.id)}">✋ Atender personalmente</button>''')
rep('''<option value="120">2 horas</option><option value="-1">Hasta reactivar</option>''',
'''<option value="120">2 horas</option><option value="180">3 horas</option><option value="-1">Hasta reactivar</option>''')
rep('''    if(button.dataset.pauseInbox){''',
'''    if(button.dataset.sellerInbox){
      const msg=state.inbox.find(i=>i.id===button.dataset.sellerInbox);
      if(!msg)return;
      const current=sellerFor(msg.channel,msg.contact);
      if(current){
        state.sellerContacts=state.sellerContacts.filter(x=>x!==current);
        save();render();notify("Se quitó el modo vendedor de este chat.");return;
      }
      state.sellerContacts.push({id:token(),channel:msg.channel,
        contact:msg.contact,phone:"",assistant:"movieplay"});
      save();render();
      notify("Vendedor MoviePlay: solo gracias y pagos. Puedes cambiar el negocio en Contactos.");
      return;
    }
    if(button.dataset.pauseInbox){''')
rep('''      if(![30,60,120,-1].includes(minutes))return notify("Tiempo de pausa inválido.");''',
'''      if(![30,60,120,180,-1].includes(minutes))return notify("Tiempo de pausa inválido.");''')
rep('''  function renderSettings(){return cadenceSettingsPanel()+''',
'''  function sellerSettingsPanel(){
    const minutes=Number(state.settings.humanReplyPauseMinutes||180);
    return '<div class="card stack" style="margin-bottom:16px">'+
      '<h2>✋ Cuando yo respondo personalmente</h2>'+
      '<p class="small muted">Si WhatsApp informa a Android que enviaste un mensaje manual, '+
      'pausa las respuestas habituales en ese chat. Para vendedores solo quedan '+
      'agradecimientos y medios de pago, incluso durante la pausa.</p>'+
      '<div class="form-control"><label>Duración de la pausa automática</label>'+
      '<select id="humanReplyPauseMinutes">'+
      '<option value="120"'+(minutes===120?' selected':'')+'>2 horas</option>'+
      '<option value="180"'+(minutes===180?' selected':'')+'>3 horas</option>'+
      '</select></div>'+
      '<div class="notice">WhatsApp no siempre genera notificaciones de tus mensajes enviados. '+
      'Marca a los vendedores desde la bandeja para garantizar el silencio del catálogo.</div>'+
      '</div>';
  }
  function renderSettings(){return sellerSettingsPanel()+cadenceSettingsPanel()+''')
rep('''    if(t.dataset.cadence){''',
'''    if(t.id==="humanReplyPauseMinutes"){
      const minutes=Number(t.value);
      if(![120,180].includes(minutes))return notify("Elige 2 o 3 horas.");
      state.settings.humanReplyPauseMinutes=minutes;
      save();render();notify("Pausa automática configurada.");return;
    }
    if(t.dataset.cadence){''')
p.write_text(s,encoding="utf-8")
(root/"android/app/src/main/assets/app.js").write_text(s,encoding="utf-8")
print("Per-conversation one-tap vendor classification, human-handoff interval 2/3h and vendor-only inbox badge added.")
