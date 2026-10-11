from pathlib import Path

root=Path("source/autoresponder-pro")
source=root/"android/app/src/main/java/com/autoresponder/pro"
p=source/"CourtesyReplies.kt"
p.write_text(r'''package com.autoresponder.pro

import java.text.Normalizer
import java.util.Locale

/** Reply to stand-alone thanks; never mistake a payment, request or receipt for gratitude. */
internal object CourtesyReplies {
    const val message = "Gracias por confiar en nuestro servicio. 🙌\n" +
        "Para nosotros es un honor poder atenderte y ayudarte."

    private val spanish=Regex(
        """^(?:(?:ok|vale|listo|perfecto)\s+)?(?:(?:muchas?|mil|muchisimas|infinitas|de verdad|un millon de)\s+)?""" +
        """(?:gracias+|grasias+|grax+|grx+)(?:\s+(?:por todo|por tu ayuda|por la ayuda|por su ayuda|por ayudarme|de corazon|de verdad|muy amable|a ustedes|mucho))?$"""
    )
    private val english=Regex(
        """^(?:tenkiu+s?|tenkyu+s?|tenquiu+s?|tenkius|thank\s*(?:you|u)|thanks+|thankss+|thankyou|thanx+|thx+|tnx+|tks+)(?:\s+(?:much|so much|very much|mucho))?$"""
    )
    private val extra=Regex(
        """^(?:te lo agradezco(?: mucho)?|se le agradece|muy amable gracias|que amable gracias|gracias muy amable|muchas gracias por todo|muchisimas gracias por todo)$"""
    )

    fun matches(text:String):Boolean {
        val clean=Normalizer.normalize(text.lowercase(Locale.ROOT),Normalizer.Form.NFD)
            .replace(Regex("\\p{M}+"),"")
            .replace(Regex("[^a-z0-9 ]+")," ")
            .replace(Regex("\\s+")," ").trim()
        if(clean.length !in 2..90)return false
        return spanish.matches(clean) || english.matches(clean) || extra.matches(clean)
    }
}
''',encoding="utf-8")

p=source/"NativeAutoReplyEngine.kt"
s=p.read_text(encoding="utf-8")
anchor='''        val route=assignedBusiness(config,channel,c,m,rememberedBusiness,awaitingChoice)'''
assert s.count(anchor)==1
s=s.replace(anchor,'''        // A short expression of gratitude is universal to both businesses.
        // This deliberately runs after consent, exclusions, safety and pauses,
        // but before business identification and out-of-hours messages.
        if(CourtesyReplies.matches(m))
            return Decision(text=CourtesyReplies.message,reason="Agradecimiento automático",
                routeSource="courtesy")
'''+anchor,1)
p.write_text(s,encoding="utf-8")

# Let customers thank the shop right after a purchase reply without being held
# by the general anti-burst limit. Keep an independent courtesy cooldown to
# avoid sending several thank-yous to a rapid series of appreciative messages.
p=source/"WhatsAppNotificationListener.kt"
s=p.read_text(encoding="utf-8")
a='''                    val sinceLast=now-throttle.getLong(conversationKey,0L)
                    val repeatedPrompt=decision.needsChoice && pending'''
b='''                    val sinceLast=now-throttle.getLong(conversationKey,0L)
                    val courtesyKey=fingerprint("courtesy|$channel|$contact")
                    val lastCourtesy=throttle.getLong(courtesyKey,0L)
                    val courtesyCooling=decision.routeSource=="courtesy" &&
                        lastCourtesy>0L && now-lastCourtesy in 0L until (90L*1000L)
                    val repeatedPrompt=decision.needsChoice && pending'''
assert s.count(a)==1
s=s.replace(a,b,1)
a='''decision.routeSource !in setOf("choice","detected","payment_choice","payment_specific")'''
b='''decision.routeSource !in setOf("choice","detected","payment_choice","payment_specific","courtesy")'''
assert s.count(a)==1
s=s.replace(a,b,1)
a='''                    if(repeatedPrompt || rapid) {
                        incoming.put("autoStatus",
                            if(repeatedPrompt)"clarification_waiting" else "throttled")'''
