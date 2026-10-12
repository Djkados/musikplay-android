from pathlib import Path
root=Path("source/autoresponder-pro/android/app/src/main/java/com/autoresponder/pro")
(root/"ApprovedLearning.kt").write_text(r'''package com.autoresponder.pro

import org.json.JSONObject
import java.text.Normalizer
import java.util.Locale

/**
 * Owner-approved short phrases mapped to existing safe response families.
 * This is NOT autonomous AI training; it is deterministic offline routing.
 * Never persist or infer banking credentials from phrases.
 */
internal object ApprovedLearning {
    data class Intent(val name:String,val phrase:String)
    private val kinds=setOf("payment","payment_nequi","payment_bancolombia",
        "payment_daviplata","payment_llave","courtesy","renewal","human")
    fun normalize(s:String):String=Normalizer.normalize(s.lowercase(Locale.ROOT),
        Normalizer.Form.NFD).replace(Regex("\\p{M}+"),"")
        .replace(Regex("[^a-z0-9 ]+")," ").replace(Regex("\\s+")," ").trim()
    fun valid(raw:String,intent:String):Boolean {
        if(intent !in kinds || raw.length !in 4..100)return false
        val n=normalize(raw)
        if(n.length !in 4..90 || raw.any {it.isDigit() || it=='@'})return false
        if(raw.contains("://")||raw.contains("www.")||raw.contains("/") ||
            raw.contains("content:"))return false
        if(IncomingSafety.isPaymentEvidence(raw))return false
        if(Regex("\\b(comprobante|recibo|adjunto|foto|imagen|captura|documento|"+
            "transferencia realizada|ya pague|renovado|contrasena|password|"+
            "clave|token|pin|otp|cedula|tarjeta|direccion|numero de tarjeta)\\b")
            .containsMatchIn(n))return false
        if(n in setOf("pago","cuenta","info","ok","hola","si","no","dinero","plata"))
            return false
        if(intent.startsWith("payment") &&
            n.split(" ").size==1 &&
            n !in setOf("nequi","daviplata","bancolombia","llave"))
            return false
        return n.isNotBlank()
    }
    fun match(config:JSONObject,text:String):Intent? {
        val n=normalize(text)
        val candidates=mutableSetOf(n)
        for(prefix in listOf("hola ","buenas ","buenos dias ","buenas tardes ",
            "buenas noches ","oye ","oe ","porfa ","por favor ")) {
            if(n.startsWith(prefix))candidates.add(n.removePrefix(prefix).trim())
        }
        val arr=config.optJSONArray("intentAliases")?:return null
        for(i in 0 until minOf(100,arr.length())){
            val alias=arr.optJSONObject(i)?:continue
            val kind=alias.optString("intent")
            val raw=alias.optString("phrase")
            if(!alias.optBoolean("active",false) || !valid(raw,kind))continue
            if(normalize(raw) in candidates)return Intent(kind,normalize(raw))
        }
        return null
    }

    fun respond(config:JSONObject,intent:Intent,rememberedBusiness:String?,
        sellerBusiness:String?):NativeAutoReplyEngine.Decision? {
        val kind=intent.name
        if(kind=="human")return NativeAutoReplyEngine.Decision(
            reason="Asociación aprobada: requiere atención humana",
            routeSource="manual_review")
        if(kind=="courtesy")return NativeAutoReplyEngine.Decision(
            text=CourtesyReplies.message,reason="Agradecimiento aprendido y aprobado",
            routeSource="courtesy")
        if(kind=="renewal"){
            if(sellerBusiness=="tresm" || rememberedBusiness=="tresm")return null
            return NativeAutoReplyEngine.Decision(text=RenewalReplies.MESSAGE,
                business="movieplay",reason="Renovación solicitada con frase aprobada",
                routeSource="renewal")
        }
        val paymentMethod=when(kind){
            "payment" -> "medios de pago"
            "payment_nequi" -> "Nequi"
            "payment_bancolombia" -> "Bancolombia"
            "payment_daviplata" -> "DaviPlata"
            "payment_llave" -> "Llave"
            else -> return null
        }
        val bank=PaymentReplies.reply(config,"movieplay",paymentMethod,casual=true)
            ?:return null
        return NativeAutoReplyEngine.Decision(text=bank.text,
            business=rememberedBusiness?.takeIf{it=="movieplay" || it=="tresm"},
            reason="Medio de pago con frase aprobada",
            routeSource="payment_specific",paymentMenu=bank.isMenu)
    }
}
''',encoding="utf-8")

p=root/"NativeAutoReplyEngine.kt"
s=p.read_text(encoding="utf-8")
needle='''        val seller=sellerBusiness(config,channel,c)
        if(seller!=null) {'''
replacement='''        val seller=sellerBusiness(config,channel,c)
        val approved=ApprovedLearning.match(config,m)
        val approvedAnswer=approved?.let {
            ApprovedLearning.respond(config,it,rememberedBusiness,seller)
        }
        if(seller!=null) {
            if(approvedAnswer!=null)return approvedAnswer'''
assert s.count(needle)==1
s=s.replace(needle,replacement,1)
needle='''        if(humanHandoff){
            if(RenewalReplies.isRequest(m)'''
replacement='''        if(humanHandoff){
            if(approvedAnswer!=null)return approvedAnswer
            if(RenewalReplies.isRequest(m)'''
assert s.count(needle)==1
s=s.replace(needle,replacement,1)
needle='''        // A renewal acknowledgment is NOT proof that it was processed. It is'''
replacement='''        // Approved phrases may route to built-in thank-you, payment,
        // renewal or manual-review response. Never run before safety checks.
        if(approvedAnswer!=null)return approvedAnswer
        // A renewal acknowledgment is NOT proof that it was processed. It is'''
assert s.count(needle)==1
s=s.replace(needle,replacement,1)
p.write_text(s,encoding="utf-8")
print("Native Android recognizes owner-approved exact/safe aliases for payment, bank, gratitude, renewal and human attention without touching catalog or receipts.")
