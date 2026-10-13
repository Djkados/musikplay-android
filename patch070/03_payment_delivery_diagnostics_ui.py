from pathlib import Path
root=Path("source/autoresponder-pro")
p=root/"web/app.js"
s=p.read_text(encoding="utf-8")
def edit(a,b,label):
 global s
 assert s.count(a)==1,(label,s.count(a))
 s=s.replace(a,b,1)

edit("i.autoStatus==='no_quick_reply'?' · WhatsApp no ofreció respuesta directa':''",
'''i.autoStatus==='no_quick_reply'?(i.manualPaymentReply?
       ' · ⚠️ Banco reconocido, pero WhatsApp no permitió responder automáticamente':
       ' · WhatsApp no ofreció respuesta directa'):''',
"clear bank delivery error")

edit('''${sellerBadge(i)}${humanBadge(i)}<div class="row">''',
'''${i.autoStatus==='no_quick_reply'&&i.manualPaymentReply&&i.preparedText?
      '<div class="notice">⚠️ Reconocí el medio de pago, pero WhatsApp no ofreció la respuesta directa. Los datos NO se enviaron automáticamente. Verifica el destinatario para compartirlos manualmente.</div>'+
      '<button class="btn primary mini" data-send-pending-bank="'+safe(i.id)+'">💳 Enviar datos manualmente</button>':''}
      ${sellerBadge(i)}${humanBadge(i)}<div class="row">''',
"safe manual payment followup")

needle="    if(button.dataset.useInbox){"
handler='''    if(button.dataset.sendPendingBank){
      const item=state.inbox.find(x=>x.id===button.dataset.sendPendingBank);
      if(!item || item.autoStatus!=="no_quick_reply" ||
         !item.manualPaymentReply || !item.preparedText)
        return notify("No hay un mensaje de pago pendiente.");
      if(!confirm("WhatsApp no envió estos datos automáticamente.\\n\\n"+
          "¿Deseas compartirlos MANUALMENTE?\\n"+
          "Comprueba que el destinatario sea "+item.contact+" antes de enviar."))
        return;
      shareText(item.preparedText,item.channel);
      return;
    }
'''
assert s.count(needle)==1
s=s.replace(needle,handler+needle,1)

edit('''<div class="notice">Prueba Netflix, hamburguesa, horario o soporte un domingo. El contexto de 24 horas se aplica a las notificaciones Android; el simulador evalúa cada mensaje de forma independiente.</div>''',
'''<div class="notice">Prueba «Bancolombia», «2», «Nequi», Netflix o hamburguesas. El nombre del banco debe funcionar sin menú previo. La entrega real depende de que WhatsApp habilite la respuesta directa; el simulador no envía mensajes.</div>''',
"simulator bank instructions")

p.write_text(s,encoding="utf-8")
(root/"android/app/src/main/assets/app.js").write_text(s,encoding="utf-8")
print("Inbox explains when bank is recognized but WhatsApp cannot reply and offers a consented manual-share button.")
