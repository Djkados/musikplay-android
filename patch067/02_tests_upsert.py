from pathlib import Path
root=Path("source/autoresponder-pro")
p=root/"web/app.js"
s=p.read_text(encoding="utf-8")
def edit(old,new,reason):
 global s
 assert s.count(old)==1,(reason,s.count(old),old[:100])
 s=s.replace(old,new,1)

# Saving an existing vendor must also update their WhatsApp scope, not only
# the name, phone and business. Without this, selecting Ambos can look saved
# but silently retain the previous (incorrect) WhatsApp.
edit('''        existing.contact=name||phone;existing.phone=phone;existing.assistant=assistant;''',
     '''        existing.contact=name||phone;existing.phone=phone;
        existing.assistant=assistant;existing.channel=channel;''',
     "existing vendor scope must be updated")

# Other contact types (blocked, allowlist, etc.) still default to normal.
# "Both" is selected automatically only when sellerContacts is chosen.
edit('''          <option value="both">Ambos WhatsApp / No sé</option>
          <option value="normal">WhatsApp normal</option><option value="business">WhatsApp Business</option></select>''',
     '''          <option value="normal">WhatsApp normal</option><option value="business">WhatsApp Business</option>
          <option value="both">Ambos WhatsApp / No sé</option></select>''',
     "do not default other contact types to both")
edit('''      if(row)row.hidden=!['exceptions','sellerContacts'].includes(e.target.value);''',
     '''      if(row)row.hidden=!['exceptions','sellerContacts'].includes(e.target.value);
      const selector=$('#ctChannel');
      if(selector && e.target.value==="sellerContacts")selector.value="both";
      else if(selector && selector.value==="both")selector.value="normal";''',
     "auto-select both only for vendors")
p.write_text(s,encoding="utf-8")
(root/"android/app/src/main/assets/app.js").write_text(s,encoding="utf-8")

p=root/"android/app/src/test/java/com/autoresponder/pro/NativeAutoReplyEngineTest.kt"
s=p.read_text(encoding="utf-8")
assert s.rstrip().endswith("}")
s=s.rstrip()[:-1]+'''
    @Test fun sellerRegisteredOnBothWhatsappIsNeverSentPublicCatalogOnEitherApp() {
        val c=config()
        c.getJSONObject("settings").put("requireAllowlist",false)
            .getJSONObject("autoReplies").put("normal",true)
        c.put("sellerContacts",JSONArray().put(JSONObject()
            .put("id","seller_both_test")
            .put("channel","both")
            .put("contact","Vendedor Dos WhatsApp")
            .put("phone","3001112222")
            .put("assistant","movieplay")))
        val today=clock("2026-10-12","19:00")
        assertEquals("movieplay",NativeAutoReplyEngine.sellerBusiness(
            c,"normal","Vendedor Dos WhatsApp"))
        assertEquals("movieplay",NativeAutoReplyEngine.sellerBusiness(
            c,"business","+57 300 111 2222"))
        for(ch in listOf("normal","business")) {
            val noCatalog=NativeAutoReplyEngine.decide(c,ch,"Vendedor Dos WhatsApp",
                "precios netflix 30 dias",today)
            assertNull(noCatalog.text)
            assertEquals("seller_human",noCatalog.routeSource)
            val renewal=NativeAutoReplyEngine.decide(c,ch,"Vendedor Dos WhatsApp",
                "renueva netflix",today)
            assertEquals(RenewalReplies.MESSAGE,renewal.text)
            val thanks=NativeAutoReplyEngine.decide(c,ch,"Vendedor Dos WhatsApp",
                "tenkiu",today)
            assertEquals(CourtesyReplies.message,thanks.text)
        }
        assertNull(NativeAutoReplyEngine.sellerBusiness(c,"normal","Otro contacto"))
    }

    @Test fun legacyVendorOnlyBusinessRemainsBusinessOnlyUnlessChanged() {
        val c=config()
        c.put("sellerContacts",JSONArray().put(JSONObject()
            .put("channel","business").put("contact","Solo Business")
            .put("assistant","movieplay")))
        assertEquals("movieplay",NativeAutoReplyEngine.sellerBusiness(c,"business","Solo Business"))
        assertNull(NativeAutoReplyEngine.sellerBusiness(c,"normal","Solo Business"))
    }
}
'''
p.write_text(s,encoding="utf-8")

# JS simulator must use the same "both" semantics as Android.
p=root/"tests/smoke.test.cjs"
s=p.read_text(encoding="utf-8")
s+='''

const scopedBoth=JSON.parse(JSON.stringify(friendlyConfig));
scopedBoth.sellerContacts=[
  {id:'vendor-both-067',contact:'Revendedor Ambos',
    phone:'3001112222',channel:'both',assistant:'movieplay'}
];
const answerBoth=create(scopedBoth).api;
for(const ch of ['normal','business']){
 assert.match(answerBoth.respond(ch,'Revendedor Ambos','precios de Netflix').reason,/Vendedor/);
 assert.equal(answerBoth.respond(ch,'Revendedor Ambos','Gracias').reply,gratitude);
 assert.match(answerBoth.respond(ch,'Revendedor Ambos','Nequi').reply,/3045214937/);
}
assert.equal(answerBoth.getConfig().sellerContacts[0].channel,'both');
console.log('OK — marcar vendedor en Ambos WhatsApp silencia catálogos en los dos canales.');
'''
p.write_text(s,encoding="utf-8")
print("Both-channel Kotlin engine test, legacy-scoped test, JS simulator and change-channel fix added")