b='''                    if(repeatedPrompt || rapid || courtesyCooling) {
                        incoming.put("autoStatus",when {
                            repeatedPrompt -> "clarification_waiting"
                            courtesyCooling -> "courtesy_throttled"
                            else -> "throttled"
                        })'''
assert s.count(a)==1
s=s.replace(a,b,1)
a='''                                action.actionIntent.send(this,0,intent)
                                // Persist route only after Android accepts the send.'''
b='''                                action.actionIntent.send(this,0,intent)
                                if(decision.routeSource=="courtesy")
                                    throttle.edit().putLong(courtesyKey,now).apply()
                                // Persist route only after Android accepts the send.'''
assert s.count(a)==1
s=s.replace(a,b,1)
p.write_text(s,encoding="utf-8")

# The in-app simulator uses exactly the same text and tight phrase matching.
p=root/"web/app.js"
s=p.read_text(encoding="utf-8")
a='''  function respond(channel,contact,text,group=false,at=new Date()){'''
new=r'''  const COURTESY_RESPONSE="Gracias por confiar en nuestro servicio. 🙌\nPara nosotros es un honor poder atenderte y ayudarte.";
  function courtesyReply(text) {
    const value=normalize(text).replace(/[^a-z0-9 ]+/g," ").replace(/\s+/g," ").trim();
    if(value.length<2||value.length>90)return null;
    const spanish=/^(?:(?:ok|vale|listo|perfecto)\s+)?(?:(?:muchas?|mil|muchisimas|infinitas|de verdad|un millon de)\s+)?(?:gracias+|grasias+|grax+|grx+)(?:\s+(?:por todo|por tu ayuda|por la ayuda|por su ayuda|por ayudarme|de corazon|de verdad|muy amable|a ustedes|mucho))?$/;
    const english=/^(?:tenkiu+s?|tenkyu+s?|tenquiu+s?|tenkius|thank\s*(?:you|u)|thanks+|thankss+|thankyou|thanx+|thx+|tnx+|tks+)(?:\s+(?:much|so much|very much|mucho))?$/;
    const extra=/^(?:te lo agradezco(?: mucho)?|se le agradece|muy amable gracias|que amable gracias|gracias muy amable|muchas gracias por todo|muchisimas gracias por todo)$/;
    return spanish.test(value)||english.test(value)||extra.test(value)?COURTESY_RESPONSE:null;
  }
''' +a
assert s.count(a)==1
s=s.replace(a,new,1)
a='''    const assign=assignmentFor(channel,contact,text);'''
b='''    const thanks=courtesyReply(text);
    if(thanks)return {reply:thanks,assistant:null,unit:null,
      method:"courtesy",status:"open",image:null};
    const assign=assignmentFor(channel,contact,text);'''
assert s.count(a)==1
s=s.replace(a,b,1)
a="throttled:'Espera breve para evitar respuestas repetidas',"
b="throttled:'Espera breve para evitar respuestas repetidas',courtesy_throttled:'Ya se agradeció a este contacto recientemente',"
assert s.count(a)==1
s=s.replace(a,b,1)
s=s.replace("AutoResponder Pro v0.6.1","AutoResponder Pro v0.6.2",1)
p.write_text(s,encoding="utf-8")
(root/"android/app/src/main/assets/app.js").write_text(s,encoding="utf-8")

# Stable signing config from v0.6.1 stays untouched. Only version increases.
p=root/"android/app/build.gradle.kts"
s=p.read_text(encoding="utf-8")
assert s.count('versionCode = 16')==1 and s.count('versionName = "0.6.1"')==1
p.write_text(s.replace('versionCode = 16','versionCode = 17')
              .replace('versionName = "0.6.1"','versionName = "0.6.2"'),encoding="utf-8")
for f in ["web/index.html","android/app/src/main/assets/index.html"]:
    p=root/f
    h=p.read_text(encoding="utf-8")
    p.write_text(h.replace("Versión 0.6.1","Versión 0.6.2"),encoding="utf-8")

print("v0.6.2 gratitude reply: isolated channel-safe thanks, media/receipt exclusion, own-message echo and courtesy cooldown")
