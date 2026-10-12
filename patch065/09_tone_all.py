from pathlib import Path
import json,re
root=Path("source/autoresponder-pro")
native=root/"android/app/src/main/java/com/autoresponder/pro"

# Short, human-sounding catalog responses in Android. Keep original verified
# prices, plans, offers, availability labels and source item IDs unchanged.
p=native/"LocalCatalog.kt"
s=p.read_text(encoding="utf-8")
def ch(a,b):
 global s
 assert s.count(a)==1,(a[:90],s.count(a))
 s=s.replace(a,b,1)
ch('''        val chosen=selected.take(7)
        val lines=mutableListOf(if(business=="tresm")"🍔 *LAS TRES M*" else "🎬 *MOVIEPLAY*",
            "",if(business=="tresm")"📋 *Consulta de nuestro menú*" else "📺 *Planes y precios disponibles*","")''',
'''        val showAll=Regex("\\\\b(todos|todas|lista completa|todos los precios|catalogo completo)\\\\b")
            .containsMatchIn(normalized)
        val chosen=selected.take(if(showAll)7 else 5)
        val lines=mutableListOf(if(business=="tresm")
            "¡Claro! 😊 Tengo estas opciones de Las Tres M:"
            else "¡Claro! 😊 Tengo estas opciones en MoviePlay:","")''')
ch('''            lines.add("• *$name*"+details)
            lines.add("  💵 $amount"+if(validOffer && item.optBoolean("active",false))
                " (oferta hasta $until)" else "")
            if(!item.optBoolean("active",false))
                lines.add("  🚫 *NO DISPONIBLE POR EL MOMENTO*")''',
'''            lines.add("• *$name*"+details+" — *$amount*"+
                if(validOffer && item.optBoolean("active",false))" (oferta hasta $until)" else "")
            if(!item.optBoolean("active",false))
                lines.add("  🚫 *NO DISPONIBLE POR EL MOMENTO*")''')
ch('''        if(!anythingAvailable){
            lines.add("Este producto está temporalmente fuera de venta. El precio es solo informativo.")
            lines.add("Si deseas, te contamos las opciones disponibles. 😊")
        } else if(business=="tresm"){
            lines.add("📲 *Menú completo y pedidos:*")
            lines.add("https://lastresm.netlify.app")
            lines.add("")
            lines.add("¿Qué se te antoja? 😊")
        } else {
            lines.add("¿Cuál opción disponible te interesa? 😊")
        }''',
'''        if(!anythingAvailable){
            lines.add("Esos productos no están disponibles ahora. El precio es de referencia.")
            lines.add("¿Te busco otra opción?")
        } else if(business=="tresm"){
            lines.add("Menú: https://lastresm.netlify.app")
            lines.add("¿Cuál te gustaría pedir?")
        } else {
            if(selected.size>chosen.size)lines.add("Tengo más opciones si las necesitas.")
            lines.add("¿Cuál te interesa?")
        }''')
p.write_text(s,encoding="utf-8")

# Keep the owner's exact thank-you text but shorten the generic clarification
# and business-specific welcome replies.
p=native/"NativeAutoReplyEngine.kt"
s=p.read_text(encoding="utf-8")
old='''text="""👋 *¡HOLA! BIENVENIDO*

Para atenderte mejor, elige tu negocio:

*1️⃣ 🎬 MOVIEPLAY*
Streaming, planes, combos y soporte.

*2️⃣ 🍔 LAS TRES M*
Comidas rápidas, menú y pedidos.

✍️ *Responde 1 o 2, o escribe MoviePlay / Las Tres M.*""",'''
new='''text="""¡Hola! 😊 ¿Me escribes por cuál negocio?

1️⃣ 🎬 *MoviePlay*
2️⃣ 🍔 *Las Tres M*

Responde 1 o 2, o escribe el nombre y te ayudo.""",'''
assert s.count(old)==1
s=s.replace(old,new,1)
old='''"movieplay" -> """🎬 *MOVIEPLAY*

¡Hola! 👋 Bienvenido.

📺 *¿Qué plataforma necesitas?*
Te ayudamos con planes, precios, combos y soporte.

💚 Cuéntanos qué servicio deseas consultar."""
                    "tresm" -> """🍔 *LAS TRES M*

¡Hola! 👋 Bienvenido.

📋 *Menú, precios y pedidos:*
https://lastresm.netlify.app

📍 Barrio Ciudadela, La Ceja.

❤️ ¿Qué comida te interesa?"""'''
new='''"movieplay" -> "¡Hola! 😊 Dime qué plataforma necesitas y te paso los precios."
                    "tresm" -> "¡Hola! 😊 Te paso el menú: https://lastresm.netlify.app\\\\n¿Qué te gustaría pedir?"'''
assert s.count(old)==1
s=s.replace(old,new,1)
# Set first-person, short payment replies for ALL customers and sellers.
old='''PaymentReplies.reply(config,business,m,paymentMenuPending)?.let {'''
assert s.count(old)==1
s=s.replace(old,'''PaymentReplies.reply(config,business,m,paymentMenuPending,casual=true)?.let {''',1)
p.write_text(s,encoding="utf-8")

# The user approved an exact thank-you message. Do not change it.
p=native/"PaymentReplies.kt"
s=p.read_text(encoding="utf-8")
old='''return Result("Claro 😊 ¿Por cuál medio te queda más fácil?\\\\n\\\\n"+
                "1️⃣ Nequi\\\\n2️⃣ Bancolombia\\\\n3️⃣ DaviPlata\\\\n4️⃣ Llave\\\\n\\\\n"+
                "Dime el número o el medio y te paso los datos.",isMenu=true)'''
