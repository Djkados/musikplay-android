from pathlib import Path
root=Path("source/autoresponder-pro/android/app/src/main/java/com/autoresponder/pro")
p=root/"LocalCatalog.kt"
s=p.read_text(encoding="utf-8")
anchor='''    fun detects(config:JSONObject,business:String,message:String):Boolean {'''
assert s.count(anchor)==1
s=s.replace(anchor,'''    fun items(config:JSONObject,business:String):List<JSONObject> {
        val arr=config.optJSONArray("catalog")?:return emptyList()
        return (0 until arr.length()).mapNotNull{arr.optJSONObject(it)}
            .filter {it.optString("assistant")==business}
    }
    fun matched(config:JSONObject,business:String,message:String):List<JSONObject> =
        items(config,business).filter{matches(it,message)}
'''+anchor,1)
p.write_text(s,encoding="utf-8")

code=r'''package com.autoresponder.pro

import org.json.JSONObject
import java.time.LocalDate
import java.util.Locale

/**
 * Conversation guidance without storing messages, names, addresses or bank data.
 * Only local catalog item IDs, a step and small quantities are persisted per chat.
 * Price is always loaded from the current catalog when composing a response.
 */
internal object ConversationFlow {
    data class Memory(val productId:String,val stage:String,val quantity:Int=0)
    data class Response(val text:String,val productId:String,val stage:String,
        val quantity:Int=0,val reason:String="Seguimiento comercial")
    private fun norm(s:String)=NativeAutoReplyEngine.normalize(s)
        .replace(Regex("[^a-z0-9 ]+")," ").replace(Regex("\\s+")," ").trim()
    private fun family(item:JSONObject)=norm(item.optString("keywords").substringBefore(","))
    private fun duration(s:String):String? {
        val n=norm(s)
        val m=Regex("\\b(?:26|28|30|60|90|180|365)\\s*(?:dias?|d)\\b|"+
            "\\b(?:2|3|6|12)\\s*(?:mes|meses)\\b").find(n)
        if(m!=null)return norm(m.value).replace(Regex("\\bdia\\b|\\bd\\b"),"dias")
            .replace(Regex("\\bmes\\b"),"meses")
        return Regex("^(?:el de |quiero el de |el |la |de )?(26|28|30|60|90|180|365)$")
            .find(n)?.groupValues?.get(1)?.let{it+" dias"}
    }
    private fun option(items:List<JSONObject>,msg:String):JSONObject? {
        val n=norm(msg)
        val qualifiers=listOf("premium","estandar","basico","internacional",
            "sencilla","especial","pollo","cerdo","queso")
            .filter{Regex("\\b"+it+"\\b").containsMatchIn(n)}
        val narrowed=if(qualifiers.isEmpty())items else items.filter{p->
            qualifiers.any{Regex("\\b"+it+"\\b").containsMatchIn(norm(p.optString("name")))}
        }.ifEmpty{items}
        return narrowed.firstOrNull()
    }
    fun remember(config:JSONObject,business:String,message:String,reason:String):Memory? {
        if(reason !in setOf("Catálogo aprobado","Compra guiada; pendiente de confirmación",
                "Solicitud de pedido; falta revisión"))return null
        val matches=LocalCatalog.matched(config,business,message)
        if(matches.isEmpty())return null
        val requested=duration(message)
        val dated=if(requested==null)matches else matches.filter{
            norm(it.optString("duration"))==requested
        }.ifEmpty{matches}
        val chosen=option(dated,message)?:return null
        val id=chosen.optString("id")
        if(id.isBlank())return null
        val n=norm(message)
        val explicit=Regex("\\b(especial|sencilla|pollo|cerdo|premium|basico|estandar)\\b")
            .containsMatchIn(n)
        val sameFamily=matches.count{family(it)==family(chosen)}
        val stage=when{
            business=="movieplay" && requested!=null -> "payment_offer"
            business=="movieplay" -> "plan"
            business=="tresm" && sameFamily>1 && !explicit -> "variant"
            business=="tresm" -> "quantity"
            else -> ""
        }
        return Memory(id,stage)
    }
    private fun price(item:JSONObject,today:LocalDate):Long{
        val p=item.optLong("price",0L)
        val sale=item.optLong("salePrice",0L)
        val valid=sale>0L && sale<p && runCatching {
            !LocalDate.parse(item.optString("offerUntil")).isBefore(today)
        }.getOrDefault(false)
        return if(valid&&item.optBoolean("active",false))sale else p
    }
    private fun money(v:Long)="$"+String.format(Locale.GERMANY,"%,d",v)
    private fun number(s:String):Int? {
        val n=norm(s)
        val words=mapOf("un" to 1,"una" to 1,"uno" to 1,"dos" to 2,
            "tres" to 3,"cuatro" to 4,"cinco" to 5)
        val x=Regex("^(?:quiero |son |serian |me das )?(\\d{1,2})(?: unidades?)?$")
            .find(n)?.groupValues?.get(1)?.toIntOrNull()?:words[n]
        return x?.takeIf{it in 1..15}
    }
    fun followUp(config:JSONObject,business:String,message:String,
        productId:String,stage:String,quantity:Int,today:LocalDate):Response? {
        if(stage.isBlank()||productId.isBlank())return null
        val items=LocalCatalog.items(config,business)
        val original=items.firstOrNull{it.optString("id")==productId}?:return null
        val n=norm(message)
        if(n.isBlank() || LocalCatalog.matched(config,business,message).isNotEmpty())return null
        val group=items.filter{family(it)==family(original)}
        if(business=="movieplay"){
            val requested=duration(n)
            if(stage in setOf("plan","payment_offer") && requested!=null){
                val candidates=group.filter{
                    norm(it.optString("name"))==norm(original.optString("name")) &&
                        norm(it.optString("duration"))==requested
                }
                if(candidates.size!=1)
                    return Response("🎬 *MOVIEPLAY*\n\nConfirma el plan y la modalidad para darte el valor correcto.",
                        productId,stage,reason="Plan ambiguo: requiere confirmación")
                val item=candidates.first()
                val cost=price(item,today)
                val available=item.optBoolean("active",false) && cost>0
                val summary="🎬 *MOVIEPLAY*\n\n🧾 *RESUMEN DE TU SOLICITUD*\n\n"+
                    "📺 *"+item.optString("name")+
                    "*\n📅 "+item.optString("duration")+
                    "\n💵 *Precio:* "+(if(cost>0)money(cost) else "Por confirmar")+"\n\n"
                return Response(summary+if(available)
                    "✅ Solicitud preparada.\n\n¿Deseas ver los medios de pago?\n\n"+
                    "🔐 La disponibilidad y el pago se verifican antes de la entrega."
                else "🚫 *NO DISPONIBLE POR EL MOMENTO*\nEl precio es solo informativo.",
                    item.optString("id"),if(available)"payment_offer" else "plan")
            }
            if(stage=="payment_offer" &&
                n in setOf("si","claro","dale","listo","por favor","porfa",
                    "si quiero","quiero pagar","enviame los medios")){
                val pay=PaymentReplies.reply(config,business,"medios de pago")?:return null
                return Response(pay.text,productId,"payment_menu",
                    reason="Cliente solicitó medios de pago")
            }
        } else if(business=="tresm"){
            if(stage=="variant"){
                val qualifier=Regex("\\b(especial|sencilla|pollo|cerdo|queso)\\b")
                    .find(n)?.value?:return null
                val candidates=group.filter{
                    Regex("\\b"+qualifier+"\\b").containsMatchIn(norm(it.optString("name")))
                }
                if(candidates.size!=1)return null
                val item=candidates.first()
                return Response("🍔 *LAS TRES M*\n\n• *"+item.optString("name")+
                    "*\n💵 Valor: "+(if(price(item,today)>0)money(price(item,today))
                        else "Por confirmar")+"\n\n¿Cuántas unidades deseas? (1 a 15)",
                    item.optString("id"),"quantity")
            }
            if(stage=="quantity"){
                val count=number(n)?:return null
                if(!original.optBoolean("active",false))
                    return Response("🍔 *LAS TRES M*\n\n🚫 Producto no disponible por el momento.",
                        productId,"quantity")
                val subtotal=price(original,today)*count
                return Response("🍔 *LAS TRES M*\n\n📝 *SOLICITUD DE PEDIDO*\n\n"+
                    "• "+count+" × "+original.optString("name")+
                    "\n💵 *Subtotal de referencia:* "+(if(subtotal>0)money(subtotal)
                        else "Por confirmar")+"\n\n¿Es para *recoger* o *domicilio*?\n"+
                    "⚠️ Pendiente de confirmar disponibilidad y valor final.",
                    productId,"delivery",count)
            }
            if(stage=="delivery" && quantity in 1..15){
                val home=n in setOf("domicilio","a domicilio","domi","domicilios")
                val pickup=n in setOf("recoger","para recoger","para llevar","recogida")
                if(home||pickup) {
                    val subtotal=price(original,today)*quantity
                    return Response("🍔 *LAS TRES M*\n\n🧾 *PEDIDO PENDIENTE DE REVISIÓN*\n\n"+
                        "• "+quantity+" × "+original.optString("name")+
                        "\n💵 Subtotal de referencia: "+(if(subtotal>0)money(subtotal)
                            else "Por confirmar")+
                        "\n🚗 Modalidad: "+(if(home)"Domicilio" else "Recoger")+
                        "\n\n"+(if(home)"📍 Comparte tu dirección directamente en WhatsApp.\n\n" else "")+
                        "✅ Nuestro equipo confirmará el pedido y el valor final.",
                        productId,"review",quantity,reason="Pedido guiado sin confirmar")
                }
            }
        }
        return null
    }
}
'''
(root/"ConversationFlow.kt").write_text(code,encoding="utf-8")

