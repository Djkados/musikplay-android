from pathlib import Path

root=Path("source/autoresponder-pro")
native=root/"android/app/src/test/java/com/autoresponder/pro"

p=native/"PaymentRepliesTest.kt"
s=p.read_text(encoding="utf-8")
assert s.rstrip().endswith("}")
s=s.rstrip()[:-1]+r'''
    @Test fun bancolombiaWrittenByNameWorksExactlyLike2AfterThePaymentMenu() {
        val c=config()
        val variants=listOf("Bancolombia","bancolombia",
            "Banco Colombia","BANC OLOMBIA".replace(" ",""),
            "por Bancolombia","Bancolombia porfa","Banco Colombia!","bancolomvia")
        for(q in variants){
            val withMenu=PaymentReplies.reply(c,"movieplay",q,
                pendingMenu=true,casual=true)
            assertNotNull("Name must be enough: $q",withMenu)
            assertFalse("Do not re-send menu for $q",withMenu!!.isMenu)
            assertTrue("Use actual bank details for $q",
                withMenu.text.contains("912 752309 23"))
            assertTrue(withMenu.text.contains("@castano454"))
            assertFalse(withMenu.text.contains("@3045214937"))
            val withoutMenu=PaymentReplies.reply(c,"movieplay",q,
                pendingMenu=false,casual=true)
            assertNotNull("Name works even without a previous menu: $q",withoutMenu)
            assertTrue(withoutMenu!!.text.contains("912 752309 23"))
        }
        val number=PaymentReplies.reply(c,"movieplay","2",
            pendingMenu=true,casual=true)
        assertNotNull(number)
        assertTrue(number!!.choice)
        assertEquals(number.text,
            PaymentReplies.reply(c,"movieplay","Bancolombia",
                pendingMenu=true,casual=true)!!.text)
        assertNull(PaymentReplies.reply(c,"movieplay","2",
            pendingMenu=false,casual=true))
        assertNull(PaymentReplies.reply(c,"movieplay",
            "Ya te envié el comprobante Bancolombia",pendingMenu=true,casual=true))
    }
}
'''
# "BANC OLOMBIA" above joins to BANCOLOMBIA exactly.
p.write_text(s,encoding="utf-8")

p=native/"NativeAutoReplyEngineTest.kt"
s=p.read_text(encoding="utf-8")
assert s.rstrip().endswith("}")
s=s.rstrip()[:-1]+r'''
    @Test fun bankNameAfterPaymentMenuRoutesBeforeHumanPauseAndSellerSilence() {
        val c=config()
        c.getJSONObject("settings").put("requireAllowlist",false)
            .getJSONObject("autoReplies").put("normal",true)
        c.put("payments",JSONObject().put("movieplay",JSONObject()
            .put("holder","Titular prueba")
            .put("nequi",JSONObject().put("number","3001112222"))
            .put("bancolombia",JSONObject().put("number","123456789")
                .put("key","@llaveprueba"))
            .put("daviplata",JSONObject().put("number","3111111111"))))
        c.put("sellerContacts",JSONArray().put(JSONObject()
            .put("channel","both").put("contact","Vendedor de prueba")
            .put("assistant","movieplay")))
        val now=clock("2026-10-12","19:00")
        for(ch in listOf("business","normal")){
            for(handoff in listOf(false,true)){
                for(name in listOf("Bancolombia","Banco Colombia",
                    "por Bancolombia")){
                    val d=NativeAutoReplyEngine.decide(c,ch,
                        "Cliente nuevo",name,now,
                        paymentMenuPending=true,humanHandoff=handoff)
                    assertNotNull(d.text)
                    assertEquals("payment_specific",d.routeSource)
                    assertFalse(d.paymentMenu)
                    assertTrue(d.text!!.contains("123456789"))
                    assertFalse(d.text!!.contains("3001112222"))
                }
                val seller=NativeAutoReplyEngine.decide(c,ch,
                    "Vendedor de prueba","Bancolombia",now,
                    paymentMenuPending=true,humanHandoff=handoff)
                assertEquals("payment_specific",seller.routeSource)
                assertTrue(seller.text!!.contains("123456789"))
                val n=NativeAutoReplyEngine.decide(c,ch,
                    "Cliente nuevo","2",now,paymentMenuPending=true,
                    humanHandoff=handoff)
                assertEquals("payment_choice",n.routeSource)
                assertTrue(n.text!!.contains("123456789"))
            }
        }
    }
}
'''
p.write_text(s,encoding="utf-8")

