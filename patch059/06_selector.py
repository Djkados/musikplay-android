from pathlib import Path
root=Path("source/autoresponder-pro")
native=root/"android/app/src/main/java/com/autoresponder/pro/NativeAutoReplyEngine.kt"
s=native.read_text(encoding="utf-8")
def replace(a,b):
 global s
 assert s.count(a)==1,(a[:80],s.count(a))
 s=s.replace(a,b,1)
replace('''    private val food = listOf("las tres m",''','''    private val food = listOf("tres m", "las 3 m", "las tres emes", "las tres m",''')
replace('''        val normalized=normalize(message)
        val m=movie.any { normalized.contains(it) }''','''        val normalized=normalize(message)
        val choice=normalized.replace("\\uFE0F","").replace("\\u20E3","")
            .replace(Regex("[^a-z0-9 ]")," ").replace(Regex("\\\\s+")," ").trim()
        val m=movie.any { normalized.contains(it) }''')
replace('''            if(normalized in setOf("1","opcion 1","la primera","primera"))
                return Route("movieplay","choice")
            if(normalized in setOf("2","opcion 2","la segunda","segunda"))
                return Route("tresm","choice")''',
'''            if(choice in setOf("1","opcion 1","opcion uno","uno","la primera","primera","quiero la 1","la 1","quiero movieplay"))
                return Route("movieplay","choice")
            if(choice in setOf("2","opcion 2","opcion dos","dos","la segunda","segunda","quiero la 2","la 2","quiero las tres m"))
                return Route("tresm","choice")''')
replace('''text="¡Hola! 👋 ¿Tu consulta es para 🎬 MoviePlay (1) o 🍔 Las Tres M (2)? Así te damos la información y el horario correctos.",''',
'''text="""👋 *¡HOLA! BIENVENIDO*

Para atenderte mejor, elige tu negocio:

*1️⃣ 🎬 MOVIEPLAY*
Streaming, planes, combos y soporte.

*2️⃣ 🍔 LAS TRES M*
Comidas rápidas, menú y pedidos.

✍️ *Responde 1 o 2, o escribe MoviePlay / Las Tres M.*""",''')
replace('''"movieplay" -> "🎬 ¡Bienvenido a MoviePlay! ¿Qué plataforma deseas consultar? Te ayudamos con planes, precios y soporte."
                    "tresm" -> "🍔 ¡Bienvenido a Las Tres M! Mira el menú y los precios en https://lastresm.netlify.app. ¿Qué comida te interesa?"''',
'''"movieplay" -> """🎬 *MOVIEPLAY*

¡Hola! 👋 Bienvenido.

📺 *¿Qué plataforma necesitas?*
Te ayudamos con planes, precios, combos y soporte.

💚 Cuéntanos qué servicio deseas consultar."""
                    "tresm" -> """🍔 *LAS TRES M*

¡Hola! 👋 Bienvenido.

📋 *Menú, precios y pedidos:*
https://lastresm.netlify.app

📍 Barrio Ciudadela, La Ceja.

❤️ ¿Qué comida te interesa?"""''')
native.write_text(s,encoding="utf-8")

js=root/"web/app.js"
w=js.read_text(encoding="utf-8")
old='''reply:'¡Hola! 👋 Gracias por escribir. ¿Tu consulta es para 🎬 MoviePlay o para 🍔 Las Tres M? Así te compartimos la información y el horario correctos.','''
new='''reply:"👋 *¡HOLA! BIENVENIDO*\\n\\nPara atenderte mejor, elige tu negocio:\\n\\n*1️⃣ 🎬 MOVIEPLAY*\\nStreaming, planes, combos y soporte.\\n\\n*2️⃣ 🍔 LAS TRES M*\\nComidas rápidas, menú y pedidos.\\n\\n✍️ *Responde 1 o 2, o escribe MoviePlay / Las Tres M.*",'''
assert w.count(old)==1
w=w.replace(old,new,1)
w=w.replace("i.autoStatus==='throttled'?' · Autoenvío limitado por seguridad'",
            "i.autoStatus==='throttled'?' · Esperando siguiente consulta tras respuesta'",1)