# In generated Kotlin source, Python unescaping is applied to the patch. Handle
# both one and two backslash forms, avoiding unexpected changes.
if s.count(old)!=1:
    old=old.replace("\\\\\\\\n","\\\\n")
if s.count(old)!=1:raise AssertionError("seller payment menu changed")
new=old.replace('Claro 😊 ¿Por cuál medio te queda más fácil?','Claro 😊 ¿Por cuál medio te queda más fácil?').replace('1️⃣ Nequi','💳 *MEDIOS DE PAGO*\\\\n\\\\n1️⃣ Nequi')
# Unit test checks that a payment menu says MEDIOS DE PAGO even in the casual tone.
s=s.replace(old,new,1)
# Ensure the no-account fallback doesn't promise human delivery or confirmation.
s=s.replace('''"$title\\n\\n💳 Los datos de pago para este negocio se confirman directamente con nuestro equipo.\\n\\n" +
            "Escríbenos cuando estés listo para pagar. 😊"''',
''' "Por ahora no tengo configurados los datos de pago de este negocio. Te los confirmo por aquí. 😊"''')
p.write_text(s,encoding="utf-8")

# Simulator gives the same short prices and personal tone.
p=root/"web/app.js"
s=p.read_text(encoding="utf-8")
old='''    const items=(scoped.length?scoped:matching).slice(0,7);
    const firstActive=items.find(i=>i.active);
    const lines=[business==="tresm"?"🍔 *LAS TRES M*":"🎬 *MOVIEPLAY*",
       "",business==="tresm"?"📋 *Consulta de nuestro menú*":"📺 *Planes y precios disponibles*",""];'''
new='''    const choices=scoped.length?scoped:matching;
    const showAll=/\\b(todos|todas|lista completa|todos los precios|catalogo completo)\\b/.test(normalize(message));
    const items=choices.slice(0,showAll?7:5);
    const firstActive=items.find(i=>i.active);
    const lines=[business==="tresm"?"¡Claro! 😊 Tengo estas opciones de Las Tres M:":
      "¡Claro! 😊 Tengo estas opciones en MoviePlay:",""];'''
assert s.count(old)==1
s=s.replace(old,new,1)
old='''      lines.push("• *"+item.name+"*"+(item.duration?" · "+item.duration:""));
      lines.push("  💵 "+(amount>0?"$"+amount.toLocaleString("es-CO"):
        business==="tresm"?"Consultar en el menú":"Precio por confirmar")+
        (valid&&item.active?" (oferta hasta "+item.offerUntil+")":""));'''
new='''      lines.push("• *"+item.name+"*"+(item.duration?" · "+item.duration:"")+
        " — *"+(amount>0?"$"+amount.toLocaleString("es-CO"):
        business==="tresm"?"Consultar en el menú":"Precio por confirmar")+"*"+
        (valid&&item.active?" (oferta hasta "+item.offerUntil+")":""));'''
assert s.count(old)==1
s=s.replace(old,new,1)
old='''      lines.push("Este producto está temporalmente fuera de venta. El precio es solo informativo.",
        "Si deseas, te contamos las opciones disponibles. 😊");
    } else if(business==="tresm")lines.push("📲 *Menú completo y pedidos:*",
      "https://lastresm.netlify.app","","¿Qué se te antoja? 😊");
    else lines.push("¿Cuál opción disponible te interesa? 😊");'''
new='''      lines.push("Esos productos no están disponibles ahora. El precio es de referencia.",
        "¿Te busco otra opción?");
    } else if(business==="tresm")lines.push("Menú: https://lastresm.netlify.app",
      "¿Cuál te gustaría pedir?");
    else {
      if(choices.length>items.length)lines.push("Tengo más opciones si las necesitas.");
      lines.push("¿Cuál te interesa?");
    }'''
assert s.count(old)==1
s=s.replace(old,new,1)
old='''    if(type==="menu")return "Claro 😊 ¿Por cuál medio te queda más fácil?\\n\\n"+
        "1️⃣ Nequi\\n2️⃣ Bancolombia\\n3️⃣ DaviPlata\\n4️⃣ Llave\\n\\n"+'''
new='''    if(type==="menu")return "Claro 😊 ¿Por cuál medio te queda más fácil?\\n\\n"+
        "💳 *MEDIOS DE PAGO*\\n\\n1️⃣ Nequi\\n2️⃣ Bancolombia\\n3️⃣ DaviPlata\\n4️⃣ Llave\\n\\n"+'''
assert s.count(old)==1
s=s.replace(old,new,1)
old='''    const payment=paymentAnswer(assistant,text);'''
assert s.count(old)==1
s=s.replace(old,'''    const payment=paymentAnswer(assistant,text,true);''',1)
old='''reply:"👋 *¡HOLA! BIENVENIDO*\\n\\nPara atenderte mejor, elige tu negocio:\\n\\n*1️⃣ 🎬 MOVIEPLAY*\\nStreaming, planes, combos y soporte.\\n\\n*2️⃣ 🍔 LAS TRES M*\\nComidas rápidas, menú y pedidos.\\n\\n✍️ *Responde 1 o 2, o escribe MoviePlay / Las Tres M.*",'''
new='''reply:"¡Hola! 😊 ¿Me escribes por cuál negocio?\\n\\n1️⃣ 🎬 *MoviePlay*\\n2️⃣ 🍔 *Las Tres M*\\n\\nResponde 1 o 2, o escribe el nombre y te ayudo.",'''
assert s.count(old)==1
s=s.replace(old,new,1)
p.write_text(s,encoding="utf-8")
(root/"android/app/src/main/assets/app.js").write_text(s,encoding="utf-8")
print("First-person concise catalog, payment, welcome, and selector for both businesses while retaining exact thank-you template")
