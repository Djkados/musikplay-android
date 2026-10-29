from pathlib import Path
root=Path("source/autoresponder-pro")
native=root/"android/app/src/main/java/com/autoresponder/pro"
web=root/"web"
assets=root/"android/app/src/main/assets"
tests=root/"android/app/src/test/java/com/autoresponder/pro"
def change(path,old,new,label):
    s=path.read_text(encoding="utf-8")
    assert s.count(old)==1,(label,s.count(old),str(path))
    path.write_text(s.replace(old,new,1),encoding="utf-8")

guide=native/"GuidedAssistant.kt"
change(guide,'''        if(business=="movieplay"){
            val intro=quote?.text ?: "$header\\n\\n🛒 *Solicitud de compra*"''',
'''        if(business=="movieplay"){
            // Let the customer pick the Disney tier once, without printing all
            // Disney prices or appending a second confusing question.
            if(quote!=null && DisneyPlanScope.needsClarification(business,message,
                    LocalCatalog.items(config,business)))
                return Guidance(quote.text,"Compra guiada; pendiente de confirmación",
                    quote.imageTag)
            val intro=quote?.text ?: "$header\\n\\n🛒 *Solicitud de compra*"''',"Guide Disney clarity")
change(guide,'''                "¿Te paso los medios de pago? 😊\\nAntes de entregarlo verifico disponibilidad y pago."''',
'''                "Antes de entregarlo verifico disponibilidad y pago."''',
"Guide avoid repeated checkout")

flow=native/"ConversationFlow.kt"
change(flow,'''        if(business=="movieplay"){
            val requested=duration(n)''',
'''        if(business=="movieplay"){
            // The customer can answer just "sin deportes" / "Premium" to a
            // previous generic "Disney" question, no need to repeat the brand.
            if(stage=="plan" && DisneyPlanScope.isDisney(original)){
                val qualifier=DisneyPlanScope.followUpVariant(message)
                if(qualifier!=null){
                    val candidates=group.filter{
                        DisneyPlanScope.isDisney(it) &&
                        Regex("\\\\b"+qualifier+"\\\\b").containsMatchIn(
                            norm(it.optString("name")))
                    }
                    val item=candidates.singleOrNull()
                    if(item==null||!item.optBoolean("active",false)||
                        price(item,today)<=0L)
                        return Response("🎬 *MOVIEPLAY*\\n\\nEse plan de Disney no aparece "+
                            "disponible. ¿Quieres consultar otra modalidad?",
                            productId,"plan",reason="Plan Disney no disponible")
                    return Response("🎬 *MOVIEPLAY*\\n\\n📺 *"+
                        item.optString("name")+"* · "+item.optString("duration")+
                        "\\n💵 *Precio:* "+money(price(item,today))+
                        "\\n\\n¿Te paso los medios de pago? 😊\\n"+
                        "La disponibilidad y el pago se verifican antes de la entrega.",
                        item.optString("id"),"payment_offer")
                }
            }
            val requested=duration(n)''',"Native follow-up exact Disney")
app=web/"app.js"
change(app,'''    if(quote && !active)return {reply:intro+"\\n\\nEste producto figura temporalmente no disponible. ¿Quieres consultar otra opción?",image:null};
    const steps=business==="movieplay"?''',
'''    if(quote && !active)return {reply:intro+"\\n\\nEste producto figura temporalmente no disponible. ¿Quieres consultar otra opción?",image:null};
    if(business==="movieplay" && quote && (
        window.DisneyPlanScope?.needsClarification(business,text,state.catalog) ||
        quote?.reply?.includes("¿Te paso los medios de pago?")))
      return {reply:intro+(quote.reply.includes("¿Te paso los medios de pago?")?
        "\\n\\nAntes de entregar verificamos disponibilidad y pago.":""),image:null};
    const steps=business==="movieplay"?''',"Web guided single exact selected plan")
