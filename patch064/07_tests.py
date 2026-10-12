from pathlib import Path
root=Path("source/autoresponder-pro")
test=root/"android/app/src/test/java/com/autoresponder/pro"
(test/"ConversationFlowTest.kt").write_text(r'''package com.autoresponder.pro

import org.json.JSONArray
import org.json.JSONObject
import org.junit.Assert.*
import org.junit.Test
import java.time.LocalDate

class ConversationFlowTest {
    private val today=LocalDate.parse("2026-10-12")
    private fun item(id:String,business:String,name:String,keywords:String,
        duration:String,price:Long,active:Boolean=true):JSONObject =
        JSONObject().put("id",id).put("assistant",business)
            .put("name",name).put("keywords",keywords)
            .put("duration",duration).put("price",price).put("active",active)
    private fun config():JSONObject{
        val items=JSONArray()
            .put(item("nf26","movieplay","Netflix Premium 4K","netflix","26 días",14000L))
            .put(item("nf28","movieplay","Netflix Premium 4K","netflix","28 días",16000L))
            .put(item("nf30","movieplay","Netflix Premium 4K","netflix","30 días",18000L))
            .put(item("nfi","movieplay","Netflix Internacional","netflix","30 días",18000L))
            .put(item("ham","tresm","Hamburguesa sencilla","hamburguesa","",15000L))
            .put(item("hame","tresm","Hamburguesa especial","hamburguesa","",20000L))
        val payments=JSONObject().put("movieplay",JSONObject()
            .put("holder","Nombre de prueba")
            .put("nequi",JSONObject().put("number","3000000000"))
            .put("bancolombia",JSONObject())
            .put("daviplata",JSONObject()))
        return JSONObject().put("catalog",items).put("payments",payments)
    }
    @Test fun netflixRemembersFamilyAndExact30DayPriceFromCurrentCatalog() {
        val c=config()
        val memory=ConversationFlow.remember(c,"movieplay","¿Cuánto vale Netflix?",
            "Catálogo aprobado")
        assertNotNull(memory)
        assertEquals("plan",memory!!.stage)
        val offer=ConversationFlow.followUp(c,"movieplay","El de 30 días",
            memory.productId,memory.stage,0,today)
        assertNotNull(offer)
        assertEquals("nf30",offer!!.productId)
        assertEquals("payment_offer",offer.stage)
        assertTrue(offer.text.contains("$18.000"))
        assertTrue(offer.text.contains("verifican"))
        assertFalse(offer.text.contains("Compra confirmada"))
        val accepted=ConversationFlow.followUp(c,"movieplay","Sí",
            offer.productId,offer.stage,0,today)
        assertNotNull(accepted)
        assertEquals("payment_menu",accepted!!.stage)
        assertTrue(accepted.text.contains("MEDIOS DE PAGO"))
        assertFalse(accepted.text.contains("3000000000"))
    }
    @Test fun pricesAreAlwaysReadLiveAndUnavailableProductsAreNotSold() {
        val c=config()
        c.getJSONArray("catalog").getJSONObject(2).put("price",19500)
        val result=ConversationFlow.followUp(c,"movieplay","30 días","nf26","plan",0,today)
        assertTrue(result!!.text.contains("$19.500"))
        c.getJSONArray("catalog").getJSONObject(2).put("active",false)
        val out=ConversationFlow.followUp(c,"movieplay","30 días","nf26","plan",0,today)
        assertTrue(out!!.text.contains("NO DISPONIBLE"))
        assertEquals("plan",out.stage)
    }
    @Test fun foodVariantQuantityAndDeliveryNeedHumanApproval() {
        val c=config()
        val first=ConversationFlow.remember(c,"tresm","Quiero pedir hamburguesa",
            "Solicitud de pedido; falta revisión")
        assertNotNull(first)
        assertEquals("variant",first!!.stage)
        val variant=ConversationFlow.followUp(c,"tresm","especial",
            first.productId,first.stage,0,today)
        assertEquals("hame",variant!!.productId)
        assertEquals("quantity",variant.stage)
        val qty=ConversationFlow.followUp(c,"tresm","2",
            variant.productId,variant.stage,0,today)
        assertEquals("delivery",qty!!.stage)
        assertEquals(2,qty.quantity)
        assertTrue(qty.text.contains("$40.000"))
        val pickup=ConversationFlow.followUp(c,"tresm","domicilio",
            qty.productId,qty.stage,qty.quantity,today)
        assertNotNull(pickup)
        assertEquals("review",pickup!!.stage)
        assertTrue(pickup.text.contains("PENDIENTE DE REVISIÓN"))
        assertFalse(pickup.text.contains("Pedido confirmado"))
    }
    @Test fun productMemoryCannotLeakBetweenBusinessesOrAcceptUnknownReply() {
        val c=config()
        assertNull(ConversationFlow.followUp(c,"tresm","30 dias","nf26","plan",0,today))
        assertNull(ConversationFlow.followUp(c,"movieplay","30 dias","missing","plan",0,today))
        assertNull(ConversationFlow.followUp(c,"movieplay","Hola","nf26","plan",0,today))
        assertNull(ConversationFlow.remember(c,"movieplay","comprobante","Catálogo aprobado"))
    }
}
'''.replace('"$18.000"','"\\$18.000"')
    .replace('"$19.500"','"\\$19.500"')
    .replace('"$40.000"','"\\$40.000"'),encoding="utf-8")

