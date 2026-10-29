from pathlib import Path
root=Path("source/autoresponder-pro")
native=root/"android/app/src/main/java/com/autoresponder/pro"
web=root/"web"
def change(path,old,new,label):
 s=path.read_text(encoding="utf-8")
 assert s.count(old)==1,(label,s.count(old))
 path.write_text(s.replace(old,new,1),encoding="utf-8")
DEFAULT="En MoviePlay, Netflix Internacional identifica una cuenta de una región fuera de Colombia; Netflix habitual corresponde a la modalidad Colombia. Pueden cambiar las condiciones de acceso y verificación según el dispositivo y la cuenta. No significa automáticamente más calidad, más películas ni que no existan restricciones de hogar. Confirmamos la compatibilidad antes de la entrega."
(native/"NetflixInternationalInfo.kt").write_text(r'''package com.autoresponder.pro

import org.json.JSONObject
import java.text.Normalizer
import java.util.Locale

/** Owner-configurable, safety-conscious FAQ; price always comes from current catalog. */
internal object NetflixInternationalInfo {
    const val DEFAULT = "En MoviePlay, Netflix Internacional identifica una cuenta de una región fuera de Colombia; Netflix habitual corresponde a la modalidad Colombia. Pueden cambiar las condiciones de acceso y verificación según el dispositivo y la cuenta. No significa automáticamente más calidad, más películas ni que no existan restricciones de hogar. Confirmamos la compatibilidad antes de la entrega."
    private fun norm(s:String):String=Normalizer.normalize(s.lowercase(Locale.ROOT),Normalizer.Form.NFD)
        .replace(Regex("\\p{M}+"),"").replace(Regex("[^a-z0-9 ]+")," ")
        .replace(Regex(" +")," ").trim()
    fun question(message:String):Boolean {
        val n=norm(message)
        if(!Regex("\\bnetflix\\b").containsMatchIn(n) ||
            !Regex("\\binternacional\\b").containsMatchIn(n))return false
        return Regex("\\b(que es|que significa|que quiere decir|diferencia|diferente|comparacion|"+
            "comparado|en que cambia|como funciona|cual es mejor|por que es internacional|"+
            "normal o internacional|internacional o normal|explicame|explica|eso de netflix)\\b")
            .containsMatchIn(n)
    }
    fun answer(config:JSONObject,message:String):String? {
        if(!question(message))return null
        val info=config.optString("netflixInternationalInfo").trim()
            .takeIf{it.length in 20..850} ?: DEFAULT
        val active=LocalCatalog.items(config,"movieplay").filter{
            it.optBoolean("active",false) && it.optLong("price",0L)>0L &&
                norm(it.optString("name")).contains("netflix")
        }
        val intl=active.firstOrNull{norm(it.optString("name")).contains("internacional")}
        val others=active.filterNot{norm(it.optString("name")).contains("internacional")}
        val line=if(intl!=null){
            val price="$"+String.format(Locale.GERMANY,"%,d",intl.optLong("price",0L))
            "📺 *Netflix Internacional "+intl.optString("duration")+": "+price+"*"
        }else "📺 *Netflix Internacional:* precio y disponibilidad por confirmar."
        val durations=others.map{it.optString("duration")}.filter{it.isNotBlank()}.distinct().take(4)
        val normal=if(durations.isNotEmpty())"\nPlanes habituales: "+durations.joinToString(", ")+"." else ""
        return ("🎬 *¿QUÉ ES NETFLIX INTERNACIONAL?*\n\n"+info+"\n\n"+
            line+normal+"\n\n💚 ¿Quieres cotizar el habitual o el Internacional?").take(1600)
    }
}
''',encoding="utf-8")
change(native/"NativeAutoReplyEngine.kt",'''        if(business=="movieplay" && unit=="sales"){
            ComboSales.respond''','''        if(business=="movieplay" && unit=="sales"){
            NetflixInternationalInfo.answer(config,m)?.let{
                return Decision(text=it,business=business,department=unit,
                    reason="Información Netflix Internacional",
                    routeSource="netflix_international_info")
            }
            ComboSales.respond''',"Kotlin FAQ routing")
