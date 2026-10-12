from pathlib import Path
root=Path("source/autoresponder-pro")
p=root/"web/app.js";s=p.read_text(encoding="utf-8")
def rep(a,b,why):
 global s
 a=a.replace("§{","$"+"{");b=b.replace("§{","$"+"{")
 assert s.count(a)==1,(why,s.count(a),a[:95])
 s=s.replace(a,b,1)

rep("const headings = {aprendizaje:",
    "const headings = {vendedores:['CONTACTOS / VENDEDORES','Vendedores y revendedores'],aprendizaje:",
    "new heading")
rep("contactos:renderContacts,reglas:renderRules,",
    "contactos:renderContacts,vendedores:renderVendors,reglas:renderRules,",
    "render vendors route")
marker="  function renderCatalog() {"
assert s.count(marker)==1
ui='''  function renderVendors(){
    const people=state.sellerContacts||[];
    const optsVendor=(value)=>'<option value="movieplay"'+(value==="movieplay"?' selected':'')+
      '>🎬 MoviePlay</option><option value="tresm"'+(value==="tresm"?' selected':'')+'>🍔 Las Tres M</option>';
    const card=x=>'<article class="card stack">'+
      '<div class="between"><strong>👤 '+safe(x.contact||x.phone)+'</strong>'+
      '<span class="pill">Vendedor / Revendedor</span></div>'+
      (x.phone&&x.phone!==x.contact?'<p class="tiny muted">☎ '+safe(x.phone)+'</p>':'')+
      '<p class="small muted">'+safe(channelNames[x.channel])+
      ' · Solo agradecimientos, renovación y medios de pago</p>'+
      '<div class="form-control"><label>Negocio asociado</label>'+
      '<select class="field" data-vendor-business="'+safe(x.id)+'">'+
      optsVendor(x.assistant)+'</select></div>'+
      '<div class="row"><button class="btn soft mini" data-edit-vendor="'+safe(x.id)+
      '">Editar</button>'+
      '<button class="btn danger mini" data-delete-contact="sellerContacts:'+safe(x.id)+
      '">Quitar vendedor</button></div></article>';
    return '<div class="home-intro"><div><span class="pill">PRIORIDAD HUMANA</span>'+
      '<h2>👤 Vendedores y revendedores</h2>'+
      '<p>Aquí registras a quienes atiendes personalmente. No recibirán catálogos, menús, '+
      'saludos ni avisos de horario. Solo agradecimientos, renovación y medios de pago.</p>'+
      '</div></div>'+
      '<div class="grid cols2"><div class="card stack" id="vendorEditor">'+
      '<h2>+ Agregar vendedor</h2>'+
      (native?'<button class="btn soft" data-action="pick-contact">♧ Elegir de mis contactos Android</button>':'')+
      '<div class="form-control"><label>Nombre visible en WhatsApp</label>'+
      '<input id="vendorName" class="field" autocomplete="off" placeholder="Ej. Carlos, revendedor"></div>'+
      '<div class="form-control"><label>Teléfono (opcional si escribiste nombre)</label>'+
      '<input id="vendorPhone" class="field" type="tel" inputmode="tel" placeholder="Ej. 300 123 4567"></div>'+
      '<div class="form-control"><label>WhatsApp donde te escribe</label>'+
      '<select id="vendorChannel" class="field"><option value="business">WhatsApp Business</option>'+
      '<option value="normal">WhatsApp normal</option></select></div>'+
      '<div class="form-control"><label>Negocio del vendedor</label>'+
      '<select id="vendorBusiness" class="field">'+optsVendor("movieplay")+'</select></div>'+
      '<button class="btn primary" data-action="save-vendor">Guardar vendedor</button>'+
      '<div class="notice">Si WhatsApp muestra el nombre guardado en una notificación, '+
      'escríbelo también para identificar correctamente ese chat. '+
      'El mismo contacto puede estar registrado en ambos WhatsApp.</div></div>'+
      '<div class="stack"><div class="section-header"><h2>Registrados ('+people.length+')</h2>'+
      '<button class="btn soft mini" data-go="bandeja">Ver bandeja</button></div>'+
      (people.length?people.map(card).join(''):
      '<div class="empty">Todavía no hay vendedores. Agrégalos arriba, incluso si no han escrito.</div>')+
      '</div></div>';
  }
'''
s=s.replace(marker,ui+marker,1)

rep('<div class="stack"><div class="card"><h2>👤 Vendedores y revendedores</h2>',
    '<div class="stack"><div class="card"><div class="between"><h2>👤 Vendedores y revendedores</h2>'+
    '<button class="btn primary" data-go="vendedores">+ Administrar vendedores</button></div>',
    "contact list vendor entry")
rep('<button class="btn soft" data-go="horarios">Gestionar horarios →</button>',
    '<button class="btn soft" data-go="horarios">Gestionar horarios →</button>'+
    '<button class="btn primary" data-go="vendedores">👤 Mis vendedores</button>',
    "home shortcut")
rep('<button class="btn soft" data-action="refresh-inbox">↻ Actualizar</button>',
    '<div class="row"><button class="btn primary" data-go="vendedores">👤 Vendedores</button>'+
    '<button class="btn soft" data-action="refresh-inbox">↻ Actualizar</button></div>',
    "inbox shortcut")
rep('<span class="pill">§{safe(channelNames[i.channel]||i.channel)}</span></div><p class="message top-space">',
    '<span class="pill">§{safe(channelNames[i.channel]||i.channel)}</span></div>'+
    '<div class="row top-space"><button class="btn primary mini" data-seller-inbox="§{safe(i.id)}">'+
    "§{sellerFor(i.channel,i.contact)?'✓ Vendedor · quitar':'👤 Marcar vendedor'}</button></div>"+
    '<p class="message top-space">',
    "prominent inbox button")
rep('<button class="btn mini soft" data-seller-inbox="§{safe(i.id)}">§{sellerFor(i.channel,i.contact)?\'Quitar modo vendedor\':\'👤 Marcar vendedor\'}</button>',
    '',"remove duplicate buried action")
rep("if(runtime.route!=='contactos')return;",
    "if(!['contactos','vendedores'].includes(runtime.route))return;",
    "Android contact picker")
rep("    if($('#ctPhone'))$('#ctPhone').value=phone;",
    "    if($('#ctPhone'))$('#ctPhone').value=phone;\n    if($('#vendorPhone'))$('#vendorPhone').value=phone;",
    "picked number")
rep("    if($('#ctName'))$('#ctName').value=name;",
    "    if($('#ctName'))$('#ctName').value=name;\n    if($('#vendorName'))$('#vendorName').value=name;",
    "picked name")
p.write_text(s,encoding="utf-8")
(root/"android/app/src/main/assets/app.js").write_text(s,encoding="utf-8")
for name in ["web/index.html","android/app/src/main/assets/index.html"]:
 p=root/name;h=p.read_text(encoding="utf-8")
 anchor='<button class="navbtn" data-route="contactos"><span>♧</span> Contactos y excepciones</button>'
 assert h.count(anchor)==1
 h=h.replace(anchor,anchor+'\n        <button class="navbtn" data-route="vendedores"><span>👤</span> Vendedores y revendedores</button>',1)
 h=h.replace('</button>\\\\n        <button','</button>\n        <button')
 p.write_text(h,encoding="utf-8")
print("New visible seller screen linked from menu, contacts, home and inbox; Android contact picker supports it.")
