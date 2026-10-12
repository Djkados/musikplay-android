from pathlib import Path
root=Path("source/autoresponder-pro")
native=root/"android/app/src/test/java/com/autoresponder/pro"
p=native/"NativeAutoReplyEngineTest.kt"
s=p.read_text(encoding="utf-8")
old='''assertTrue(ask.text!!.contains("MoviePlay / Las Tres M"))'''
new='''assertTrue(ask.text!!.contains("MoviePlay") && ask.text!!.contains("Las Tres M"))'''
assert s.count(old)==1
s=s.replace(old,new,1)
p.write_text(s,encoding="utf-8")

p=native/"LocalCatalogTest.kt"
s=p.read_text(encoding="utf-8")
assert s.count('¿Cuál opción disponible te interesa?')==2
s=s.replace('¿Cuál opción disponible te interesa?','¿Cuál te interesa?')
assert s.rstrip().endswith("}")
s=s.rstrip()[:-1]+'''
    @Test fun shortHumanRepliesKeepPricesDurationsAndUnavailableLabels() {
        val c=catalog()
        val reply=LocalCatalog.reply(c,"movieplay","Netflix 30 días",
            LocalDate.parse("2026-10-15"))!!
        assertTrue(reply.text.startsWith("¡Claro!"))
        assertTrue(reply.text.contains("$11.000"))
        assertTrue(reply.text.contains("30 días"))
        assertFalse(reply.text.contains("📺 *Planes y precios disponibles*"))
        val missing=LocalCatalog.reply(c,"tresm","hamburguesa",
            LocalDate.parse("2026-10-15"))!!
        assertTrue(missing.text.contains("Consultar en el menú"))
        c.getJSONArray("catalog").getJSONObject(0).put("active",false)
        val disabled=LocalCatalog.reply(c,"movieplay","Netflix 26 días",
            LocalDate.parse("2026-10-15"))!!
        assertTrue(disabled.text.contains("NO DISPONIBLE POR EL MOMENTO"))
    }
}
'''
p.write_text(s.replace('"$11.000"','"\\$11.000"'),encoding="utf-8")

p=native/"GuidedAssistantTest.kt"
s=p.read_text(encoding="utf-8")
assert s.count('''response.text.contains("se verifican")''')==1
assert s.count('''response.text.contains("se confirman")''')==1
s=s.replace('''response.text.contains("se verifican")''','''response.text.contains("Yo verifico")''')
s=s.replace('''response.text.contains("se confirman")''','''response.text.contains("te confirmo")''')
p.write_text(s,encoding="utf-8")

p=native/"ConversationFlowTest.kt"
s=p.read_text(encoding="utf-8")
assert s.rstrip().endswith("}")
s=s.rstrip()[:-1]+'''
    @Test fun paymentMenuAfterSelectedPlanRetainsShortConversationalTone() {
        val c=config()
        val result=ConversationFlow.followUp(c,"movieplay","sí",
            "nf30","payment_offer",0,today)
        assertNotNull(result)
        assertEquals("payment_menu",result!!.stage)
        assertTrue(result.text.contains("MEDIOS DE PAGO"))
    }
}
'''
p.write_text(s,encoding="utf-8")

p=root/"tests/smoke.test.cjs"
s=p.read_text(encoding="utf-8")
s+='''

const friendlyConfig=JSON.parse(JSON.stringify(test.getConfig()));
friendlyConfig.blocked=[];
friendlyConfig.exceptions=[];
friendlyConfig.sellerContacts=[{
  id:'seller-065',channel:'business',contact:'Vendedor de prueba',assistant:'movieplay'
}];
friendlyConfig.settings.requireAllowlist=false;
const friendly=create(friendlyConfig).api;
assert.match(friendly.respond('business','Vendedor de prueba','hola').reason,/Vendedor/);
assert.match(friendly.respond('business','Vendedor de prueba','Netflix 30 días').reason,/Vendedor/);
assert.equal(friendly.respond('business','Vendedor de prueba','Tenkiu').reply,gratitude);
assert.match(friendly.respond('business','Vendedor de prueba','¿dónde te transfiero?').reply,/Claro/);
assert.match(friendly.respond('business','Vendedor de prueba','¿dónde te transfiero?').reply,/MEDIOS DE PAGO/);
assert.match(friendly.respond('business','Vendedor de prueba','Bancolombia').reply,/Cuenta de ahorros/);
assert.match(friendly.respond('business','Cliente de prueba','Netflix').reply,/¡Claro!/);
assert.match(friendly.respond('business','Cliente de prueba','¿dónde te transfiero?').reply,/Claro/);
assert.notEqual(friendly.respond('business','Cliente de prueba','Gracias').reply,
  friendly.respond('business','Cliente de prueba','Netflix').reply);
console.log('OK — replies concise and first-person for all chats; seller only payment and thanks.');
'''
p.write_text(s,encoding="utf-8")
print("Regression tests adapted for concise first-person language while preserving safety, catalog prices and exact thank-you")
