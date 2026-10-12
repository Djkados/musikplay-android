from pathlib import Path
root=Path("source/autoresponder-pro")
native=root/"android/app/src/test/java/com/autoresponder/pro"
(native/"RenewalRepliesTest.kt").write_text(r'''package com.autoresponder.pro

import org.junit.Assert.*
import org.junit.Test

class RenewalRepliesTest {
    @Test fun identifiesRealRequestsInNaturalWriting() {
        for(text in listOf("Renueva","RENUEVA!","renuévame","renuevame",
            "Renueva Netflix","Hola, renueva Netflix 30 días",
            "Quiero renovar","necesito renovar","Me puedes renovar",
            "¿Me renuevas?","Renovación","renovar","porfa renueva")) {
            assertTrue("Must recognize renewal request: $text",RenewalReplies.isRequest(text))
        }
    }
    @Test fun doesNotTreatQuestionsOrProofAsUnfulfilledRenewals() {
        for(text in listOf("Ya renové","ya me renovaron","no quiero renovar",
            "No renueves","Cuánto cuesta renovar","¿Cómo renuevo?",
            "¿Cuándo se renueva?","renovado","renovación confirmada",
            "Comprobante","Pago Pedro Páez","Nequi","gracias")) {
            assertFalse("Should not acknowledge as renewal: $text",
                RenewalReplies.isRequest(text))
        }
    }
    @Test fun exactFirstPersonCopyNeverClaimsCompletedRenewal() {
        assertEquals("Claro 😊, dame un momento y te confirmo la renovación.",
            RenewalReplies.MESSAGE)
        assertFalse(RenewalReplies.MESSAGE.contains("renovado"))
    }
}
''',encoding="utf-8")

p=native/"NativeAutoReplyEngineTest.kt";s=p.read_text(encoding="utf-8")
assert s.rstrip().endswith("}")
s=s.rstrip()[:-1]+'''
    @Test fun renewalIsAcknowledgedForBothChannelsAndSellersButNeverCompleted() {
        val c=config()
        c.getJSONObject("settings").put("requireAllowlist",false)
            .getJSONObject("autoReplies").put("normal",true)
        c.put("sellerContacts",JSONArray().put(JSONObject()
            .put("channel","business").put("contact","Revendedor Prueba")
            .put("assistant","movieplay")))
        val at=clock("2026-10-12","23:00")
        for(ch in listOf("business","normal")){
            val incoming=NativeAutoReplyEngine.decide(c,ch,"Cliente nuevo","Renueva",at)
            assertEquals(RenewalReplies.MESSAGE,incoming.text)
            assertEquals("renewal",incoming.routeSource)
            assertEquals("movieplay",incoming.business)
        }
        val reseller=NativeAutoReplyEngine.decide(c,"business","Revendedor Prueba",
            "Hola, quiero renovar Netflix",at)
        assertEquals(RenewalReplies.MESSAGE,reseller.text)
        assertEquals("renewal",reseller.routeSource)
        val notAsked=NativeAutoReplyEngine.decide(c,"business","Revendedor Prueba",
            "Cuánto cuesta renovar",at)
        assertNull(notAsked.text)
        val already=NativeAutoReplyEngine.decide(c,"business","Cliente nuevo",
            "Ya renové",at)
        assertNotEquals("renewal",already.routeSource)
        c.getJSONArray("blocked").put(JSONObject()
            .put("channel","business").put("contact","Revendedor Prueba"))
        assertNull(NativeAutoReplyEngine.decide(c,"business","Revendedor Prueba",
            "Renueva",at).text)
    }
    @Test fun paymentInquiryBeforeBusinessChoiceDoesNotDiscloseBankData() {
        val c=config()
        c.getJSONObject("settings").put("requireAllowlist",false)
        c.put("payments",JSONObject().put("movieplay",
            JSONObject().put("nequi",JSONObject()
                .put("number","3000000000"))
                .put("bancolombia",JSONObject()).put("daviplata",JSONObject())))
        val at=clock("2026-10-12","19:00")
        val ambiguous=NativeAutoReplyEngine.decide(c,"business","Cliente nuevo",
            "¿Dónde te transfiero?",at)
        assertTrue(ambiguous.needsChoice)
        assertEquals("payment_business_prompt",ambiguous.routeSource)
        assertFalse(ambiguous.text!!.contains("3000000000"))
        val choseMovie=NativeAutoReplyEngine.decide(c,"business","Cliente nuevo","1",at,
            awaitingChoice=true,paymentBusinessPending=true)
        assertTrue(choseMovie.text!!.contains("MEDIOS DE PAGO"))
        assertEquals("movieplay",choseMovie.business)
        assertTrue(choseMovie.paymentMenu)
        val choseFood=NativeAutoReplyEngine.decide(c,"business","Cliente nuevo","2",at,
            awaitingChoice=true,paymentBusinessPending=true)
        assertFalse(choseFood.text!!.contains("3000000000"))
        assertEquals("tresm",choseFood.business)
    }
}
'''
p.write_text(s,encoding="utf-8")

p=root/"tests/smoke.test.cjs";s=p.read_text(encoding="utf-8")
s+='''
for(const phrase of ["renueva","quiero renovar","renuévame","Hola, renueva Netflix"]){
  assert.equal(friendly.respond("business","Cliente de prueba",phrase).reply,
    "Claro 😊, dame un momento y te confirmo la renovación.");
  assert.equal(friendly.respond("business","Vendedor de prueba",phrase).reply,
    "Claro 😊, dame un momento y te confirmo la renovación.");
}
for(const phrase of ["no renueves","ya renové","cuánto cuesta renovar"]){
  assert.notEqual(friendly.respond("business","Vendedor de prueba",phrase).reply,
    "Claro 😊, dame un momento y te confirmo la renovación.");
}
const unsure=JSON.parse(JSON.stringify(friendlyConfig));
unsure.exceptions=[];
const unknown=create(unsure).api;
const pending=unknown.respond("business","Cliente sin negocio","¿dónde te transfiero?");
assert.match(pending.reply,/MoviePlay/);
assert.match(pending.reply,/Las Tres M/);
assert.doesNotMatch(pending.reply,/912 752309 23/);
console.log("OK — renovaciones pendientes y pagos con selección de negocio segura.");
'''
p.write_text(s,encoding="utf-8")
print("Renewal and ambiguous payment selection regressions added, including seller and both WhatsApps")