p=root/"NativeAutoReplyEngine.kt"
s=p.read_text(encoding="utf-8")
a='''val routeSource: String = "none", val needsChoice: Boolean = false, val imageTag:String = "", val paymentMenu:Boolean=false)'''
b='''val routeSource: String = "none", val needsChoice: Boolean = false,
        val imageTag:String = "", val paymentMenu:Boolean=false,
        val memoryProductId:String="",val memoryStage:String="",val memoryQuantity:Int=0)'''
assert s.count(a)==1
s=s.replace(a,b,1)
a='''rememberedBusiness:String?=null,awaitingChoice:Boolean=false,paymentMenuPending:Boolean=false):Decision {'''
b='''rememberedBusiness:String?=null,awaitingChoice:Boolean=false,paymentMenuPending:Boolean=false,
        rememberedProductId:String="",rememberedProductStage:String="",rememberedQuantity:Int=0):Decision {'''
assert s.count(a)==1
s=s.replace(a,b,1)
a='''        GuidedAssistant.suggest(config,business,m,now.toLocalDate())?.let {'''
b='''        ConversationFlow.followUp(config,business,m,rememberedProductId,
            rememberedProductStage,rememberedQuantity,now.toLocalDate())?.let {
            return Decision(text=it.text,business=business,department=unit,reason=it.reason,
                routeSource="memory",memoryProductId=it.productId,
                memoryStage=it.stage,memoryQuantity=it.quantity)
        }
        GuidedAssistant.suggest(config,business,m,now.toLocalDate())?.let {'''
assert s.count(a)==1
p.write_text(s.replace(a,b,1),encoding="utf-8")
print("ConversationFlow.kt adds current-catalog followups and customer-safe plan, quantity and pickup stages")
