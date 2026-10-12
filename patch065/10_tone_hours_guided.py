from pathlib import Path
import json,re
root=Path("source/autoresponder-pro")
p=root/"web/schedule-engine.js"
js=p.read_text(encoding="utf-8")
pattern=r'away:("(?:\\.|[^"\\])*")'
entries=list(re.finditer(pattern,js))
assert len(entries)==3,("Expected MoviePlay sales, support, Las Tres M",len(entries))
oldTexts=[json.loads(x.group(1)) for x in entries]
short=[
    """¡Hola! 😊 Ahora estoy fuera del horario de ventas.

🕘 Atiendo todos los días de 9:00 a. m. a 10:00 p. m.

En cuanto regrese, te respondo. 💚""",
    """¡Hola! 👋 Ahora estoy fuera del horario de soporte.

🕘 Lunes a sábado: 9:00 a. m. a 10:00 p. m.
🕘 Domingos y festivos: 9:00 a. m. a 5:00 p. m.

En cuanto esté disponible, te respondo.""",
    """¡Hola! 😊 Ahora no estoy atendiendo pedidos.

🍔 Atiendo sábados y domingos de 6:00 p. m. a 10:30 p. m.
📍 Barrio Ciudadela, La Ceja

Menú: https://lastresm.netlify.app

Cuando abra, te respondo. 💚"""
]
for match,new in reversed(list(zip(entries,short))):
    js=js[:match.start(1)]+json.dumps(new,ensure_ascii=False)+js[match.end(1):]
p.write_text(js,encoding="utf-8")
(root/"android/app/src/main/assets/schedule-engine.js").write_text(js,encoding="utf-8")
p=root/"web/app.js"
app=p.read_text(encoding="utf-8")
old='''  function migrateScheduleConfig(){'''
new='''  const LEGACY_FACTORY_AWAY_065='''+json.dumps(dict(zip([
    "movieplay:sales","movieplay:support","tresm:orders"
],oldTexts)),ensure_ascii=False,separators=(",",":"))+''';
  function migrateScheduleConfig(){'''
assert app.count(old)==1
app=app.replace(old,new,1)
old='''      if(state.schedules[group][unit].away===LEGACY_AWAY[group+':'+unit])
        state.schedules[group][unit].away=fresh[group][unit].away;'''
new='''      if(state.schedules[group][unit].away===LEGACY_AWAY[group+':'+unit] ||
        state.schedules[group][unit].away===LEGACY_FACTORY_AWAY_065[group+':'+unit])
        state.schedules[group][unit].away=fresh[group][unit].away;'''
assert app.count(old)==1
app=app.replace(old,new,1)
p.write_text(app,encoding="utf-8")
(root/"android/app/src/main/assets/app.js").write_text(app,encoding="utf-8")

p=root/"android/app/src/main/java/com/autoresponder/pro/GuidedAssistant.kt"
s=p.read_text(encoding="utf-8")
old='''else "📌 *Para continuar:*\\n1️⃣ Indica plataforma y duración.\\n"+
                "2️⃣ Confirma cuál plan te interesa.\\n3️⃣ Solicita el medio de pago que prefieras.\\n\\n"+
                "🔐 La disponibilidad, el comprobante y la entrega se verifican antes de activar el servicio."'''
new='''else "Dime qué plan y duración prefieres, y te paso los medios de pago. 😊\\n"+
                "Yo verifico disponibilidad y pago antes de entregarlo."'''
assert s.count(old)==1
s=s.replace(old,new,1)
old='''else "📝 *Para preparar tu solicitud:*\\n1️⃣ Dinos los productos y cantidades.\\n"+
                "2️⃣ Indica adiciones o cambios.\\n3️⃣ Confirma si es para recoger o a domicilio.\\n\\n"+
                "📍 Para domicilio, comparte la dirección directamente en WhatsApp.\\n"+
                "✅ El pedido y el valor final se confirman cuando lo revisemos."'''
new='''else "Dime las cantidades, las adiciones y si es a domicilio o para recoger. 🍔\\n"+
                "Yo reviso el pedido y te confirmo el valor final."'''
assert s.count(old)==1
s=s.replace(old,new,1)
p.write_text(s,encoding="utf-8")
p=root/"web/app.js"
s=p.read_text(encoding="utf-8")
old='''      "📌 *Para continuar:*\\n1️⃣ Indica la plataforma y duración.\\n2️⃣ Confirma el plan que te interesa.\\n3️⃣ Solicita el medio de pago de tu preferencia.\\n\\n"+
      "🔐 La disponibilidad, el pago y la entrega se verifican antes de activar el servicio.":'''
new='''      "Dime qué plan y duración prefieres, y te paso los medios de pago. 😊\\n"+
      "Yo verifico disponibilidad y pago antes de entregarlo.":'''
assert s.count(old)==1
s=s.replace(old,new,1)
old='''      "📝 *Para preparar tu solicitud:*\\n1️⃣ Dinos los productos y cantidades.\\n2️⃣ Indica adiciones o cambios.\\n3️⃣ Confirma si es para recoger o a domicilio.\\n\\n"+
      "📍 Para domicilio comparte la dirección por WhatsApp.\\n✅ El pedido y valor final se confirman al revisarlo.";'''
new='''      "Dime las cantidades, las adiciones y si es a domicilio o para recoger. 🍔\\n"+
      "Yo reviso el pedido y te confirmo el valor final.";'''
assert s.count(old)==1
s=s.replace(old,new,1)
p.write_text(s,encoding="utf-8")
(root/"android/app/src/main/assets/app.js").write_text(s,encoding="utf-8")
print("Short first-person default sales/support/food-hours messages and guided sales/order texts; only migrate unchanged factory text")
