from pathlib import Path
root=Path("source/autoresponder-pro/android/app/src/main/java/com/autoresponder/pro")

p=root/"NativeAutoReplyEngine.kt"
s=p.read_text(encoding="utf-8")
marker='''    private fun assignedBusiness(config:JSONObject,channel:String,contact:String,'''
insert='''    /**
     * A seller/revendedor is explicitly marked by the owner, NEVER inferred
     * from free-form chat. A match is scoped to the selected WhatsApp channel.
     */
    fun sellerBusiness(config:JSONObject,channel:String,contact:String):String? {
        val sellers=config.optJSONArray("sellerContacts")?:return null
        for(i in 0 until sellers.length()){
            val seller=sellers.optJSONObject(i)?:continue
            if(seller.optString("channel")==channel && matchContact(seller,contact)){
                val business=seller.optString("assistant")
                return business.takeIf{it=="movieplay" || it=="tresm"}
            }
        }
        return null
    }

'''
assert s.count(marker)==1
s=s.replace(marker,insert+marker,1)
# Define the seller only mode ahead of generic pauses/welcome/schedules:
# safety, blocked/allowlist still take full precedence.
marker='''        val paused=config.optJSONArray("paused")'''
insert='''        val seller=sellerBusiness(config,channel,c)
        if(seller!=null) {
            // In this mode no catalog, welcome, business selection, away
            // notices, support, order, guided sale or learning response is sent.
            // Gratitude and explicit bank requests work even after a human reply.
            if(CourtesyReplies.matches(m))
                return Decision(text=CourtesyReplies.message,reason="Agradecimiento al vendedor",
                    routeSource="courtesy")
            PaymentReplies.reply(config,seller,m,paymentMenuPending,casual=true)?.let {
                return Decision(text=it.text,business=seller,department="sales",
                    reason=if(it.isMenu)"Medios de pago para vendedor" else
                        "Medio de pago para vendedor",
                    routeSource=if(it.choice)"payment_choice" else "payment_specific",
                    paymentMenu=it.isMenu)
            }
            return Decision(reason="Vendedor: conversación humana; solo agradecimientos y pagos",
                business=seller,routeSource="seller_human")
        }
'''
assert s.count(marker)==1
s=s.replace(marker,insert+marker,1)
p.write_text(s,encoding="utf-8")

p=root/"PaymentReplies.kt"
s=p.read_text(encoding="utf-8")
needle='''        pendingMenu:Boolean=false):Result? {'''
replacement='''        pendingMenu:Boolean=false,casual:Boolean=false):Result? {'''
assert s.count(needle)==1
s=s.replace(needle,replacement,1)
# Add common, more natural payment requests that do not contain bank names,
# e.g. "donde te transfiero" without confusing statements of a past payment.
needle=r'''            "\\ba donde transfiero\\b|\\bpagar el servicio\\b"'''
# Source contains Kotlin escaped regex sequences: in Python these are literal \\b
if s.count(needle)!=1:
    raise AssertionError(("payment anchor",s.count(needle)))
s=s.replace(needle,'''            "\\\\ba donde transfiero\\\\b|\\\\bpagar el servicio\\\\b|"+
            "\\\\b(?:donde|a donde|por donde|en donde) (?:te |le |les |puedo )?(?:transfiero|transferir|consigno|deposito)\\\\b|"+
            "\\\\b(?:a que|a cual) (?:cuenta|numero|llave) (?:te )?(?:transfiero|transfieren|transfiera|puedo transferir)?\\\\b|"+
            "\\\\b(?:pasame|mandame|enviame|me pasas|me mandas|me compartes) (?:las? )?(?:cuentas?|datos? (?:de|para) pago|medios? de pago|numero|llave)\\\\b|"+
            "\\\\b(?:quiero|voy a|puedo) (?:transferirte|transferir|pagarte)\\\\b"''',1)

needle='''        val intro=if(method=="menu"){'''
seller='''        // Seller messages are deliberately short and written in a personal
        // voice. The standard customer templates remain unchanged.
        if(casual && method=="menu"){
            return Result("Claro 😊 ¿Por cuál medio te queda más fácil?\\\\n\\\\n"+
                "1️⃣ Nequi\\\\n2️⃣ Bancolombia\\\\n3️⃣ DaviPlata\\\\n4️⃣ Llave\\\\n\\\\n"+
                "Dime el número o el medio y te paso los datos.",isMenu=true)
        }
        if(casual){
            if(method=="llaves"){
                val keys=listOf("Nequi" to nequi,"Bancolombia" to bank,
                    "DaviPlata" to davi).mapNotNull { (label,record)->
                    record?.optString("key")?.takeIf{it.isNotBlank()}?.let{label+": "+it}
                }
                return Result("Claro 🙌 Estas son las llaves que manejo:\\\\n\\\\n"+
                    keys.joinToString("\\\\n")+
                    "\\\\n\\\\nCuando transfieras, me envías el comprobante y lo reviso.")
            }
            val title=when(method) {
                "nequi"->"Nequi"
                "bancolombia"->"Bancolombia"
                else->"DaviPlata"
            }
            val record=when(method) {
                "nequi"->nequi
                "bancolombia"->bank
                else->davi
            }
            val number=record?.optString("number","")?.trim().orEmpty()
            val key=record?.optString("key","")?.trim().orEmpty()
            val pieces=mutableListOf("Claro 😊 Te paso los datos de $title:","")
            if(holder.isNotEmpty())pieces.add("👤 $holder")
            if(number.isNotEmpty())pieces.add((if(method=="bancolombia")
                "🏦 Cuenta de ahorros: " else "📲 Número: ")+number)
            if(key.isNotEmpty())pieces.add("🔑 Llave: "+key)
            pieces.add("")
            pieces.add("Cuando transfieras, me envías el comprobante y lo reviso. 🙌")
            return Result(pieces.joinToString("\\\\n"),choice=shortcut!=null)
        }
        val intro=if(method=="menu"){'''
assert s.count(needle)==1
s=s.replace(needle,seller,1)
# Kotlin source has strings with double backslash? Verify actual generated expected.
p.write_text(s,encoding="utf-8")
print("Native seller identification is explicit, scoped per WhatsApp; seller only thanks/payment. Added colloquial transfer phrase and short personal payment tone.")
