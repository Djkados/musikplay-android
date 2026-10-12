from pathlib import Path
root=Path("source/autoresponder-pro")
p=root/"web/app.js"
s=p.read_text(encoding="utf-8")
def rep(a,b):
 global s
 assert s.count(a)==1,(a[:100],s.count(a))
 s=s.replace(a,b,1)
anchor="  function renderInbox(){return "
helper='''  function humanPauseInfo(channel,contact){
    if(native && window.AndroidBridge.getConversationPause){
      try {
        const r=JSON.parse(window.AndroidBridge.getConversationPause(channel,contact));
        if(r.active)return r;
      }catch(_){}
    }
    const existing=state.paused.find(x=>x.channel===channel &&
      sameContact(x,contact) && Number(x.until)>Date.now());
    return existing?{active:true,until:Number(existing.until),
      indefinite:Number(existing.until)>1e14}:{active:false};
  }
  function humanBadge(entry){
    const info=humanPauseInfo(entry.channel,entry.contact);
    if(!info.active)return "";
    return '<div class="notice">✋ Atención humana activa · '+
      (info.indefinite?'Hasta reactivar':'Hasta '+new Date(info.until).toLocaleString("es-CO"))+
      '. El asistente permanecerá en silencio en este chat.</div>';
  }
'''
assert s.count(anchor)==1
s=s.replace(anchor,helper+anchor,1)
varname='$'+'{safe(i.id)}'
old='<button class="btn mini soft" data-pause-inbox="'+varname+'">Pausar 1 h</button>'
new='<select aria-label="Tiempo de pausa" data-human-duration="'+varname+'">'+\
    '<option value="30">30 min</option><option value="60" selected>1 hora</option>'+\
    '<option value="120">2 horas</option><option value="-1">Hasta reactivar</option></select>'+\
    '<button class="btn mini soft" data-pause-inbox="'+varname+'">✋ Atender personalmente</button>'+\
    '<button class="btn mini soft" data-resume-inbox="'+varname+'">▶ Reanudar</button>'+\
    '<button class="btn mini soft" data-clear-context="'+varname+'">Reiniciar memoria</button>'
rep(old,new)
old='<div class="row">'+ '$'+'{r.image?'
new= '$'+'{humanBadge(i)}' + old
rep(old,new)
old='''    if(button.dataset.pauseInbox){
      const msg=state.inbox.find(i=>i.id===button.dataset.pauseInbox);
      if(msg){
        const existing=state.paused.find(x=>x.channel===msg.channel&&sameContact(x,msg.contact));
        if(existing)existing.until=Date.now()+60*60*1000;
        else state.paused.push({id:token(),channel:msg.channel,contact:msg.contact,until:Date.now()+60*60*1000});
        save();render();notify('Pausa manual de 1 hora para '+msg.contact);
      }return;
    }'''
new='''    if(button.dataset.pauseInbox){
      const msg=state.inbox.find(i=>i.id===button.dataset.pauseInbox);
      if(!msg)return;
      const control=Array.from(document.querySelectorAll("[data-human-duration]"))
        .find(x=>x.dataset.humanDuration===msg.id);
      const minutes=Number(control?.value||60);
      if(![30,60,120,-1].includes(minutes))return notify("Tiempo de pausa inválido.");
      if(native && window.AndroidBridge.setConversationPause &&
          !window.AndroidBridge.setConversationPause(msg.channel,msg.contact,minutes))
        return notify("No se pudo pausar este chat en Android.");
      const until=minutes===-1?Number.MAX_SAFE_INTEGER:Date.now()+minutes*60_000;
      const previous=state.paused.find(x=>x.channel===msg.channel&&sameContact(x,msg.contact));
      if(previous)previous.until=until;
      else state.paused.push({id:token(),channel:msg.channel,contact:msg.contact,until});
      save();render();notify("Atención humana activada en este chat.");return;
    }
    if(button.dataset.resumeInbox){
      const msg=state.inbox.find(i=>i.id===button.dataset.resumeInbox);
      if(!msg)return;
      if(native && window.AndroidBridge.setConversationPause &&
          !window.AndroidBridge.setConversationPause(msg.channel,msg.contact,0))
        return notify("Android no pudo reanudar la atención automática.");
      state.paused=state.paused.filter(x=>!(x.channel===msg.channel&&sameContact(x,msg.contact)));
      save();render();notify("Asistente reactivado solo en este chat.");return;
    }
    if(button.dataset.clearContext){
      const msg=state.inbox.find(i=>i.id===button.dataset.clearContext);
      if(!msg)return;
      if(!confirm("¿Borrar la selección de negocio y el progreso de este chat?"))return;
      if(native && window.AndroidBridge.clearConversationMemory &&
          !window.AndroidBridge.clearConversationMemory(msg.channel,msg.contact))
        return notify("Android no pudo reiniciar esta conversación.");
      render();notify("Memoria de este chat reiniciada; se conservan las pausas.");return;
    }'''
rep(old,new)
p.write_text(s,encoding="utf-8")
(root/"android/app/src/main/assets/app.js").write_text(s,encoding="utf-8")
print("Added per-chat pause/select/resume/reset controls in inbox, including native pause state")