(web/"netflix-international.js").write_text(r'''/* Netflix Internacional: deterministic answer; only active catalog prices are quoted. */
(function(root,factory){const api=factory();if(typeof module==='object'&&module.exports)module.exports=api;
if(root)root.NetflixInternationalInfo=api;})(typeof window!=='undefined'?window:null,function(){
'use strict';
const DEFAULT='En MoviePlay, Netflix Internacional identifica una cuenta de una región fuera de Colombia; Netflix habitual corresponde a la modalidad Colombia. Pueden cambiar las condiciones de acceso y verificación según el dispositivo y la cuenta. No significa automáticamente más calidad, más películas ni que no existan restricciones de hogar. Confirmamos la compatibilidad antes de la entrega.';
const norm=s=>String(s||'').toLowerCase().normalize('NFD').replace(/[\u0300-\u036f]/g,'')
    .replace(/[^a-z0-9 ]+/g,' ').replace(/ +/g,' ').trim();
const question=message=>{
  const n=norm(message);
  return /\bnetflix\b/.test(n)&&/\binternacional\b/.test(n)&&
    /\b(que es|que significa|que quiere decir|diferencia|diferente|comparacion|comparado|en que cambia|como funciona|cual es mejor|por que es internacional|normal o internacional|internacional o normal|explicame|explica|eso de netflix)\b/.test(n);
};
const answer=(catalog,message,editable)=>{
  if(!question(message))return null;
  const info=typeof editable==='string'&&editable.trim().length>=20&&editable.trim().length<=850?
    editable.trim():DEFAULT;
  const active=(catalog||[]).filter(p=>p.assistant==='movieplay'&&p.active&&Number(p.price)>0&&/\bnetflix\b/.test(norm(p.name)));
  const intl=active.find(p=>/\binternacional\b/.test(norm(p.name)));
  const usual=[...new Set(active.filter(p=>!/\binternacional\b/.test(norm(p.name))).map(p=>p.duration).filter(Boolean))].slice(0,4);
  const price=intl?'📺 *Netflix Internacional '+(intl.duration||'')+': $'+Number(intl.price).toLocaleString('es-CO')+'*':
    '📺 *Netflix Internacional:* precio y disponibilidad por confirmar.';
  return ('🎬 *¿QUÉ ES NETFLIX INTERNACIONAL?*\n\n'+info+'\n\n'+price+
    (usual.length?'\nPlanes habituales: '+usual.join(', ')+'.':'')+
    '\n\n💚 ¿Quieres cotizar el habitual o el Internacional?').slice(0,1600);
};
return {DEFAULT,question,answer};
});
''',encoding="utf-8")
change(web/"index.html",'''  <script src="combo-sales.js"></script>
  <script src="app.js"></script>''','''  <script src="combo-sales.js"></script>
  <script src="netflix-international.js"></script>
  <script src="app.js"></script>''',"FAQ HTML import")
p=web/"app.js"
change(p,'''    learningSuggestions:[],intentAliases:[],inbox:[]
''','''    learningSuggestions:[],intentAliases:[],inbox:[],
    netflixInternationalInfo:window.NetflixInternationalInfo?.DEFAULT||""
''',"FAQ defaults")
change(p,'''  state.sellerContacts ||= [];
''','''  state.sellerContacts ||= [];
  state.netflixInternationalInfo ||= window.NetflixInternationalInfo?.DEFAULT||"";
''',"FAQ legacy state")
change(p,'''    if(assistant==='movieplay'&&unit==='sales'&&window.ComboSales){''',
'''    if(assistant==='movieplay'&&unit==='sales'&&window.NetflixInternationalInfo){
      const explanation=window.NetflixInternationalInfo.answer(state.catalog,text,state.netflixInternationalInfo);
      if(explanation)return {reply:explanation,assistant,unit,
        method:'netflix_international_info',status:'open',image:null};
    }
    if(assistant==='movieplay'&&unit==='sales'&&window.ComboSales){''',"FAQ simulator")
change(p,'''      '<div class="card stack"><h2>Ejemplo de atención</h2>'+''','''      '<div class="card stack"><h2>Netflix Internacional · explicación</h2>'+
      '<p class="small muted">El bot responde dudas sobre la modalidad y usa el precio actual del catálogo, sin prometer ventajas no verificadas.</p>'+
      '<textarea id="netflixInfo" maxlength="850" rows="7">'+safe(state.netflixInternationalInfo)+'</textarea>'+
      '<button class="btn primary" data-action="save-netflix-info">Guardar explicación</button></div>'+
      '<div class="card stack"><h2>Ejemplo de atención</h2>'+''',"FAQ edit screen")
change(p,'''payments,comboSales,schedules,scheduleOverrides,settings,intentAliases}=state;''',
'''payments,comboSales,netflixInternationalInfo,schedules,scheduleOverrides,settings,intentAliases}=state;''',"FAQ native sync objects")
change(p,'''payments,comboSales,schedules,scheduleOverrides,settings,intentAliases}));''',
'''payments,comboSales,netflixInternationalInfo,schedules,scheduleOverrides,settings,intentAliases}));''',"FAQ native sync payload")
change(p,'''    if(a==='refresh-activity'){''','''    if(a==='save-netflix-info'){
      const value=String($('#netflixInfo')?.value||'').trim();
      if(value.length<20||value.length>850)return notify('Descripción entre 20 y 850 caracteres.');
      state.netflixInternationalInfo=value;save();render();
      notify('Explicación guardada y sincronizada.');return;
    }
    if(a==='refresh-activity'){''',"FAQ save event")
change(p,'''    state.comboSales={...defaults().comboSales,...(state.comboSales||{})};''',
'''    state.comboSales={...defaults().comboSales,...(state.comboSales||{})};
    state.netflixInternationalInfo=state.netflixInternationalInfo||
      window.NetflixInternationalInfo?.DEFAULT||"";''',"FAQ import migration")
for name in ["index.html","app.js","netflix-international.js"]:
    (root/"android/app/src/main/assets"/name).write_text(
        (web/name).read_text(encoding="utf-8"),encoding="utf-8")
print("v0.6.12: editable Netflix Internacional FAQ ready.")
