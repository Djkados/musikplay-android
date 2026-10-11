from pathlib import Path
root=Path("source/autoresponder-pro")
p=root/"web/app.js"
s=p.read_text(encoding="utf-8")
def change(a,b):
 global s
 assert s.count(a)==1,(a[:80],s.count(a))
 s=s.replace(a,b,1)
change("const headings = {automatizacion:", "const headings = {catalogo:['CONTENIDO / CATÁLOGO','Productos y precios'],automatizacion:")
change("const runtime = {route:'inicio',", "const runtime = {catalogEdit:null,route:'inicio',")
before="  function renderRules(){"
ui='''  function renderCatalog() {
    const editing=state.catalog.find(x=>x.id===runtime.catalogEdit) || {};
    const select=(v,k,label)=>'<option value="'+k+'"'+(v===k?' selected':'')+'>'+label+'</option>';
    const field=(id,label,value,type="text")=>'<div class="form-control"><label for="'+id+'">'+label+
      '</label><input class="field" id="'+id+'" type="'+type+'" value="'+safe(value??"")+'"></div>';
    const price=n=>Number(n)>0?'$'+Number(n).toLocaleString('es-CO'):'Sin precio configurado';
    const card=i=>'<article class="card stack"><div class="between"><div><span class="pill">'+
      (i.assistant==="movieplay"?"🎬 MoviePlay":"🍔 Las Tres M")+'</span><h2 class="top-space">'+safe(i.name)+
      '</h2><p class="small muted">'+safe(i.duration||i.type)+' · '+price(i.price)+'</p></div>'+
      '<input type="checkbox" class="toggle" data-catalog-toggle="'+safe(i.id)+'"'+(i.active?' checked':'')+'></div>'+
      (Number(i.salePrice)>0?'<span class="chip">Oferta: '+price(i.salePrice)+
      (i.offerUntil?' hasta '+safe(i.offerUntil):' sin fecha de vencimiento')+'</span>':'')+
      '<p class="tiny muted">Palabras clave: '+safe(i.keywords)+'</p><div class="row">'+
      '<button class="btn soft mini" data-catalog-edit="'+safe(i.id)+'">Editar</button>'+
      '<button class="btn danger mini" data-catalog-delete="'+safe(i.id)+'">Eliminar</button></div></article>';
    return '<div class="home-intro"><div><span class="pill">DATOS LOCALES · SIN API</span>'+
      '<h2>Catálogo y precios automáticos</h2>'+
      '<p class="small muted">Edita el valor una sola vez: se sincronizará con las respuestas que envía Android. '+
      'No se inventan precios, ofertas ni disponibilidad.</p></div></div>'+
      '<div class="card stack"><h2>'+(editing.id?'Editar producto o combo':'Agregar producto o combo')+'</h2>'+
      '<div class="grid cols2"><div class="form-control"><label>Negocio</label><select id="catAssistant">'+
      select(editing.assistant||'movieplay','movieplay','🎬 MoviePlay')+
      select(editing.assistant||'movieplay','tresm','🍔 Las Tres M')+'</select></div>'+
      '<div class="form-control"><label>Tipo</label><select id="catType">'+
      select(editing.type||'service','service','Servicio')+
      select(editing.type||'service','combo','Combo')+
      select(editing.type||'service','food','Comida')+'</select></div></div>'+
      '<div class="grid cols2">'+field('catName','Nombre del producto / combo',editing.name||'')+
      field('catDuration','Duración (si aplica)',editing.duration||'')+'</div>'+
      '<div class="grid cols2">'+field('catPrice','Precio en COP, sin puntos',editing.price||'','number')+
      field('catOffer','Precio oferta, opcional',editing.salePrice||'','number')+'</div>'+
      '<div class="grid cols2">'+field('catUntil','Oferta válida hasta',editing.offerUntil||'','date')+
      field('catImage','Etiqueta de imagen',editing.imageTag||'')+'</div>'+
      field('catKeywords','Palabras clave separadas por comas',editing.keywords||'')+
      '<p class="tiny muted">Solo se mostrarán ofertas con fecha vigente y valor inferior al precio normal. '+
      'Las imágenes se abren para revisión, nunca se envían solas.</p>'+
      '<div class="row"><button class="btn primary" data-action="catalog-save">'+
      (editing.id?'Actualizar producto':'Agregar al catálogo')+'</button>'+
      (editing.id?'<button class="btn soft" data-action="catalog-cancel">Cancelar edición</button>':'')+
      '</div></div>'+
      '<div class="section"><h2 class="section-title">Productos activos y disponibles para editar</h2>'+
      '<div class="grid cols2">'+state.catalog.map(card).join('')+'</div></div>';
  }
'''
assert s.count(before)==1
s=s.replace(before,ui+before,1)
change("contactos:renderContacts,reglas:renderRules,imagenes:", "contactos:renderContacts,reglas:renderRules,catalogo:renderCatalog,imagenes:")
needle="    if(a==='new-rule'){runtime.route='rule-edit';"
actions='''    if(a==='catalog-cancel'){runtime.catalogEdit=null;render();return;}
    if(button.dataset.catalogEdit){
      runtime.catalogEdit=button.dataset.catalogEdit;render();return;
    }
    if(button.dataset.catalogDelete){
      if(!confirm('¿Eliminar este producto del catálogo?'))return;
      state.catalog=state.catalog.filter(x=>x.id!==button.dataset.catalogDelete);
      if(runtime.catalogEdit===button.dataset.catalogDelete)runtime.catalogEdit=null;
      save();render();notify('Producto eliminado.');return;
    }
    if(a==='catalog-save'){
      const name=$('#catName').value.trim(),keywords=$('#catKeywords').value.trim();
      const price=Number($('#catPrice').value||0),offer=Number($('#catOffer').value||0);
      const until=$('#catUntil').value;
      if(name.length<3||name.length>90||!keywords)return notify('Escribe un nombre y palabras clave.');
      if(!Number.isSafeInteger(price)||price<0||!Number.isSafeInteger(offer)||offer<0)
        return notify('Los precios deben ser números enteros no negativos.');
      if(offer>0 && (price===0||offer>=price||!until))
        return notify('La oferta necesita un precio menor al normal y fecha de vencimiento.');
      const prev=state.catalog.find(x=>x.id===runtime.catalogEdit);
      const product={
        id:prev?.id||token(),assistant:$('#catAssistant').value,type:$('#catType').value,
        name,duration:$('#catDuration').value.trim().slice(0,50),price,salePrice:offer,
        offerUntil:until,keywords:keywords.slice(0,300),
        imageTag:$('#catImage').value.trim().slice(0,60),active:prev?.active??true
      };
      if(prev)Object.assign(prev,product);else state.catalog.push(product);
      runtime.catalogEdit=null;save();render();notify('Catálogo actualizado y sincronizado.');return;
    }
'''
assert s.count(needle)==1
s=s.replace(needle,actions+needle,1)
needle="    if(t.dataset.ruleToggle){"
toggle='''    if(t.dataset.catalogToggle){
      const p=state.catalog.find(x=>x.id===t.dataset.catalogToggle);
      if(p){p.active=t.checked;save();render();}return;
    }
'''
assert s.count(needle)==1
s=s.replace(needle,toggle+needle,1)
p.write_text(s,encoding="utf-8")
(root/"android/app/src/main/assets/app.js").write_text(s,encoding="utf-8")
p=root/"web/index.html";s=p.read_text(encoding="utf-8")
needle='<button class="navbtn" data-route="reglas"><span>≡</span> Respuestas y reglas</button>'
assert s.count(needle)==1
s=s.replace(needle,needle+'\n        <button class="navbtn" data-route="catalogo"><span>＄</span> Catálogo y precios</button>',1)
s=s.replace('Modo seguro de pruebas.</strong> Los mensajes automáticos de texto están APAGADOS por defecto y requieren activación independiente por canal y contacto autorizado.',
'''Modo de respuesta controlada.</strong> Los mensajes automáticos requieren activación por WhatsApp, no necesitan autorización individual si la lista restrictiva está desactivada.''')
s=s.replace('Versión 0.5 · Autotexto opcional','Versión 0.5.9 · Autotexto opcional')
p.write_text(s,encoding="utf-8")
(root/"android/app/src/main/assets/index.html").write_text(s,encoding="utf-8")
print("Catalog editor and accessible Android navigation created")