p=native/"NotificationCaptureRegressionTest.kt"
s=p.read_text(encoding="utf-8")
old='''"assistant_cadence", "routing_context"'''
assert s.count(old)==1
s=s.replace(old,'''"assistant_cadence", "routing_context", "payment_menu_context"''',1)
assert s.rstrip().endswith("}")
s=s.rstrip()[:-1]+r'''
    @Test fun bankNameAtNotificationLayerIsPreparedForReplyAfterMenu() {
        localConfig()
        val prefs=listener.getSharedPreferences("automation_rules",Context.MODE_PRIVATE)
        val cfg=org.json.JSONObject(prefs.getString("config","{}"))
        cfg.put("payments",org.json.JSONObject().put("movieplay",
            org.json.JSONObject()
                .put("holder","Titular prueba")
                .put("nequi",org.json.JSONObject().put("number","3001112222"))
                .put("bancolombia",org.json.JSONObject().put("number","123456789"))
                .put("daviplata",org.json.JSONObject().put("number","3111111111"))))
        prefs.edit().putString("config",cfg.toString()).commit()
        val id=hashForCadence("normal|Contacto de prueba")
        listener.getSharedPreferences("payment_menu_context",Context.MODE_PRIVATE)
            .edit().putLong(id,System.currentTimeMillis()-60_000L).commit()
        // The mock notification has no RemoteInput action: engine must
        // prepare bank text and clearly report the Android limitation,
        // not mark the request as unrecognized or throttled.
        post(notification(text="Bancolombia",age=10_000L),"com.whatsapp",id=56)
        val first=inbox().getJSONObject(0)
        assertEquals("payment_specific",first.getString("routeMethod"))
        assertTrue(first.getString("preparedText").contains("123456789"))
        assertEquals("no_quick_reply",first.getString("autoStatus"))
        assertTrue(first.getBoolean("manualPaymentReply"))

        post(notification(text="2",age=9_000L),"com.whatsapp",id=57)
        val second=inbox().getJSONObject(0)
        assertEquals("payment_choice",second.getString("routeMethod"))
        assertTrue(second.getString("preparedText").contains("123456789"))
        assertEquals("no_quick_reply",second.getString("autoStatus"))
    }

    @Test fun identicalBankWordsFromTwoSeparateMessagesAreNotBlockedForFiveMinutes() {
        localConfig()
        val cfg=org.json.JSONObject(listener.getSharedPreferences(
            "automation_rules",Context.MODE_PRIVATE).getString("config","{}"))
        cfg.put("payments",org.json.JSONObject().put("movieplay",
            org.json.JSONObject()
                .put("nequi",org.json.JSONObject().put("number","3001112222"))
                .put("bancolombia",org.json.JSONObject().put("number","123456789"))
                .put("daviplata",org.json.JSONObject().put("number","3111111111"))))
        listener.getSharedPreferences("automation_rules",Context.MODE_PRIVATE)
            .edit().putString("config",cfg.toString()).commit()
        post(notification(text="Bancolombia",age=50_000L),"com.whatsapp",id=61)
        val first=inbox().getJSONObject(0)
        assertEquals("payment_specific",first.getString("routeMethod"))
        // Simulate >4s passing between two distinct incoming messages,
        // without sleeping or repeating an old WhatsApp notification.
        val fastHash=hashForCadence("rapid_repeat|normal|Contacto de prueba|Bancolombia")
        listener.getSharedPreferences("recent_notifications",Context.MODE_PRIVATE)
            .edit().putLong(fastHash,System.currentTimeMillis()-6000L).commit()
        post(notification(text="Bancolombia",age=10_000L),"com.whatsapp",id=62)
        assertEquals(2,inbox().length())
        assertEquals("payment_specific",inbox().getJSONObject(0).getString("routeMethod"))
        assertEquals("no_quick_reply",inbox().getJSONObject(0).getString("autoStatus"))
        // Reposting the SAME exact WhatsApp message is still blocked.
        post(notification(text="Bancolombia",age=10_000L),"com.whatsapp",id=63)
        // New event uses a new time generated above, so this final post
        // should be suppressed by the 4-second rapid-copy gate.
        assertEquals(2,inbox().length())
    }
}
'''
p.write_text(s,encoding="utf-8")
print("Tests assert 2 and Bancolombia are equivalent; both channels, human pause, seller mode, notification intake, and safe repeat dedup.")
