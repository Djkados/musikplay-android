from pathlib import Path
import json
root=Path("source/autoresponder-pro")
old=[
"¡Hola! 🎬 Gracias por escribir a MoviePlay. Nuestro horario de VENTAS es todos los días de 9:00 a. m. a 10:00 p. m. Te atenderemos en el próximo horario disponible.",
"¡Hola! 🛟 El soporte de MoviePlay atiende de lunes a sábado de 9:00 a. m. a 10:00 p. m.; domingos y festivos de 9:00 a. m. a 5:00 p. m. Tu solicitud quedará pendiente para el siguiente horario de atención.",
"¡Hola! 🍔 Gracias por escribir a Las Tres M. Atendemos sábados y domingos de 6:00 p. m. a 10:30 p. m. en el barrio Ciudadela, La Ceja. Puedes consultar el menú en https://lastresm.netlify.app. Te responderemos en nuestro próximo horario de servicio."
]
new=[
"""🎬 *MOVIEPLAY*

¡Hola! 👋 Gracias por escribirnos.

🕘 *HORARIO DE VENTAS*
📅 Todos los días
⏰ 9:00 a. m. a 10:00 p. m.

🌙 En este momento estamos fuera de nuestro horario de atención.

✅ Hemos recibido tu mensaje y te responderemos en nuestro próximo horario de ventas.

💚 *¡Gracias por preferir MoviePlay!*""",
"""🛟 *SOPORTE MOVIEPLAY*

¡Hola! 👋 Gracias por contactarnos.

🕘 *HORARIO DE SOPORTE*
📅 Lunes a sábado: 9:00 a. m. a 10:00 p. m.
📅 Domingos y festivos: 9:00 a. m. a 5:00 p. m.

🌙 Actualmente estamos fuera del horario de soporte.

✅ Tu solicitud será atendida en nuestro próximo horario de atención.

💚 *¡Gracias por tu paciencia!*""",
"""🍔 *LAS TRES M*

¡Hola! 👋 Gracias por escribirnos.

🕕 *HORARIO DE ATENCIÓN*
📅 Sábados y domingos
⏰ 6:00 p. m. a 10:30 p. m.

📍 *Ubicación:* Barrio Ciudadela, La Ceja.

📲 *Consulta nuestro menú:*
https://lastresm.netlify.app

🌙 En este momento estamos fuera de servicio. Te responderemos en nuestro próximo horario de atención.

❤️ *¡Gracias por tu comprensión!*"""
]
units=["movieplay:sales","movieplay:support","tresm:orders"]
p=root/"web/schedule-engine.js"
js=p.read_text(encoding="utf-8")
for original,replacement in zip(old,new):
    text="away:"+json.dumps(original,ensure_ascii=False).replace('"',"'")
    assert js.count(text)==1,(text[:50],js.count(text))
    js=js.replace(text,"away:"+json.dumps(replacement,ensure_ascii=False),1)
p.write_text(js,encoding="utf-8")
(root/"android/app/src/main/assets/schedule-engine.js").write_text(js,encoding="utf-8")

p=root/"web/app.js"
s=p.read_text(encoding="utf-8")
anchor="  function migrateScheduleConfig(){"
assert s.count(anchor)==1
s=s.replace(anchor,"  const LEGACY_AWAY="+json.dumps(dict(zip(units,old)),ensure_ascii=False)+";\n"+anchor,1)
needle="""      state.schedules[group][unit].days ||= JSON.parse(JSON.stringify(fresh[group][unit].days));
      for(let d=0;d<7;d++)state.schedules[group][unit].days[d] ||= JSON.parse(JSON.stringify(fresh[group][unit].days[d]));"""
assert s.count(needle)==1
s=s.replace(needle,needle+"""
      // Upgrade only untouched factory copy; preserve customized messages.
      if(state.schedules[group][unit].away===LEGACY_AWAY[group+':'+unit])
        state.schedules[group][unit].away=fresh[group][unit].away;""",1)
s=s.replace("  migrateScheduleConfig();\n  state.settings ||=",
            "  migrateScheduleConfig();\n  localStorage.setItem(KEY,JSON.stringify(state));\n  state.settings ||=",1)
s=s.replace('rows="4">', 'rows="9">')
s=s.replace("AutoResponder Pro v0.5.8", "AutoResponder Pro v0.5.9",1)
p.write_text(s,encoding="utf-8")
(root/"android/app/src/main/assets/app.js").write_text(s,encoding="utf-8")
t=root/"tests/schedules.test.cjs"
s=t.read_text(encoding="utf-8")
anchor="// End-to-end with rules + app safety gate + hours at specified Bogota time."
assert anchor in s
tests=r"""const formatted=engine.defaultSchedules();
for(const unit of [formatted.movieplay.sales,formatted.movieplay.support,formatted.tresm.orders]){
  assert.match(unit.away,/\n\n/);
  assert.match(unit.away,/\*[^*]+\*/);
}
assert.match(formatted.movieplay.sales.away,/9:00 a\. m\./);
assert.match(formatted.tresm.orders.away,/https:\/\/lastresm\.netlify\.app/);

"""
s=s.replace(anchor,tests+anchor,1)
t.write_text(s,encoding="utf-8")
print("WhatsApp-friendly multiline schedules applied")
