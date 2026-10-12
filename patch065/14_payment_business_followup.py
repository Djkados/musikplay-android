from pathlib import Path
root=Path("source/autoresponder-pro")
p=root/"android/app/src/main/java/com/autoresponder/pro/NativeAutoReplyEngine.kt"
s=p.read_text(encoding="utf-8")
def rep(a,b):
 global s
 assert s.count(a)==1,("Engine anchor",a[:100],s.count(a))
 s=s.replace(a,b,1)
rep('''        humanHandoff:Boolean=false):Decision {''',
'''        humanHandoff:Boolean=false,paymentBusinessPending:Boolean=false):Decision {''')
rep('''        val route=assignedBusiness(config,channel,c,m,rememberedBusiness,awaitingChoice)
        val business=route.business ?: run {''',
'''        val route=assignedBusiness(config,channel,c,m,rememberedBusiness,awaitingChoice)
        if(route.business==null &&
            PaymentReplies.reply(config,"movieplay",m)!=null) {
            return Decision(
                text="Claro 😊 ¿Es para 🎬 MoviePlay (1) o 🍔 Las Tres M (2)?\\nDime cuál y te paso los medios de pago.",
                reason="Falta identificar negocio para entregar datos de pago",
                routeSource="payment_business_prompt",needsChoice=true)
        }
        val business=route.business ?: run {''')
rep('''        // Payment details are useful 24/7 even when sales support is closed.
        PaymentReplies.reply(config,business,m,paymentMenuPending,casual=true)?.let {''',
'''        // When the customer chose MoviePlay or Las Tres M after asking
        // "donde te transfiero", immediately provide that business's methods.
        if(paymentBusinessPending && route.source in setOf("choice","detected")) {
            PaymentReplies.reply(config,business,"medios de pago",casual=true)?.let {
                return Decision(text=it.text,business=business,department=unit,
                    reason="Medios de pago según negocio confirmado",
                    routeSource="payment_specific",paymentMenu=it.isMenu)
            }
        }
        // Payment details are useful 24/7 even when sales support is closed.
        PaymentReplies.reply(config,business,m,paymentMenuPending,casual=true)?.let {''')
p.write_text(s,encoding="utf-8")

p=root/"android/app/src/main/java/com/autoresponder/pro/WhatsAppNotificationListener.kt"
s=p.read_text(encoding="utf-8")
def rep(a,b):
 global s
 assert s.count(a)==1,("Listener anchor",a[:95],s.count(a))
 s=s.replace(a,b,1)
rep('''                val paymentMenuPending=fresh && previous.optBoolean("pendingPaymentMenu",false) &&
                    now-previous.optLong("paymentMenuAt",0L) in 0L until 600_000L''',
'''                val paymentMenuPending=fresh && previous.optBoolean("pendingPaymentMenu",false) &&
                    now-previous.optLong("paymentMenuAt",0L) in 0L until 600_000L
                val paymentBusinessPending=pending &&
                    previous.optBoolean("pendingPaymentBusiness",false)''')
rep('''                    humanHandoff=now<humanPauseUntil)''',
'''                    humanHandoff=now<humanPauseUntil,
                    paymentBusinessPending=paymentBusinessPending)''')
rep('''                        incoming.put("autoStatus",when {
                            menuCooling -> "menu_cooldown_12h"''',
'''                        if(menuCooling && decision.routeSource=="payment_business_prompt"){
                            // The client already saw the business selector.
                            // Store only intent so choosing 1/2 now returns payment
                            // methods without repeating the selection message.
                            val saved=JSONObject(previous.toString())
                                .put("pendingPaymentBusiness",true)
                            routes.edit().putString(routeKey,saved.toString()).apply()
                        }
                        incoming.put("autoStatus",when {
                            menuCooling -> "menu_cooldown_12h"''')
rep('''                                        .put("pendingPaymentMenu",false)
                                        .put("productId","")''',
'''                                        .put("pendingPaymentMenu",false)
                                        .put("pendingPaymentBusiness",
                                            decision.routeSource=="payment_business_prompt")
                                        .put("productId","")''')
rep('''                                        .put("pendingChoice",false)
                                        .put("promptAt",0L)
                                        .put("pendingPaymentMenu",decision.paymentMenu)''',
'''                                        .put("pendingChoice",false).put("promptAt",0L)
                                        .put("pendingPaymentBusiness",false)
                                        .put("pendingPaymentMenu",decision.paymentMenu)''')
p.write_text(s,encoding="utf-8")

# The standalone simulator cannot inspect Android's per-chat pending intent.
# Show a helpful clarifying message rather than inventing a business/account.
p=root/"web/app.js"
s=p.read_text(encoding="utf-8")
a='''    const assign=assignmentFor(channel,contact,text);'''
b='''    const assign=assignmentFor(channel,contact,text);
    if(!assign.assistant){
      const genericPay=paymentAnswer("movieplay",text,true);
      if(genericPay)return {reply:"Claro 😊 ¿Es para 🎬 MoviePlay (1) o 🍔 Las Tres M (2)?\\nDime cuál y te paso los medios de pago.",
        method:"payment_business_prompt",status:"open",image:null};
    }'''
assert s.count(a)==1
s=s.replace(a,b,1)
p.write_text(s,encoding="utf-8")
(root/"android/app/src/main/assets/app.js").write_text(s,encoding="utf-8")
print("Ambiguous transfer questions now ask business first; selecting 1/2 sends the correct bank menu, no accidental cross-business leakage")
