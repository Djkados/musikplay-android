from pathlib import Path
root=Path("source/autoresponder-pro")
native=root/"android/app/src/test/java/com/autoresponder/pro"
native.mkdir(parents=True,exist_ok=True)
(native/"Sales360AndNetflixInfoTest.kt").write_text(r'''package com.autoresponder.pro

import android.content.Context
import org.json.JSONArray
import org.json.JSONObject
import org.junit.Assert.*
import org.junit.Test
import org.junit.runner.RunWith
import org.robolectric.RobolectricTestRunner
import org.robolectric.RuntimeEnvironment

@RunWith(RobolectricTestRunner::class)
class Sales360AndNetflixInfoTest {
    private fun infoConfig(active:Boolean=true,price:Int=18000):JSONObject{
        val array=JSONArray()
            .put(JSONObject().put("id","nf30").put("assistant","movieplay")
                .put("name","Netflix Premium 4K").put("duration","30 días")
                .put("active",true).put("price",18000))
            .put(JSONObject().put("id","nfi").put("assistant","movieplay")
                .put("name","Netflix Internacional").put("duration","30 días")
                .put("active",active).put("price",price))
        return JSONObject().put("catalog",array)
    }
    @Test fun netflixQuestionsGetAccurateCatalogPricing(){
        val c=infoConfig()
        for(m in listOf("¿Qué es eso de Netflix Internacional?",
            "Qué diferencia hay entre Netflix normal y Netflix internacional",
            "¿Netflix Internacional qué significa?"))
            assertTrue(NetflixInternationalInfo.answer(c,m).orEmpty().contains("Internacional"))
        val a=NetflixInternationalInfo.answer(c,"qué diferencia hay con Netflix Internacional")!!
        assertTrue(a.contains("\$18.000"))
        assertTrue(a.contains("30 días"))
        assertTrue(a.contains("restricciones de hogar"))
        assertNull(NetflixInternationalInfo.answer(c,"cuánto cuesta Netflix internacional"))
        assertNull(NetflixInternationalInfo.answer(c,"Netflix 30 días y Disney"))
        val out=NetflixInternationalInfo.answer(infoConfig(active=false),
            "qué es Netflix Internacional")!!
        assertTrue(out.contains("por confirmar"))
        assertFalse(out.contains("\$18.000"))
    }
    @Test fun quoteToPaymentRequiresManualVerification(){
        val ctx:Context=RuntimeEnvironment.getApplication()
        val now=System.currentTimeMillis()
        val phone="cliente-v360-"+now
        val quote=NativeAutoReplyEngine.Decision(
            text="💚 MÁS AHORRO\nTOTAL DEL COMBO: \$26.000",
            business="movieplay",reason="Cotización Más Ahorro",routeSource="combo_sale")
        Sales360Store.observe(ctx,"business",phone,quote,now,"submitted_unverified")
        var lead=Sales360Store.read(ctx).let{a->(0 until a.length())
            .map{a.getJSONObject(it)}.first{it.optString("contact")==phone}}
        assertEquals("quoted",lead.optString("stage"))
        assertEquals(26000L,lead.optLong("total"))
        assertFalse(lead.optBoolean("confirmedByHuman",false))
        val bank=NativeAutoReplyEngine.Decision(
            text="Cuenta Nequi: ...",business="movieplay",
            routeSource="payment_specific")
        Sales360Store.observe(ctx,"business",phone,bank,now+1,"submitted_unverified")
        Sales360Store.evidence(ctx,"business",phone,now+2)
        lead=Sales360Store.read(ctx).let{a->(0 until a.length())
            .map{a.getJSONObject(it)}.first{it.optString("contact")==phone}}
        assertEquals("review",lead.optString("stage"))
        assertFalse(lead.optBoolean("confirmedByHuman",false))
        assertTrue(Sales360Store.update(ctx,lead.getString("id"),"confirmed"))
        lead=Sales360Store.read(ctx).let{a->(0 until a.length())
            .map{a.getJSONObject(it)}.first{it.optString("contact")==phone}}
        assertEquals("confirmed",lead.optString("stage"))
        assertTrue(lead.optBoolean("confirmedByHuman"))
        Sales360Store.observe(ctx,"business",phone,quote,now+3,"submitted_unverified")
        assertEquals("confirmed",Sales360Store.read(ctx).let{a->(0 until a.length())
            .map{a.getJSONObject(it)}.first{it.optString("contact")==phone}
            .optString("stage")})
    }
    @Test fun failsClosedForUnrelatedBusinessesAndCanDelete(){
        val ctx:Context=RuntimeEnvironment.getApplication()
        val now=System.currentTimeMillis()
        val who="tresm-unknown-"+now
        Sales360Store.observe(ctx,"business",who,
            NativeAutoReplyEngine.Decision(text="Precio: \$15.000",
                business="tresm",reason="Catálogo aprobado"),now,"submitted_unverified")
        assertFalse((0 until Sales360Store.read(ctx).length()).any{
            Sales360Store.read(ctx).getJSONObject(it).optString("contact")==who})
        assertFalse(Sales360Store.update(ctx,"badid","confirmed"))
    }
}
''',encoding="utf-8")
tests=root/"tests"
(tests/"ventas360_072.test.cjs").write_text(r''' 'use strict';
const assert=require('node:assert/strict');
const N=require('../web/netflix-international.js');
const S=require('../web/sales-360.js');
const fs=require('node:fs');
const cat=[
 {assistant:'movieplay',name:'Netflix Premium 4K',duration:'30 días',price:18000,active:true},
 {assistant:'movieplay',name:'Netflix Internacional',duration:'30 días',price:18000,active:true}
];
for(const question of [
  'qué es eso de netflix internacional',
  '¿Qué diferencia hay entre Netflix normal y Netflix internacional?',
  'NETFLIX INTERNACIONAL qué significa',
  'Explícame Netflix Internacional'
])assert.match(N.answer(cat,question),/fuera de Colombia/);
assert.match(N.answer(cat,'Qué es Netflix Internacional'),/\$18\.000/);
assert.equal(N.answer(cat,'cuánto vale netflix internacional'),null);
assert.equal(N.answer(cat,'Quiero Netflix 30 días y Disney'),null);
assert.match(N.answer(cat.map(x=>x.name==='Netflix Internacional'?{...x,active:false}:x),
 'qué es netflix internacional'),/por confirmar/);
assert.doesNotMatch(N.answer(cat.map(x=>x.name==='Netflix Internacional'?{...x,active:false}:x),
 'qué es netflix internacional'),/\$18\.000/);
const leads=[
 {stage:'quoted',quote:'Combo',contact:'A'},
 {stage:'payment_requested',quote:'Combo',contact:'B'},
 {stage:'review',quote:'Combo',contact:'C'},
 {stage:'confirmed',quote:'Combo',contact:'D'},
 {stage:'opt_out',quote:'Combo',contact:'E'}
];
assert.deepEqual(S.metrics(leads),{quoted:5,payment:2,review:1,confirmed:1,pending:3});
assert.match(S.followup(leads[0]),/cotización/);
assert.match(S.followup(leads[1]),/medios de pago/);
assert.equal(S.followup(leads[2]),null);
assert.equal(S.followup(leads[4]),null);
const html=fs.readFileSync(require('node:path').join(__dirname,'../web/index.html'),'utf8');
const app=fs.readFileSync(require('node:path').join(__dirname,'../web/app.js'),'utf8');
assert.match(html,/data-route="ventas360"/);
assert.match(html,/netflix-international.js/);
assert.match(html,/sales-360.js/);
assert.match(app,/setSales360Status/);
assert.match(app,/netflixInternationalInfo/);
console.log('Ventas 360 + Netflix Internacional: 19 aserciones principales correctas.');
''',encoding="utf-8")
gradle=root/"android/app/build.gradle.kts"
s=gradle.read_text(encoding="utf-8")
assert s.count('versionCode = 26')==1
assert s.count('versionName = "0.6.11"')==1
gradle.write_text(s.replace('versionCode = 26','versionCode = 27',1)
    .replace('versionName = "0.6.11"','versionName = "0.6.12"',1),encoding="utf-8")
p=root/"web/app.js"
s=p.read_text(encoding="utf-8").replace("/* AutoResponder Pro v0.6.11","/* AutoResponder Pro v0.6.12",1)
p.write_text(s,encoding="utf-8")
(root/"android/app/src/main/assets/app.js").write_text(s,encoding="utf-8")
print("0.6.12: web and Kotlin regression tests, updated versionCode 27, preserved app ID.")
