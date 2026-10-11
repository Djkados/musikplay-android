from pathlib import Path
root=Path("source/autoresponder-pro")
p=root/"android/app/src/test/java/com/autoresponder/pro/NativeAutoReplyEngineTest.kt"
s=p.read_text()
assert s.rstrip().endswith("}")
s=s.rstrip()[:-1]+'''
    @Test fun dualWhatsAppClarificationRemembersBusinessAndAcceptsQuickChoice() {
        val c=config();c.getJSONObject("settings").put("requireAllowlist",false)
            .getJSONObject("autoReplies").put("normal",true)
        val t=clock("2026-10-10","19:00")
        val request=NativeAutoReplyEngine.decide(c,"business","Nuevo","Hola",t)
        assertEquals(true,request.needsChoice)
        assertEquals("clarify",request.routeSource)
        val food=NativeAutoReplyEngine.decide(c,"business","Nuevo","2",t,
            awaitingChoice=true)
        assertEquals("tresm",food.business)
        assertEquals("choice",food.routeSource)
        val movie=NativeAutoReplyEngine.decide(c,"normal","Guardado","1",t,
            awaitingChoice=true)
        assertEquals("movieplay",movie.business)
        assertEquals("choice",movie.routeSource)
        val neutral=NativeAutoReplyEngine.decide(c,"normal","Nuevo","2",t)
        assertEquals(true,neutral.needsChoice)
    }
    @Test fun businessContextHandlesFollowUpsAndCanSwitchWhenExplicit() {
        val c=config();c.getJSONObject("settings").put("requireAllowlist",false)
        val t=clock("2026-10-10","19:00")
        val food=NativeAutoReplyEngine.decide(c,"business","Nuevo","precio",t,
            rememberedBusiness="tresm")
        assertEquals("tresm",food.business)
        assertEquals("context",food.routeSource)
        assertEquals(true,food.text?.contains("lastresm.netlify.app"))
        val movie=NativeAutoReplyEngine.decide(c,"business","Nuevo","Netflix",t,
            rememberedBusiness="tresm")
        assertEquals("movieplay",movie.business)
        assertEquals("detected",movie.routeSource)
        assertEquals("Precios MoviePlay",movie.text)
        val switched=NativeAutoReplyEngine.decide(c,"normal","Nuevo","hamburguesa",t,
            rememberedBusiness="movieplay")
        assertEquals("tresm",switched.business)
        assertEquals("Menú Las Tres M",switched.text)
        val ambiguous=NativeAutoReplyEngine.decide(c,"business","Nuevo",
            "Netflix y hamburguesa",t,rememberedBusiness="movieplay")
        assertEquals(true,ambiguous.needsChoice)
        assertNull(ambiguous.business)
    }
    @Test fun contextIsStillBoundByBusinessHoursAndExplicitExceptions() {
        val c=config();c.getJSONObject("settings").put("requireAllowlist",false)
        val night=clock("2026-10-10","23:18")
        assertEquals("Ventas cerradas",
            NativeAutoReplyEngine.decide(c,"business","Nuevo","precio",night,
                rememberedBusiness="movieplay").text)
        assertEquals("Pedidos cerrados",
            NativeAutoReplyEngine.decide(c,"business","Nuevo","precio",night,
                rememberedBusiness="tresm").text)
        c.getJSONArray("exceptions").put(JSONObject().put("channel","business")
            .put("contact","Nuevo").put("assistant","tresm"))
        val fixed=NativeAutoReplyEngine.decide(c,"business","Nuevo","Netflix",night,
            rememberedBusiness="movieplay")
        assertEquals("tresm",fixed.business)
        assertEquals("exception",fixed.routeSource)
    }
    @Test fun blockedSensitiveAndOwnMessageRemainExcludedWithBusinessContext() {
        val c=config();c.getJSONObject("settings").put("requireAllowlist",false)
        val t=clock("2026-10-10","19:00")
        assertNull(NativeAutoReplyEngine.decide(c,"business","Tú","Netflix",t,
            rememberedBusiness="movieplay").text)
        assertNull(NativeAutoReplyEngine.decide(c,"business","Cliente","OTP 101999",t,
            rememberedBusiness="movieplay").text)
        c.getJSONArray("blocked").put(JSONObject().put("channel","business")
            .put("contact","Cliente"))
        assertNull(NativeAutoReplyEngine.decide(c,"business","Cliente","Netflix",t,
            rememberedBusiness="movieplay").text)
    }
}
'''
p.write_text(s)
js=root/"tests/schedules.test.cjs"
s=js.read_text()
old="// End-to-end with rules + app safety gate + hours at specified Bogota time."
assert old in s
extra="""// Context is scoped to a particular WhatsApp and must not override mixed intent.
assert.equal(engine.resolveAssignment('normal','Nuev@','2',channels,[],{awaitingChoice:true}).assistant,'tresm');
assert.equal(engine.resolveAssignment('business','Cliente','1',channels,[],{awaitingChoice:true}).assistant,'movieplay');
assert.equal(engine.resolveAssignment('business','Cliente','precio',channels,[],{business:'movieplay'}).assistant,'movieplay');
assert.equal(engine.resolveAssignment('normal','Cliente','hamburguesa',channels,[],{business:'movieplay'}).assistant,'tresm');
assert.equal(engine.resolveAssignment('normal','Cliente','Netflix y hamburguesa',channels,[],{business:'movieplay'}).method,'clarify');
assert.equal(engine.resolveAssignment('business','Cliente','precio',channels,[]).method,'clarify');
// Per-contact manual override wins over the remembered assistant.
assert.equal(engine.resolveAssignment('business','Cliente','Netflix',channels,[{channel:'business',contact:'Cliente',assistant:'tresm'}],{business:'movieplay'}).assistant,'tresm');

"""
s=s.replace(old,extra+old,1)
js.write_text(s)
print("Android and JavaScript dual-business regression tests added")
