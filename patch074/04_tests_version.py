from pathlib import Path

root=Path("source/autoresponder-pro")
native=root/"android/app/src/test/java/com/autoresponder/pro"
native.mkdir(parents=True,exist_ok=True)
(native/"PlanPrecision074Test.kt").write_text(r'''package com.autoresponder.pro

import org.json.JSONArray
import org.json.JSONObject
import org.junit.Assert.*
import org.junit.Test
import java.time.LocalDate

class PlanPrecision074Test {
    private val day=LocalDate.parse("2026-10-29")
    private fun product(id:String,name:String,price:Long=18000L,
        duration:String="30 días",active:Boolean=true):JSONObject =
        JSONObject().put("id",id).put("name",name).put("assistant","movieplay")
            .put("type","service").put("duration",duration)
            .put("price",price).put("active",active).put("imageTag",name.lowercase())
            .put("keywords",when{
                name.startsWith("Netflix")->"netflix,netflis,neflis"
                name.startsWith("Disney")->"disney,disney plus"
                name.startsWith("Max")->"max,max premium"
                name.startsWith("Prime")->"prime,prime video"
                else->name.lowercase()
            })
    private fun config():JSONObject {
        val cat=JSONArray()
            .put(product("n26","Netflix Premium 4K",14000L,"26 días"))
            .put(product("n30","Netflix Premium 4K",18000L,"30 días"))
            .put(product("nint","Netflix Internacional",18000L,"30 días"))
            .put(product("dp","Disney+ Premium",19000L))
            .put(product("de","Disney+ Estándar",10000L))
            .put(product("db","Disney+ Básico",6000L))
            .put(product("mp","Max Premium",10000L))
            .put(product("me","Max Estándar",6000L))
            .put(product("prime","Prime Video",10000L))
        return JSONObject().put("catalog",cat)
            .put("comboSales",JSONObject().put("enabled",true)
                .put("minServices",2).put("amountPerService",1000))
    }
    @Test fun typosMapToExactlyTheRequestedPlan() {
        val c=config()
        for((message,id) in listOf("quiero disnei premiun" to "dp",
            "Disney+ premuim" to "dp","max premiun" to "mp",
            "max estandard" to "me","Netflix inter" to "nint")){
            val actual=LocalCatalog.matched(c,"movieplay",message)
            assertEquals(message,1,actual.size)
            assertEquals(message,id,actual.single().optString("id"))
        }
        assertEquals("n30",LocalCatalog.matched(c,"movieplay",
            "Netflix 30 días").single{it.optString("duration")=="30 días"}.optString("id"))
        assertFalse(LocalCatalog.matched(c,"movieplay","Netflix 30 días")
            .any{it.optString("id")=="nint"})
    }
    @Test fun adjectiveNeverMovesFromMaxToDisney() {
        val c=config()
        val hits=LocalCatalog.matched(c,"movieplay","Disney y Max Premium")
        assertTrue(hits.any{it.optString("id")=="dp"})
        assertTrue(hits.any{it.optString("id")=="de"})
        assertTrue(hits.any{it.optString("id")=="mp"})
        assertFalse(hits.any{it.optString("id")=="me"})
        assertEquals("premium",PlanPrecision074.variant(
            "Disney Premium y Max","disney"))
        assertNull(PlanPrecision074.variant(
            "Disney y Max Premium","disney"))
    }
    @Test fun noSubstitutionWhenSpecificDurationIsUnavailable() {
        val c=config()
        val no=LocalCatalog.reply(c,"movieplay","Netflix 28 días",day)!!.text
        assertTrue(no.contains("No encuentro la duración"))
        assertFalse(no.contains("\$14.000"))
        assertFalse(no.contains("\$18.000"))
        val disney=LocalCatalog.reply(c,"movieplay","Disney Premiun",day)!!.text
        assertTrue(disney.contains("Disney+ Premium"))
        assertFalse(disney.contains("Disney+ Estándar"))
        assertFalse(disney.contains("\$10.000"))
    }
    @Test fun completedPlanMayBeChangedByShortFollowup() {
        val c=config()
        val start=ConversationFlow.remember(c,"movieplay","Netflix 30 días",
            "Compra guiada; pendiente de confirmación")!!
        assertEquals("n30",start.productId)
        val change=ConversationFlow.followUp(c,"movieplay","internacional",
            start.productId,start.stage,0,day)!!
        assertEquals("nint",change.productId)
        assertEquals("payment_offer",change.stage)
        assertTrue(change.text.contains("Netflix Internacional"))
        assertFalse(change.text.contains("Netflix Premium 4K"))
        val d=ConversationFlow.remember(c,"movieplay","Quiero Disney Premiun",
            "Compra guiada; pendiente de confirmación")!!
        assertEquals("dp",d.productId)
        val switch=ConversationFlow.followUp(c,"movieplay","estándar",
            d.productId,d.stage,0,day)!!
        assertEquals("de",switch.productId)
        assertTrue(switch.text.contains("\$10.000"))
    }
    @Test fun resetNeverCancelsUnrelatedRenewals(){
        assertTrue(ConversationSafety074.shouldReset("cancelar mi cotización",true))
        assertTrue(ConversationSafety074.shouldReset("empezar de nuevo",true))
        assertFalse(ConversationSafety074.shouldReset("cancelar mi cotización",false))
        assertFalse(ConversationSafety074.shouldReset("cancelar renovación",true))
        assertFalse(ConversationSafety074.shouldReset("comprobante de pago",true))
    }
    @Test fun comboUnderstandsTyposWithoutSwitchingFamily(){
        val answer=ComboSales.respond(config(),"quiero netflis 30 días y disnei premiun",
            day)!!
        assertTrue(answer.text.contains("Disney+ Premium"))
        assertTrue(answer.text.contains("Netflix Premium 4K"))
        assertTrue(answer.text.contains("\$35.000"))
        assertFalse(answer.text.contains("Disney+ Estándar"))
    }
}
''',encoding="utf-8")

