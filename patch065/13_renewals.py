from pathlib import Path

root=Path("source/autoresponder-pro")
native=root/"android/app/src/main/java/com/autoresponder/pro"
(native/"RenewalReplies.kt").write_text(r'''package com.autoresponder.pro

import java.text.Normalizer
import java.util.Locale

/**
 * Only acknowledge a request to renew, never claim an actual renewal.
 * Excludes questions about prices/expiry, cancellation and completed renewals.
 */
internal object RenewalReplies {
    const val MESSAGE="Claro 😊, dame un momento y te confirmo la renovación."
    private fun clean(raw:String):String=
        Normalizer.normalize(raw.lowercase(Locale.ROOT),Normalizer.Form.NFD)
            .replace(Regex("\\p{M}+"),"")
            .replace(Regex("[^a-z0-9 ]+")," ")
            .replace(Regex("\\s+")," ").trim()

    // Digest input only: individual renewal requests can arrive minutes apart.
    // Chat content and customer identifiers are never saved in plain text.
    fun repeatIdentity(text:String):String=clean(text)

    fun isRequest(text:String):Boolean {
        val n=clean(text)
        if(n.length !in 6..180)return false
        if(Regex("\\b(no renovar|no renueva|no renueves|no quiero renovar|"+
            "cancelar la renovacion|cancelar renovacion|ya renove|ya me renovaron|"+
            "ya esta renovado|renovacion confirmada|renovado|renovada|"+
            "cuando renueva|cuando se renueva|cuanto cuesta renovar|"+
            "cuanto vale renovar|precio de renovacion|como renovar|"+
            "como renuevo|fecha de renovacion|cuando vence|renovacion pendiente de pago)\\b")
            .containsMatchIn(n))return false

        val verb=Regex("\\b(renueva|renuevame|renuevamelo|renuevalo|renuevala|"+
            "renueven|renuevenme|renuevas|renovame|renovar|renovarme|renovacion)\\b")
        if(!verb.containsMatchIn(n))return false

        if(Regex("^(cuanto|como|cuando|donde|cual|por que|porque|que precio)\\b")
            .containsMatchIn(n))return false

        return Regex("^(?:hola|buenas|oye|oe|ey|por favor|porfa|porfis|listo|"+
            "quiero|quisiera|necesito|me puedes|me podrias|puedes|podrias|"+
            "por favor me|favor|vamos a|me ayudas a|te pido|te agradezco si|"+
            "hazme|hagame|hagamos|dale|puedo|otra vez|me hace el favor y|"+
            "te escribo para|deseo|si|bueno)\\b").containsMatchIn(n) ||
            n.startsWith("renuev") || n.startsWith("renov") ||
            Regex("\\bme renuevas\\b|\\bque me renueven\\b|\\bme lo renuevas\\b")
                .containsMatchIn(n)
    }
}
''',encoding="utf-8")
p=native/"NativeAutoReplyEngine.kt"
s=p.read_text(encoding="utf-8")
def rep(a,b):
 global s
 assert s.count(a)==1,("native engine",a[:90],s.count(a))
 s=s.replace(a,b,1)
# Explicit sellers only get acknowledgements + payments, never prices, menus.
rep('''        if(seller!=null) {
            // In this mode no catalog''',
'''        if(seller!=null) {
            if(seller=="movieplay" && RenewalReplies.isRequest(m))
                return Decision(text=RenewalReplies.MESSAGE,business="movieplay",
                    reason="Solicitud de renovación pendiente de revisión",
                    routeSource="renewal")
            // In this mode no catalog''')
rep('''        val paused=config.optJSONArray("paused")''',
'''        val paused=config.optJSONArray("paused")''')
rep('''        if(humanHandoff){
            if(CourtesyReplies.matches(m))''',
'''        if(humanHandoff){
            if(RenewalReplies.isRequest(m) && rememberedBusiness!="tresm")
                return Decision(text=RenewalReplies.MESSAGE,business="movieplay",
                    reason="Solicitud de renovación pendiente de revisión",
                    routeSource="renewal")
            if(CourtesyReplies.matches(m))''')
rep('''        // A short expression of gratitude is universal to both businesses.''',
'''        // A renewal acknowledgment is NOT proof that it was processed. It is
        // allowed 24/7, including outside MoviePlay sales hours.
        if(RenewalReplies.isRequest(m) && rememberedBusiness!="tresm")
            return Decision(text=RenewalReplies.MESSAGE,business="movieplay",
                reason="Solicitud de renovación pendiente de revisión",
                routeSource="renewal")
        // A short expression of gratitude is universal to both businesses.''')
p.write_text(s,encoding="utf-8")

