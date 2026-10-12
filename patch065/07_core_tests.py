from pathlib import Path
root=Path("source/autoresponder-pro")
tests=root/"android/app/src/test/java/com/autoresponder/pro"
p=tests/"PaymentRepliesTest.kt"
s=p.read_text(encoding="utf-8")
assert s.rstrip().endswith("}")
s=s.rstrip()[:-1]+'''
    @Test fun everydayTransferPhrasesOfferPaymentMethodsWithoutInventingConfirmation() {
        val c=config()
        for(text in listOf("donde te transfiero","¿Dónde te transfiero?",
            "a dónde te transfiero","por donde te transfiero",
            "donde consigno","a qué cuenta te transfiero","me pasas tus datos de pago",
            "donde puedo transferir","quiero transferirte")) {
            val reply=PaymentReplies.reply(c,"movieplay",text)
            assertNotNull("Must recognize $text",reply)
            assertTrue("Must offer payment method menu for $text",reply!!.isMenu)
        }
        for(text in listOf("Ya te transferí","Comprobante enviado","Pago Pedro Páez")) {
            assertNull("Already paid must NOT trigger menu: $text",
                PaymentReplies.reply(c,"movieplay",text))
        }
    }
    @Test fun sellerPaymentRepliesUseShortHumanToneButOnlyApprovedAccount() {
        val c=config()
        val menu=PaymentReplies.reply(c,"movieplay","donde te transfiero",
            casual=true)
        assertNotNull(menu)
        assertTrue(menu!!.text.startsWith("Claro"))
        assertTrue(menu.isMenu)
        assertFalse(menu.text.contains("912 752309 23"))
        val bank=PaymentReplies.reply(c,"movieplay","Bancolombia",casual=true)!!
        assertTrue(bank.text.contains("912 752309 23"))
        assertFalse(bank.text.contains("@3045214937"))
        assertTrue(bank.text.contains("me envías el comprobante"))
        val nequi=PaymentReplies.reply(c,"movieplay","Nequi",casual=true)!!
        assertTrue(nequi.text.contains("3045214937"))
        assertFalse(nequi.text.contains("@castano454"))
        assertTrue(nequi.text.contains("\\n\\n"))
    }
}
'''
p.write_text(s,encoding="utf-8")

p=tests/"NativeAutoReplyEngineTest.kt"
s=p.read_text(encoding="utf-8")
assert s.rstrip().endswith("}")
s=s.rstrip()[:-1]+'''
    @Test fun sellersGetOnlyThanksAndRequestedPaymentsEvenOutOfHours() {
        val c=config()
        c.getJSONObject("settings").put("requireAllowlist",false)
            .getJSONObject("autoReplies").put("normal",true)
        c.put("sellerContacts",JSONArray().put(JSONObject()
            .put("channel","business").put("contact","Vendedor Prueba")
            .put("phone","3001112222").put("assistant","movieplay")))
        val movie=JSONObject().put("holder","Cristian Castaño")
            .put("nequi",JSONObject().put("number","3045214937").put("key","@3045214937"))
            .put("bancolombia",JSONObject().put("number","912 752309 23")
                .put("key","@castano454"))
            .put("daviplata",JSONObject().put("number","3045214937")
                .put("key","@PLATA3045214937"))
        c.put("payments",JSONObject().put("movieplay",movie))
        val night=clock("2026-10-11","23:40")
        for(text in listOf("Hola","Netflix","Precio Disney","¿Y el de 30 días?",
            "oferta netflix","buenas noches","necesito soporte","hamburguesa")) {
            val reply=NativeAutoReplyEngine.decide(c,"business","Vendedor Prueba",text,night,
                rememberedBusiness="movieplay")
            assertNull("Seller must stay silent for $text",reply.text)
            assertEquals("seller_human",reply.routeSource)
        }
        val thanks=NativeAutoReplyEngine.decide(c,"business",
            "Vendedor Prueba","Tenkiu",night)
        assertEquals(CourtesyReplies.message,thanks.text)
        val payment=NativeAutoReplyEngine.decide(c,"business",
            "Vendedor Prueba","donde te transfiero",night)
        assertTrue(payment.text!!.startsWith("Claro 😊"))
        assertTrue(payment.text!!.contains("Nequi"))
        assertFalse(payment.text!!.contains("912 752309 23"))
        val bank=NativeAutoReplyEngine.decide(c,"business",
            "Vendedor Prueba","Bancolombia",night)
        assertTrue(bank.text!!.contains("912 752309 23"))
        assertEquals("payment_specific",bank.routeSource)
        val phone=NativeAutoReplyEngine.sellerBusiness(c,"business","+57 300 111 2222")
        assertEquals("movieplay",phone)
        assertNull(NativeAutoReplyEngine.sellerBusiness(c,"normal","Vendedor Prueba"))
        // A different WhatsApp receives the usual customer flow.
        val regular=NativeAutoReplyEngine.decide(c,"normal","Vendedor Prueba",
            "Netflix",clock("2026-10-10","19:00"))
        assertNotEquals("seller_human",regular.routeSource)
    }
    @Test fun sellerMustBeExplicitAndPaymentDetailsRespectBlockingAndReceipts() {
        val c=config()
        c.getJSONObject("settings").put("requireAllowlist",false)
        c.put("sellerContacts",JSONArray().put(JSONObject()
            .put("channel","business").put("contact","Vendedor Prueba")
            .put("assistant","movieplay")))
        val t=clock("2026-10-10","19:00")
        assertNull(NativeAutoReplyEngine.decide(c,"business","Vendedor Prueba",
            "Pago Pedro Páez",t).text)
        c.getJSONArray("blocked").put(JSONObject()
            .put("channel","business").put("contact","Vendedor Prueba"))
        assertNull(NativeAutoReplyEngine.decide(c,"business","Vendedor Prueba",
            "Gracias",t).text)
        // Not auto-designate anyone as vendor.
        assertNull(NativeAutoReplyEngine.sellerBusiness(c,"business","Cliente normal"))
    }
    @Test fun clientWithKnownMoviePlayContextCanAskWhereToTransfer() {
        val c=config()
        c.getJSONObject("settings").put("requireAllowlist",false)
        c.put("payments",JSONObject().put("movieplay",
            JSONObject().put("holder","Titular de prueba")
                .put("nequi",JSONObject().put("number","3000000000"))
                .put("bancolombia",JSONObject())
                .put("daviplata",JSONObject())))
        val t=clock("2026-10-12","18:00")
        val answer=NativeAutoReplyEngine.decide(c,"business","Cliente habitual",
            "donde te transfiero",t,rememberedBusiness="movieplay")
        assertTrue(answer.text!!.contains("MEDIOS DE PAGO"))
        assertTrue(answer.paymentMenu)
    }
}
'''
p.write_text(s,encoding="utf-8")
print("Seller-only mode, previous payment phrase regression, short personal tone and independent WhatsApp role tests added.")
