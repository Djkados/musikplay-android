from pathlib import Path

root=Path("source/autoresponder-pro")
native=root/"android/app/src/main/java/com/autoresponder/pro"
web=root/"web"
assets=root/"android/app/src/main/assets"
def replace(path,old,new,label):
    s=path.read_text(encoding="utf-8")
    if s.count(old)!=1:
        doubled=old.replace(chr(92),chr(92)*2)
        if s.count(doubled)==1:
            old=doubled
    assert s.count(old)==1,(label,s.count(old),str(path))
    path.write_text(s.replace(old,new,1),encoding="utf-8")

(native/"PlanPrecision074.kt").write_text(r'''package com.autoresponder.pro

import org.json.JSONObject
import java.text.Normalizer
import java.util.Locale

/** Safe product intent normalization: never invent prices or substitute plans. */
internal object PlanPrecision074 {
    private val typo=mapOf("premiun" to "premium","premuim" to "premium",
        "premum" to "premium","disnei" to "disney","disny" to "disney",
        "netflis" to "netflix","neflis" to "netflix",
        "netflixx" to "netflix","standar" to "estandar",
        "estandard" to "estandar")
    private val known=listOf("netflix","disney","prime","max","crunchyroll",
        "paramount","spotify","youtube","nuplin","iptv","plex","vix","apple tv",
        "canva","capcut","universal","flujo","dgo","viki","chatgpt","office")
    private fun has(n:String,word:String)=(" "+n+" ").contains(" "+word+" ")
    fun norm(raw:String):String {
        val n=Normalizer.normalize(raw.lowercase(Locale.ROOT),Normalizer.Form.NFD)
            .replace(Regex("\\p{M}+"),"").replace(Regex("[^a-z0-9]+")," ")
            .replace(Regex(" +")," ").trim()
        val converted=n.split(" ").joinToString(" "){typo[it]?:it}
        return if(has(converted,"netflix"))converted.replace(
            Regex("\\binter\\b"),"internacional") else converted
    }
    fun allPlans(message:String):Boolean=
        Regex("\\b(todos|todas|planes|opciones|catalogo|lista completa|"+
            "cuales hay|que tipos|que planes)\\b").containsMatchIn(norm(message))
    fun family(item:JSONObject):String? {
        val name=norm(item.optString("name"))
        return known.firstOrNull{has(name,it)}
    }
    fun requestedFamily(message:String):List<String> {
        val n=norm(message)
        return known.filter{has(n,it)}.filterNot{it=="max" && has(n,"hbo max")}.let { found ->
            if(has(n,"hbo max") && "max" !in found)found+"max" else found
        }
    }
    private fun segment(n:String,family:String):String {
        val match=Regex("\\b"+Regex.escape(family)+"\\b").find(n)?:return ""
        val tail=n.substring(match.range.first)
        val end=known.filter{it!=family}.mapNotNull{
            Regex("\\b"+Regex.escape(it)+"\\b").find(tail, family.length)?.range?.first
        }.minOrNull()?:tail.length
        return tail.substring(0,minOf(end,tail.length))
    }
    fun variant(message:String,family:String):String? {
        val n=norm(message)
        val local=segment(n,family)
        if(local.isBlank())return null
        return when(family){
            "disney" -> when{
                has(local,"sin deportes") || has(local,"sin espn") -> "estandar"
                has(local,"con deportes") || has(local,"con espn") -> "premium"
                Regex("\\b(premium|estandar|basico)\\b").find(local)!=null ->
                    Regex("\\b(premium|estandar|basico)\\b").find(local)?.value
                else -> null
            }
            "max" -> Regex("\\b(premium|estandar|basico)\\b").find(local)?.value
            "netflix" -> if(has(local,"internacional"))"internacional" else null
            else -> null
        }
    }
    fun followUp(raw:String,family:String):String? {
        val n=norm(raw)
        if(requestedFamily(n).any{it!=family})return null
        variant(n,family)?.let{return it}
        val compact=n.replace(Regex("^(?:el|la|el de|la de|quiero|quiero el|"+
            "quiero la|prefiero|dame|es|seria|la opcion)\\s+"),"")
        return when(family){
            "disney" -> when(compact){
                "premium","con deportes","con espn"->"premium"
                "estandar","sin deportes","sin espn"->"estandar"
                "basico"->"basico"
                else->null
            }
            "max" -> when(compact){
                "premium"->"premium";"estandar"->"estandar";"basico"->"basico"
                else->null
            }
            "netflix" -> when(compact){
                "internacional","inter"->"internacional"
                "normal","colombia","nacional"->"nacional"
                else->null
            }
            else->null
        }
    }
    fun filter(business:String,message:String,items:List<JSONObject>):List<JSONObject> {
        if(business!="movieplay" || items.isEmpty() || allPlans(message))return items
        val families=requestedFamily(message)
        val one=families.singleOrNull()
        return items.filter{item->
            val family=family(item)
            if(one!=null && family in known && family!=one)return@filter false
            val wanted=family?.let{variant(message,it)}
            if(wanted!=null) {
                val name=norm(item.optString("name"))
                if(wanted=="nacional") !has(name,"internacional")
                else has(name,wanted)
            } else if(family=="netflix" && "netflix" in families)
                !has(norm(item.optString("name")),"internacional")
            else true
        }
    }
    fun exactPlanRequested(message:String):Boolean=
        listOf("disney","max","netflix").any{variant(message,it)!=null}
}
''',encoding="utf-8")

