from pathlib import Path
root=Path("source/autoresponder-pro")
native=root/"android/app/src/main/java/com/autoresponder/pro"
(native/"CadencePolicy.kt").write_text('''package com.autoresponder.pro

import org.json.JSONObject

/** Configurable, bounded offline cooldowns; never permits sending more frequently than 1 minute. */
internal object CadencePolicy {
    fun minutes(settings:JSONObject?,key:String,default:Int,minimum:Int,maximum:Int):Long {
        val actual=settings?.optInt(key,default) ?: default
        return actual.coerceIn(minimum,maximum).toLong()*60L*1000L
    }
    fun menu(settings:JSONObject?)=minutes(settings,"menuHours",12,1,24)*60L
    fun away(settings:JSONObject?)=minutes(settings,"awayHours",12,1,24)*60L
    fun greeting(settings:JSONObject?)=minutes(settings,"greetingHours",12,1,24)*60L
    fun thanks(settings:JSONObject?)=minutes(settings,"courtesyMinutes",15,1,180)
    fun repeated(settings:JSONObject?)=minutes(settings,"repeatMinutes",2,1,30)
}
''',encoding="utf-8")
p=native/"WhatsAppNotificationListener.kt"
s=p.read_text(encoding="utf-8")
def rep(old,new):
 global s
 assert s.count(old)==1,(old[:90],s.count(old))
 s=s.replace(old,new,1)
rep('''                val config = JSONObject(configString)
                // Remember only business and timestamps against a hashed''',
'''                val config = JSONObject(configString)
                val cadenceSettings=config.optJSONObject("settings")?.optJSONObject("cadence")
                // Remember only business and timestamps against a hashed''')
rep('''                val pending=fresh && AssistantCadence.awaitingChoice(
                    now,previous.optLong("promptAt",0L),
                    previous.optBoolean("pendingChoice",false))''',
'''                val pending=fresh && previous.optBoolean("pendingChoice",false) &&
                    AssistantCadence.recent(now,previous.optLong("promptAt",0L),
                        CadencePolicy.menu(cadenceSettings))''')
rep('''                    val menuCooling=AssistantCadence.menuCooling(now,menuAt,decision.needsChoice)''',
'''                    val menuCooling=decision.needsChoice && AssistantCadence.recent(
                        now,menuAt,CadencePolicy.menu(cadenceSettings))''')
rep('''                    val awayCooling=AssistantCadence.awayCooling(
                        now,cadencePrefs.getLong(awayKey,0L),outsideHours)''',
'''                    val awayCooling=outsideHours && AssistantCadence.recent(
                        now,cadencePrefs.getLong(awayKey,0L),
                        CadencePolicy.away(cadenceSettings))''')
rep('''                    val greetingCooling=AssistantCadence.greetingCooling(
                        now,cadencePrefs.getLong(greetingKey,0L),contextGreeting)''',
'''                    val greetingCooling=contextGreeting && AssistantCadence.recent(
                        now,cadencePrefs.getLong(greetingKey,0L),
                        CadencePolicy.greeting(cadenceSettings))''')
rep('''                            AssistantCadence.COURTESY_MS)''',
'''                            CadencePolicy.thanks(cadenceSettings))''')
rep('''                            AssistantCadence.IDENTICAL_MS)''',
'''                            CadencePolicy.repeated(cadenceSettings))''')
p.write_text(s,encoding="utf-8")

p=root/"web/app.js"
s=p.read_text(encoding="utf-8")
a='''  state.settings.learningEnabled ??= true;'''
b='''  state.settings.learningEnabled ??= true;
  // Explicit local settings for conversation cadence; never synced to a server.
  state.settings.cadence ||= {menuHours:12,awayHours:12,greetingHours:12,
    courtesyMinutes:15,repeatMinutes:2};'''
assert s.count(a)==1
s=s.replace(a,b,1)
a='''  function renderSettings(){return '''
b='''  function cadenceSettingsPanel(){
    const defs=[
      ["menuHours","Menú para elegir negocio","horas",1,24,12],
      ["awayHours","Aviso fuera de horario","horas",1,24,12],
      ["greetingHours","Saludo repetido","horas",1,24,12],
      ["courtesyMinutes","Agradecimientos","minutos",1,180,15],
      ["repeatMinutes","Respuesta comercial idéntica","minutos",1,30,2]
    ];
    const panel=defs.map(([key,label,unit,min,max,fallback])=>
      '<div class="form-control"><label>'+label+'</label>'+
      '<div class="row"><input class="field" type="number" inputmode="numeric"'+
      ' min="'+min+'" max="'+max+'" step="1" data-cadence="'+key+'" value="'+
      safe(state.settings.cadence?.[key]??fallback)+'"><span class="small muted">'+unit+
      '</span></div></div>').join("");
    return '<div class="card stack" style="margin-bottom:16px"><div class="between">'+
      '<h2>🔕 Frecuencia de respuestas automáticas</h2><span class="pill">Por chat y WhatsApp</span></div>'+
      '<p class="small muted">Configura cuánto tiempo pasa antes de repetir un menú, saludo o aviso. '+
      'Las consultas nuevas sobre un producto o pago no se retrasan por estas opciones.</p>'+
      '<div class="grid cols2">'+panel+'</div>'+
      '<div class="notice">Los cambios se guardan solo en este dispositivo. '+
      'El catálogo y los precios siguen siendo locales y editables; sin conexión externa.</div></div>';
  }
  function renderSettings(){return cadenceSettingsPanel()+'''
assert s.count(a)==1
s=s.replace(a,b,1)
a='''    if(t.dataset.dayEnabled){'''
b='''    if(t.dataset.cadence){
      const key=t.dataset.cadence;
      const bounds={menuHours:[1,24],awayHours:[1,24],greetingHours:[1,24],
        courtesyMinutes:[1,180],repeatMinutes:[1,30]};
      if(!Object.hasOwn(bounds,key))return;
      const [min,max]=bounds[key],numeric=Number(t.value);
      if(!Number.isInteger(numeric)||numeric<min||numeric>max){
        notify("El valor debe estar entre "+min+" y "+max+".");render();return;
      }
      state.settings.cadence ||= {};
      state.settings.cadence[key]=numeric;
      save();render();notify("Frecuencia guardada.");return;
    }
    if(t.dataset.dayEnabled){'''
assert s.count(a)==1
s=s.replace(a,b,1)
p.write_text(s,encoding="utf-8")
(root/"android/app/src/main/assets/app.js").write_text(s,encoding="utf-8")
print("Configurable per-chat cooldowns in Settings, with native validated limits and zero external synchronization")
