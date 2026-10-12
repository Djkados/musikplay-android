from pathlib import Path
root=Path("source/autoresponder-pro")
p=root/"android/app/src/main/java/com/autoresponder/pro/MainActivity.kt"
s=p.read_text(encoding="utf-8")
old='''            if(minutes !in setOf(0,30,60,120,-1))return false'''
new='''            if(minutes !in setOf(0,30,60,120,180,-1))return false'''
assert s.count(old)==1
p.write_text(s.replace(old,new,1),encoding="utf-8")
p=root/"web/app.js"
s=p.read_text(encoding="utf-8")
a='''<p class="small muted">Control de duplicados y pausa breve entre consultas; después de elegir 1 o 2 se atiende la respuesta inmediatamente. Requiere respuesta directa de WhatsApp.</p>'''
b='''<p class="small muted">Un vendedor marcado en Contactos solo recibe agradecimientos y medios de pago. Tu respuesta manual pausa las demás respuestas 2 o 3 horas si Android puede detectarla. Requiere respuesta directa de WhatsApp.</p>'''
assert s.count(a)==1
s=s.replace(a,b,1)
a='''Cuando detecta atención humana intenta pausar la conversación 1 hora.'''
b='''Cuando Android detecta una respuesta humana, aplica una pausa de 2 o 3 horas según tu configuración. La detección no está garantizada por WhatsApp; marca a los vendedores para que nunca reciban listas de precios o saludos del bot.'''
assert s.count(a)==1
s=s.replace(a,b,1)
p.write_text(s,encoding="utf-8")
(root/"android/app/src/main/assets/app.js").write_text(s,encoding="utf-8")
print("Human pause UI supports 3 hours and does not overpromise detection from WhatsApp notifications")
