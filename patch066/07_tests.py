from pathlib import Path
root=Path("source/autoresponder-pro")
tests=root/"android/app/src/test/java/com/autoresponder/pro"
(tests/"ApprovedLearningTest.kt").write_text(r'''package com.autoresponder.pro

import org.json.JSONArray
import org.json.JSONObject
import org.junit.Assert.*
import org.junit.Test

class ApprovedLearningTest {
    private fun config():JSONObject {
        val accounts=JSONObject().put("movieplay",JSONObject()
            .put("holder","Titular de prueba")
            .put("nequi",JSONObject().put("number","3001234567").put("key","@3001234567"))
            .put("bancolombia",JSONObject().put("number","987654321"))
            .put("daviplata",JSONObject().put("number","3111234567")))
        return JSONObject().put("payments",accounts)
    }
    @Test fun recognizesOnlyExplicitActiveApprovedPhrases() {
        val cfg=config()
        cfg.put("intentAliases",JSONArray()
            .put(JSONObject().put("phrase","donde hago el giro")
                .put("intent","payment").put("active",true))
            .put(JSONObject().put("phrase","tankiuss")
                .put("intent","courtesy").put("active",true))
            .put(JSONObject().put("phrase","ve renovando el servicio")
                .put("intent","renewal").put("active",true))
            .put(JSONObject().put("phrase","oye yo necesito una persona")
                .put("intent","human").put("active",true))
            .put(JSONObject().put("phrase","alias desactivado")
                .put("intent","payment").put("active",false)))
        assertEquals("payment",ApprovedLearning.match(cfg,"¿Dónde hago el giro?")!!.name)
        assertEquals("payment",ApprovedLearning.match(cfg,"Hola, dónde hago el giro")!!.name)
        assertEquals("courtesy",ApprovedLearning.match(cfg,"TANKIUSS!")!!.name)
        assertEquals("renewal",ApprovedLearning.match(cfg,"ve renovando el servicio")!!.name)
        assertEquals("human",ApprovedLearning.match(cfg,"oye yo necesito una persona")!!.name)
        assertNull(ApprovedLearning.match(cfg,"alias desactivado"))
        assertNull(ApprovedLearning.match(cfg,"donde hago el giro, pero ya pagué"))
    }
    @Test fun producesOnlyOfficialDynamicPaymentOrApprovedThanks() {
        val cfg=config()
        val menu=ApprovedLearning.respond(cfg,
            ApprovedLearning.Intent("payment","donde hago el giro"),null,null)
        assertNotNull(menu)
        assertEquals("payment_specific",menu!!.routeSource)
        assertTrue(menu.paymentMenu)
        assertTrue(menu.text!!.contains("MEDIOS DE PAGO"))
        assertFalse(menu.text!!.contains("3001234567"))
        val nequi=ApprovedLearning.respond(cfg,
            ApprovedLearning.Intent("payment_nequi","me giras por alli"),
            "tresm",null)
        assertTrue(nequi!!.text!!.contains("3001234567"))
        assertFalse(nequi.text!!.contains("987654321"))
        val thanks=ApprovedLearning.respond(cfg,
            ApprovedLearning.Intent("courtesy","tankiuss"),null,null)
        assertEquals(CourtesyReplies.message,thanks!!.text)
        assertEquals("courtesy",thanks.routeSource)
        val renewal=ApprovedLearning.respond(cfg,
            ApprovedLearning.Intent("renewal","ve renovando el servicio"),null,"movieplay")
        assertEquals(RenewalReplies.MESSAGE,renewal!!.text)
        assertNull(ApprovedLearning.respond(cfg,
            ApprovedLearning.Intent("renewal","ve renovando el servicio"),"tresm","tresm"))
        val human=ApprovedLearning.respond(cfg,
            ApprovedLearning.Intent("human","ayudame tu"),null,null)
        assertNull(human!!.text)
        assertEquals("manual_review",human.routeSource)
    }
    @Test fun rejectsReceiptsCredentialsAndUnsafeOverBroadPhrases() {
        for(phrase in listOf("Pago Pedro Páez","ya pagué","ya te transferí",
            "Comprobante adjunto","mira mi foto","Dame mi OTP 123456",
            "cuenta 12345678","pago","ok","hola",
            "mi contraseña")) {
            assertFalse("Unsafe phrase must never be learned: $phrase",
                ApprovedLearning.valid(phrase,"payment"))
        }
        assertTrue(ApprovedLearning.valid("dónde te hago el giro","payment"))
        assertTrue(ApprovedLearning.valid("tankiu parcero","courtesy"))
        assertTrue(ApprovedLearning.valid("porfa renueva mi servicio","renewal"))
        assertFalse(ApprovedLearning.valid("donde pago","unknown_intent"))
    }
}
''',encoding="utf-8")

