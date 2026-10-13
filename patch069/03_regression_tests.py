from pathlib import Path

root=Path("source/autoresponder-pro")
tests=root/"android/app/src/test/java/com/autoresponder/pro"

p=tests/"PaymentRepliesTest.kt"
s=p.read_text(encoding="utf-8")
assert s.rstrip().endswith("}")
s=s.rstrip()[:-1]+'''
    @Test fun numberedChoicesWorkAfterMenuAndNeverAsFreeFloatingNumbers() {
        val c=config()
        val choices=listOf("1","1️⃣","1.","opcion 1","opción uno","el 1","primera")
        for(q in choices) {
            val response=PaymentReplies.reply(c,"movieplay",q,
                pendingMenu=true,casual=true)
            assertNotNull("Missing payment choice $q",response)
            assertEquals("Should be bank choice: $q",true,response!!.choice)
            assertTrue(response.text.contains("@3045214937"))
            assertFalse(response.text.contains("@castano454"))
            assertFalse(response.text.contains("@PLATA3045214937"))
        }
        for(q in listOf("2","2️⃣","3","3️⃣","4","4️⃣")) {
            assertNotNull(PaymentReplies.reply(c,"tresm",q,
                pendingMenu=true,casual=true))
        }
        assertTrue(PaymentReplies.reply(c,"movieplay","4",
            pendingMenu=true,casual=true)!!.text.contains("@castano454"))
        for(q in listOf("1","1️⃣","opcion 1","el 1","1 pedido","1 unidad")) {
            assertNull("No bank info without a sent payment menu: $q",
                PaymentReplies.reply(c,"movieplay",q,pendingMenu=false,casual=true))
        }
        assertNull(PaymentReplies.reply(c,"movieplay","Ya te pagué 1",
            pendingMenu=true,casual=true))
    }
}
'''
p.write_text(s,encoding="utf-8")

(tests/"PaymentMenuContextTest.kt").write_text('''package com.autoresponder.pro

import org.junit.Assert.*
import org.junit.Test

class PaymentMenuContextTest {
    @Test fun sentMenuSurvivesAResetBusinessRoute() {
        val now=1_700_000_000_000L
        assertTrue(PaymentMenuContext.isPending(now,false,0L,now-120_000L))
        assertTrue(PaymentMenuContext.isPending(now,true,now-240_000L,0L))
        assertFalse(PaymentMenuContext.isPending(now,false,0L,0L))
        assertFalse(PaymentMenuContext.isPending(now,false,0L,
            now-PaymentMenuContext.SENT_MENU_MS-1000L))
        assertFalse(PaymentMenuContext.isPending(now,true,now-3_600_000L,0L))
        assertFalse(PaymentMenuContext.isPending(now,false,0L,now+120_000L))
    }
}
''',encoding="utf-8")

(tests/"GreetingRepliesTest.kt").write_text('''package com.autoresponder.pro

import org.junit.Assert.*
import org.junit.Test
import java.time.ZoneId
import java.time.ZonedDateTime

class GreetingRepliesTest {
    @Test fun greetingByItselfNeverStealsAProductOrPaymentRequest() {
        for(g in listOf("Hola","holi","Hola, buenos días!",
            "Buenas noches","Muy buenas tardes","Hola, ¿cómo estás?"))
            assertTrue("Expected greeting $g",GreetingReplies.pure(g))
        for(combined in listOf("Hola quiero Netflix","Hola, forma de pago",
            "Buenas noches, cuánto vale Disney Premium",
            "Ya pagué, buenas noches"))
            assertFalse("Must route real intention $combined",GreetingReplies.pure(combined))
    }
    @Test fun greetingReflectsColombiaHour() {
        val zone=ZoneId.of("America/Bogota")
        val morning=ZonedDateTime.of(2026,10,12,9,0,0,0,zone)
        val evening=ZonedDateTime.of(2026,10,12,19,0,0,0,zone)
        assertTrue(GreetingReplies.message("movieplay",morning).startsWith("¡Buenos días!"))
        assertTrue(GreetingReplies.message("tresm",evening).startsWith("¡Buenas noches!"))
    }
}
''',encoding="utf-8")

