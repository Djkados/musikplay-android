from pathlib import Path
root=Path("source/autoresponder-pro")
p=root/"web/app.js"
s=p.read_text(encoding="utf-8")
def rep(a,b):
 global s
 assert s.count(a)==1,("web anchor",a[:85],s.count(a))
 s=s.replace(a,b,1)

rep("    exceptions:[], allowlist:[], blocked:[], paused:[],",
    "    exceptions:[], sellerContacts:[], allowlist:[], blocked:[], paused:[],")
rep("  state.learningSuggestions ||= [];",
    "  state.learningSuggestions ||= [];\n  state.sellerContacts ||= [];")
rep('''  state.settings.cadence ||= {menuHours:12,awayHours:12,greetingHours:12,
    courtesyMinutes:15,repeatMinutes:2};''',
'''  state.settings.cadence ||= {menuHours:12,awayHours:12,greetingHours:12,
    courtesyMinutes:15,repeatMinutes:2};
  state.settings.humanReplyPauseMinutes ||= 180;''')
rep("const {channel,assistants,exceptions,allowlist,blocked,paused,rules,catalog,payments,schedules,scheduleOverrides,settings}=state;",
    "const {channel,assistants,exceptions,sellerContacts,allowlist,blocked,paused,rules,catalog,payments,schedules,scheduleOverrides,settings}=state;")
rep("JSON.stringify({version:1,channel,assistants,exceptions,allowlist,blocked,paused,rules,catalog,payments,schedules,scheduleOverrides,settings})",
    "JSON.stringify({version:1,channel,assistants,exceptions,sellerContacts,allowlist,blocked,paused,rules,catalog,payments,schedules,scheduleOverrides,settings})")
rep("  function assignmentFor(channel,contact,message=''){",
'''  function sellerFor(channel,contact){
    return (state.sellerContacts||[]).find(x=>x.channel===channel&&sameContact(x,contact))||null;
  }
  function assignmentFor(channel,contact,message=''){''')
rep("""${type==='exceptions'?' → '+labelFor(x.assistant):''}""",
    """${type==='exceptions'||type==='sellerContacts'?' → '+labelFor(x.assistant):''}${type==='sellerContacts'?' · Solo gracias y pagos':''}""")
rep('''<div class="stack"><div class="card"><h2>Excepciones por contacto</h2>''',
'''<div class="stack"><div class="card"><h2>👤 Vendedores y revendedores</h2>
      <p class="small muted">A estos contactos solo se les responde agradecimientos y solicitudes de pago del negocio seleccionado.
      No se envían listas de precios al público, menús, bienvenidas ni avisos de ausencia.
      Esta protección no depende de que WhatsApp detecte tus respuestas enviadas.</p>
      ${lines(state.sellerContacts||[],'sellerContacts')}</div>
      <div class="card"><h2>Excepciones por contacto</h2>''')
rep('''<option value="exceptions">Asignar asistente</option><option value="blocked">No responder</option>''',
'''<option value="exceptions">Asignar asistente</option>
          <option value="sellerContacts">Vendedor / Revendedor · Solo gracias y pagos</option>
          <option value="blocked">No responder</option>''')
rep('''<div class="form-control" id="ctAssistantRow" hidden><label for="ctAssistant">Asistente para este contacto</label>''',
'''<div class="form-control" id="ctAssistantRow" hidden><label for="ctAssistant">Negocio asignado a este contacto</label>''')
rep("const row=$('#ctAssistantRow');if(row)row.hidden=e.target.value!=='exceptions';",
'''const row=$('#ctAssistantRow');
      if(row)row.hidden=!['exceptions','sellerContacts'].includes(e.target.value);''')
rep("      const list=state[type];if(!Array.isArray(list))return;",
'''      const list=state[type];if(!Array.isArray(list))return;
      if(type==='sellerContacts' && !['movieplay','tresm'].includes(assistant))
        return notify('Elige MoviePlay o Las Tres M para este vendedor.');''')
rep("Se reactivan después de una hora.",
    "Se reactivan según el tiempo seleccionado.")
# Seller only mode must not be overridden by local generic pause simulation.
rep('''    if ((state.paused||[]).some(x=>x.channel===channel&&sameContact(x,contact)&&x.until>Date.now())) return {reason:'Conversación pausada manualmente.'};''',
'''    if (!sellerFor(channel,contact) &&
      (state.paused||[]).some(x=>x.channel===channel&&sameContact(x,contact)&&x.until>Date.now()))
      return {reason:'Conversación pausada manualmente.'};''')
rep('''    const thanks=courtesyReply(text);
    if(thanks)return {reply:thanks,assistant:null,unit:null,
      method:"courtesy",status:"open",image:null};
    const assign=assignmentFor(channel,contact,text);''',
'''    const thanks=courtesyReply(text);
    if(thanks)return {reply:thanks,assistant:null,unit:null,
      method:"courtesy",status:"open",image:null};
    const seller=sellerFor(channel,contact);
    if(seller){
      const payment=paymentAnswer(seller.assistant,text,true);
      if(payment)return {reply:payment,assistant:seller.assistant,unit:"sales",
        method:"seller_payment",status:"open",image:null};
      return {reason:"Vendedor: atención humana. Solo agradecimientos y medios de pago.",
        assistant:seller.assistant,method:"seller_human"};
    }
    const assign=assignmentFor(channel,contact,text);''')
s=s.replace("AutoResponder Pro v0.6.4","AutoResponder Pro v0.6.5",1)
p.write_text(s,encoding="utf-8")
(root/"android/app/src/main/assets/app.js").write_text(s,encoding="utf-8")
print("Explicit seller role in contact manager and synced native config; seller chat simulator is silent except thanks/payments.")
