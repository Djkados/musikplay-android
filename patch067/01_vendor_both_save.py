from pathlib import Path
root=Path("source/autoresponder-pro")

p=root/"android/app/src/main/java/com/autoresponder/pro/NativeAutoReplyEngine.kt"
s=p.read_text(encoding="utf-8")
old='''            if(seller.optString("channel")==channel && matchContact(seller,contact)){'''
new='''            // "both" is the default when the owner does not know which
            // WhatsApp app the reseller uses. Match independently on either.
            val sellerChannel=seller.optString("channel")
            if(sellerChannel in setOf(channel,"both") && matchContact(seller,contact)){'''
assert s.count(old)==1,(old,s.count(old))
p.write_text(s.replace(old,new,1),encoding="utf-8")

p=root/"web/app.js"
s=p.read_text(encoding="utf-8")
def change(old,new,desc):
 global s
 assert s.count(old)==1,(desc,s.count(old),old[:105])
 s=s.replace(old,new,1)

change("  const channelNames = {normal:'WhatsApp normal',business:'WhatsApp Business'};",
       "  const channelNames = {normal:'WhatsApp normal',business:'WhatsApp Business',both:'Ambos WhatsApp'};",
       "channel label")
change("    return (state.sellerContacts||[]).find(x=>x.channel===channel&&sameContact(x,contact))||null;",
       "    return (state.sellerContacts||[]).find(x=>(x.channel===channel||x.channel==='both')&&sameContact(x,contact))||null;",
       "seller both-channel matching")
change("""      '<div class="form-control"><label>WhatsApp donde te escribe</label>'+
      '<select id="vendorChannel" class="field"><option value="business">WhatsApp Business</option>'+
      '<option value="normal">WhatsApp normal</option></select></div>'+""",
"""      '<div class="form-control"><label>¿Dónde aplicar el modo vendedor?</label>'+
      '<select id="vendorChannel" class="field">'+
      '<option value="both" selected>✅ Ambos WhatsApp · No sé cuál usa</option>'+
      '<option value="normal">Solo WhatsApp normal</option>'+
      '<option value="business">Solo WhatsApp Business</option></select>'+
      '<p class="tiny muted">No tienes que saber cuál usa. Con Ambos queda protegido '+
      'en los dos. Si no estás seguro del nombre, guarda también el número.</p></div>'+""",
"vendor channel selection")
change("""      '<button class="btn primary" data-action="save-vendor">Guardar vendedor</button>'+""",
"""      '<button class="btn primary" data-action="save-vendor" type="button">✓ Guardar vendedor</button>'+
      '<div id="vendorSaveFeedback" class="notice" role="status" aria-live="polite">'+
      (runtime.vendorFeedback||'Escribe el nombre, el número o ambos y pulsa Guardar.')+
      '</div>'+""",
"persistent feedback")
change("""      '<div class="notice">Si WhatsApp muestra el nombre guardado en una notificación, '+
      'escríbelo también para identificar correctamente ese chat. '+
      'El mismo contacto puede estar registrado en ambos WhatsApp.</div></div>'+""",
"""      '<div class="notice">Consejo: usa el nombre que aparece en WhatsApp o '+
      'el número del vendedor. No hay que vincular sus cuentas ni instalar WhatsApp Business.</div></div>'+""",
"vendor help")
change("""      '<p class="small muted">'+safe(channelNames[x.channel])+
      ' · Solo agradecimientos, renovación y medios de pago</p>'+""",
"""      '<p class="small muted">'+safe(channelNames[x.channel]||"Ambos WhatsApp")+
      ' · Solo agradecimientos, renovación y medios de pago</p>'+""",
"persisted vendor text")

# Keep the dedicated editor name field, but change its placeholder to a
# literal matching hint (people using phone contacts often see an alias).
change("""      '<input id="vendorName" class="field" autocomplete="off" placeholder="Ej. Carlos, revendedor"></div>'+""",
"""      '<input id="vendorName" class="field" autocomplete="off" maxlength="140" '+
      'placeholder="Ej. Carlos Pérez (como lo ves en WhatsApp)"></div>'+""",
"vendor name input")
change("""      '<input id="vendorPhone" class="field" type="tel" inputmode="tel" placeholder="Ej. 300 123 4567"></div>'+""",
"""      '<input id="vendorPhone" class="field" type="tel" inputmode="tel" '+
      'placeholder="Ej. 300 123 4567"></div>'+""",
"phone field")
change("""      '<div class="form-control"><label>WhatsApp donde te escribe</label>'""",
"""      '<div class="form-control"><label>WhatsApp donde te escribe</label>'""",
"noop") if False else None

# Newly marked vendors protect both WhatsApps by default, even though the
# message used to create them was received on only one channel.
change("""      state.sellerContacts.push({id:token(),channel:msg.channel,
        contact:msg.contact,phone:"",assistant:"movieplay"});""",
"""      const known=(state.sellerContacts||[]).find(x=>
        sameContact(x,msg.contact) &&
        (x.channel==="both" || x.channel===msg.channel));
      if(known){known.channel="both";known.assistant="movieplay";}
      else state.sellerContacts.push({id:token(),channel:"both",
        contact:msg.contact,phone:"",assistant:"movieplay"});""",
"one-tap both channels")

