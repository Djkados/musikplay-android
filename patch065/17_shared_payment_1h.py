from pathlib import Path
root=Path("source/autoresponder-pro")
native=root/"android/app/src/main/java/com/autoresponder/pro"

# One shared set of payment credentials for both businesses.
p=native/"PaymentReplies.kt"
s=p.read_text(encoding="utf-8")
a='''        val data=config.optJSONObject("payments")?.optJSONObject(business)'''
b='''        // The owner confirmed that MoviePlay and Las Tres M use the SAME
        // payment accounts. Keep a single canonical source for both businesses.
        val allPayments=config.optJSONObject("payments")
        val data=allPayments?.optJSONObject("movieplay")
            ?:allPayments?.optJSONObject("tresm")'''
assert s.count(a)==1
p.write_text(s.replace(a,b,1),encoding="utf-8")

p=native/"NativeAutoReplyEngine.kt"
s=p.read_text(encoding="utf-8")
a='''        val seller=sellerBusiness(config,channel,c)'''
b='''        // Clear payment requests do not require selecting a business:
        // both shops use the same accounts. Safety/block/allowlist checks
        // above still apply; payment proof is never treated as a request.
        PaymentReplies.reply(config,"movieplay",m,paymentMenuPending,casual=true)?.let {
            return Decision(text=it.text,business="movieplay",
                reason=if(it.isMenu)"Medios de pago compartidos" else
                    "Medio de pago solicitado",
                routeSource=if(it.choice)"payment_choice" else "payment_specific",
                paymentMenu=it.isMenu)
        }
        val seller=sellerBusiness(config,channel,c)'''
assert s.count(a)==1
s=s.replace(a,b,1)
# Remove now-redundant payment-business clarification and old follow-up state
# logic; callers that specify a business get the exact same account anyway.
start=s.index('''        if(route.business==null &&
            PaymentReplies.reply(config,"movieplay",m)!=null) {''')
end=s.index('''        val business=route.business ?: run {''',start)
s=s[:start]+s[end:]
start=s.index('''        if(paymentBusinessPending && route.source in setOf("choice","detected")) {''')
end=s.index('''        // Payment details are useful 24/7''',start)
s=s[:start]+s[end:]
p.write_text(s,encoding="utf-8")

# Always use the same bank details for unrecognized business contexts during
# operator takeover, instead of turning a transfer request into silence.
p=native/"WhatsAppNotificationListener.kt"
s=p.read_text(encoding="utf-8")
a='''                    val renewalKey=fingerprint("renewal|$channel|$contact")'''
b='''                    // Identical renewal requests are acknowledged once per hour.
                    // Different seller requests may each receive acknowledgement.
                    val renewalKey=fingerprint("renewal|$channel|$contact|"+
                        NativeAutoReplyEngine.normalize(message))'''
assert s.count(a)==1
s=s.replace(a,b,1)
a='''AssistantCadence.recent(now,renewalAt,12L*60L*60L*1000L)'''
b='''AssistantCadence.recent(now,renewalAt,60L*60L*1000L)'''
assert s.count(a)==1
s=s.replace(a,b,1)
a='''renewalCooling -> "renewal_cooldown_12h"'''
b='''renewalCooling -> "renewal_cooldown_1h"'''
assert s.count(a)==1
s=s.replace(a,b,1)
# The payment business selector is no longer shown for either shop.
a='''                        if(menuCooling && decision.routeSource=="payment_business_prompt"){
                            // The client already saw the business selector.
                            // Store only intent so choosing 1/2 now returns payment
                            // methods without repeating the selection message.
                            val saved=JSONObject(previous.toString())
                                .put("pendingPaymentBusiness",true)
                            routes.edit().putString(routeKey,saved.toString()).apply()
                        }
'''
assert s.count(a)==1
s=s.replace(a,"",1)
p.write_text(s,encoding="utf-8")

# One on-device payment form only; edits mirror to both businesses. Existing
# v0.6.4 installations keep their saved MoviePlay bank details.
p=root/"web/app.js"
s=p.read_text(encoding="utf-8")
def rep(a,b):
 global s
 assert s.count(a)==1,(a[:100],s.count(a))
 s=s.replace(a,b,1)
