from pathlib import Path

root=Path("source/autoresponder-pro")
p=root/"web/app.js"
s=p.read_text(encoding="utf-8")
def change(old,new):
    global s
    assert s.count(old)==1,(old[:110],s.count(old))
    s=s.replace(old,new,1)

# Last recorded, user-supplied Las Tres M menu prices. Existing custom values win.
upgrade=r'''
  function upgradeCatalogPrices060(){
    const migrationKey="autoresponder_catalog_prices_v0510";
    if(localStorage.getItem(migrationKey))return;
    const prices={ham:15000,hame:20000,perro:9000,patacon:18000};
    for(const item of state.catalog){
      if(Object.hasOwn(prices,item.id) && Number(item.price||0)===0)
        item.price=prices[item.id];
      // Legacy generic Chuzo could conflate pork and chicken; replace only
      // unpriced untouched default with explicit alternatives.
      if(item.id==="chuzo" && Number(item.price||0)===0)item.active=false;
    }
    const extras=[
      {id:"perra",assistant:"tresm",type:"food",name:"Perra",duration:"",price:11000,
        keywords:"perra,perra caliente",imageTag:"perro"},
      {id:"chuzo-cerdo",assistant:"tresm",type:"food",name:"Chuzo de cerdo",duration:"",price:17000,
        keywords:"chuzo,cerdo,chuzo cerdo",imageTag:"chuzo"},
      {id:"chuzo-pollo",assistant:"tresm",type:"food",name:"Chuzo de pollo",duration:"",price:17000,
        keywords:"chuzo,pollo,chuzo pollo",imageTag:"chuzo"},
      {id:"arepa-todo",assistant:"tresm",type:"food",name:"Arepa con todo",duration:"",price:16000,
        keywords:"arepa,arepa con todo",imageTag:"arepa"},
      {id:"arepa-queso",assistant:"tresm",type:"food",name:"Arepa de queso",duration:"",price:10000,
        keywords:"arepa,arepa de queso",imageTag:"arepa"},
      {id:"chorizo-cerdo",assistant:"tresm",type:"food",name:"Chorizo de cerdo",duration:"",price:10000,
        keywords:"chorizo,chorizo cerdo",imageTag:"chorizo"},
      {id:"butifarra",assistant:"tresm",type:"food",name:"Butifarra de cordero (unidad)",duration:"",price:1000,
        keywords:"butifarra,butifarras",imageTag:"butifarra"},
      {id:"adiciones",assistant:"tresm",type:"food",name:"Adiciones",duration:"",price:4000,
        keywords:"adiciones,adicion,extra,tocineta,queso extra,pollo desmechado",imageTag:"adiciones"}
    ];
    for(const item of extras){
      if(!state.catalog.some(x=>x.id===item.id ||
         (x.assistant===item.assistant && x.name.trim().toLowerCase()===item.name.toLowerCase())))
        state.catalog.push({...item,salePrice:0,offerUntil:"",active:true});
    }
    localStorage.setItem(KEY,JSON.stringify(state));
    localStorage.setItem(migrationKey,"done");
  }
  upgradeCatalogPrices060();
'''
change("  state.catalog ||= catalogDefaults();","  state.catalog ||= catalogDefaults();\n"+upgrade)

# Put the editor under the selected product card. No scrolling to the top.
change("const card=i=>'<article class=\"card stack\"><div class=\"between\">",
       "const card=i=>'<article class=\"card stack\" data-catalog-card=\"'+safe(i.id)+'\"><div class=\"between\">")
change("'<div class=\"card stack\"><h2>'+(editing.id?'Editar producto o combo':'Agregar producto o combo')+'</h2>'+",
       "'<div id=\"catalogMainEditor\" class=\"card stack\"><h2>'+(editing.id?'Editar producto o combo':'Agregar producto o combo')+'</h2>'+")
change("state.catalog.map(card).join('')+'</div></div>';",
       "state.catalog.slice().sort((a,b)=>(a.assistant===b.assistant ? (a.name||'').localeCompare(b.name||'','es') : a.assistant==='movieplay'?-1:1)).map(card).join('')+'</div></div>';")
change("function render(){const h=",
       '''function putEditorBesideSelectedProduct(){
    if(runtime.route!=="catalogo" || !runtime.catalogEdit)return;
    const host=document.querySelector("#catalogMainEditor");
    const card=Array.from(document.querySelectorAll("[data-catalog-card]"))
      .find(node=>node.dataset.catalogCard===runtime.catalogEdit);
    if(host && card){
      host.classList.add("catalog-inline-editor");
      card.appendChild(host);
      card.classList.add("catalog-card-editing");
    }
  }
  function render(){const h=''')
change("$('#screen').innerHTML=h();$('#inboxCount').textContent=state.inbox.length;",
       "$('#screen').innerHTML=h();putEditorBesideSelectedProduct();$('#inboxCount').textContent=state.inbox.length;")
change("if(a==='catalog-cancel'){runtime.catalogEdit=null;render();return;}",
       '''if(a==='catalog-cancel'){
      const previous=runtime.catalogEdit;
      runtime.catalogEdit=null;render();
      const card=Array.from(document.querySelectorAll("[data-catalog-card]"))
        .find(n=>n.dataset.catalogCard===previous);
      card?.scrollIntoView?.({block:"nearest"});
      return;
    }''')
change("runtime.catalogEdit=button.dataset.catalogEdit;render();return;",
       '''runtime.catalogEdit=button.dataset.catalogEdit;render();
      document.querySelector("#catalogMainEditor")?.scrollIntoView?.({
        behavior:"smooth",block:"nearest"
      });return;''')
# Ensure saved prices don't override catalog entries intentionally personalized.
p.write_text(s,encoding="utf-8")
(root/"android/app/src/main/assets/app.js").write_text(s,encoding="utf-8")

p=root/"web/styles.css"
css=p.read_text(encoding="utf-8")+'''
/* v0.5.10: product editing stays inside the card on phone/tablet/desktop. */
.catalog-card-editing{border-color:#45ba84;background:#132820;scroll-margin-top:16px}
.catalog-inline-editor{width:100%;max-width:100%;margin-top:8px;padding:14px;background:#0c1c18;
  border:1px solid #2e845e;border-radius:12px;scroll-margin-top:95px}
.catalog-inline-editor .grid{min-width:0;max-width:100%}
.catalog-inline-editor .form-control{min-width:0}
.catalog-inline-editor input,.catalog-inline-editor select{max-width:100%}
@media(max-width:700px){
  .catalog-inline-editor{padding:12px;scroll-margin-top:95px}
  .catalog-inline-editor .grid.cols2{grid-template-columns:minmax(0,1fr)!important}
}
'''
p.write_text(css,encoding="utf-8")
(root/"android/app/src/main/assets/styles.css").write_text(css,encoding="utf-8")
print("Catalog migrated without overwriting custom prices; editor now stays in tapped product card")
