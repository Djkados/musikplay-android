from pathlib import Path
root=Path("source/autoresponder-pro")
tests=root/"android/app/src/test/java/com/autoresponder/pro"

p=tests/"NativeAutoReplyEngineTest.kt"
s=p.read_text(encoding="utf-8")
old='''assertTrue(ask.text!!.contains("*1️⃣"))'''
new='''assertTrue(ask.text!!.contains("1️⃣ 🎬 *MoviePlay*"))'''
assert s.count(old)==1,("old formatted selector",s.count(old))
s=s.replace(old,new,1)
p.write_text(s,encoding="utf-8")

p=tests/"PaymentRepliesTest.kt"
s=p.read_text(encoding="utf-8")
old='''        assertFalse(food.contains("3045214937"))
        assertFalse(food.contains("Cristian Castaño"))'''
new='''        assertTrue(food.contains("3045214937"))
        assertTrue(food.contains("Cristian Castaño"))'''
assert s.count(old)==1,("legacy payment test",s.count(old))
s=s.replace(old,new,1)
p.write_text(s,encoding="utf-8")

p=tests/"NativeAutoReplyEngineTest.kt"
s=p.read_text(encoding="utf-8")
old='''    @Test fun paymentInquiryBeforeBusinessChoiceDoesNotDiscloseBankData() {'''
assert s.count(old)==1
start=s.index(old)
end=s.index("\n}\n",start)
s=s[:start]+'''    @Test fun paymentQuestionUsesSameMethodsImmediatelyForBothBusinesses() {
        val c=config()
        c.getJSONObject("settings").put("requireAllowlist",false)
        c.put("payments",JSONObject().put("movieplay",
            JSONObject().put("holder","Titular de prueba")
                .put("nequi",JSONObject().put("number","39999999999"))
                .put("bancolombia",JSONObject().put("number","123456789"))
                .put("daviplata",JSONObject().put("number","3111111111")))
            .put("tresm",JSONObject().put("nequi",JSONObject().put("number","9999999999"))))
        val at=clock("2026-10-12","19:00")
        val generic=NativeAutoReplyEngine.decide(c,"business","Cliente nuevo",
            "¿Dónde te transfiero?",at)
        assertEquals("payment_specific",generic.routeSource)
        assertTrue(generic.paymentMenu)
        assertTrue(generic.text!!.contains("MEDIOS DE PAGO"))
        assertFalse(generic.text!!.contains("39999999999"))
        assertFalse(generic.text!!.contains("¿Es para"))
        val pickNequi=NativeAutoReplyEngine.decide(c,"business","Cliente nuevo","1",at,
            paymentMenuPending=true)
        assertEquals("payment_choice",pickNequi.routeSource)
        assertTrue(pickNequi.text!!.contains("39999999999"))
        assertFalse(pickNequi.text!!.contains("9999999999"))
        val pickBank=NativeAutoReplyEngine.decide(c,"business","Cliente nuevo","2",at,
            paymentMenuPending=true)
        assertTrue(pickBank.text!!.contains("123456789"))
        assertEquals("payment_choice",pickBank.routeSource)
        val withFoodContext=NativeAutoReplyEngine.decide(c,"business",
            "Cliente de comida","Nequi",at,rememberedBusiness="tresm")
        assertTrue(withFoodContext.text!!.contains("39999999999"))
        assertFalse(withFoodContext.text!!.contains("9999999999"))
        val handoff=NativeAutoReplyEngine.decide(c,"business","Cliente sin negocio",
            "Dónde te transfiero",at,humanHandoff=true)
        assertTrue(handoff.text!!.contains("MEDIOS DE PAGO"))
    }
    @Test fun sameRenewalTextIsCanonicalizedWithoutBlockingOtherRequests() {
        assertEquals(RenewalReplies.repeatIdentity("RENUEVA Netflix 30 días!"),
            RenewalReplies.repeatIdentity("renueva netflix 30 dias"))
        assertNotEquals(RenewalReplies.repeatIdentity("Renueva NETFLIX venta V-001"),
            RenewalReplies.repeatIdentity("Renueva NETFLIX venta V-002"))
        assertNotEquals(RenewalReplies.repeatIdentity("Renueva Netflix cliente Ana"),
            RenewalReplies.repeatIdentity("Renueva Disney cliente Pedro"))
    }
'''+s[end:]
p.write_text(s,encoding="utf-8")

p=tests/"PaymentRepliesTest.kt"
s=p.read_text(encoding="utf-8")
assert s.rstrip().endswith("}")
s=s.rstrip()[:-1]+'''
    @Test fun sameConfiguredAccountForBothBusinesses() {
        val c=config()
        for(b in listOf("movieplay","tresm")) {
            val answer=PaymentReplies.reply(c,b,"Nequi",casual=true)
            assertNotNull(answer)
            assertTrue(answer!!.text.contains("@3045214937"))
            assertTrue(answer.text.contains("Cristian Castaño"))
        }
        assertNull(PaymentReplies.reply(c,"tresm","Ya hice transferencia"))
        assertNull(PaymentReplies.reply(c,"movieplay","Pago Pedro Páez"))
    }
}
'''
p.write_text(s,encoding="utf-8")

p=root/"tests/smoke.test.cjs"
s=p.read_text(encoding="utf-8")
old='''const pending=unknown.respond("business","Cliente sin negocio","¿dónde te transfiero?");
assert.match(pending.reply,/MoviePlay/);
assert.match(pending.reply,/Las Tres M/);
assert.doesNotMatch(pending.reply,/912 752309 23/);'''
new='''const pending=unknown.respond("business","Cliente sin negocio","¿dónde te transfiero?");
assert.match(pending.reply,/MEDIOS DE PAGO/);
assert.match(pending.reply,/Nequi/);
assert.doesNotMatch(pending.reply,/¿Es para/);
assert.doesNotMatch(pending.reply,/912 752309 23/);
assert.match(unknown.respond("business","Cliente sin negocio","Nequi").reply,/@3045214937/);'''
assert s.count(old)==1,("legacy smoke",s.count(old))
s=s.replace(old,new,1)
s+='''
assert.match(unknown.respond("business","Cliente de comida","Nequi").reply,/@3045214937/);
assert.notEqual(unknown.respond("business","Cliente nuevo","Ya te transferí").method,"payment_specific");
console.log("OK — los pagos son compartidos y una renovación repetida no bloquea otras.");
'''
p.write_text(s,encoding="utf-8")
print("Tests updated for shared payment data without business selector, real Kotlin phrase matching, and different renewals per hour")