p=native/"WhatsAppNotificationListener.kt"
s=p.read_text(encoding="utf-8")
a='''                    val courtesyKey=fingerprint("courtesy|$channel|$contact")'''
b='''                    // Only identical renewal requests have a 1-hour repeat limit.
                    // Different customer names, service or sale IDs get new keys.
                    val renewalKey=fingerprint("renewal|$channel|$contact|"+
                        RenewalReplies.repeatIdentity(message))
                    val renewalAt=cadencePrefs.getLong(renewalKey,0L)
                    val renewalCooling=decision.routeSource=="renewal" &&
                        AssistantCadence.recent(now,renewalAt,60L*60L*1000L)

                    val courtesyKey=fingerprint("courtesy|$channel|$contact")'''
assert s.count(a)==1
s=s.replace(a,b,1)
a='''                        setOf("choice","payment_choice","payment_specific","courtesy") &&'''
b='''                        setOf("choice","payment_choice","payment_specific","courtesy","renewal") &&'''
assert s.count(a)==1
s=s.replace(a,b,1)
a='''                            setOf("choice","detected","payment_choice","payment_specific","courtesy","memory")'''
b='''                            setOf("choice","detected","payment_choice","payment_specific","courtesy","renewal")'''
assert s.count(a)==1
s=s.replace(a,b,1)
a='''                    if(menuCooling || awayCooling || greetingCooling ||
                        courtesyCooling || duplicateReply || rapid) {'''
b='''                    if(menuCooling || awayCooling || greetingCooling ||
                        courtesyCooling || renewalCooling || duplicateReply || rapid) {'''
assert s.count(a)==1
s=s.replace(a,b,1)
a='''                            courtesyCooling -> "courtesy_throttled"'''
b='''                            courtesyCooling -> "courtesy_throttled"
                            renewalCooling -> "renewal_cooldown_1h"'''
assert s.count(a)==1
s=s.replace(a,b,1)
a='''                                if(decision.needsChoice)edit.putLong(menuKey,now)'''
b='''                                if(decision.needsChoice)edit.putLong(menuKey,now)
                                if(decision.routeSource=="renewal")edit.putLong(renewalKey,now)'''
assert s.count(a)==1
s=s.replace(a,b,1)
p.write_text(s,encoding="utf-8")

p=root/"web/app.js"
s=p.read_text(encoding="utf-8")
a='''  const COURTESY_RESPONSE='''
b='''  function renewalRequest(text){
    const n=normalize(text).replace(/[^a-z0-9 ]+/g," ").replace(/\\s+/g," ").trim();
    if(n.length<6||n.length>180)return false;
    if(/\\b(no renovar|no renueva|no renueves|no quiero renovar|cancelar (?:la )?renovacion|ya renove|ya me renovaron|ya esta renovado|renovacion confirmada|renovado|renovada|cuando renueva|cuando se renueva|cuanto cuesta renovar|cuanto vale renovar|precio de renovacion|como renovar|como renuevo|fecha de renovacion|cuando vence)\\b/.test(n))return false;
    if(/^\\s*(cuanto|como|cuando|donde|cual|por que|porque|que precio)\\b/.test(n))return false;
    if(!/\\b(renueva|renuevame|renuevamelo|renuevalo|renuevala|renueven|renuevenme|renuevas|renovame|renovar|renovarme|renovacion)\\b/.test(n))return false;
    return /^(hola|buenas|oye|oe|ey|por favor|porfa|porfis|listo|quiero|quisiera|necesito|me puedes|me podrias|puedes|podrias|favor|vamos a|me ayudas a|te pido|hazme|hagame|hagamos|dale|otra vez|me hace el favor y|te escribo para|deseo|si|bueno)\\b/.test(n) ||
      n.startsWith("renuev") || n.startsWith("renov") ||
      /\\bme renuevas\\b|\\bque me renueven\\b|\\bme lo renuevas\\b/.test(n);
  }
  const RENEWAL_ACK="Claro 😊, dame un momento y te confirmo la renovación.";
  const COURTESY_RESPONSE='''
assert s.count(a)==1
s=s.replace(a,b,1)
a='''    const thanks=courtesyReply(text);'''
b='''    const sellerMarked=sellerFor(channel,contact);
    if(renewalRequest(text) && (!sellerMarked || sellerMarked.assistant==="movieplay"))
      return {reply:RENEWAL_ACK,assistant:"movieplay",unit:"sales",
        method:"renewal",status:"open",image:null};
    const thanks=courtesyReply(text);'''
assert s.count(a)==1
s=s.replace(a,b,1)
a='''      repeat_answer_suppressed:'Respuesta idéntica ya enviada hace poco','''
b='''      repeat_answer_suppressed:'Respuesta idéntica ya enviada hace poco',
      renewal_cooldown_1h:'Ya confirmé que revisaré esta renovación; no repetir durante una hora','''
assert s.count(a)==1
s=s.replace(a,b,1)
p.write_text(s,encoding="utf-8")
(root/"android/app/src/main/assets/app.js").write_text(s,encoding="utf-8")
print("Renewal acknowledgment for customers and sellers, no auto-activation, one-hour per-request cooldown and payment/media exclusions")
