from pathlib import Path
root=Path("source/autoresponder-pro")
p=root/"web/app.js";s=p.read_text(encoding="utf-8")
def insert(anchor,extra,why):
 global s
 assert s.count(anchor)==1,(why,s.count(anchor))
 s=s.replace(anchor,extra+anchor,1)
insert("    if(e.target?.id==='ctType'){",
'''    if(e.target?.dataset.vendorBusiness){
      const person=state.sellerContacts.find(x=>x.id===e.target.dataset.vendorBusiness);
      if(!person || !["movieplay","tresm"].includes(e.target.value))return;
      person.assistant=e.target.value;save();render();
      notify("Negocio del vendedor actualizado.");return;
    }
''',"inline seller business selector")
insert("    if(a==='add-contact'){",
'''    if(a==='save-vendor'){
      const name=($('#vendorName')?.value||'').trim();
      const rawPhone=($('#vendorPhone')?.value||'').trim();
      const phone=phoneKey(rawPhone);
      if(rawPhone&&!phone)return notify("Número inválido. Revisa los dígitos.");
      if(!name&&!phone)return notify("Escribe el nombre de WhatsApp o un número.");
      if(name.length>140)return notify("El nombre supera el límite permitido.");
      const channel=$('#vendorChannel')?.value;
      const assistant=$('#vendorBusiness')?.value;
      if(!["normal","business"].includes(channel) ||
         !["movieplay","tresm"].includes(assistant))
        return notify("Selecciona WhatsApp y el negocio.");
      const existing=state.sellerContacts.find(x=>x.channel===channel &&
         (sameContact(x,name||phone) || (phone && sameContact(x,phone))));
      if(existing){
        existing.contact=name||phone;existing.phone=phone;existing.assistant=assistant;
      } else {
        state.sellerContacts.push({id:token(),channel,
          contact:name||phone,phone,assistant});
      }
      save();render();
      notify("Vendedor guardado: sin catálogos ni saludos automáticos.");
      return;
    }
    if(button.dataset.editVendor){
      const person=state.sellerContacts.find(x=>x.id===button.dataset.editVendor);
      if(!person)return;
      setRoute("vendedores");
      $('#vendorName').value=person.contact||"";
      $('#vendorPhone').value=person.phone||"";
      $('#vendorChannel').value=person.channel;
      $('#vendorBusiness').value=person.assistant;
      document.querySelector('#vendorEditor')?.scrollIntoView({block:"nearest"});
      return;
    }
''',"vendor form handlers")
p.write_text(s,encoding="utf-8")
(root/"android/app/src/main/assets/app.js").write_text(s,encoding="utf-8")
print("Dedicated vendor create/edit/delete and per-business switch controls wired")
