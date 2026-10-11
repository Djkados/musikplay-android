from pathlib import Path
p=Path("source/autoresponder-pro/android/app/src/main/java/com/autoresponder/pro/WhatsAppNotificationListener.kt")
s=p.read_text()
def change(a,b):
 global s
 assert s.count(a)==1, "Unexpected listener version: "+a[:80]
 s=s.replace(a,b)
change('''                val decision = NativeAutoReplyEngine.decide(config,channel,contact,message)
                incoming.put("assistant",decision.business ?: JSONObject.NULL)
                    .put("department",decision.department ?: JSONObject.NULL)
                    .put("autoReason", decision.reason)''',
'''                // Remember only business and timestamps against a hashed
                // channel/contact identity. No chat content or phone is stored.
                val routes=getSharedPreferences("routing_context",Context.MODE_PRIVATE)
                val routeKey=fingerprint("$channel|$contact")
                val previous=try {JSONObject(routes.getString(routeKey,"{}") ?: "{}")}
                    catch (_:Exception) {JSONObject()}
                val fresh=previous.optLong("lastSeen",0L).let {
                    it>0L && now-it in 0L until (24L*60L*60L*1000L)
                }
                val remembered=if(fresh)previous.optString("business")
                    .takeIf {it=="movieplay" || it=="tresm"} else null
                val pending=fresh && previous.optBoolean("pendingChoice",false) &&
                    now-previous.optLong("promptAt",0L) in 0L until 600_000L
                val decision=NativeAutoReplyEngine.decide(config,channel,contact,message,
                    rememberedBusiness=remembered,awaitingChoice=pending)
                incoming.put("assistant",decision.business ?: JSONObject.NULL)
                    .put("department",decision.department ?: JSONObject.NULL)
                    .put("autoReason",decision.reason)
                    .put("routeMethod",decision.routeSource)
                    .put("preparedText",decision.text ?: JSONObject.NULL)''')
change('''                    // At most one auto-submission per conversation every 10 minutes.
                    val throttle = getSharedPreferences("reply_throttle", Context.MODE_PRIVATE)
                    val conversationKey=fingerprint("$channel|$contact")
                    if (now - throttle.getLong(conversationKey,0L) < 10 * 60 * 1000L) {
                        incoming.put("autoStatus","throttled")
                    } else {''',
'''                    // A choice of 1/2 must be accepted promptly after clarification.
                    // Other rapid replies are throttled, and clarification is never
                    // repeated every time a customer sends another greeting.
                    val throttle=getSharedPreferences("reply_throttle",Context.MODE_PRIVATE)
                    val conversationKey=fingerprint("$channel|$contact")
                    val sinceLast=now-throttle.getLong(conversationKey,0L)
                    val repeatedPrompt=decision.needsChoice && pending
                    val rapid=sinceLast in 0L until 20_000L &&
                        decision.routeSource !in setOf("choice","detected")
                    if(repeatedPrompt || rapid) {
                        incoming.put("autoStatus",
                            if(repeatedPrompt)"clarification_waiting" else "throttled")
                    } else {''')
change('''                                action.actionIntent.send(this,0,intent)
                                incoming.put("autoStatus","submitted_unverified")''',
'''                                action.actionIntent.send(this,0,intent)
                                // Persist route only after Android accepts the send.
                                if(decision.needsChoice) {
                                    routes.edit().putString(routeKey,JSONObject()
                                        .put("business","").put("lastSeen",now)
                                        .put("pendingChoice",true)
                                        .put("promptAt",now).toString()).apply()
                                } else if(decision.business=="movieplay" || decision.business=="tresm") {
                                    routes.edit().putString(routeKey,JSONObject()
                                        .put("business",decision.business).put("lastSeen",now)
                                        .put("pendingChoice",false)
                                        .put("promptAt",0L).toString()).apply()
                                }
                                incoming.put("autoStatus","submitted_unverified")''')
p.write_text(s)
print("Listener stores route per WhatsApp and supports immediate clarifications")
