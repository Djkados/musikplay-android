from pathlib import Path
root=Path("source/autoresponder-pro")
native=root/"android/app/src/main/java/com/autoresponder/pro"
(native/"AssistantCadence.kt").write_text('''package com.autoresponder.pro

/** Offline per-chat message frequency rules. Times are epoch milliseconds. */
internal object AssistantCadence {
    const val MENU_MS=12L*60L*60L*1000L
    const val AWAY_MS=12L*60L*60L*1000L
    const val GREETING_MS=12L*60L*60L*1000L
    const val COURTESY_MS=15L*60L*1000L
    const val IDENTICAL_MS=2L*60L*1000L

    fun recent(now:Long,last:Long,window:Long)=
        last>0L && now>=last && now-last<window
    fun awaitingChoice(now:Long,last:Long,pending:Boolean)=
        pending && recent(now,last,MENU_MS)
    fun menuCooling(now:Long,last:Long,menu:Boolean)=
        menu && recent(now,last,MENU_MS)
    fun awayCooling(now:Long,last:Long,away:Boolean)=
        away && recent(now,last,AWAY_MS)
    fun greetingCooling(now:Long,last:Long,greeting:Boolean)=
        greeting && recent(now,last,GREETING_MS)
}
''',encoding="utf-8")
p=native/"WhatsAppNotificationListener.kt"
s=p.read_text(encoding="utf-8")
def rep(a,b):
 global s
 assert s.count(a)==1,("listener anchor",a[:85],s.count(a))
 s=s.replace(a,b,1)
rep('''                val pending=fresh && previous.optBoolean("pendingChoice",false) &&
                    now-previous.optLong("promptAt",0L) in 0L until 600_000L''',
'''                // A 1/2 or named business choice stays actionable for 12 hours.
                val pending=fresh && AssistantCadence.awaitingChoice(
                    now,previous.optLong("promptAt",0L),
                    previous.optBoolean("pendingChoice",false))''')
rep('''                    val courtesyKey=fingerprint("courtesy|$channel|$contact")
                    val lastCourtesy=throttle.getLong(courtesyKey,0L)
                    val courtesyCooling=decision.routeSource=="courtesy" &&
                        lastCourtesy>0L && now-lastCourtesy in 0L until (90L*1000L)
                    val repeatedPrompt=decision.needsChoice && pending
                    val rapid=sinceLast in 0L until 20_000L &&
                        decision.routeSource !in setOf("choice","detected","payment_choice","payment_specific","courtesy")
                    if(repeatedPrompt || rapid || courtesyCooling) {
                        incoming.put("autoStatus",when {
                            repeatedPrompt -> "clarification_waiting"
                            courtesyCooling -> "courtesy_throttled"
                            else -> "throttled"
                        })
                    } else {''',
'''                    // Preferences store hashed keys only, separately per WhatsApp.
                    // A prompt timestamp from the previous app version is honored
                    // immediately after an update.
                    val cadencePrefs=getSharedPreferences("assistant_cadence",Context.MODE_PRIVATE)
                    val menuKey=fingerprint("menu|$channel|$contact")
                    val formerPromptAt=if(previous.optBoolean("pendingChoice",false))
                        previous.optLong("promptAt",0L) else 0L
                    val menuAt=maxOf(formerPromptAt,cadencePrefs.getLong(menuKey,0L))
                    val menuCooling=AssistantCadence.menuCooling(now,menuAt,decision.needsChoice)

                    // Sales/support and MoviePlay/Las Tres M have separate away notices.
                    val awayKey=fingerprint("away|$channel|$contact|"+
                        decision.business.orEmpty()+"|"+decision.department.orEmpty())
                    val outsideHours=decision.reason=="Fuera de horario"
                    val awayCooling=AssistantCadence.awayCooling(
                        now,cadencePrefs.getLong(awayKey,0L),outsideHours)

                    val greetingText=NativeAutoReplyEngine.normalize(message)
                    val genericHello=greetingText in setOf("hola","buenas","buenos dias",
                        "buenas tardes","buenas noches","hola buenas")
                    val contextGreeting=decision.reason=="Consulta en contexto" && genericHello
                    val greetingKey=fingerprint("greeting|$channel|$contact|"+
                        decision.business.orEmpty())
                    val greetingCooling=AssistantCadence.greetingCooling(
                        now,cadencePrefs.getLong(greetingKey,0L),contextGreeting)

                    val courtesyKey=fingerprint("courtesy|$channel|$contact")
                    val courtesyCooling=decision.routeSource=="courtesy" &&
                        AssistantCadence.recent(now,throttle.getLong(courtesyKey,0L),
                            AssistantCadence.COURTESY_MS)

                    val duplicateReplyKey=fingerprint("answer|$channel|$contact|"+
                        decision.text.orEmpty())
                    val duplicateReply=decision.routeSource !in
                        setOf("choice","payment_choice","payment_specific","courtesy") &&
                        AssistantCadence.recent(now,
                            cadencePrefs.getLong(duplicateReplyKey,0L),
                            AssistantCadence.IDENTICAL_MS)
                    val rapid=sinceLast in 0L until 20_000L &&
                        decision.routeSource !in
                            setOf("choice","detected","payment_choice","payment_specific","courtesy")

                    if(menuCooling || awayCooling || greetingCooling ||
                        courtesyCooling || duplicateReply || rapid) {
                        incoming.put("autoStatus",when {
                            menuCooling -> "menu_cooldown_12h"
                            awayCooling -> "away_cooldown_12h"
                            greetingCooling -> "greeting_cooldown_12h"
                            courtesyCooling -> "courtesy_throttled"
                            duplicateReply -> "repeat_answer_suppressed"
                            else -> "throttled"
                        })
                    } else {''')