# Default "both" applies even when an older version opened a vendor form
# before update; UI exposes the specific selectors only when the user chooses.
change("""      if(!["normal","business"].includes(channel) ||
         !["movieplay","tresm"].includes(assistant))
        return notify("Selecciona WhatsApp y el negocio.");""",
"""      if(!["normal","business","both"].includes(channel) ||
         !["movieplay","tresm"].includes(assistant)){
        runtime.vendorFeedback="Revisa el negocio. La opción Ambos WhatsApp es válida.";
        render();return notify("Revisa el negocio y vuelve a guardar.");
      }""",
"allow both")
change("""      const existing=state.sellerContacts.find(x=>x.channel===channel &&
         (sameContact(x,name||phone) || (phone && sameContact(x,phone))));""",
"""      const existing=state.sellerContacts.find(x=>
        (x.channel===channel||x.channel==="both"||channel==="both") &&
        (sameContact(x,name||phone) || (phone && sameContact(x,phone))));""",
"upsert seller across channels")
change("""      save();render();
      notify("Vendedor guardado: sin catálogos ni saludos automáticos.");
      return;""",
"""      // A transient inline confirmation remains visible even if the toast
      // disappears behind the Android keyboard. Verify disk persistence,
      // so we never claim saved when localStorage rejected the write.
      try {
        save();
        const saved=JSON.parse(localStorage.getItem(KEY)||"{}");
        if(!Array.isArray(saved.sellerContacts) ||
          !saved.sellerContacts.some(x=>(x.channel===channel||x.channel==="both") &&
            (sameContact(x,name||phone)||(phone&&sameContact(x,phone))))){
          throw Error("No se pudo comprobar el guardado local");
        }
        runtime.vendorFeedback="✅ Vendedor guardado correctamente. Protegido en "+
          (channel==="both"?"ambos WhatsApp":channelNames[channel])+
          ". Solo responderá a agradecimientos, renovaciones y pagos.";
        render();
        document.querySelector("#vendorSaveFeedback")?.scrollIntoView?.({
          block:"nearest",behavior:"smooth"
        });
        notify("✓ Vendedor guardado correctamente.");
      }catch(error){
        runtime.vendorFeedback="No se pudo guardar. Libera espacio del teléfono "+
          "o revisa el almacenamiento de la aplicación y vuelve a intentarlo.";
        render();notify("Error guardando: "+String(error?.message||error));
      }
      return;""",
"persistent saving and verification")

# Clear field errors with a visible form-level message instead of an
# ephemeral toast. Do not force the user to fill both fields.
change("""      if(rawPhone&&!phone)return notify("Número inválido. Revisa los dígitos.");
      if(!name&&!phone)return notify("Escribe el nombre de WhatsApp o un número.");
      if(name.length>140)return notify("El nombre supera el límite permitido.");""",
"""      const invalid=(msg,field)=>{
        runtime.vendorFeedback="⚠️ "+msg;
        const notice=$('#vendorSaveFeedback');
        if(notice)notice.textContent=runtime.vendorFeedback;
        if(field)field.focus();
        notify(msg);return;
      };
      if(rawPhone&&!phone)
        return invalid("Número inválido. Escribe entre 7 y 15 dígitos, o déjalo vacío y usa el nombre.",$('#vendorPhone'));
      if(!name&&!phone)
        return invalid("Escribe al menos el nombre de WhatsApp o el teléfono.",$('#vendorName'));
      if(name.length>140)
        return invalid("El nombre es demasiado largo.",$('#vendorName'));""",
"durable validation errors")

# Older contact-management screen now supports both WhatsApps when the
# owner chooses the vendor role, without touching other exception categories.
change("""        <div class="form-control"><label for="ctChannel">WhatsApp donde escribe</label><select id="ctChannel"><option value="normal">WhatsApp normal</option><option value="business">WhatsApp Business</option></select></div>""",
"""        <div class="form-control"><label for="ctChannel">WhatsApp donde escribe</label><select id="ctChannel">
          <option value="both">Ambos WhatsApp / No sé</option>
          <option value="normal">WhatsApp normal</option><option value="business">WhatsApp Business</option></select>
        <p class="tiny muted">Ambos es recomendable solo para vendedores; las demás excepciones siguen siendo por canal.</p></div>""",
"contact dropdown")
change("""      const channel=$('#ctChannel').value,type=$('#ctType').value,assistant=$('#ctAssistant').value;
      const list=state[type];if(!Array.isArray(list))return;""",
"""      const channel=$('#ctChannel').value,type=$('#ctType').value,assistant=$('#ctAssistant').value;
      if(channel==="both" && type!=="sellerContacts"){
        return notify("Ambos WhatsApp solo se permite para vendedores. Elige uno para otras reglas.");
      }
      const list=state[type];if(!Array.isArray(list))return;""",
"keep other roles scoped")
change("""      const exists=list.find(x=>x.channel===channel&&(sameContact(x,contact)||(phone&&sameContact(x,phone))));""",
"""      const exists=list.find(x=>(x.channel===channel||
        (type==="sellerContacts"&&(channel==="both"||x.channel==="both"))) &&
        (sameContact(x,contact)||(phone&&sameContact(x,phone))));""",
"legacy contact upsert")

p.write_text(s,encoding="utf-8")
(root/"android/app/src/main/assets/app.js").write_text(s,encoding="utf-8")
print("Vendor save provides permanent inline success/errors; defaults to both WhatsApps; all channel paths and Android engine honor 'both'.")