(test/"CadencePolicyTest.kt").write_text(r'''package com.autoresponder.pro

import org.json.JSONObject
import org.junit.Assert.*
import org.junit.Test

class CadencePolicyTest {
    @Test fun defaultsMatchPreviouslyTestedCadence() {
        assertEquals(12L*60L*60L*1000L,CadencePolicy.menu(null))
        assertEquals(12L*60L*60L*1000L,CadencePolicy.away(null))
        assertEquals(15L*60L*1000L,CadencePolicy.thanks(null))
        assertEquals(2L*60L*1000L,CadencePolicy.repeated(null))
    }
    @Test fun customSettingsBoundedAndIndependent() {
        val c=JSONObject().put("menuHours",6)
            .put("awayHours",24).put("greetingHours",3)
            .put("courtesyMinutes",90).put("repeatMinutes",1)
        assertEquals(6L*60L*60L*1000L,CadencePolicy.menu(c))
        assertEquals(24L*60L*60L*1000L,CadencePolicy.away(c))
        assertEquals(3L*60L*60L*1000L,CadencePolicy.greeting(c))
        assertEquals(90L*60L*1000L,CadencePolicy.thanks(c))
        assertEquals(60_000L,CadencePolicy.repeated(c))
        c.put("menuHours",500).put("repeatMinutes",0)
        assertEquals(24L*60L*60L*1000L,CadencePolicy.menu(c))
        assertEquals(60_000L,CadencePolicy.repeated(c))
    }
}
''',encoding="utf-8")

p=root/"tests/learning.test.cjs"
s=p.read_text(encoding="utf-8")
s+='''

// Similar unanswered questions about one topic become ONE supervised proposal.
const cluster=LE.absorb([],[as('¿Cuánto vale nerflis?'),as('¿Tienen nerflis?')]);
assert.equal(cluster.length,1);
assert.equal(cluster[0].count,2);
const isolated=LE.absorb(cluster,[as('¿Tienen nerflis?', {assistant:'tresm'})]);
assert.equal(isolated.length,2);
const protectedData=LE.absorb(isolated,[as('Pago Pedro Páez',{autoStatus:'manual_review'}),
  as('Envío comprobante',{hasAttachment:true})]);
assert.equal(protectedData.length,2);
console.log('OK — las consultas similares se agrupan sin mezclar negocios ni comprobantes.');
'''
p.write_text(s,encoding="utf-8")
print("Native and JavaScript tests cover plan selection, changed prices, food quantities, privacy isolation, cadence settings and supervised grouping")
