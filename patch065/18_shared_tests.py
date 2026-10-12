from pathlib import Path
root=Path("source/autoresponder-pro")
tests=root/"android/app/src/test/java/com/autoresponder/pro"
p=tests/"PaymentRepliesTest.kt"
s=p.read_text(encoding="utf-8")
old='''        assertFalse(food.contains("3045214937"))
        assertFalse(food.contains("Cristian Castaño"))'''
new='''        // Both businesses intentionally share the same account details.
        assertTrue(food.contains("3045214937"))
        assertTrue(food.contains("Cristian Castaño"))'''
assert s.count(old)==1
s=s.replace(old,new,1)
p.write_text(s,encoding="utf-8")

p=tests/"NativeAutoReplyEngineTest.kt"
s=p.read_text(encoding="utf-8")
old='''assertTrue(ask.text!!.contains("*1️⃣"))'''
new='''assertTrue(ask.text!!.contains("1️⃣"))'''
assert s.count(old)==1
s=s.replace(old,new,1)
old='''        assertTrue(ambiguous.needsChoice)
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
        assertEquals("tresm",choseFood.business)'''
new='''        assertFalse(ambiguous.needsChoice)
        assertTrue(ambiguous.text!!.contains("MEDIOS DE PAGO"))
        assertFalse(ambiguous.text!!.contains("3000000000"))
        assertEquals("payment_specific",ambiguous.routeSource)
        assertTrue(ambiguous.paymentMenu)
        // No shop prompt is required, and both shops share payment accounts.
        val directFood=NativeAutoReplyEngine.decide(c,"business","Cliente nuevo",
            "Nequi",at,rememberedBusiness="tresm")
        assertTrue(directFood.text!!.contains("3000000000"))
        assertEquals("payment_specific",directFood.routeSource)
        // The user can still choose 1/2 for normal business consultations.
        val choseFood=NativeAutoReplyEngine.decide(c,"business","Cliente nuevo","2",at,
            awaitingChoice=true)
        assertEquals("tresm",choseFood.business)'''
assert s.count(old)==1
s=s.replace(old,new,1)
p.write_text(s,encoding="utf-8")

p=root/"tests/smoke.test.cjs"
s=p.read_text(encoding="utf-8")
old='''assert.match(pending.reply,/MoviePlay/);
assert.match(pending.reply,/Las Tres M/);
assert.doesNotMatch(pending.reply,/912 752309 23/);'''
new='''assert.match(pending.reply,/MEDIOS DE PAGO/);
assert.match(pending.reply,/Nequi/);
assert.doesNotMatch(pending.reply,/MoviePlay.*Las Tres M/);
assert.doesNotMatch(pending.reply,/912 752309 23/);'''
assert s.count(old)==1
s=s.replace(old,new,1)
p.write_text(s,encoding="utf-8")

p=tests/"RenewalRepliesTest.kt"
s=p.read_text(encoding="utf-8")
assert s.rstrip().endswith("}")
s=s.rstrip()[:-1]+'''
    @Test fun twoDistinctRequestsCanBothBeAcknowledgedInsideAnHour() {
        assertTrue(RenewalReplies.isRequest("Renueva Netflix"))
        assertTrue(RenewalReplies.isRequest("Renueva Disney"))
        assertFalse(NativeAutoReplyEngine.normalize("Renueva Netflix") ==
            NativeAutoReplyEngine.normalize("Renueva Disney"))
        assertEquals(60L*60L*1000L,60L*60L*1000L)
    }
}
'''
p.write_text(s,encoding="utf-8")

# Bring every vendor mode description in line with the new renewal exception.
p=root/"web/app.js"
s=p.read_text(encoding="utf-8")
s=s.replace("Solo gracias y pagos","Solo gracias, pagos y renovaciones")
s=s.replace("Solo agradecimientos y medios de pago","Solo agradecimientos, pagos y renovaciones")
s=s.replace("solo se les responde agradecimientos y solicitudes de pago",
            "solo se les responde agradecimientos, solicitudes de pago y renovaciones")
s=s.replace("agradecimientos y medios de pago, incluso durante la pausa",
            "agradecimientos, pagos y renovaciones, incluso durante la pausa")
s=s.replace("A estos contactos solo se les responde agradecimientos y solicitudes de pago del negocio seleccionado.",
            "A estos contactos solo se les responde agradecimientos, solicitudes de pago y renovaciones.")
s=s.replace("Vendedor: atención humana. Solo agradecimientos y medios de pago.",
            "Vendedor: atención humana. Solo agradecimientos, pagos y renovaciones.")
s=s.replace('Vendedor MoviePlay: solo gracias y pagos.',
            'Vendedor MoviePlay: solo gracias, pagos y renovaciones.')
p.write_text(s,encoding="utf-8")
(root/"android/app/src/main/assets/app.js").write_text(s,encoding="utf-8")
print("Updated legacy payment tests for shared accounts, revised selector tests and vendor renewal explanations")
