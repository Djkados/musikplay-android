from pathlib import Path
import json

p=Path("source/autoresponder-pro/web/app.js")
s=p.read_text(encoding="utf-8")

def item(id,name,price,keywords,duration="",notes="",image="",active=True):
    return {"id":id,"assistant":"movieplay","type":"service","name":name,
      "duration":duration,"price":price,"salePrice":0,"offerUntil":"",
      "keywords":keywords,"imageTag":image or id.split("-")[0],
      "notes":notes,"active":active}

poster=[
    item("apple-30","Apple TV+",9000,"apple tv,apple tv plus","30 días",image="apple"),
    item("apple-3m","Apple TV+",20000,"apple tv,apple tv plus","3 meses",image="apple"),
    item("crunchy-30","Crunchyroll",9000,"crunchyroll,crunchy","30 días",image="crunchyroll"),
    item("disney-basic","Disney+ Básico",6000,"disney,disney plus,disney basico",duration="30 días",notes="Con anuncios",image="disney"),
    item("disney-standard","Disney+ Estándar",10000,"disney,disney plus,disney estandar",duration="30 días",notes="Sin anuncios",image="disney"),
    item("flujo-30","Flujo TV",17000,"flujo,flujo tv,flujotv","30 días","Deportes, series y películas","flujo"),
    item("iptv-30","IPTV",14000,"iptv,television iptv","30 días","Deportes, series y películas","iptv"),
    item("max-standard","Max Estándar",6000,"max,hbo max,max estandar",duration="30 días",notes="Con anuncios",image="max"),
    item("netflix-int","Netflix Internacional",18000,"netflix,neflis,netflis,netflix internacional","30 días",image="netflix"),
    item("nuplin-30","Nuplin",30000,"nuplin,nup lin","30 días","Incluye Win+ y ESPN","nuplin"),
    item("paramount-30","Paramount+",14000,"paramount,paramount plus","30 días","Deportes, series y películas","paramount"),
    item("plex-30","Plex",10000,"plex","30 días","Películas y series","plex"),
    item("universal-30","Universal+",7000,"universal,universal plus","30 días",image="universal"),
    item("viki-30","Viki Rakuten",9000,"viki,viki rakuten,rakuten","30 días",image="viki"),
    item("vix-30","ViX",7000,"vix,vix premium","30 días",image="vix"),
    item("spotify-30","Spotify",15000,"spotify,spotifi","30 días",image="spotify"),
    item("spotify-2m","Spotify",20000,"spotify,spotifi","2 meses",image="spotify"),
    item("spotify-3m","Spotify",27000,"spotify,spotifi","3 meses",image="spotify"),
    item("youtube-30","YouTube Premium",15000,"youtube,youtube premium,yutub","30 días",image="youtube"),
    item("chatgpt-30","ChatGPT",30000,"chatgpt,chat gpt","30 días","Cuenta compartida","chatgpt"),
    item("capcut-30","CapCut",20000,"capcut,cap cut","30 días",image="capcut"),
    item("canva-30","Canva",8000,"canva","30 días",image="canva"),
    item("canva-3m","Canva",19000,"canva","3 meses",image="canva"),
    item("canva-6m","Canva",36000,"canva","6 meses",image="canva"),
    item("canva-12m","Canva",50000,"canva","12 meses",image="canva"),
    item("office-6m","Office 365",36000,"office,office 365,microsoft 365,ofice","6 meses",image="office"),
    item("office-12m","Office 365",50000,"office,office 365,microsoft 365,ofice","12 meses",image="office")
]
old_prices={"dp30":19000,"pv30":10000,"mp30":10000}
existing_names={"dp30":"Disney+ Premium","mp30":"Max Premium"}
existing_notes={"dp30":"Incluye deportes","mp30":"Sin anuncios"}

# Keep user modifications, only fill previous unpriced factory cards.
migration='''  const flyerUpgradeKey="autoresponder_catalog_poster_20261011";
  if(!localStorage.getItem(flyerUpgradeKey)){
    const flyerRecords='''+json.dumps(poster,ensure_ascii=False,separators=(",",":"))+''';
    const previousPrices='''+json.dumps(old_prices,ensure_ascii=False)+''';
    const previousNames='''+json.dumps(existing_names,ensure_ascii=False)+''';
    const previousNotes='''+json.dumps(existing_notes,ensure_ascii=False)+''';
    for(const row of state.catalog){
      if(Object.hasOwn(previousPrices,row.id)){
        if(!Number(row.price||0))row.price=previousPrices[row.id];
        if(row.name==="Disney Premium" && row.id==="dp30")row.name=previousNames.dp30;
        if(row.id==="mp30")row.name=previousNames.mp30;
        if(!row.notes)row.notes=previousNotes[row.id]||"";
        if(row.id==="dp30" && !row.duration)row.duration="30 días";
        if(row.id==="mp30" && !row.duration)row.duration="30 días";
      }
    }
    for(const row of flyerRecords){
      if(!state.catalog.some(p=>p.id===row.id))state.catalog.push(row);
    }
    localStorage.setItem(KEY,JSON.stringify(state));
    localStorage.setItem(flyerUpgradeKey,"done");
  }
'''
marker='  const runtime = {catalogEdit:null,route:'
assert s.count(marker)==1
s=s.replace(marker,migration+"  const runtime = {catalogEdit:null,route:",1)
# Preserve notes in editors and display catalog description.
before="'<p class=\"tiny muted\">Palabras clave: '+safe(i.keywords)+'</p><div class=\"row\">'"
after="'<p class=\"tiny muted\">'+safe(i.notes||'')+'</p><p class=\"tiny muted\">Palabras clave: '+safe(i.keywords)+'</p><div class=\"row\">'"
assert s.count(before)==1
s=s.replace(before,after,1)
before="field('catKeywords','Palabras clave separadas por comas',editing.keywords||'')+"
after=before+"\n      field('catNotes','Características (opcional)',editing.notes||'')+"
assert s.count(before)==1
s=s.replace(before,after,1)
before="imageTag:$('#catImage').value.trim().slice(0,60),active:prev?.active??true"
after="imageTag:$('#catImage').value.trim().slice(0,60),notes:$('#catNotes').value.trim().slice(0,130),active:prev?.active??true"
assert s.count(before)==1
s=s.replace(before,after,1)
p.write_text(s,encoding="utf-8")
Path("source/autoresponder-pro/android/app/src/main/assets/app.js").write_text(s,encoding="utf-8")
print("Loaded poster catalogue:",len(poster),"new price options + preserved existing Netflix, Disney, Max and Prime cards")
