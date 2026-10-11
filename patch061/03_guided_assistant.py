from pathlib import Path
root=Path("source/autoresponder-pro/android/app/src/main/java/com/autoresponder/pro")
p=root/"GuidedAssistant.kt"
p.write_text(r'''package com.autoresponder.pro

import org.json.JSONObject
import java.time.LocalDate

/**
 * Local, deterministic pre-sales guidance. It never accepts an order, verifies
 * payment, allocates an account, promises delivery, or initiates a WhatsApp chat.
 */
internal object GuidedAssistant {
    data class Guidance(val text:String,val reason:String,val imageTag:String="")
    fun wantsHuman(normalized:String):Boolean =
        Regex("\\b(asesor humano|asesora humana|persona real|atencion personal|"+
            "hablar con alguien|hablar con asesor|hablar con una persona|"+
            "necesito un asesor|quiero hablar contigo|me atiendes tu|"+
            "llamame|llamenme|operador humano)\\b").containsMatchIn(normalized)

    fun suggest(config:JSONObject,business:String,message:String,day:LocalDate):Guidance? {
        val n=NativeAutoReplyEngine.normalize(message)
        val wantsOrder=Regex("\\b(quiero comprar|quiero contratar|me interesa|"+
            "quiero adquirir|como compro|como comprar|hacer una compra|"+
            "quiero renovar|comprar el servicio|quiero pedir|hacer un pedido|"+
            "quiero un domicilio|me lo llevo|lo quiero comprar|para comprar|"+
            "para pedir|necesito un pedido|quiero ordenar)\\b").containsMatchIn(n)
        if(!wantsOrder)return null
        val quote=LocalCatalog.reply(config,business,message,day)
        val header=if(business=="movieplay")"🎬 *MOVIEPLAY*" else "🍔 *LAS TRES M*"
        if(business=="movieplay"){
            val intro=quote?.text ?: "$header\n\n🛒 *Solicitud de compra*"
            val extra=if(quote!=null && quote.imageTag.isBlank())
                "Este plan figura como no disponible. Puedes preguntarnos por otra opción."
            else "📌 *Para continuar:*\n1️⃣ Indica plataforma y duración.\n"+
                "2️⃣ Confirma cuál plan te interesa.\n3️⃣ Solicita el medio de pago que prefieras.\n\n"+
                "🔐 La disponibilidad, el comprobante y la entrega se verifican antes de activar el servicio."
            return Guidance("$intro\n\n$extra","Compra guiada; pendiente de confirmación",
                quote?.imageTag.orEmpty())
        }
        if(business=="tresm"){
            val intro=quote?.text ?: "$header\n\n🍟 *Preparar tu pedido*"
            val extra=if(quote!=null && quote.imageTag.isBlank())
                "Este producto aparece no disponible. ¿Deseas consultar otra alternativa?"
            else "📝 *Para preparar tu solicitud:*\n1️⃣ Dinos los productos y cantidades.\n"+
                "2️⃣ Indica adiciones o cambios.\n3️⃣ Confirma si es para recoger o a domicilio.\n\n"+
                "📍 Para domicilio, comparte la dirección directamente en WhatsApp.\n"+
                "✅ El pedido y el valor final se confirman cuando lo revisemos."
            return Guidance("$intro\n\n$extra","Solicitud de pedido; falta revisión",
                quote?.imageTag.orEmpty())
        }
        return null
    }
}
''',encoding="utf-8")
p=root/"NativeAutoReplyEngine.kt"
s=p.read_text(encoding="utf-8")
a='''        if(IncomingSafety.isPaymentEvidence(m))
            return Decision(reason="Comprobante o pago reportado: verificar manualmente",
                routeSource="manual_review")'''
b='''        if(IncomingSafety.isPaymentEvidence(m))
            return Decision(reason="Comprobante o pago reportado: verificar manualmente",
                routeSource="manual_review")
        if(GuidedAssistant.wantsHuman(normalize(m)))
            return Decision(reason="El cliente pidió atención humana",
                routeSource="manual_review")'''
assert s.count(a)==1
s=s.replace(a,b,1)
a='''        if(unit.isNotEmpty())scheduledReply(config,business,unit,now)?.let {return it.copy(routeSource=route.source)}
        LocalCatalog.reply(config,business,m,now.toLocalDate())?.let {'''
b='''        if(unit.isNotEmpty())scheduledReply(config,business,unit,now)?.let {return it.copy(routeSource=route.source)}
        GuidedAssistant.suggest(config,business,m,now.toLocalDate())?.let {
            return Decision(text=it.text,business=business,department=unit,
                reason=it.reason,routeSource="guided",imageTag=it.imageTag)
        }
        LocalCatalog.reply(config,business,m,now.toLocalDate())?.let {'''
assert s.count(a)==1
p.write_text(s.replace(a,b,1),encoding="utf-8")
print("Guided sales and food-order flows added; never auto-confirm orders, payments or deliveries")
