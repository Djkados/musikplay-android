from pathlib import Path

root=Path("source/autoresponder-pro")
src=root/"android/app/src/main/java/com/autoresponder/pro"

def change(path,old,new,label):
    p=src/path
    s=p.read_text(encoding="utf-8")
    assert s.count(old)==1,(label,s.count(old))
    p.write_text(s.replace(old,new,1),encoding="utf-8")

change("LocalCatalog.kt",'''            if(selected.size>chosen.size)lines.add("Tengo más opciones si las necesitas.")
            lines.add("¿Cuál te interesa?")''',
'''            if(selected.size>chosen.size)lines.add("Tengo más opciones si las necesitas.")
            val oneAvailable=selected.size==1 && selected.first().optBoolean("active",false) &&
                selected.first().optLong("price",0L)>0L
            lines.add(if(oneAvailable)"¿Te paso los medios de pago? 😊"
                else "¿Cuál te interesa?")''',"offer payments after one available quoted plan")

change("ConversationFlow.kt",'''        val stage=when{
            business=="movieplay" && requested!=null -> "payment_offer"
            business=="movieplay" -> "plan"''',
'''        val stage=when{
            business=="movieplay" && chosen.optBoolean("active",false) &&
                chosen.optLong("price",0L)>0L &&
                (requested!=null || matches.size==1) -> "payment_offer"
            business=="movieplay" -> "plan"''',"remember exact plan for payment consent")
# Replace only the contextual payment-consent arm; the rest of the customer
# conversation engine stays as built by previous versions.
p=src/"ConversationFlow.kt"
s=p.read_text(encoding="utf-8")
start=s.index('''            if(stage=="payment_offer" &&''')
end=s.index('''        } else if(business=="tresm"){''',start)
accepted='''            if(stage=="payment_offer" &&
                n in setOf("si","sii","siii","claro","claro que si","dale",
                    "de una","listo","por favor","porfa","si porfa","si por favor",
                    "ok","bueno","perfecto","hagale","si quiero","quiero pagar",
                    "enviame los medios","pasame los medios","mandamelos",
                    "enviamelos","si envialos","dale pasame los datos",
                    "si mandame los datos")){
                val pay=PaymentReplies.reply(config,business,"medios de pago",
                    casual=true)?:return null
                return Response(pay.text,productId,"payment_menu",
                    reason="Cliente solicitó medios de pago")
            }
'''
assert s.count('''            if(stage=="payment_offer" &&''')==1
s=s[:start]+accepted+s[end:]
p.write_text(s,encoding="utf-8")

# An imageTag is optional artwork metadata, not a sold-out stock indicator.
change("GuidedAssistant.kt",'''if(quote!=null && !quote.available)
                "Este plan figura como no disponible. Puedes preguntarnos por otra opción."
            else "Dime qué plan y duración prefieres, y te paso los medios de pago. 😊\\n"+
                "Yo verifico disponibilidad y pago antes de entregarlo."''',
'''if(quote!=null && !quote.available)
                "Este plan figura como no disponible. Puedes preguntarnos por otra opción."
            else if(quote!=null && ConversationFlow.remember(config,business,message,
                    "Compra guiada; pendiente de confirmación")?.stage=="payment_offer")
                "¿Te paso los medios de pago? 😊\\nAntes de entregarlo verifico disponibilidad y pago."
            else "Dime qué plan y duración prefieres, y te paso los medios de pago. 😊\\n"+
                "Yo verifico disponibilidad y pago antes de entregarlo."''',"natural guided purchase and no image availability confusion")

(src/"GreetingReplies.kt").write_text('''package com.autoresponder.pro

import java.time.ZonedDateTime

/** Greetings are recognized only when the whole message is a greeting.
 * A greeting plus product/payment request proceeds to its real intent. */
internal object GreetingReplies {
    fun pure(text:String):Boolean {
        val n=NativeAutoReplyEngine.normalize(text)
            .replace(Regex("[^a-z ]+")," ").replace(Regex("\\\\s+")," ").trim()
        return n in setOf("hola","holaa","holaaa","holi","buenas",
            "buen dia","buenos dias","buenas tardes","buenas noches",
            "hola buenas","hola buen dia","hola buenos dias",
            "hola buenas tardes","hola buenas noches","muy buenas",
            "muy buenos dias","muy buenas tardes","muy buenas noches",
            "hola que tal","que tal","hola como estas","buenas como estas",
            "hola todo bien")
    }
    fun opening(now:ZonedDateTime):String=when(now.hour){
        in 5..11 -> "¡Buenos días!"
        in 12..18 -> "¡Buenas tardes!"
        else -> "¡Buenas noches!"
    }
    fun message(business:String,now:ZonedDateTime):String =
        if(business=="tresm")
            opening(now)+" 😊 Te comparto el menú: https://lastresm.netlify.app\\n¿Qué te gustaría pedir?"
        else opening(now)+" 😊 ¿Qué servicio necesitas? Te ayudo con los precios."
}
''',encoding="utf-8")

# This is the existing fallback greeting classifier; keep the source's
# other recognition rules unchanged and broaden only stand-alone greetings.
import re
p=src/"NativeAutoReplyEngine.kt"
s=p.read_text(encoding="utf-8")
pattern=r'val greeting=n in setOf\([\s\S]{0,300}?\)'
assert len(re.findall(pattern,s))==1,("greeting fallback",len(re.findall(pattern,s)))
s=re.sub(pattern,'val greeting=GreetingReplies.pure(m) || n in setOf("gracias","ok","listo","si")',
    s,count=1)
p.write_text(s,encoding="utf-8")
change("NativeAutoReplyEngine.kt",'''"movieplay" -> "¡Hola! 😊 Dime qué plataforma necesitas y te paso los precios."''',
'''"movieplay" -> GreetingReplies.message(business,now)''',"movieplay personalized time greeting")
change("NativeAutoReplyEngine.kt",'''"tresm" -> "¡Hola! 😊 Te paso el menú: https://lastresm.netlify.app\\n¿Qué te gustaría pedir?"''',
'''"tresm" -> GreetingReplies.message(business,now)''',"Las Tres M personalized greeting")
change("WhatsAppNotificationListener.kt",'''                    val greetingText=NativeAutoReplyEngine.normalize(message)
                    val genericHello=greetingText in setOf("hola","buenas","buenos dias",
                        "buenas tardes","buenas noches","hola buenas")''',
'''                    val genericHello=GreetingReplies.pure(message)''',"greeting throttled by chat, not by text variant")
print("0.6.9: short time-aware greetings; active single-plan quotes ask permission for payment; yes/de una leads to correct menu.")