rep('''                                if(decision.routeSource=="courtesy")
                                    throttle.edit().putLong(courtesyKey,now).apply()
                                // Persist route only after Android accepts the send.''',
'''                                if(decision.routeSource=="courtesy")
                                    throttle.edit().putLong(courtesyKey,now).apply()
                                // Do not consume a cooldown until Android accepts
                                // the outgoing reply action.
                                val edit=cadencePrefs.edit()
                                if(decision.needsChoice)edit.putLong(menuKey,now)
                                if(outsideHours)edit.putLong(awayKey,now)
                                if(contextGreeting)edit.putLong(greetingKey,now)
                                edit.putLong(duplicateReplyKey,now).apply()
                                // Persist route only after Android accepts the send.''')
p.write_text(s,encoding="utf-8")
p=root/"web/app.js"
s=p.read_text(encoding="utf-8")
anchor="courtesy_throttled:'Ya se agradeció a este contacto recientemente',"
assert s.count(anchor)==1
s=s.replace(anchor,anchor+"""
      menu_cooldown_12h:'Menú ya enviado: esperando elección sin repetirlo por 12 horas',
      away_cooldown_12h:'Horario informado: no repetir aviso por 12 horas',
      greeting_cooldown_12h:'Saludo inicial enviado: no repetirlo por 12 horas',
      repeat_answer_suppressed:'Respuesta idéntica ya enviada hace poco',""",1)
s=s.replace("AutoResponder Pro v0.6.2","AutoResponder Pro v0.6.3",1)
p.write_text(s,encoding="utf-8")
(root/"android/app/src/main/assets/app.js").write_text(s,encoding="utf-8")
p=root/"android/app/build.gradle.kts"
s=p.read_text(encoding="utf-8")
assert s.count('versionCode = 17')==1 and s.count('versionName = "0.6.2"')==1
p.write_text(s.replace('versionCode = 17','versionCode = 18')
    .replace('versionName = "0.6.2"','versionName = "0.6.3"'),encoding="utf-8")
for name in ["web/index.html","android/app/src/main/assets/index.html"]:
 p=root/name
 p.write_text(p.read_text(encoding="utf-8").replace("Versión 0.6.2","Versión 0.6.3"),
              encoding="utf-8")
print("0.6.3: 12h menu, 12h away and greeting, 15m courtesy, 2m duplicate commercial reply cooldown")