js.write_text(w,encoding="utf-8")
(root/"android/app/src/main/assets/app.js").write_text(w,encoding="utf-8")
engine=root/"web/schedule-engine.js"
e=engine.read_text(encoding="utf-8")
old="['las tres m',12]"
assert e.count(old)==1
e=e.replace(old,"['las tres m',12],['las 3 m',12],['tres m',12]",1)
old="const answer=normalize(message);"
assert e.count(old)==1
e=e.replace(old,"const answer=normalize(message).replace(/[\\uFE0F\\u20E3]/g,'').replace(/[^a-z0-9 ]/g,' ').replace(/\\s+/g,' ').trim();",1)
e=e.replace("['1','opcion 1','la primera','primera']", "['1','opcion 1','opcion uno','uno','la primera','primera','quiero la 1','la 1']",1)
e=e.replace("['2','opcion 2','la segunda','segunda']", "['2','opcion 2','opcion dos','dos','la segunda','segunda','quiero la 2','la 2']",1)
engine.write_text(e,encoding="utf-8")
(root/"android/app/src/main/assets/schedule-engine.js").write_text(e,encoding="utf-8")
p=root/"tests/schedules.test.cjs";t=p.read_text(encoding="utf-8")
assert "/MoviePlay.*Las Tres M/" in t
t=t.replace("/MoviePlay.*Las Tres M/",r"/MoviePlay[\s\S]*Las Tres M/")
anchor="// End-to-end with rules + app safety gate + hours at specified Bogota time."
extra="""assert.equal(engine.resolveAssignment('normal','Nuevo','1️⃣',channels,[],{awaitingChoice:true}).assistant,'movieplay');
assert.equal(engine.resolveAssignment('business','Nuevo','2️⃣',channels,[],{awaitingChoice:true}).assistant,'tresm');
assert.equal(engine.resolveAssignment('normal','Nuevo','MoviePlay',channels,[],{awaitingChoice:true}).assistant,'movieplay');
assert.equal(engine.resolveAssignment('business','Nuevo','Las Tres M',channels,[],{awaitingChoice:true}).assistant,'tresm');
"""
assert anchor in t
p.write_text(t.replace(anchor,extra+anchor,1),encoding="utf-8")
# native test the short and textual responses in both WhatsApp channels
p=root/"android/app/src/test/java/com/autoresponder/pro/NativeAutoReplyEngineTest.kt"
t=p.read_text(encoding="utf-8")
assert t.rstrip().endswith("}")
t=t.rstrip()[:-1]+'''
    @Test fun formattedSelectorAcceptsNumbersAndBusinessNames() {
        val c=config()
        c.getJSONObject("settings").put("requireAllowlist",false)
            .getJSONObject("autoReplies").put("normal",true)
        val at=clock("2026-10-10","19:00")
        val ask=NativeAutoReplyEngine.decide(c,"business","Nuevo","hola",at)
        assertTrue(ask.text!!.contains("\\n\\n"))
        assertTrue(ask.text!!.contains("*1️⃣"))
        assertTrue(ask.text!!.contains("MoviePlay / Las Tres M"))
        for(ch in listOf("normal","business")) {
            assertEquals("movieplay",NativeAutoReplyEngine.decide(c,ch,"Nuevo","1",at,awaitingChoice=true).business)
            assertEquals("tresm",NativeAutoReplyEngine.decide(c,ch,"Nuevo","2",at,awaitingChoice=true).business)
            assertEquals("movieplay",NativeAutoReplyEngine.decide(c,ch,"Nuevo","MoviePlay",at,awaitingChoice=true).business)
            assertEquals("tresm",NativeAutoReplyEngine.decide(c,ch,"Nuevo","Las Tres M",at,awaitingChoice=true).business)
        }
    }
}
'''
p.write_text(t,encoding="utf-8")
print("Formatted selector and numeric/name replies implemented")