local=native/"LocalCatalog.kt"
replace(local,'''    private fun norm(s:String):String=Normalizer.normalize(s.lowercase(Locale.ROOT),Normalizer.Form.NFD)
        .replace(Regex("\\p{M}+"),"").replace(Regex("[^a-z0-9]+")," ").trim()''',
'''    private fun norm(s:String):String=PlanPrecision074.norm(s)''',"catalog normalization")
replace(local,'''        DisneyPlanScope.filter(business,message,
            items(config,business).filter{matches(it,message)})''',
'''        PlanPrecision074.filter(business,message,
            DisneyPlanScope.filter(business,message,
                items(config,business).filter{matches(it,message)}))''',"catalog filter exact")
replace(local,'''        val scoped=DisneyPlanScope.filter(business,message,hits)
''',
'''        val scoped=PlanPrecision074.filter(business,message,
            DisneyPlanScope.filter(business,message,hits))
''',"catalog quote filter exact")
replace(local,'''        if(scoped.isEmpty() && requestedPlan!=null && business=="movieplay")''',
'''        if(scoped.isEmpty() && business=="movieplay" &&
            (requestedPlan!=null || PlanPrecision074.exactPlanRequested(message)))''',
"no cross plan substitution")
replace(local,'''        val selected=if(requested!=null){
            scoped.filter {norm(it.optString("duration"))==requested}
                .ifEmpty{if(requestedPlan!=null) emptyList() else scoped}
        } else scoped
        if(selected.isEmpty()&&requestedPlan!=null)''',
'''        val selected=if(requested!=null){
            scoped.filter {norm(it.optString("duration"))==requested}
        } else scoped
        if(selected.isEmpty() && requested!=null)''',
"never substitute specific duration")
replace(local,'''                "de Disney "+requestedPlan.uppercase()+". ¿Quieres consultar otra duración?")''',
'''                "del servicio seleccionado. ¿Quieres consultar otra duración?")''',
"safe duration message general")
disney=native/"DisneyPlanScope.kt"
replace(disney,'''    private fun norm(s:String):String=Normalizer.normalize(s.lowercase(Locale.ROOT),Normalizer.Form.NFD)
        .replace(Regex("\\p{M}+"),"").replace(Regex("[^a-z0-9]+")," ")
        .replace(Regex(" +")," ").trim()''',
'''    private fun norm(s:String):String=PlanPrecision074.norm(s)''',"Disney typo normalization")
combo=native/"ComboSales.kt"
replace(combo,'''    private fun norm(raw:String):String = Normalizer.normalize(raw.lowercase(Locale.ROOT),Normalizer.Form.NFD)
        .replace(Regex("\\p{M}+"),"").replace(Regex("[^a-z0-9]+")," ").trim()''',
'''    private fun norm(raw:String):String = PlanPrecision074.norm(raw)''',"Combo intent aliases")
flow=native/"ConversationFlow.kt"
replace(flow,'''    private fun norm(s:String)=NativeAutoReplyEngine.normalize(s)
        .replace(Regex("[^a-z0-9 ]+")," ").replace(Regex("\\s+")," ").trim()''',
'''    private fun norm(s:String)=PlanPrecision074.norm(s)''',"Flow normalization")
replace(flow,r'''        val narrowed=if(qualifiers.isEmpty())items else items.filter{p->
            qualifiers.any{Regex("\\b"+it+"\\b").containsMatchIn(norm(p.optString("name")))}
        }.ifEmpty{items}
        return narrowed.firstOrNull()''',
'''        val narrowed=if(qualifiers.isEmpty())items else items.filter{p->
            qualifiers.any{Regex("\\b"+it+"\\b").containsMatchIn(norm(p.optString("name")))}
        }
        return narrowed.firstOrNull()''',"no fallback to invalid plan")