a='''  state.payments ||= paymentDefaults();'''
b='''  state.payments ||= paymentDefaults();
  // Both businesses use the same owner-approved accounts. Old Las Tres M
  // placeholders must not override the MoviePlay payment records.
  state.payments.tresm=JSON.parse(JSON.stringify(
    state.payments.movieplay||paymentDefaults().movieplay));'''
rep(a,b)
# Keep two objects only for backwards compatibility with old imported backups.
rep('''const pay=state.payments[assistant]||paymentDefaults()[assistant];''',
'''const pay=state.payments.movieplay||paymentDefaults().movieplay;''')
rep('''<div class="grid cols2">'+card("movieplay")+card("tresm")+'</div>';''',
'''<div class="stack">'+card("movieplay")+'</div>';''')
rep('''      state.payments[business]=next;save();render();''',
'''      state.payments.movieplay=next;
      state.payments.tresm=JSON.parse(JSON.stringify(next));
      save();render();''')
rep('''<h2>Respuestas de pago separadas por negocio</h2>''',
'''<h2>Medios de pago compartidos por ambos negocios</h2>''')
rep('''pero nunca comparte las cuentas de uno con clientes del otro. Las llaves y números son editables.''',
'''y utiliza exactamente las mismas cuentas para ambos, según tu configuración. Las llaves y números son editables.''')
rep('''Esta información solo se ofrece a consultas de este negocio. ''',
'''Esta información se utiliza en MoviePlay y Las Tres M. ''')
rep('''Una consulta por Nequi entrega solo Nequi; “medios de pago” muestra el menú para escoger.''',
'''Una consulta por Nequi entrega solo Nequi; “medios de pago” muestra el menú sin preguntar el negocio.''')
rep('''    if(!assign.assistant){
      const genericPay=paymentAnswer("movieplay",text,true);
      if(genericPay)return {reply:"Claro 😊 ¿Es para 🎬 MoviePlay (1) o 🍔 Las Tres M (2)?\\nDime cuál y te paso los medios de pago.",
        method:"payment_business_prompt",status:"open",image:null};
    }''',
'''    // Payment info is shared; the assistant must never ask for the shop.
    // A receipt or reported transfer was filtered before reaching this step.
    const sharedPayment=paymentAnswer("movieplay",text,true);
    if(sharedPayment)return {reply:sharedPayment,assistant:null,unit:null,
      method:"payment_specific",status:"open",image:null};''')
# The choice can be returned directly before reaching the business selection.
# This also covers first-contact questions about a bank name or an account.
a='''    const assign=assignmentFor(channel,contact,text);'''
b='''    const commonPayment=paymentAnswer("movieplay",text,true);
    if(commonPayment)return {reply:commonPayment,assistant:null,unit:null,
      method:"payment_specific",status:"open",image:null};
    const assign=assignmentFor(channel,contact,text);'''
rep(a,b)
# The above old fallback still tests a false assign branch and becomes inert,
# but avoid a redundant second payment lookup.
a='''    // Payment info is shared; the assistant must never ask for the shop.
    // A receipt or reported transfer was filtered before reaching this step.
    const sharedPayment=paymentAnswer("movieplay",text,true);
    if(sharedPayment)return {reply:sharedPayment,assistant:null,unit:null,
      method:"payment_specific",status:"open",image:null};
'''
assert s.count(a)==1
s=s.replace(a,"",1)
rep('''renewal_cooldown_12h:'Ya confirmé que revisaré esta renovación; no repetir durante 12 horas',''',
'''renewal_cooldown_1h:'Ya confirmé esta solicitud; no repetir la misma durante una hora',''')
# Both workflows preserve business selection for non-payment queries.
p.write_text(s,encoding="utf-8")
(root/"android/app/src/main/assets/app.js").write_text(s,encoding="utf-8")
print("Shared MoviePlay/Las Tres M payment accounts; direct replies without business selector; renewal duplicate cooldown 1 hour per distinct request")
