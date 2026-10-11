from pathlib import Path
root=Path("source/autoresponder-pro")
p=root/"android/app/src/test/java/com/autoresponder/pro/LocalCatalogTest.kt"
s=p.read_text(encoding="utf-8")
assert s.rstrip().endswith("}")
s=s.rstrip()[:-1]+'''
    @Test fun unavailablePlanShowsPriceAndCannotAdvertisePromo() {
        val c=catalog()
        val rows=c.getJSONArray("catalog")
        rows.getJSONObject(0).put("active",false)
        val result=LocalCatalog.reply(c,"movieplay","Netflix 26 dias",
            LocalDate.parse("2026-10-15"))
        assertNotNull(result)
        assertTrue(result!!.text.contains("\\$14.000"))
        assertTrue(result.text.contains("NO DISPONIBLE POR EL MOMENTO"))
        assertEquals("",result.imageTag)
        assertTrue(LocalCatalog.detects(c,"movieplay","Netflix 26 dias"))
        assertFalse(result.text.contains("¿Cuál opción disponible te interesa?"))
    }
    @Test fun onlyOneDurationCanBeDisabledWithoutHidingOtherPlans() {
        val c=catalog()
        c.getJSONArray("catalog").getJSONObject(0).put("active",false)
        val result=LocalCatalog.reply(c,"movieplay","Netflix",
            LocalDate.parse("2026-11-01"))
        assertNotNull(result)
        assertTrue(result!!.text.contains("NO DISPONIBLE POR EL MOMENTO"))
        assertTrue(result.text.contains("\\$18.000"))
        assertTrue(result.text.contains("¿Cuál opción disponible te interesa?"))
    }
}
'''
p.write_text(s,encoding="utf-8")
p=root/"android/app/src/test/java/com/autoresponder/pro/PaymentRepliesTest.kt"
p.write_text('''package com.autoresponder.pro

import org.json.JSONObject
import org.junit.Assert.*
import org.junit.Test

class PaymentRepliesTest {
    private fun config():JSONObject {
        val movie=JSONObject().put("holder","Cristian Castaño")
            .put("nequi",JSONObject().put("number","3045214937")
                .put("key","@3045214937"))
            .put("bancolombia",JSONObject().put("number","912 752309 23")
                .put("key","@castano454"))
            .put("daviplata",JSONObject().put("number","3045214937")
                .put("key","@PLATA3045214937"))
        val food=JSONObject().put("holder","")
            .put("nequi",JSONObject()).put("bancolombia",JSONObject())
            .put("daviplata",JSONObject())
        return JSONObject().put("payments",JSONObject()
            .put("movieplay",movie).put("tresm",food))
    }
    @Test fun directBankRequestReturnsOnlyThatBankAndReceiptReminder() {
        val c=config()
        val nequi=PaymentReplies.reply(c,"movieplay","Nequi")!!
        assertTrue(nequi.text.contains("@3045214937"))
        assertFalse(nequi.text.contains("@castano454"))
        assertFalse(nequi.text.contains("PLATA3045214937"))
        assertTrue(nequi.text.contains("comprobante"))
        val bank=PaymentReplies.reply(c,"movieplay","Bancolombia")!!
        assertTrue(bank.text.contains("912 752309 23"))
        assertFalse(bank.text.contains("@3045214937"))
        assertTrue(bank.text.contains("@castano454"))
        val davi=PaymentReplies.reply(c,"movieplay","DaviPlata")!!
        assertTrue(davi.text.contains("@PLATA3045214937"))
        assertFalse(davi.text.contains("@castano454"))
    }
    @Test fun genericPaymentRequestShowsOnlyMethodsAndNumericChoice() {
        val c=config()
        for(request in listOf("medios de pago","dame cuentas","donde pago",
            "formas de pago","cómo pago","a donde transfiero")) {
            val answer=PaymentReplies.reply(c,"movieplay",request)
            assertNotNull("Missing $request",answer)
            assertTrue(answer!!.isMenu)
            assertTrue(answer.text.contains("1️⃣ *Nequi*"))
            assertTrue(answer.text.contains("2️⃣ *Bancolombia*"))
            assertFalse(answer.text.contains("912 752309 23"))
        }
        assertTrue(PaymentReplies.reply(c,"movieplay","1",true)!!.choice)
        assertTrue(PaymentReplies.reply(c,"movieplay","2",true)!!.text.contains("@castano454"))
        assertTrue(PaymentReplies.reply(c,"movieplay","3",true)!!.text.contains("@PLATA3045214937"))
        assertTrue(PaymentReplies.reply(c,"movieplay","4",true)!!.text.contains("PAGO CON LLAVE"))
        assertNull(PaymentReplies.reply(c,"movieplay","1",false))
    }
    @Test fun keysOnlyAndStrictSeparationForLasTresM() {
        val c=config()
        val keys=PaymentReplies.reply(c,"movieplay","Llave")!!.text
        assertTrue(keys.contains("@3045214937"))
        assertTrue(keys.contains("@castano454"))
        assertTrue(keys.contains("@PLATA3045214937"))
        assertFalse(keys.contains("912 752309 23"))
        val food=PaymentReplies.reply(c,"tresm","Nequi")!!.text
        assertTrue(food.contains("LAS TRES M"))
        assertFalse(food.contains("3045214937"))
        assertFalse(food.contains("Cristian Castaño"))
        assertNull(PaymentReplies.reply(c,"movieplay","Netflix 30 días"))
    }
}
''',encoding="utf-8")
print("Native regression tests cover inactive prices, merchant payment isolation, all payment methods and numeric selection")
