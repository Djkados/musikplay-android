from pathlib import Path
root=Path("source/autoresponder-pro")
native=root/"android/app/src/test/java/com/autoresponder/pro"
p=native/"NotificationCaptureRegressionTest.kt"
s=p.read_text(encoding="utf-8")
assert s.rstrip().endswith("}")
s=s.rstrip()[:-1]+'''
    private fun imageWithCaption(caption:String):Notification {
        val sender=Person.Builder().setName("Contacto de prueba").setKey("remote-person").build()
        val image=NotificationCompat.MessagingStyle.Message(
            caption,System.currentTimeMillis(),sender)
            .setData("image/jpeg",android.net.Uri.parse("content://whatsapp/media/photo"))
        return NotificationCompat.Builder(listener,"messages")
            .setSmallIcon(android.R.drawable.ic_dialog_info)
            .setCategory(Notification.CATEGORY_MESSAGE)
            .setStyle(NotificationCompat.MessagingStyle(Person.Builder().setName("Yo").build())
                .addMessage(image)).build()
    }

    @Test fun paymentImageCaptionNeverRepliesOrStoresReceiptText() {
        post(imageWithCaption("Pago Pedro Páez"),"com.whatsapp.w4b")
        assertEquals(1,inbox().length())
        val review=inbox().getJSONObject(0)
        assertEquals("manual_review",review.getString("autoStatus"))
        assertTrue(review.getBoolean("hasAttachment"))
        assertFalse(review.getString("text").contains("Pedro"))
        assertFalse(review.toString().contains("Pago Pedro"))
        assertEquals("adjunto_revision_manual",listener.getSharedPreferences("listener_status",Context.MODE_PRIVATE)
            .getString("lastReason",""))
    }
    @Test fun paymentEvidencePlainTextAlsoNeedsManualReview() {
        post(notification(text="Pago Pedro Páez"),"com.whatsapp")
        assertEquals("manual_review",inbox().getJSONObject(0).getString("autoStatus"))
        assertEquals("comprobante_revision_manual",listener.getSharedPreferences("listener_status",Context.MODE_PRIVATE)
            .getString("lastReason",""))
        assertFalse(inbox().getJSONObject(0).optBoolean("learnEligible",true))
    }
    @Test fun plainTextNequiRemainsEligibleForNormalProcessing() {
        post(notification(text="Nequi"),"com.whatsapp.w4b")
        assertEquals(1,inbox().length())
        assertEquals("Nequi",inbox().getJSONObject(0).getString("text"))
        assertFalse(inbox().getJSONObject(0).optBoolean("hasAttachment",false))
    }
    @Test fun photoWithBankNameInCaptionStillCannotTriggerPaymentMenu() {
        post(imageWithCaption("Nequi"),"com.whatsapp")
        assertEquals("manual_review",inbox().getJSONObject(0).getString("autoStatus"))
        assertFalse(inbox().getJSONObject(0).getString("text").contains("Nequi"))
    }
    @Test fun repeatedPaymentProofDoesNotCreateDuplicateManualReview() {
        val receipt=notification(text="Ya pagué, te envío comprobante")
        post(receipt,"com.whatsapp.w4b",22)
        post(receipt,"com.whatsapp.w4b",22)
        assertEquals(1,inbox().length())
    }
}
'''
p.write_text(s,encoding="utf-8")
p=native/"PaymentRepliesTest.kt"
s=p.read_text(encoding="utf-8")
assert s.rstrip().endswith("}")
s=s.rstrip()[:-1]+'''
    @Test fun paymentReceiptsAreNeverRequestsForBankDetails() {
        val c=config()
        for(message in listOf("Pago Pedro Páez","Ya pagué","Comprobante adjunto",
            "Pago realizado","Te envié el comprobante","Transferencia realizada")) {
            assertNull("Evidence must not generate bank info: $message",
                PaymentReplies.reply(c,"movieplay",message))
        }
        assertTrue(PaymentReplies.reply(c,"movieplay","Nequi")!!.text.contains("@3045214937"))
        assertTrue(PaymentReplies.reply(c,"movieplay","Medios de pago")!!.isMenu)
    }
}
'''
p.write_text(s,encoding="utf-8")
p=native/"GuidedAssistantTest.kt"
p.write_text(r'''package com.autoresponder.pro

import org.json.JSONArray
import org.json.JSONObject
import org.junit.Assert.*
import org.junit.Test
import java.time.LocalDate

class GuidedAssistantTest {
    private val date=LocalDate.parse("2026-10-10")
    private fun config():JSONObject {
        val records=JSONArray()
            .put(JSONObject().put("name","Netflix Premium 4K")
                .put("assistant","movieplay").put("active",true)
                .put("keywords","netflix").put("duration","30 días").put("price",18000))
            .put(JSONObject().put("name","Hamburguesa especial")
                .put("assistant","tresm").put("active",true)
                .put("keywords","hamburguesa").put("price",20000))
        return JSONObject().put("catalog",records)
    }
    @Test fun presaleGuidesCustomerButNeverConfirmsPurchaseOrPayment() {
        val response=GuidedAssistant.suggest(config(),"movieplay","Quiero comprar Netflix",date)
        assertNotNull(response)
        assertTrue(response!!.text.contains("$18.000"))
        assertTrue(response.text.contains("se verifican"))
        assertFalse(response.text.contains("Compra confirmada"))
        assertEquals("Compra guiada; pendiente de confirmación",response.reason)
    }
    @Test fun foodOrderCollectsQuantitiesAndDeliveryWithoutAcceptingOrder() {
        val response=GuidedAssistant.suggest(config(),"tresm","Quiero pedir hamburguesa",date)
        assertNotNull(response)
        assertTrue(response!!.text.contains("cantidades"))
        assertTrue(response.text.contains("a domicilio"))
        assertTrue(response.text.contains("se confirman"))
        assertFalse(response.text.contains("Pedido confirmado"))
    }
    @Test fun explicitHumanRequestTriggersEscalation() {
        assertTrue(GuidedAssistant.wantsHuman("quiero hablar con asesor humano"))
        assertTrue(GuidedAssistant.wantsHuman("necesito un asesor"))
        assertFalse(GuidedAssistant.wantsHuman("precio de netflix"))
    }
    @Test fun silentOnPaymentProofAndUnrequestedPurchase() {
        assertNull(GuidedAssistant.suggest(config(),"movieplay","Precio Netflix",date))
        assertNull(GuidedAssistant.suggest(config(),"tresm","hamburguesa",date))
    }
}
'''.replace('"$18.000"','"\\$18.000"'),encoding="utf-8")
p=root/"tests/learning.test.cjs"
p.write_text(r'''const assert = require('node:assert/strict');
const LE=require('../web/learning-engine.js');
const as=(text,extra={})=>({
  text,autoReason:'Consulta sin regla aprobada',autoStatus:'skipped',
  assistant:'movieplay',learnEligible:true,hasAttachment:false,...extra
});
assert.equal(LE.safePhrase('¿Tienen fluji TV?'),'¿tienen fluji tv?');
for(const t of ['Pago Pedro Páez','Ya pagué','Nequi','comprobante adjunto',
  'Foto: pago Pedro','Mi número 3045214937','clave otp','transferencia realizada'])
  assert.equal(LE.safePhrase(t),null,t);
assert.equal(LE.safeAlias('pago'),false);
assert.equal(LE.safeAlias('flujito'),true);
assert.equal(LE.safeAlias('cuanto vale'),false);
const incoming=[
  as('¿Tienen fluji TV?'),
  as('Pago Pedro Páez',{autoStatus:'manual_review',hasAttachment:true}),
  as('¿Tienen caput?',{hasAttachment:true}),
  as('Nequi',{learnEligible:false}),
  as('¿Tienen algo?',{autoReason:'Fuera de horario'}),
];
const result=LE.absorb([],incoming);
assert.equal(result.length,1);
assert.equal(result[0].count,1);
assert.equal(result[0].assistant,'movieplay');
const repeated=LE.absorb(result,[incoming[0]]);
assert.equal(repeated.length,1);
assert.equal(repeated[0].count,2);
repeated[0].status='ignored';
assert.equal(LE.absorb(repeated,[incoming[0]])[0].status,'ignored');
console.log('OK — supervisión local y exclusión de adjuntos y datos sensibles.');
''',encoding="utf-8")
print("Media receipt, payment request, supervised learning and guided-order tests installed")
