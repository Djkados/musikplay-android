from pathlib import Path
root=Path("source/autoresponder-pro")
native=root/"android/app/src/main/java/com/autoresponder/pro"
web=root/"web"
assets=root/"android/app/src/main/assets"

def change(path,old,new,label):
 s=path.read_text(encoding="utf-8")
 assert s.count(old)==1,(label,s.count(old),str(path))
 path.write_text(s.replace(old,new,1),encoding="utf-8")

(native/"ConversationSafety074.kt").write_text(r'''package com.autoresponder.pro

/** Reset only a known, active commercial request; never a renewal or complaint. */
internal object ConversationSafety074 {
    private val phrases=setOf("empezar de nuevo","empecemos de nuevo",
        "reiniciar mi cotizacion","reinicia mi cotizacion",
        "cancelar mi cotizacion","cancela mi cotizacion",
        "cancelar el combo","cancelar combo","olvida el combo",
        "borra el combo","borrar mi pedido","descartar mi pedido",
        "ya no quiero ese combo","ya no quiero ese servicio")
    fun shouldReset(text:String,hasContext:Boolean):Boolean =
        hasContext && PlanPrecision074.norm(text) in phrases
}
''',encoding="utf-8")
flow=native/"ConversationFlow.kt"
change(flow,'''        if(business=="movieplay"){
            // The customer can answer just "sin deportes" / "Premium"''',
'''        if(business=="movieplay"){
            // A short follow-up is scoped to the previously selected platform,
            // not every product that shares "Premium" in another name.
            if(stage in setOf("plan","payment_offer")){
                val brand=PlanPrecision074.family(original)
                val qualifier=brand?.let{PlanPrecision074.followUp(message,it)}
                if(brand in setOf("netflix","disney","max") && qualifier!=null){
                    val candidates=items.filter{item->
                        PlanPrecision074.family(item)==brand &&
                        (if(qualifier=="nacional")
                            !PlanPrecision074.norm(item.optString("name")).contains("internacional")
                         else Regex("\\\\b"+qualifier+"\\\\b").containsMatchIn(
                            PlanPrecision074.norm(item.optString("name")))) &&
                        PlanPrecision074.norm(item.optString("duration"))==
                            PlanPrecision074.norm(original.optString("duration"))
                    }
                    val item=candidates.singleOrNull()
                    if(item==null){
                        return Response("🎬 *MOVIEPLAY*\\n\\nNo encuentro esa modalidad con "+
                            "la duración que elegiste. ¿Qué plan y duración prefieres?",
                            productId,"plan",reason="Modalidad sin duración disponible")
                    }
                    val cost=price(item,today)
                    if(!item.optBoolean("active",false)||cost<=0L)
                        return Response("🎬 *MOVIEPLAY*\\n\\nEse plan figura como "+
                            "*NO DISPONIBLE*. No lo sustituiré por otro. ¿Buscamos otra opción?",
                            productId,"plan",reason="Plan solicitado no disponible")
                    return Response("🎬 *MOVIEPLAY*\\n\\n📺 *"+
                        item.optString("name")+"* · "+item.optString("duration")+
                        "\\n💵 *Precio:* "+money(cost)+
                        "\\n\\n¿Te paso los medios de pago? 😊\\n"+
                        "La disponibilidad y el pago se verifican antes de la entrega.",
                        item.optString("id"),"payment_offer",
                        reason="Modalidad elegida en la conversación")
                }
            }
            // The customer can answer just "sin deportes" / "Premium"''',
"smart follow-up switch")
# Product memory shouldn't use 24h across business handoffs and resets.
engine=native/"NativeAutoReplyEngine.kt"
change(engine,'''        if(business=="movieplay" && unit=="sales"){
            NetflixInternationalInfo.answer''',
'''        if(business=="movieplay" && unit=="sales" &&
            ConversationSafety074.shouldReset(m,
                rememberedProductStage.isNotBlank()||rememberedComboState.isNotBlank()))
            return Decision(text="Entendido 😊 Reinicié la cotización. "+
                "¿Qué servicio necesitas ahora?",business=business,department=unit,
                reason="Cotización reiniciada por el cliente",
                routeSource="conversation_reset",memoryComboState="")
        if(business=="movieplay" && unit=="sales"){
            NetflixInternationalInfo.answer''',
"engine reset after eligibility")
listener=native/"WhatsAppNotificationListener.kt"
change(listener,'''                                val currentProduct=when {
                                    decision.routeSource=="memory"''',
'''                                val currentProduct=when {
                                    decision.routeSource=="conversation_reset"->null
                                    decision.routeSource=="memory"''',"clear product state on reset")
change(listener,'''                                        .put("comboState",decision.memoryComboState ?: comboState)
                                        .put("comboAt",if(decision.memoryComboState!=null)now else''',
'''                                        .put("comboState",decision.memoryComboState ?: comboState)
                                        .put("comboAt",if(decision.routeSource=="conversation_reset")0L
                                            else if(decision.memoryComboState!=null)now else''',
"clear combo context on reset")
change(listener,'''                            } catch (_: PendingIntent.CanceledException) {
                                echoes.edit().remove(echoKey).apply()
                                incoming.put("autoStatus","failed_canceled")
                            } catch (_: SecurityException) {
                                echoes.edit().remove(echoKey).apply()
                                incoming.put("autoStatus","failed_permission")
                            } catch (_: Exception) {
                                echoes.edit().remove(echoKey).apply()
                                incoming.put("autoStatus","failed")
                            }''',
'''                            } catch (_: PendingIntent.CanceledException) {
                                echoes.edit().remove(echoKey).apply()
                                // Failed Android submissions must not throttle the next
                                // real customer message or create phantom chat memory.
                                if(throttle.getLong(conversationKey,0L)==now)
                                    throttle.edit().remove(conversationKey).apply()
                                incoming.put("autoStatus","failed_canceled")
                            } catch (_: SecurityException) {
                                echoes.edit().remove(echoKey).apply()
                                if(throttle.getLong(conversationKey,0L)==now)
                                    throttle.edit().remove(conversationKey).apply()
                                incoming.put("autoStatus","failed_permission")
                            } catch (_: Exception) {
                                echoes.edit().remove(echoKey).apply()
                                if(throttle.getLong(conversationKey,0L)==now)
                                    throttle.edit().remove(conversationKey).apply()
                                incoming.put("autoStatus","failed")
                            }''',
"do not throttle on error")
# A routing decision from precise plan must take precedence over stale memory.
# LocalCatalog.matched is now strict and stored only when a successful reply exists.
print("0.6.14: exact-plan followup, explicit cancellation and safe retry after failed send.")