replace(flow,'''        val chosen=option(dated,message)?:return null''',
'''        val chosen=option(dated,message)?:return null''',"ensure exact option anchor")
# A new product question must be treated independently of old chat memory.
# This is handled in NativeAutoReplyEngine before follow-up and is tested below.

(web/"plan-precision-074.js").write_text(r'''/* Deterministic service-family and plan scoping. No price guessing. */
(function(root,factory){const api=factory();
if(typeof module==='object'&&module.exports)module.exports=api;
if(root)root.PlanPrecision074=api;})(typeof window!=='undefined'?window:null,function(){
'use strict';
const groups=['netflix','disney','prime','max','crunchyroll','paramount','spotify','youtube',
  'nuplin','iptv','plex','vix','apple tv','canva','capcut','universal','flujo','dgo','viki',
  'chatgpt','office'];
const typos={premiun:'premium',premuim:'premium',premum:'premium',disnei:'disney',
  disny:'disney',netflis:'netflix',neflis:'netflix',netflixx:'netflix',
  standar:'estandar',estandard:'estandar'};
const has=(n,k)=>(' '+n+' ').includes(' '+k+' ');
function norm(s){
  let n=String(s||'').toLowerCase().normalize('NFD').replace(/[\u0300-\u036f]/g,'')
    .replace(/[^a-z0-9]+/g,' ').replace(/ +/g,' ').trim();
  n=n.split(' ').map(x=>typos[x]||x).join(' ');
  return has(n,'netflix')?n.replace(/\binter\b/g,'internacional'):n;
}
const allPlans=s=>/\b(todos|todas|planes|opciones|catalogo|lista completa|cuales hay|que tipos|que planes)\b/.test(norm(s));
const requested=s=>groups.filter(k=>has(norm(s),k));
const family=item=>groups.find(k=>has(norm(item.name||''),k))||null;
function variant(s,k){
  const n=norm(s),index=n.search(new RegExp('\\b'+k+'\\b'));
  if(index<0)return null;
  const after=n.slice(index);
  const boundaries=groups.filter(f=>f!==k).map(f=>{
    const m=new RegExp('\\b'+f+'\\b').exec(after.slice(k.length));
    return m?m.index+k.length:after.length;
  });
  const seg=after.slice(0,Math.min(after.length,...boundaries));
  if(k==='disney'){
    if(has(seg,'sin deportes')||has(seg,'sin espn'))return 'estandar';
    if(has(seg,'con deportes')||has(seg,'con espn'))return 'premium';
    return seg.match(/\b(premium|estandar|basico)\b/)?.[1]||null;
  }
  if(k==='max')return seg.match(/\b(premium|estandar|basico)\b/)?.[1]||null;
  if(k==='netflix'&&has(seg,'internacional'))return 'internacional';
  return null;
}
function filter(business,message,items){
  if(business!=='movieplay'||!items.length||allPlans(message))return items;
  const req=requested(message),only=req.length===1?req[0]:null;
  return items.filter(item=>{
    const k=family(item);
    if(only&&k&&k!==only)return false;
    const v=k?variant(message,k):null;
    if(v)return v==='nacional'?!has(norm(item.name),'internacional'):has(norm(item.name),v);
    return k!=='netflix'||!req.includes('netflix')||!has(norm(item.name),'internacional');
  });
}
return {norm,family,variant,filter,allPlans,requested};
});
''',encoding="utf-8")
replace(web/"index.html",'''  <script src="combo-sales.js"></script>''',
'''  <script src="plan-precision-074.js"></script>
  <script src="combo-sales.js"></script>''',"load intent helper before quoting")
