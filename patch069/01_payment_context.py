from pathlib import Path

root=Path("source/autoresponder-pro")
src=root/"android/app/src/main/java/com/autoresponder/pro"

p=src/"PaymentReplies.kt"
s=p.read_text(encoding="utf-8")
old='''        val shortcut=if(pendingMenu)when(clean){
            "1","uno","opcion 1"->"nequi"
            "2","dos","opcion 2"->"bancolombia"
            "3","tres","opcion 3"->"daviplata"
            "4","cuatro","opcion 4"->"llaves"
            else->null
        }else null'''
new='''        // Keycap emojis and ordinary punctuation must not break a selection.
        // A bare digit is a bank choice ONLY if a menu was actually sent to
        // this chat; otherwise "1" may mean a business or food quantity.
        val option=clean.replace(Regex("[^a-z0-9áéíóú ]+")," ")
            .replace(Regex(" +")," ").trim()
        val shortcut=if(pendingMenu)when(option){
            "1","uno","opcion 1","opción 1","opcion uno","opción uno",
                "el 1","la 1","la primera","primera"->"nequi"
            "2","dos","opcion 2","opción 2","opcion dos","opción dos",
                "el 2","la 2","la segunda","segunda"->"bancolombia"
            "3","tres","opcion 3","opción 3","opcion tres","opción tres",
                "el 3","la 3","la tercera","tercera"->"daviplata"
            "4","cuatro","opcion 4","opción 4","opcion cuatro","opción cuatro",
                "el 4","la 4","la cuarta","cuarta"->"llaves"
            else->null
        }else null'''
assert s.count(old)==1,("Unexpected PaymentReplies menu parser",s.count(old))
p.write_text(s.replace(old,new,1),encoding="utf-8")

(src/"PaymentMenuContext.kt").write_text('''package com.autoresponder.pro

/** Payment choices remain scoped to one channel + chat; only hashed keys
 * are stored. An independent marker survives a lost business-routing state.
 * Never accept 1/2/3/4 as a bank choice without an unexpired sent-menu marker.
 */
internal object PaymentMenuContext {
    const val SENT_MENU_MS=60L*60L*1000L
    const val LEGACY_MENU_MS=10L*60L*1000L
    fun isPending(now:Long,routingPending:Boolean,routingAt:Long,sentAt:Long):Boolean =
        routingPending && AssistantCadence.recent(now,routingAt,LEGACY_MENU_MS) ||
            AssistantCadence.recent(now,sentAt,SENT_MENU_MS)
}
''',encoding="utf-8")

p=src/"WhatsAppNotificationListener.kt"
s=p.read_text(encoding="utf-8")
old='''                val paymentMenuPending=fresh && previous.optBoolean("pendingPaymentMenu",false) &&
                    now-previous.optLong("paymentMenuAt",0L) in 0L until 600_000L'''
new='''                // The routing JSON may be reset by an unrelated reply or
                // upgraded app. Restore the last menu confirmed sent to this
                // exact WhatsApp/channel even when its business route was lost.
                val verifiedMenuAt=getSharedPreferences("payment_menu_context",
                    Context.MODE_PRIVATE).getLong(routeKey,0L)
                val paymentMenuPending=PaymentMenuContext.isPending(now,
                    fresh && previous.optBoolean("pendingPaymentMenu",false),
                    previous.optLong("paymentMenuAt",0L),verifiedMenuAt)
                incoming.put("paymentMenuPending",paymentMenuPending)'''
assert s.count(old)==1,("Unexpected listener menu reading",s.count(old))
s=s.replace(old,new,1)
old='''                                action.actionIntent.send(this,0,intent)'''
new='''                                action.actionIntent.send(this,0,intent)
                                // Store ONLY after Android accepts the reply.
                                // This is independent of business-choice and
                                // product-flow state. A successful bank reply
                                // consumes the menu; another request reopens it.
                                val payMemory=getSharedPreferences(
                                    "payment_menu_context",Context.MODE_PRIVATE)
                                if(decision.paymentMenu)
                                    payMemory.edit().putLong(routeKey,now).commit()
                                else if(decision.routeSource in
                                    setOf("payment_choice","payment_specific"))
                                    payMemory.edit().remove(routeKey).commit()'''
assert s.count(old)==1,("Unexpected successful send location",s.count(old))
p.write_text(s.replace(old,new,1),encoding="utf-8")
print("0.6.9: payment options accept keycaps and natural numeric choices. Verified per-chat sent-menu backup prevents losing 1=Nequi after route updates.")