(assets/"app.js").write_text(app.read_text(encoding="utf-8"),encoding="utf-8")

(tests/"DisneyPlanPrecisionTest.kt").write_text(r'''package com.autoresponder.pro

import org.json.JSONArray
import org.json.JSONObject
import org.junit.Assert.*
import org.junit.Test
import java.time.LocalDate

class DisneyPlanPrecisionTest {
    private val today=LocalDate.parse("2026-10-29")
    private fun config():JSONObject {
        val rows=JSONArray()
        fun item(id:String,name:String,price:Long)=JSONObject().put("id",id)
            .put("assistant","movieplay").put("type","service")
            .put("name",name).put("keywords","disney,disney plus,"+
                name.lowercase().replace("+"," "))
            .put("duration","30 días").put("price",price).put("active",true)
        rows.put(item("dp","Disney+ Premium",19000L))
            .put(item("de","Disney+ Estándar",10000L))
            .put(item("db","Disney+ Básico",6000L))
            .put(JSONObject().put("id","mp").put("assistant","movieplay")
                .put("name","Max Premium").put("keywords","max,max premium")
                .put("duration","30 días").put("price",10000L).put("active",true))
        return JSONObject().put("catalog",rows)
    }
    @Test fun explicitPlanQuotesOnlyItsOwnPrice() {
        val config=config()
        for(text in listOf("Quiero Disney Premium","Disney+ Premium",
            "¿Cuánto vale Premium de Disney?","Disney con deportes")){
            val matches=LocalCatalog.matched(config,"movieplay",text)
            assertEquals(text,1,matches.size)
            assertEquals(text,"dp",matches.first().optString("id"))
            val reply=LocalCatalog.reply(config,"movieplay",text,today)!!.text
            assertTrue(reply.contains("Disney+ Premium"))
            assertTrue(reply.contains("\$19.000"))
            assertFalse(reply.contains("Disney+ Estándar"))
            assertFalse(reply.contains("Disney+ Básico"))
            assertFalse(reply.contains("\$10.000"))
            assertFalse(reply.contains("\$6.000"))
        }
        val saved=ConversationFlow.remember(config,"movieplay","Quiero Disney Premium",
            "Compra guiada; pendiente de confirmación")
        assertEquals("dp",saved!!.productId)
        assertEquals("payment_offer",saved.stage)
        val guided=GuidedAssistant.suggest(config,"movieplay","Quiero Disney Premium",today)!!
        assertEquals(1,"¿Te paso los medios de pago?".toRegex().findAll(guided.text).count())
        assertFalse(guided.text.contains("Disney+ Estándar"))
    }
    @Test fun standardAndBasicNeverIncludePremium() {
        for((query,id,price) in listOf(
            Triple("Disney Estándar","de","\$10.000"),
            Triple("Disney sin deportes","de","\$10.000"),
            Triple("Disney Básico","db","\$6.000"))){
            assertEquals(id,LocalCatalog.matched(config(),"movieplay",query).single().optString("id"))
            val text=LocalCatalog.reply(config(),"movieplay",query,today)!!.text
            assertTrue(text.contains(price))
            assertFalse(text.contains("Disney+ Premium"))
        }
    }
    @Test fun genericDisneyAsksAndRemembersFollowup() {
        val c=config()
        val reply=LocalCatalog.reply(c,"movieplay","Quiero Disney",today)!!.text
        assertTrue(reply.contains("con deportes"))
        assertFalse(reply.contains("\$19.000"))
        val memory=ConversationFlow.remember(c,"movieplay","Quiero Disney",
            "Compra guiada; pendiente de confirmación")!!
        assertEquals("plan",memory.stage)
        val next=ConversationFlow.followUp(c,"movieplay","sin deportes",
            memory.productId,memory.stage,0,today)!!
        assertEquals("de",next.productId)
        assertEquals("payment_offer",next.stage)
        assertTrue(next.text.contains("\$10.000"))
        assertFalse(next.text.contains("\$19.000"))
        val listing=LocalCatalog.reply(c,"movieplay","Qué planes de Disney tienes",today)!!.text
        assertTrue(listing.contains("Disney+ Premium"))
        assertTrue(listing.contains("Disney+ Estándar"))
        assertTrue(listing.contains("Disney+ Básico"))
    }
    @Test fun specificUnavailableVariantNeverSubstitutesOthers() {
        val c=config()
        c.getJSONArray("catalog").getJSONObject(0).put("active",false)
        val out=LocalCatalog.reply(c,"movieplay","Quiero Disney Premium",today)!!.text
        assertTrue(out.contains("NO DISPONIBLE"))
        assertFalse(out.contains("Disney+ Estándar"))
        assertFalse(out.contains("Disney+ Básico"))
        val wrong=LocalCatalog.reply(c,"movieplay","Disney Premium 60 días",today)!!.text
        assertTrue(wrong.contains("No encuentro la duración"))
        assertFalse(wrong.contains("\$19.000"))
    }
    @Test fun qualifierBelongingToMaxDoesNotSelectDisneyPremium() {
        assertNull(DisneyPlanScope.namedVariant("Disney y Max Premium"))
        assertEquals("premium",DisneyPlanScope.namedVariant("Disney Premium y Max"))
        assertTrue(DisneyPlanScope.needsClarification("movieplay","Disney",LocalCatalog.items(config(),"movieplay")))
        assertFalse(DisneyPlanScope.needsClarification("movieplay","Disney y Max Premium",LocalCatalog.items(config(),"movieplay")))
    }
}
''',encoding="utf-8")
(root/"tests/disney_precision_073.test.cjs").write_text(r''' 'use strict';
const assert=require('node:assert/strict');
const P=require('../web/disney-plan-scope.js');
const fs=require('node:fs');
const products=[
 {id:'dp',assistant:'movieplay',name:'Disney+ Premium',price:19000,duration:'30 días',active:true},
 {id:'de',assistant:'movieplay',name:'Disney+ Estándar',price:10000,duration:'30 días',active:true},
 {id:'db',assistant:'movieplay',name:'Disney+ Básico',price:6000,duration:'30 días',active:true},
 {id:'mp',assistant:'movieplay',name:'Max Premium',price:10000,duration:'30 días',active:true}
];
for(const [msg,id] of [
 ['Quiero Disney Premium','dp'],['Disney+ Premium','dp'],
 ['Premium de Disney','dp'],['Disney con deportes','dp'],
 ['Disney Estándar','de'],['Disney sin deportes','de'],['Disney Básico','db']
]){
 assert.equal(P.filter('movieplay',msg,products).filter(x=>x.name.includes('Disney')).length,1,msg);
 assert.equal(P.filter('movieplay',msg,products).filter(x=>x.name.includes('Disney'))[0].id,id,msg);
}
assert.equal(P.namedVariant('Disney y Max Premium'),null);
assert.equal(P.namedVariant('Disney Premium y Max'),'premium');
assert.ok(P.needsClarification('movieplay','Quiero Disney',products));
assert.ok(!P.needsClarification('movieplay','Disney y Max Premium',products));
assert.equal(P.filter('movieplay','Qué planes de Disney tienes',products).length,4);
const html=fs.readFileSync(require('node:path').join(__dirname,'../web/index.html'),'utf8');
const app=fs.readFileSync(require('node:path').join(__dirname,'../web/app.js'),'utf8');
assert.match(html,/disney-plan-scope\.js/);
assert.match(app,/DisneyPlanScope\?\.filter/);
assert.match(app,/No encuentro esa duración de Disney/);
console.log('Disney Premium: selección específica y clarificación comprobadas.');
''',encoding="utf-8")
print("Disney conversation follow-up, guided copy, and Kotlin/Node regressions are ready.")
