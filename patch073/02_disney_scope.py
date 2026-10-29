from pathlib import Path
root=Path("source/autoresponder-pro")
native=root/"android/app/src/main/java/com/autoresponder/pro"
web=root/"web"
assets=root/"android/app/src/main/assets"
def change(path,old,new,label):
    s=path.read_text(encoding="utf-8")
    assert s.count(old)==1,(label,s.count(old),str(path))
    path.write_text(s.replace(old,new,1),encoding="utf-8")

(native/"DisneyPlanScope.kt").write_text(r'''package com.autoresponder.pro

import org.json.JSONObject
import java.text.Normalizer
import java.util.Locale

/** Prevent the common "Disney" keyword from selecting an unrequested tier. */
internal object DisneyPlanScope {
    private fun norm(s:String):String=Normalizer.normalize(s.lowercase(Locale.ROOT),Normalizer.Form.NFD)
        .replace(Regex("\\p{M}+"),"").replace(Regex("[^a-z0-9]+")," ")
        .replace(Regex(" +")," ").trim()
    fun isDisney(i:JSONObject):Boolean=Regex("\\bdisney\\b").containsMatchIn(norm(i.optString("name")))
    private val direct=Regex("\\bdisney(?:\\s+plus)?\\s+(premium|estandar|basico)\\b")
    private val reverse=Regex("\\b(premium|estandar|basico)\\s+(?:de|del|para)\\s+disney\\b")
    private val sports=Regex("\\bdisney(?:\\s+plus)?\\s+(con|sin)\\s+(?:los\\s+)?(?:deportes|espn)\\b")
    private val others=Regex("\\b(netflix|prime|hbo|max|paramount|youtube|crunchyroll|"+
        "spotify|iptv|nuplin|vix|apple|canva|capcut|universal|flujo|dgo|plex|viki)\\b")
    fun namedVariant(message:String):String?{
        val n=norm(message)
        sports.find(n)?.let{return if(it.groupValues[1]=="sin")"estandar" else "premium"}
        direct.find(n)?.let{return it.groupValues[1]}
        reverse.find(n)?.let{return it.groupValues[1]}
        return null
    }
    fun followUpVariant(message:String):String?{
        namedVariant(message)?.let{return it}
        val n=norm(message)
        if(others.containsMatchIn(n))return null
        if(Regex("\\bsin\\s+(?:los\\s+)?(?:deportes|espn)\\b").containsMatchIn(n))return "estandar"
        if(Regex("\\bcon\\s+(?:los\\s+)?(?:deportes|espn)\\b").containsMatchIn(n))return "premium"
        return Regex("^(?:quiero|el|la|prefiero|de|dame|me das|seria|seria el)?\\s*"+
            "(premium|estandar|basico)$").find(n)?.groupValues?.get(1)
    }
    fun allPlans(message:String):Boolean=
        Regex("\\b(todos|todas|lista completa|todos los precios|catalogo completo|"+
            "planes|opciones|que tipos|que planes)\\b").containsMatchIn(norm(message))
    fun filter(business:String,message:String,items:List<JSONObject>):List<JSONObject>{
        if(business!="movieplay"||allPlans(message))return items
        val selected=namedVariant(message)?:return items
        return items.filter{!isDisney(it)||
            Regex("\\b"+selected+"\\b").containsMatchIn(norm(it.optString("name")))}
    }
    fun needsClarification(business:String,message:String,items:List<JSONObject>):Boolean{
        if(business!="movieplay")return false
        val n=norm(message)
        if(!Regex("\\bdisney\\b").containsMatchIn(n)||others.containsMatchIn(n)||
            namedVariant(message)!=null||allPlans(message))return false
        val options=items.filter{isDisney(it)&&it.optBoolean("active",false)&&
            it.optLong("price",0L)>0L}.mapNotNull{
                Regex("\\b(premium|estandar|basico)\\b")
                    .find(norm(it.optString("name")))?.value
            }.distinct()
        return options.size>1
    }
}
''',encoding="utf-8")

local=native/"LocalCatalog.kt"
change(local,'''        items(config,business).filter{matches(it,message)}''',
'''        DisneyPlanScope.filter(business,message,
            items(config,business).filter{matches(it,message)})''',"native matched")
change(local,'''        if(hits.isEmpty())return null
        // If a plan length was explicitly given, don't quote other durations.''',
'''        val requestedPlan=DisneyPlanScope.namedVariant(message)
        val scoped=DisneyPlanScope.filter(business,message,hits)
        if(scoped.isEmpty() && requestedPlan!=null && business=="movieplay")
            return Match("🎬 *MOVIEPLAY*\\n\\nNo encuentro ese plan de Disney en el catálogo. "+
                "Un asesor confirmará la disponibilidad, sin sustituirlo por otro.")
        if(scoped.isEmpty())return null
        if(DisneyPlanScope.needsClarification(business,message,scoped))
            return Match("🎬 *MOVIEPLAY · DISNEY*\\n\\n"+
                "¿Prefieres *Disney con deportes (Premium)* o *sin deportes (Estándar)*? 😊",
                count=0,available=true)
        // If a plan length was explicitly given, don't quote other durations.''',"native reply scope")
change(local,'''        val selected=if(requested!=null){
            hits.filter {norm(it.optString("duration"))==requested}.ifEmpty {hits}
        } else hits''',
'''        val selected=if(requested!=null){
            scoped.filter {norm(it.optString("duration"))==requested}
                .ifEmpty{if(requestedPlan!=null) emptyList() else scoped}
        } else scoped
        if(selected.isEmpty()&&requestedPlan!=null)
            return Match("🎬 *MOVIEPLAY*\\n\\nNo encuentro la duración solicitada "+
                "de Disney "+requestedPlan.uppercase()+". ¿Quieres consultar otra duración?")''',
"native precise duration")

