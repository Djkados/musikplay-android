from pathlib import Path

root=Path("source/autoresponder-pro")
src=root/"android/app/src/main/java/com/autoresponder/pro"
p=src/"PaymentReplies.kt"
p.write_text(r'''package com.autoresponder.pro

import org.json.JSONObject
import java.text.Normalizer
import java.util.Locale

/** Deterministic per-business payment information supplied by the owner. */
internal object PaymentReplies {
    data class Result(val text:String, val isMenu:Boolean=false, val choice:Boolean=false)
    private fun normalize(text:String):String =
        Normalizer.normalize(text.lowercase(Locale.ROOT),Normalizer.Form.NFD)
            .replace(Regex("\\p{M}+"),"").replace(Regex("\\s+")," ").trim()

    fun reply(config:JSONObject,business:String,message:String,
        pendingMenu:Boolean=false):Result? {
        val clean=normalize(message)
        val shortcut=if(pendingMenu)when(clean){
            "1","uno","opcion 1"->"nequi"
            "2","dos","opcion 2"->"bancolombia"
            "3","tres","opcion 3"->"daviplata"
            "4","cuatro","opcion 4"->"llaves"
            else->null
        }else null
        val hasNequi=Regex("\\bnequi\\b").containsMatchIn(clean)
        val hasBanco=Regex("\\bbancolombia\\b|\\bbanco colombia\\b").containsMatchIn(clean)
        val hasDavi=Regex("\\bdaviplata\\b|\\bdavi plata\\b").containsMatchIn(clean)
        val hasKeys=Regex("\\bllaves?\\b|\\bbre ?b\\b").containsMatchIn(clean)
        val generic=Regex(
            "\\bmedios? de pago\\b|\\bformas? de pago\\b|\\bcomo pago\\b|"+
            "\\bdonde (?:puedo )?pago\\b|\\ba donde pago\\b|\\bdatos (?:de|para) pago\\b|"+
            "\\bcuentas? (?:bancarias?|para pagar|de pago)\\b|\\bdame (?:las? )?cuentas?\\b|"+
            "\\bnumero de cuenta\\b|\\bpara transferir\\b|\\bcomo te pago\\b|"+
            "\\ba donde transfiero\\b|\\bpagar el servicio\\b"
        ).containsMatchIn(clean)
        val count=listOf(hasNequi,hasBanco,hasDavi).count{it}
        val method=when {
            shortcut!=null->shortcut
            count>1->"menu"
            hasNequi->"nequi"
            hasBanco->"bancolombia"
            hasDavi->"daviplata"
            hasKeys->"llaves"
            generic->"menu"
            else->return null
        }
        // The same two WhatsApps cover different merchants. Never share
        // MoviePlay's account details in a Las Tres M conversation.
        val data=config.optJSONObject("payments")?.optJSONObject(business)
        val holder=data?.optString("holder","")?.trim().orEmpty()
        val nequi=data?.optJSONObject("nequi")
        val bank=data?.optJSONObject("bancolombia")
        val davi=data?.optJSONObject("daviplata")
        val hasAccounts=listOf(nequi,bank,davi).any {
            it!=null && (it.optString("number").isNotBlank()||it.optString("key").isNotBlank())
        }
        val title=if(business=="movieplay")"🎬 *MOVIEPLAY*" else "🍔 *LAS TRES M*"
        if(!hasAccounts) return Result(
            "$title\n\n💳 Los datos de pago para este negocio se confirman directamente con nuestro equipo.\n\n" +
            "Escríbenos cuando estés listo para pagar. 😊")
        val receipt="📩 *Después de pagar, envíanos el comprobante* para verificar tu pago."
        val owner=if(holder.isNotBlank())"👤 *Titular:* $holder\n\n" else ""
        fun part(name:String,json:JSONObject?,bankAccount:Boolean=false):String {
            val key=json?.optString("key","")?.trim().orEmpty()
            val number=json?.optString("number","")?.trim().orEmpty()
            val out=mutableListOf("💳 *$name*","")
            if(number.isNotBlank())out.add((if(bankAccount)"🏦 *Cuenta de ahorros:* " else "📲 *Número:* ")+number)
            if(key.isNotBlank())out.add("🔑 *Llave:* $key")
            return out.joinToString("\n")
        }
        val intro=if(method=="menu"){
            val text="$title\n\n💳 *MEDIOS DE PAGO*\n\n"+owner+
                "1️⃣ *Nequi*\n2️⃣ *Bancolombia*\n3️⃣ *DaviPlata*\n4️⃣ *Pago con llave*\n\n"+
                "✍️ *Responde 1, 2, 3 o 4; también puedes escribir el nombre del medio que prefieras.*"
            return Result(text,isMenu=true)
        }else when(method) {
            "nequi"->part("NEQUI",nequi)
            "bancolombia"->part("BANCOLOMBIA",bank,true)
            "daviplata"->part("DAVIPLATA",davi)
            else->{
                val pairs=listOf("Nequi" to nequi,"Bancolombia" to bank,"DaviPlata" to davi)
                    .mapNotNull { (label,item)->
                        item?.optString("key")?.takeIf{it.isNotBlank()}?.let{
                            "*$label:* $it"
                        }
                    }
                "🔑 *PAGO CON LLAVE*\n\n"+pairs.joinToString("\n")
            }
        }
        return Result("$title\n\n"+owner+intro+"\n\n"+receipt,choice=shortcut!=null)
    }
}
''',encoding="utf-8")

