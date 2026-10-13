from pathlib import Path

root=Path("source/autoresponder-pro")
src=root/"android/app/src/main/java/com/autoresponder/pro"

p=src/"PaymentReplies.kt"
s=p.read_text(encoding="utf-8")
old='''        val hasBanco=Regex("\\\\bbancolombia\\\\b|\\\\bbanco colombia\\\\b").containsMatchIn(clean)'''
new='''        // Treat the bank's NAME like menu choice "2", independently of
        // payment-menu state. Typical WhatsApp punctuation is tolerated.
        val natural=clean.replace(Regex("[^a-z0-9 ]+")," ")
            .replace(Regex(" +")," ").trim()
        val hasBanco=Regex("\\\\b(?:bancolombia|banco colombia|bancolomvia)\\\\b")
            .containsMatchIn(natural)'''
assert s.count(old)==1,("Bank-name intent detection anchor",s.count(old))
p.write_text(s.replace(old,new,1),encoding="utf-8")

p=src/"WhatsAppNotificationListener.kt"
s=p.read_text(encoding="utf-8")
old='''        val key = fingerprint("$channel|$contact|$message")
        val prefs = getSharedPreferences("private_inbox", Context.MODE_PRIVATE)
        val seen = getSharedPreferences("recent_notifications", Context.MODE_PRIVATE)
        val now = System.currentTimeMillis()
        if (now - seen.getLong(key,0L) < 5 * 60 * 1000L) {
            trace(channel, "duplicate_skipped"); return
        }
        // A reissued notification may represent the same message. Mark it before acting.
        seen.edit().putLong(key,now).apply()'''
new='''        // A repeated NOTIFICATION has the same WhatsApp message timestamp.
        // A genuinely NEW customer message may have the same words (e.g.
        // "Bancolombia", "Nequi", "2") a few minutes later: do NOT block
        // it for five minutes merely because its text was used before.
        val key=fingerprint("$channel|$contact|$messageTime|$message")
        val fastKey=fingerprint("rapid_repeat|$channel|$contact|$message")
        val prefs=getSharedPreferences("private_inbox",Context.MODE_PRIVATE)
        val seen=getSharedPreferences("recent_notifications",Context.MODE_PRIVATE)
        val now=System.currentTimeMillis()
        val eventSeen=seen.getLong(key,0L)
        val fastSeen=seen.getLong(fastKey,0L)
        val repeatedEvent=eventSeen>0L && now-eventSeen in 0L until 300_000L
        val rapidCopy=fastSeen>0L && now-fastSeen in 0L until 4_000L
        if(repeatedEvent || rapidCopy){
            trace(channel,if(repeatedEvent)"duplicate_notification_skipped"
                else "rapid_duplicate_skipped")
            return
        }
        // Persist before sending so notification updates cannot send twice.
        seen.edit().putLong(key,now).putLong(fastKey,now).apply()'''
assert s.count(old)==1,("Exact text dedup anchor",s.count(old))
s=s.replace(old,new,1)
old='''                        val action = notification.actions?.firstOrNull { a ->
                            a.remoteInputs?.any { it.allowFreeFormInput } == true && a.actionIntent != null
                        }
                        if (action == null) {
                            incoming.put("autoStatus","no_quick_reply")
                        } else if (throttle.edit().putLong(conversationKey,now).commit()) {'''
new='''                        fun directReply(n:Notification?):Notification.Action? =
                            n?.actions?.firstOrNull { a ->
                                a.remoteInputs?.any { it.allowFreeFormInput }==true &&
                                    a.actionIntent!=null
                            }
                        // Some WhatsApp versions update the notification in
                        // place and move its RemoteInput action. For an explicit
                        // PAYMENT inquiry only, try a newer active notification
                        // belonging to the EXACT SAME Android notification key.
                        // Never take actions from another chat or other app.
                        val action=directReply(notification) ?: if(
                            decision.routeSource in setOf("payment_specific","payment_choice"))
                            try {
                                activeNotifications?.firstOrNull { active ->
                                    active.packageName==sbn.packageName &&
                                        active.key==sbn.key &&
                                        kotlin.math.abs(now-active.postTime)<=60_000L
                                }?.notification?.let {directReply(it)}
                            } catch (_:Exception){null}
                        else null
                        if(action==null){
                            incoming.put("autoStatus","no_quick_reply")
                            if(decision.routeSource in setOf("payment_specific","payment_choice"))
                                incoming.put("manualPaymentReply",true)
                        } else if(throttle.edit().putLong(conversationKey,now).commit()) {'''
assert s.count(old)==1,("WhatsApp quick reply action anchor",s.count(old))
s=s.replace(old,new,1)
p.write_text(s,encoding="utf-8")
print("Payment bank-name recognition and notification pipeline updated: new identical texts accepted after 4s; active same-chat RemoteInput fallback; manual status if WhatsApp does not expose reply.")
