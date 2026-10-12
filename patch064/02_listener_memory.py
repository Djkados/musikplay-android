from pathlib import Path
p=Path("source/autoresponder-pro/android/app/src/main/java/com/autoresponder/pro/WhatsAppNotificationListener.kt")
s=p.read_text(encoding="utf-8")
def rep(a,b):
 global s
 assert s.count(a)==1,(a[:115],s.count(a))
 s=s.replace(a,b,1)
rep('''                val paymentMenuPending=fresh && previous.optBoolean("pendingPaymentMenu",false) &&
                    now-previous.optLong("paymentMenuAt",0L) in 0L until 600_000L
                val decision=if(now<humanPauseUntil)''',
'''                val paymentMenuPending=fresh && previous.optBoolean("pendingPaymentMenu",false) &&
                    now-previous.optLong("paymentMenuAt",0L) in 0L until 600_000L
                // Product memory is independent of the business name and expires
                // after 24h. Stored fields are IDs, states and a small quantity only.
                val productFresh=fresh && AssistantCadence.recent(now,
                    previous.optLong("productAt",0L),24L*60L*60L*1000L)
                val memoryId=if(productFresh)previous.optString("productId") else ""
                val memoryStage=if(productFresh)previous.optString("productStage") else ""
                val memoryQuantity=if(productFresh)
                    previous.optInt("productQuantity",0).coerceIn(0,15) else 0
                val decision=if(now<humanPauseUntil)''')
rep('''                    rememberedBusiness=remembered,awaitingChoice=pending,
                    paymentMenuPending=paymentMenuPending)''',
'''                    rememberedBusiness=remembered,awaitingChoice=pending,
                    paymentMenuPending=paymentMenuPending,
                    rememberedProductId=memoryId,rememberedProductStage=memoryStage,
                    rememberedQuantity=memoryQuantity)''')
rep('''                    .put("imageTag",decision.imageTag)
                    .put("learnEligible",''',
'''                    .put("imageTag",decision.imageTag)
                    .put("conversationStep",if(decision.routeSource=="memory")
                        decision.memoryStage else "")
                    .put("learnEligible",''')
rep('''setOf("choice","detected","payment_choice","payment_specific","courtesy")''',
'''setOf("choice","detected","payment_choice","payment_specific","courtesy","memory")''')
rep('''                                // Persist route only after Android accepts the send.
                                if(decision.needsChoice) {''',
'''                                // The context is updated only after the quick-reply
                                // PendingIntent succeeds. No address or message text.
                                val currentProduct=when {
                                    decision.routeSource=="memory" && decision.memoryProductId.isNotBlank() ->
                                        ConversationFlow.Memory(decision.memoryProductId,
                                            decision.memoryStage,decision.memoryQuantity)
                                    decision.business!=null &&
                                        (decision.business!=remembered || !productFresh) &&
                                        decision.reason !in setOf("Catálogo aprobado",
                                            "Compra guiada; pendiente de confirmación",
                                            "Solicitud de pedido; falta revisión") -> null
                                    decision.business in setOf("movieplay","tresm") ->
                                        ConversationFlow.remember(config,decision.business!!,
                                            message,decision.reason)
                                        ?: if(productFresh && decision.business==remembered)
                                            ConversationFlow.Memory(memoryId,memoryStage,memoryQuantity)
                                        else null
                                    else -> null
                                }
                                val contextAt=if(decision.routeSource=="memory" ||
                                    currentProduct?.productId!=memoryId ||
                                    currentProduct?.stage!=memoryStage)now
                                    else previous.optLong("productAt",0L)
                                // Persist route only after Android accepts the send.
                                if(decision.needsChoice) {''')
rep('''                                        .put("pendingPaymentMenu",false).toString()).apply()''',
'''                                        .put("pendingPaymentMenu",false)
                                        .put("productId","").put("productStage","")
                                        .put("productQuantity",0).put("productAt",0L)
                                        .toString()).apply()''')
rep('''                                        .put("paymentMenuAt",if(decision.paymentMenu)now else 0L)
                                        .toString()).apply()''',
'''                                        .put("paymentMenuAt",if(decision.paymentMenu)now else 0L)
                                        .put("productId",currentProduct?.productId.orEmpty())
                                        .put("productStage",currentProduct?.stage.orEmpty())
                                        .put("productQuantity",currentProduct?.quantity ?: 0)
                                        .put("productAt",if(currentProduct!=null)contextAt else 0L)
                                        .toString()).apply()''')
p.write_text(s,encoding="utf-8")
print("Persist approved product IDs/quantity/step for 24h per WhatsApp conversation; prioritize context follow-up without breaking payment menus")