p=src/"NativeAutoReplyEngine.kt";s=p.read_text(encoding="utf-8")
def edit(a,b):
 global s
 assert s.count(a)==1,(a[:85],s.count(a))
 s=s.replace(a,b,1)
edit('val routeSource: String = "none", val needsChoice: Boolean = false, val imageTag:String = "")',
     'val routeSource: String = "none", val needsChoice: Boolean = false, val imageTag:String = "", val paymentMenu:Boolean=false)')
edit('rememberedBusiness:String?=null,awaitingChoice:Boolean=false):Decision {',
     'rememberedBusiness:String?=null,awaitingChoice:Boolean=false,paymentMenuPending:Boolean=false):Decision {')
edit('''        if(unit.isNotEmpty())scheduledReply(config,business,unit,now)?.let {return it.copy(routeSource=route.source)}''',
'''        // Payment details are useful 24/7 even when sales support is closed.
        PaymentReplies.reply(config,business,m,paymentMenuPending)?.let {
            return Decision(text=it.text,business=business,department=unit,
                reason=if(it.isMenu)"Menú de medios de pago" else "Medio de pago solicitado",
                routeSource=if(it.choice)"payment_choice" else "payment_specific",
                paymentMenu=it.isMenu)
        }
        if(unit.isNotEmpty())scheduledReply(config,business,unit,now)?.let {return it.copy(routeSource=route.source)}''')
p.write_text(s,encoding="utf-8")

p=src/"WhatsAppNotificationListener.kt";s=p.read_text(encoding="utf-8")
def edit(a,b):
 global s
 assert s.count(a)==1,(a[:85],s.count(a))
 s=s.replace(a,b,1)
edit('''                val decision=if(now<humanPauseUntil)''',
'''                val paymentMenuPending=fresh && previous.optBoolean("pendingPaymentMenu",false) &&
                    now-previous.optLong("paymentMenuAt",0L) in 0L until 600_000L
                val decision=if(now<humanPauseUntil)''')
edit('''                    rememberedBusiness=remembered,awaitingChoice=pending)''',
'''                    rememberedBusiness=remembered,awaitingChoice=pending,
                    paymentMenuPending=paymentMenuPending)''')
edit('''                        decision.routeSource !in setOf("choice","detected")''',
'''                        decision.routeSource !in setOf("choice","detected","payment_choice","payment_specific")''')
edit('''                                        .put("promptAt",now).toString()).apply()''',
'''                                        .put("promptAt",now)
                                        .put("pendingPaymentMenu",false).toString()).apply()''')
edit('''                                        .put("promptAt",0L).toString()).apply()''',
'''                                        .put("promptAt",0L)
                                        .put("pendingPaymentMenu",decision.paymentMenu)
                                        .put("paymentMenuAt",if(decision.paymentMenu)now else 0L)
                                        .toString()).apply()''')
p.write_text(s,encoding="utf-8")
print("Native payment menu, specific bank replies and per-contact numeric selection integrated")