(root/"tests/intelligence_074.test.cjs").write_text(r''' 'use strict';
const assert=require('node:assert/strict');
const P=require('../web/plan-precision-074.js');
const D=require('../web/diagnostics-074.js');
const fs=require('node:fs');
const catalog=[
 {id:'n26',name:'Netflix Premium 4K',assistant:'movieplay',duration:'26 días',price:14000,active:true},
 {id:'n30',name:'Netflix Premium 4K',assistant:'movieplay',duration:'30 días',price:18000,active:true},
 {id:'ni',name:'Netflix Internacional',assistant:'movieplay',duration:'30 días',price:18000,active:true},
 {id:'dp',name:'Disney+ Premium',assistant:'movieplay',duration:'30 días',price:19000,active:true},
 {id:'de',name:'Disney+ Estándar',assistant:'movieplay',duration:'30 días',price:10000,active:true},
 {id:'me',name:'Max Estándar',assistant:'movieplay',duration:'30 días',price:6000,active:true},
 {id:'mp',name:'Max Premium',assistant:'movieplay',duration:'30 días',price:10000,active:true}
];
for(const [msg,id] of [
 ['disnei premiun','dp'],['Disney+ premuim','dp'],['Max premiun','mp'],
 ['max standAR','me'],['Netflix inter','ni']
]) assert.deepEqual(P.filter('movieplay',msg,catalog).filter(x=>x.name.toLowerCase()
    .includes(P.requested(msg)[0])),[catalog.find(x=>x.id===id)],msg);
assert.equal(P.variant('Disney y Max Premium','disney'),null);
assert.equal(P.variant('Disney Premium y Max','disney'),'premium');
assert.ok(P.filter('movieplay','Netflix 30 días',catalog).every(x=>x.id!=='ni'));
assert.equal(P.filter('movieplay','Qué planes de Netflix tienes',catalog).length,catalog.length);
const sample=[
 {reason:'no_quick_reply',channel:'business',at:1700000000000},
 {reason:'submitted_unverified',channel:'normal',at:1700000001000},
 {reason:'failed_permission',channel:'normal',at:1700000002000},
 {reason:'human_reply_paused',channel:'business',at:1700000003000}
];
assert.deepEqual(D.metrics(sample),{total:4,errors:2,review:1,submitted:1});
assert.equal(D.entries(sample,'error').length,2);
assert.match(D.explain('no_quick_reply').advice,/WhatsApp/);
assert.match(D.explain('submitted_unverified').advice,/No confirma/);
assert.equal(D.entries([{reason:'failed',channel:'other',at:1}], 'all').length,0);
const app=fs.readFileSync(require('node:path').join(__dirname,'../web/app.js'),'utf8');
const html=fs.readFileSync(require('node:path').join(__dirname,'../web/index.html'),'utf8');
assert.match(html,/diagnostico074/);
assert.match(html,/plan-precision-074\.js/);
assert.match(app,/renderDiagnostics074/);
assert.match(app,/No encuentro esa duración del servicio seleccionado/);
console.log('v0.6.14: reconocimiento y diagnóstico — pruebas superadas.');
''',encoding="utf-8")

gradle=root/"android/app/build.gradle.kts"
s=gradle.read_text(encoding="utf-8")
assert s.count("versionCode = 28")==1
assert s.count('versionName = "0.6.13"')==1
gradle.write_text(s.replace("versionCode = 28","versionCode = 29",1)
    .replace('versionName = "0.6.13"','versionName = "0.6.14"',1),
    encoding="utf-8")
print("0.6.14: 6 native regression groups and Node tests; versionCode 29.")
