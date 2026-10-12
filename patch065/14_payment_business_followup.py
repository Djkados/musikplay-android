from pathlib import Path

root=Path("source/autoresponder-pro")
native=root/"android/app/src/main/java/com/autoresponder/pro"

# All sales channels use ONE verified set of payment accounts, independent of
# whether the chat is about MoviePlay or Las Tres M.
p=native/"PaymentReplies.kt"
s=p.read_text(encoding="utf-8")
a='''val data=config.optJSONObject("payments")?.optJSONObject(business)'''
b='''val data=config.optJSONObject("payments")?.optJSONObject("movieplay")
            ?: config.optJSONObject("payments")?.optJSONObject(business)'''
assert s.count(a)==1
p.write_text(s.replace(a,b,1),encoding="utf-8")

p=native/"NativeAutoReplyEngine.kt"
s=p.read_text(encoding="utf-8")
def replace(old,new):
 global s
 assert s.count(old)==1,("native anchor",old[:100],s.count(old))
 s=s.replace(old,new,1)

# Payments are an allowed exception during attention by a person, even if the
# customer has never selected a business. Safety/exclusions still run first.
replace('''            val business=assignedBusiness(config,channel,c,m,rememberedBusiness,awaitingChoice)
                .business?.takeIf{it=="movieplay" || it=="tresm"}
            if(business!=null){
                PaymentReplies.reply(config,business,m,paymentMenuPending,casual=true)?.let{
                    return Decision(text=it.text,business=business,
                        reason="Medio de pago durante atención humana",
                        routeSource=if(it.choice)"payment_choice" else "payment_specific",
                        paymentMenu=it.isMenu)
                }
            }''',
'''            PaymentReplies.reply(config,"movieplay",m,paymentMenuPending,casual=true)?.let{
                return Decision(text=it.text,
                    business=rememberedBusiness?.takeIf{b->b=="movieplay" || b=="tresm"},
                    reason="Medio de pago durante atención humana",
                    routeSource=if(it.choice)"payment_choice" else "payment_specific",
                    paymentMenu=it.isMenu)
            }''')

replace('''        val route=assignedBusiness(config,channel,c,m,rememberedBusiness,awaitingChoice)
        val business=route.business ?: run {''',
'''        // Shared payment data does not require the user to choose a business.
        // It also works after the menu's 1/2/3/4 selection, if pending.
        PaymentReplies.reply(config,"movieplay",m,paymentMenuPending,casual=true)?.let {
            return Decision(text=it.text,
                business=rememberedBusiness?.takeIf{b->b=="movieplay" || b=="tresm"},
                reason=if(it.isMenu)"Medios de pago compartidos" else
                    "Medio de pago compartido",
                routeSource=if(it.choice)"payment_choice" else "payment_specific",
                paymentMenu=it.isMenu)
        }
        val route=assignedBusiness(config,channel,c,m,rememberedBusiness,awaitingChoice)
        val business=route.business ?: run {''')
p.write_text(s,encoding="utf-8")

p=native/"WhatsAppNotificationListener.kt"
s=p.read_text(encoding="utf-8")
# A bank selection may be requested before a business is known.
old='''                                } else if(decision.business=="movieplay" || decision.business=="tresm") {'''
new='''                                } else if(decision.business==null &&
                                    decision.routeSource in setOf("payment_specific","payment_choice")) {
                                    val saved=JSONObject(previous.toString())
                                        .put("lastSeen",now)
                                        .put("pendingPaymentMenu",decision.paymentMenu)
                                        .put("paymentMenuAt",if(decision.paymentMenu)now else 0L)
                                    routes.edit().putString(routeKey,saved.toString()).apply()
                                } else if(decision.business=="movieplay" || decision.business=="tresm") {'''
assert s.count(old)==1
p.write_text(s.replace(old,new,1),encoding="utf-8")

p=root/"web/app.js"
s=p.read_text(encoding="utf-8")
a='''const pay=state.payments[assistant]||paymentDefaults()[assistant];'''
b='''const pay=state.payments.movieplay||paymentDefaults().movieplay;'''
assert s.count(a)==1
s=s.replace(a,b,1)
# An unknown business should receive the shared methods immediately.
old='''    const assign=assignmentFor(channel,contact,text);'''
new='''    const sharedPayment=paymentAnswer("movieplay",text,true);
    if(sharedPayment)return {reply:sharedPayment,assistant:null,unit:null,
      method:"payment_specific",status:"open",image:null};
    const assign=assignmentFor(channel,contact,text);'''
assert s.count(old)==1
s=s.replace(old,new,1)

# The operator edits shared payment data once, for both businesses.
old='''    return '<div class="home-intro"><div><span class="pill">PAGOS · DATOS LOCALES</span>'+'''
new='''    return '<div class="home-intro"><div><span class="pill">PAGOS · DATOS COMPARTIDOS</span>'+'''
assert s.count(old)==1
s=s.replace(old,new,1)
old='''      '</div></div><div class="grid cols2">'+card("movieplay")+card("tresm")+'</div>';'''
new='''      '</div></div><div class="grid cols2">'+card("movieplay")+'</div>';'''
assert s.count(old)==1
s=s.replace(old,new,1)
old='''      state.payments[business]=next;save();render();'''
new='''      state.payments.movieplay=next;
      state.payments.tresm=JSON.parse(JSON.stringify(next));
      save();render();'''
assert s.count(old)==1
s=s.replace(old,new,1)
p.write_text(s,encoding="utf-8")
(root/"android/app/src/main/assets/app.js").write_text(s,encoding="utf-8")
print("Payments shared automatically: no selector, no duplicated merchant accounts, safe 1-4 follow-up even before business selection")