(web/"disney-plan-scope.js").write_text(r'''/* Disney variants must be explicitly selected; no invented alternatives. */
(function(root,factory){const api=factory();if(typeof module==='object'&&module.exports)module.exports=api;
if(root)root.DisneyPlanScope=api;})(typeof window!=='undefined'?window:null,function(){
'use strict';
const norm=s=>String(s||'').toLowerCase().normalize('NFD')
  .replace(/[\u0300-\u036f]/g,'').replace(/[^a-z0-9]+/g,' ').replace(/ +/g,' ').trim();
const disney=p=>/\bdisney\b/.test(norm(p.name||''));
const other=/\b(netflix|prime|hbo|max|paramount|youtube|crunchyroll|spotify|iptv|nuplin|vix|apple|canva|capcut|universal|flujo|dgo|plex|viki)\b/;
function namedVariant(text){
 const n=norm(text);
 const sports=n.match(/\bdisney(?:\s+plus)?\s+(con|sin)\s+(?:los\s+)?(?:deportes|espn)\b/);
 if(sports)return sports[1]==='sin'?'estandar':'premium';
 const direct=n.match(/\bdisney(?:\s+plus)?\s+(premium|estandar|basico)\b/);
 if(direct)return direct[1];
 const reverse=n.match(/\b(premium|estandar|basico)\s+(?:de|del|para)\s+disney\b/);
 return reverse?.[1]||null;
}
const allPlans=text=>/\b(todos|todas|lista completa|todos los precios|catalogo completo|planes|opciones|que tipos|que planes)\b/.test(norm(text));
function filter(business,text,products){
 if(business!=='movieplay'||allPlans(text))return products;
 const v=namedVariant(text);
 return v?products.filter(p=>!disney(p)||new RegExp('\\b'+v+'\\b').test(norm(p.name))):products;
}
function needsClarification(business,text,catalog){
 const n=norm(text);
 if(business!=='movieplay'||!/\bdisney\b/.test(n)||other.test(n)||
   namedVariant(text)||allPlans(text))return false;
 const options=[...new Set((catalog||[]).filter(p=>disney(p)&&p.active&&
   Number(p.price)>0).map(p=>norm(p.name).match(/\b(premium|estandar|basico)\b/)?.[1]).filter(Boolean))];
 return options.length>1;
}
return {namedVariant,allPlans,filter,needsClarification};
});
''',encoding="utf-8")

change(web/"index.html",'''  <script src="netflix-international.js"></script>''',
'''  <script src="disney-plan-scope.js"></script>
  <script src="netflix-international.js"></script>''',"load web matcher")
app=web/"app.js"
change(app,'''    return state.catalog.filter(i=>i.assistant===business&&
      (String(i.keywords||"").split(",").concat(i.name||"")).some(term=>{''',
'''    const results=state.catalog.filter(i=>i.assistant===business&&
      (String(i.keywords||"").split(",").concat(i.name||"")).some(term=>{''',
"prepare web match filter")
change(app,'''           (alias.length>=5&&!alias.includes(" ")&&words.some(w=>w.length>=4&&oneEdit(w,alias))));
      }));
  }
  function catalogAnswer''',
'''           (alias.length>=5&&!alias.includes(" ")&&words.some(w=>w.length>=4&&oneEdit(w,alias))));
      }));
    return window.DisneyPlanScope?.filter(business,message,results)||results;
  }
  function catalogAnswer''',
"filter web matches")
change(app,'''    if(!matching.length)return null;
    const plan=normalize(message).match''',
'''    if(!matching.length){
      const requested=window.DisneyPlanScope?.namedVariant(message);
      return business==="movieplay"&&requested?
        {reply:"🎬 *MOVIEPLAY*\\n\\nNo encuentro ese plan de Disney en el catálogo. "+
          "Un asesor confirmará su disponibilidad, sin sustituirlo por otro.",
          imageTag:"",catalogId:"",available:false}:null;
    }
    if(window.DisneyPlanScope?.needsClarification(business,message,matching))
      return {reply:"🎬 *MOVIEPLAY · DISNEY*\\n\\n"+
        "¿Prefieres *Disney con deportes (Premium)* o *sin deportes (Estándar)*? 😊",
        imageTag:"",catalogId:"",available:true};
    const plan=normalize(message).match''',
"web clarification")
change(app,'''    const scoped=plan?matching.filter(i=>normalize(i.duration||"")===plan[0]):matching;
    const choices=scoped.length?scoped:matching;''',
'''    const scoped=plan?matching.filter(i=>normalize(i.duration||"")===plan[0]):matching;
    const requested=window.DisneyPlanScope?.namedVariant(message);
    const choices=scoped.length?scoped:(requested?[]:matching);
    if(!choices.length&&requested)
      return {reply:"🎬 *MOVIEPLAY*\\n\\nNo encuentro esa duración de Disney "+
        requested.toUpperCase()+". ¿Quieres consultar otra duración?",
        imageTag:"",catalogId:"",available:false};''',
"web exact duration")
change(app,'''      lines.push("¿Cuál te interesa?");
    }
    return {reply:lines.join("\\n"),''',
'''      lines.push(choices.length===1&&choices[0].active&&Number(choices[0].price)>0?
        "¿Te paso los medios de pago? 😊":"¿Cuál te interesa?");
    }
    return {reply:lines.join("\\n"),''',
"web one-item payment option")
for name in ["index.html","app.js","disney-plan-scope.js"]:
    (assets/name).write_text((web/name).read_text(encoding="utf-8"),encoding="utf-8")
print("Disney variant-specific matching applied in native and simulator.")