p=tests/"NativeAutoReplyEngineTest.kt"
s=p.read_text(encoding="utf-8")
assert s.rstrip().endswith("}")
s=s.rstrip()[:-1]+'''
    @Test fun learnedIntentsAreSynchronizedAcrossBothWhatsAppWithSellerPriority() {
        val c=config()
        c.getJSONObject("settings").put("requireAllowlist",false)
            .getJSONObject("autoReplies").put("normal",true)
        c.put("payments",JSONObject().put("movieplay",JSONObject()
            .put("holder","Titular de prueba")
            .put("nequi",JSONObject().put("number","3001234567"))
            .put("bancolombia",JSONObject()).put("daviplata",JSONObject())))
        c.put("intentAliases",JSONArray()
            .put(JSONObject().put("phrase","donde hago el giro").put("intent","payment")
                .put("active",true))
            .put(JSONObject().put("phrase","tankiuss").put("intent","courtesy")
                .put("active",true))
            .put(JSONObject().put("phrase","me vas renovando").put("intent","renewal")
                .put("active",true)))
        c.put("sellerContacts",JSONArray().put(JSONObject()
            .put("channel","business").put("contact","Revendedor")
            .put("assistant","movieplay")))
        val now=clock("2026-10-10","19:00")
        for(ch in listOf("normal","business")) {
            val reply=NativeAutoReplyEngine.decide(c,ch,"Cliente nuevo",
                "¿Dónde hago el giro?",now)
            assertTrue(reply.text!!.contains("MEDIOS DE PAGO"))
            assertTrue(reply.paymentMenu)
            assertEquals("payment_specific",reply.routeSource)
            val thx=NativeAutoReplyEngine.decide(c,ch,"Cliente nuevo","Tankiuss",now)
            assertEquals(CourtesyReplies.message,thx.text)
            val renewal=NativeAutoReplyEngine.decide(c,ch,"Cliente nuevo",
                "me vas renovando",now)
            assertEquals(RenewalReplies.MESSAGE,renewal.text)
        }
        val sellerPay=NativeAutoReplyEngine.decide(c,"business","Revendedor",
            "donde hago el giro",now)
        assertTrue(sellerPay.text!!.contains("MEDIOS DE PAGO"))
        val sellerSilent=NativeAutoReplyEngine.decide(c,"business","Revendedor",
            "Netflix precio",now)
        assertNull(sellerSilent.text)
        assertEquals("seller_human",sellerSilent.routeSource)
        val receipt=NativeAutoReplyEngine.decide(c,"business","Cliente nuevo",
            "Pago Pedro Páez",now)
        assertNull(receipt.text)
    }
}
'''
p.write_text(s,encoding="utf-8")

p=root/"tests/learning.test.cjs";s=p.read_text(encoding="utf-8")
s+='''
for(const tuple of [
  ["¿Dónde hago el giro?","payment"],
  ["tenkiu parcero","courtesy"],
  ["me vas renovando","renewal"],
  ["llamame por favor","human"],
  ["nequi","payment_nequi"],
  ["me compartes la llave","payment_llave"]
])assert.equal(LE.safeIntentAlias(tuple[0],tuple[1]),true,tuple[0]);
for(const phrase of ["Pago Pedro Páez","Comprobante enviado","Ya pagué",
   "transferencia realizada","Mi número 3001234567","pago","hola"]){
  assert.equal(LE.safeIntentAlias(phrase,"payment"),false,phrase);
}
const safeBankQuestion=LE.absorb([],[as("¿Dónde puedo girarte?")]);
assert.equal(safeBankQuestion.length,1);
assert.equal(safeBankQuestion[0].status,"pending");
console.log("OK — sugerencias de pago seguras y tipos de respuesta general con aprobación.");
'''
p.write_text(s,encoding="utf-8")

# Exercise the same learned intent inside the browser simulator; the old
# test seam needs the real LearningEngine because it used only schedules.
p=root/"tests/smoke.test.cjs";s=p.read_text(encoding="utf-8")
s=s.replace("const engine = require('../web/schedule-engine.js');",
    "const engine = require('../web/schedule-engine.js');\nconst learningEngine = require('../web/learning-engine.js');",1)
s=s.replace("window:{ScheduleEngine:engine,addEventListener(){}}",
    "window:{ScheduleEngine:engine,LearningEngine:learningEngine,addEventListener(){}}",1)
s+='''
const trainedConfig=JSON.parse(JSON.stringify(friendlyConfig));
trainedConfig.intentAliases=[
  {id:"learn-payment",phrase:"donde hago el giro",intent:"payment",active:true},
  {id:"learn-thanks",phrase:"tankiuss",intent:"courtesy",active:true},
  {id:"learn-renewal",phrase:"me vas renovando",intent:"renewal",active:true},
  {id:"learn-human",phrase:"necesito alguien de verdad",intent:"human",active:true}
];
const taught=create(trainedConfig).api;
assert.match(taught.respond("business","Cliente de prueba","donde hago el giro").reply,/MEDIOS DE PAGO/);
assert.equal(taught.respond("business","Vendedor de prueba","tankiuss").reply,gratitude);
assert.equal(taught.respond("normal","Cliente de prueba","me vas renovando").reply,
 "Claro 😊, dame un momento y te confirmo la renovación.");
assert.match(taught.respond("business","Cliente de prueba","necesito alguien de verdad").reason,/atención humana/);
assert.notEqual(taught.respond("business","Cliente de prueba","Pago Pedro Páez").method,"payment_specific");
console.log("OK — asociaciones aprobadas se usan sin cambiar las respuestas bancarias.");
'''
p.write_text(s,encoding="utf-8")
print("JUnit and JS regressions for learned bank/gratitude/renewal/human intents, vendor isolation, blocked receipts, and no automatic training.")