p=tests/"ConversationFlowTest.kt"
s=p.read_text(encoding="utf-8")
assert s.rstrip().endswith("}")
s=s.rstrip()[:-1]+'''
    @Test fun oneChosenAvailablePlanOffersPaymentAfterPrice() {
        val c=config()
        val one=c.getJSONArray("catalog").getJSONObject(2)
        c.put("catalog",JSONArray().put(one))
        val quote=LocalCatalog.reply(c,"movieplay","Netflix Premium 30 días",today)
        assertNotNull(quote)
        assertTrue(quote!!.text.contains("¿Te paso los medios de pago?"))
        val memo=ConversationFlow.remember(c,"movieplay",
            "Quiero Netflix Premium 30 días","Compra guiada; pendiente de confirmación")
        assertNotNull(memo)
        assertEquals("payment_offer",memo!!.stage)
        for(yes in listOf("si","Sí, porfa","de una","dale","siii","perfecto")) {
            val answer=ConversationFlow.followUp(c,"movieplay",yes,
                memo.productId,memo.stage,0,today)
            assertNotNull("Not recognized: $yes",answer)
            assertEquals("payment_menu",answer!!.stage)
            assertTrue(answer.text.contains("MEDIOS DE PAGO"))
            assertFalse(answer.text.contains("3000000000"))
        }
        assertNull(ConversationFlow.followUp(c,"movieplay","no gracias",
            memo.productId,memo.stage,0,today))
        val guided=GuidedAssistant.suggest(c,"movieplay",
            "Quiero Netflix Premium 30 días",today)
        assertNotNull(guided)
        assertTrue(guided!!.text.contains("¿Te paso los medios de pago?"))
        assertFalse(guided.text.contains("no disponible"))
    }
    @Test fun genericPriceListAsksCustomerToChoosePlanFirst() {
        val c=config()
        val quote=LocalCatalog.reply(c,"movieplay","Netflix",today)
        assertNotNull(quote)
        assertFalse(quote!!.text.contains("¿Te paso los medios de pago?"))
        assertEquals("plan",ConversationFlow.remember(c,"movieplay",
            "¿Cuánto vale Netflix?","Catálogo aprobado")!!.stage)
    }
}
'''
p.write_text(s,encoding="utf-8")

p=tests/"NativeAutoReplyEngineTest.kt"
s=p.read_text(encoding="utf-8")
assert s.rstrip().endswith("}")
s=s.rstrip()[:-1]+'''
    @Test fun selectedNequiWorksWithLostBusinessStateOrHumanHandoff() {
        val c=config()
        c.getJSONObject("settings").put("requireAllowlist",false)
        c.put("payments",JSONObject().put("movieplay",JSONObject()
            .put("holder","Titular de prueba")
            .put("nequi",JSONObject().put("number","3000000000"))
            .put("bancolombia",JSONObject().put("number","123456789"))
            .put("daviplata",JSONObject().put("number","3111111111"))))
        val t=clock("2026-10-12","19:07")
        for(handoff in listOf(false,true)) {
            val selected=NativeAutoReplyEngine.decide(c,"normal","Cliente XYZ","1",t,
                paymentMenuPending=true,humanHandoff=handoff)
            assertEquals("payment_choice",selected.routeSource)
            assertTrue(selected.text!!.contains("3000000000"))
            assertFalse(selected.text!!.contains("123456789"))
        }
        val noMenu=NativeAutoReplyEngine.decide(c,"normal","Cliente XYZ","1",t,
            paymentMenuPending=false)
        assertFalse(noMenu.text.orEmpty().contains("3000000000"))
    }
}
'''
p.write_text(s,encoding="utf-8")
print("Payment, menu-memory, greetings, quoted-plan followup, native routing and safety regression tests for 0.6.9.")
