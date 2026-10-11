from pathlib import Path

root=Path("source/autoresponder-pro")
test=root/"android/app/src/test/java/com/autoresponder/pro/NativeAutoReplyEngineTest.kt"
s=test.read_text(encoding="utf-8")
assert s.rstrip().endswith("}")
s=s.rstrip()[:-1]+'''
    @Test fun gratitudeReplyIsExactlyOwnersTextOnBothWhatsappChannelsOutsideHours() {
        val c=config()
        c.getJSONObject("settings").put("requireAllowlist",false)
            .getJSONObject("autoReplies").put("normal",true)
        val night=clock("2026-10-11","23:45")
        val expected="Gracias por confiar en nuestro servicio. 🙌\\\\n" +
            "Para nosotros es un honor poder atenderte y ayudarte."
        val examples=listOf("Gracias","Muchas gracias","Mil gracias","Muchísimas gracias",
            "Graciasss!!","Grasias","Grax","Tenkiu","TENKIU!!","Tenkyu","Thank you",
            "Thanks!","Muchas gracias por todo","Perfecto gracias","te lo agradezco")
        for(channel in listOf("normal","business")) {
            for(message in examples) {
                val d=NativeAutoReplyEngine.decide(c,channel,"Cliente nuevo",message,night)
                assertEquals("Expected gratitude reply for $channel / $message",expected,d.text)
                assertEquals("courtesy",d.routeSource)
                assertEquals("Agradecimiento automático",d.reason)
            }
        }
    }

    @Test fun gratitudeCannotBypassDisabledChannelBlockedOrUnapprovedContact() {
        val c=config()
        val day=clock("2026-10-10","19:00")
        // A disabled reply channel is always silent.
        assertNull(NativeAutoReplyEngine.decide(c,"normal","Prueba","gracias",day).text)
        c.getJSONObject("settings").getJSONObject("autoReplies").put("normal",true)
        // With allowlist required, other contacts remain excluded.
        assertNull(NativeAutoReplyEngine.decide(c,"normal","Desconocido","gracias",day).text)
        c.getJSONArray("blocked").put(JSONObject().put("channel","business").put("contact","Prueba"))
        assertNull(NativeAutoReplyEngine.decide(c,"business","Prueba","tenkiu",day).text)
        val paused=JSONObject().put("channel","normal").put("contact","Prueba")
            .put("until",day.toInstant().toEpochMilli()+3600000L)
        c.getJSONArray("paused").put(paused)
        assertNull(NativeAutoReplyEngine.decide(c,"normal","Prueba","gracias",day).text)
    }

    @Test fun gratitudeDoesNotInterceptQuestionsReceiptsOrOwnMessages() {
        val c=config()
        val day=clock("2026-10-10","19:00")
        c.getJSONObject("settings").put("requireAllowlist",false)
        val unsafe=listOf("Gracias, ¿cuánto cuesta Netflix?",
            "Gracias ya pagué","Pago Pedro Páez","Comprobante gracias","Nequi gracias",
            "Muchas gracias por la transferencia","Gracias por enviarme la cuenta",
            "Gracias por comprar la hamburguesa")
        for(text in unsafe) {
            val result=NativeAutoReplyEngine.decide(c,"business","Cliente",text,day)
            assertTrue("Must not intercept: $text",result.routeSource!="courtesy")
        }
        assertNull(NativeAutoReplyEngine.decide(c,"business","Tú","gracias",day).text)
    }
}
'''
# Triple quoted Python above emits literal "\\n" as Kotlin escaped newline,
# so the expected value must contain a real newline after Kotlin string decoding.
s=s.replace('🙌\\\\n" +','🙌\\n" +')
# The replacement is Python representation of one escape slash + letter n in Kotlin.
# Validate the Kotlin source line is still a single physical line.
for line in s.splitlines():
    if "val expected=" in line:
        assert "🙌\\n" in line,repr(line)
test.write_text(s,encoding="utf-8")

p=root/"android/app/src/test/java/com/autoresponder/pro/CourtesyRepliesTest.kt"
p.write_text(r'''package com.autoresponder.pro

import org.junit.Assert.*
import org.junit.Test

class CourtesyRepliesTest {
    @Test fun matchesCommonStandaloneThanks() {
        for(value in listOf("Gracias","gracias!","MUCHAS GRACIAS","mil gracias",
            "Muchísimas gracias", "Tenkiu", "Tenkiu!!", "tenkyu", "thank you",
            "thank u", "Thanks", "grasias","Grax", "Te lo agradezco")) {
            assertTrue("Unrecognized: $value",CourtesyReplies.matches(value))
        }
    }
    @Test fun doesNotMatchPaymentQuestionsOrReceipts() {
        for(value in listOf("Pago Pedro Páez","Gracias ya pagué","gracias por consignar",
            "¿Cuánto vale Netflix? Gracias","gracias quiero Netflix 30 días",
            "Nequi","gracias al banco por confirmar la transferencia",
            "Gracias por el comprobante","Foto: Gracias")) {
            assertFalse("Not standalone: $value",CourtesyReplies.matches(value))
        }
    }
    @Test fun replyTextIsExactTwoLines() {
        assertEquals("Gracias por confiar en nuestro servicio. 🙌\n"+
            "Para nosotros es un honor poder atenderte y ayudarte.",CourtesyReplies.message)
    }
}
''',encoding="utf-8")

# Confirm the app's simulator mirrors the on-device response and doesn't
# intercept commerce or media/payment-evidence messages.
p=root/"tests/smoke.test.cjs"
s=p.read_text(encoding="utf-8")
anchor="assert.match(test.respond('business','Cliente de prueba','mi código de acceso').reason,/seguridad/);"
assert s.count(anchor)==1
extra=r"""
const gratitude="Gracias por confiar en nuestro servicio. 🙌\nPara nosotros es un honor poder atenderte y ayudarte.";
for(const phrase of ['Gracias','Muchas gracias','Mil gracias','Tenkiu','TENKIU!',
    'Graciasss!!','Grax','Thank you','Te lo agradezco']) {
  assert.equal(test.respond('business','Cliente de prueba',phrase,false,
    new Date('2026-10-11T23:45:00-05:00')).reply,gratitude);
}
assert.notEqual(test.respond('business','Cliente de prueba',
    'Gracias, ¿cuánto cuesta Netflix?').reply,gratitude);
assert.notEqual(test.respond('business','Cliente de prueba',
    'Gracias, ya pagué').reply,gratitude);
assert.notEqual(test.respond('business','Cliente de prueba',
    'Foto: Gracias').reply,gratitude);
"""
s=s.replace(anchor,anchor+"\n"+extra,1)
p.write_text(s,encoding="utf-8")
print("Kotlin and WebView regression tests added for gratitude variations, exact reply, both WhatsApps, night hours and safety precedence")
