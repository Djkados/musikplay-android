from pathlib import Path
root=Path("source/autoresponder-pro/android/app/src/main/java/com/autoresponder/pro")
p=root/"NativeAutoReplyEngine.kt"
s=p.read_text(encoding="utf-8")
def rep(a,b):
 global s
 assert s.count(a)==1,(a[:100],s.count(a))
 s=s.replace(a,b,1)
rep('''rememberedProductId:String="",rememberedProductStage:String="",rememberedQuantity:Int=0):Decision {''',
'''rememberedProductId:String="",rememberedProductStage:String="",rememberedQuantity:Int=0,
        humanHandoff:Boolean=false):Decision {''')
anchor='''        // A short expression of gratitude is universal to both businesses.'''
block='''        // During a detected human takeover, the bot stays silent except for
        // a stand-alone thank-you or a clear, context-safe payment inquiry.
        // This also handles "donde te transfiero" after the operator replied
        // to a regular customer, not only to configured sellers.
        if(humanHandoff){
            if(CourtesyReplies.matches(m))
                return Decision(text=CourtesyReplies.message,
                    reason="Agradecimiento durante atención humana",routeSource="courtesy")
            val business=assignedBusiness(config,channel,c,m,rememberedBusiness,awaitingChoice)
                .business?.takeIf{it=="movieplay" || it=="tresm"}
            if(business!=null){
                PaymentReplies.reply(config,business,m,paymentMenuPending,casual=true)?.let{
                    return Decision(text=it.text,business=business,
                        reason="Medio de pago durante atención humana",
                        routeSource=if(it.choice)"payment_choice" else "payment_specific",
                        paymentMenu=it.isMenu)
                }
            }
            return Decision(reason="Atención humana: solo gracias y medios de pago",
                routeSource="human_pause")
        }
'''
assert s.count(anchor)==1
s=s.replace(anchor,block+anchor,1)
p.write_text(s,encoding="utf-8")

p=root/"WhatsAppNotificationListener.kt"
s=p.read_text(encoding="utf-8")
a='''                val decision=if(now<humanPauseUntil && sellerBusiness==null)
                    NativeAutoReplyEngine.Decision(reason="Atención humana pausada",
                        routeSource="human_pause")
                else NativeAutoReplyEngine.decide(config,channel,contact,message,'''
b='''                val decision=NativeAutoReplyEngine.decide(config,channel,contact,message,'''
assert s.count(a)==1
s=s.replace(a,b,1)
a='''                    rememberedProductId=memoryId,rememberedProductStage=memoryStage,
                    rememberedQuantity=memoryQuantity)'''
b='''                    rememberedProductId=memoryId,rememberedProductStage=memoryStage,
                    rememberedQuantity=memoryQuantity,
                    humanHandoff=now<humanPauseUntil)'''
assert s.count(a)==1
s=s.replace(a,b,1)
# Don't keep a redundant, unused sellerBusiness variable in the listener.
a='''                val sellerBusiness=NativeAutoReplyEngine.sellerBusiness(config,channel,contact)
                // Seller mode is permanently quiet except thanks/payments, even
                // while the chat is under the temporary human-takeover timer.
'''
assert s.count(a)==1
s=s.replace(a,"",1)
p.write_text(s,encoding="utf-8")
print("Human takeover whitelist: only gratitude or safely scoped payment inquiries, for sellers and customers; all other bot responses are paused.")