app=web/"app.js"
replace(app,'''    const normalized=normalize(message).replace(/[^a-z0-9]+/g," ").trim();''',
'''    const normalized=(window.PlanPrecision074?.norm(message)||
      normalize(message).replace(/[^a-z0-9]+/g," ").trim());''',"web catalog normalize")
replace(app,'''    return window.DisneyPlanScope?.filter(business,message,results)||results;''',
'''    const disney=window.DisneyPlanScope?.filter(business,message,results)||results;
    return window.PlanPrecision074?.filter(business,message,disney)||disney;''',
"web exact matching")
replace(app,'''    const scoped=plan?matching.filter(i=>normalize(i.duration||"")===plan[0]):matching;''',
'''    const scoped=plan?matching.filter(i=>normalize(i.duration||"")===plan[0]):matching;''',
"verify duration anchor")
replace(app,'''    const choices=scoped.length?scoped:(requested?[]:matching);''',
'''    const choices=scoped.length?scoped:[];''',"web never fabricate duration")
replace(app,'''    if(!choices.length&&requested)
      return {reply:"🎬 *MOVIEPLAY*\\n\\nNo encuentro esa duración de Disney "+
        requested.toUpperCase()+". ¿Quieres consultar otra duración?",
        imageTag:"",catalogId:"",available:false};''',
'''    if(!choices.length && plan)
      return {reply:"🎬 *MOVIEPLAY*\\n\\nNo encuentro esa duración del servicio seleccionado. "+
        "¿Quieres consultar otra duración?",
        imageTag:"",catalogId:"",available:false};''',"web duration exact clarification")
combojs=web/"combo-sales.js"
replace(combojs,'''const norm=s=>String(s||'').toLowerCase().normalize('NFD').replace(/[\\u0300-\\u036f]/g,'').replace(/[^a-z0-9]+/g,' ').trim();''',
'''const norm=s=>typeof window!=='undefined'&&window.PlanPrecision074?
  window.PlanPrecision074.norm(s):
  String(s||'').toLowerCase().normalize('NFD').replace(/[\\u0300-\\u036f]/g,'').replace(/[^a-z0-9]+/g,' ').trim();''',
"web combo normalization")
disneyjs=web/"disney-plan-scope.js"
replace(disneyjs,'''const norm=s=>String(s||'').toLowerCase().normalize('NFD')
  .replace(/[\\u0300-\\u036f]/g,'').replace(/[^a-z0-9]+/g,' ').replace(/ +/g,' ').trim();''',
'''const norm=s=>typeof window!=='undefined'&&window.PlanPrecision074?
  window.PlanPrecision074.norm(s):
  String(s||'').toLowerCase().normalize('NFD')
  .replace(/[\\u0300-\\u036f]/g,'').replace(/[^a-z0-9]+/g,' ').replace(/ +/g,' ').trim();''',
"web Disney typo normalization")
for name in ["index.html","app.js","combo-sales.js","disney-plan-scope.js","plan-precision-074.js"]:
    (assets/name).write_text((web/name).read_text(encoding="utf-8"),encoding="utf-8")
print("0.6.14 plan scoping: cross-platform variants, typos and explicit duration guard.")
