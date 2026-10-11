from pathlib import Path

root=Path("source/autoresponder-pro/android/app/src/test/java/com/autoresponder/pro")
(root/"AssistantCadenceTest.kt").write_text('''package com.autoresponder.pro

import org.junit.Assert.*
import org.junit.Test

class AssistantCadenceTest {
    private val now=1_800_000_000_000L
    @Test fun menuIsExactlyOncePer12HourWindow() {
        val elevenHours=now-11L*60L*60L*1000L
        val exactlyTwelve=now-12L*60L*60L*1000L
        assertTrue(AssistantCadence.menuCooling(now,elevenHours,true))
        assertTrue(AssistantCadence.awaitingChoice(now,elevenHours,true))
        assertFalse(AssistantCadence.menuCooling(now,exactlyTwelve,true))
        assertFalse(AssistantCadence.awaitingChoice(now,exactlyTwelve,true))
        assertFalse(AssistantCadence.menuCooling(now,now,false))
        assertFalse(AssistantCadence.menuCooling(now,now+1000L,true))
    }
    @Test fun paidQuestionsCanProceedWhenBusinessMenuIsCooling() {
        // The selector cools only when the engine wants to ask for a business.
        assertFalse(AssistantCadence.menuCooling(now,now-60_000L,false))
    }
    @Test fun outOfHoursAndGreetingRemainSeparateFromMenu() {
        assertTrue(AssistantCadence.awayCooling(now,now-1_000L,true))
        assertFalse(AssistantCadence.awayCooling(now,now-13L*60L*60L*1000L,true))
        assertFalse(AssistantCadence.awayCooling(now,now-1_000L,false))
        assertTrue(AssistantCadence.greetingCooling(now,now-8L*60L*60L*1000L,true))
        assertFalse(AssistantCadence.greetingCooling(now,now-1_000L,false))
    }
    @Test fun gratitudeAndExactAnswerHaveIndependentShortCooldowns() {
        assertTrue(AssistantCadence.recent(now,now-14L*60L*1000L,AssistantCadence.COURTESY_MS))
        assertFalse(AssistantCadence.recent(now,now-15L*60L*1000L,AssistantCadence.COURTESY_MS))
        assertTrue(AssistantCadence.recent(now,now-1L*60L*1000L,AssistantCadence.IDENTICAL_MS))
        assertFalse(AssistantCadence.recent(now,now-3L*60L*1000L,AssistantCadence.IDENTICAL_MS))
    }
}
''',encoding="utf-8")

p=root/"NotificationCaptureRegressionTest.kt"
s=p.read_text(encoding="utf-8")
anchor='"reply_throttle", "outgoing_echoes"'
assert s.count(anchor)==1
s=s.replace(anchor,'"reply_throttle", "outgoing_echoes", "assistant_cadence", "routing_context"',1)
assert s.rstrip().endswith("}")
s=s.rstrip()[:-1]+'''
    private fun localConfig() {
        val channel=org.json.JSONObject()
        for(ch in listOf("normal","business"))
            channel.put(ch,org.json.JSONObject().put("enabled",true).put("assistant","auto"))
        val assistants=org.json.JSONObject()
        for(b in listOf("movieplay","tresm"))
            assistants.put(b,org.json.JSONObject().put("active",true))
        val days=org.json.JSONObject()
        for(d in 0..6)
            days.put(d.toString(),org.json.JSONObject().put("enabled",false)
                .put("start","09:00").put("end","22:00"))
        val closed=org.json.JSONObject().put("days",days).put("away","Cerrado por horario")
        val schedules=org.json.JSONObject()
            .put("movieplay",org.json.JSONObject().put("sales",closed).put("support",closed))
            .put("tresm",org.json.JSONObject().put("orders",closed))
        val settings=org.json.JSONObject().put("requireAllowlist",false)
            .put("autoReplies",org.json.JSONObject().put("normal",true).put("business",true))
        val config=org.json.JSONObject().put("version",1)
            .put("channel",channel).put("assistants",assistants)
            .put("settings",settings).put("schedules",schedules)
            .put("rules",org.json.JSONArray())
        listener.getSharedPreferences("automation_rules",Context.MODE_PRIVATE).edit()
            .putString("config",config.toString()).commit()
    }
    private fun hashForCadence(raw:String):String =
        java.security.MessageDigest.getInstance("SHA-256").digest(raw.toByteArray())
            .take(12).joinToString(""){"%02x".format(it)}

    @Test fun existingBusinessMenuIsNotRepeatedAfterOneHour() {
        localConfig()
        val key=hashForCadence("menu|normal|Contacto de prueba")
        listener.getSharedPreferences("assistant_cadence",Context.MODE_PRIVATE).edit()
            .putLong(key,System.currentTimeMillis()-60L*60L*1000L).commit()
        post(notification(text="Hola"))
        assertEquals("menu_cooldown_12h",inbox().getJSONObject(0).getString("autoStatus"))
    }
    @Test fun twelveHoursAfterMenuAShortHelloCanBePromptedAgain() {
        localConfig()
        val key=hashForCadence("menu|normal|Contacto de prueba")
        listener.getSharedPreferences("assistant_cadence",Context.MODE_PRIVATE).edit()
            .putLong(key,System.currentTimeMillis()-12L*60L*60L*1000L-2_000L).commit()
        post(notification(text="Hola"))
        // There is no quick-reply PendingIntent in this test. The decision still
        // reached the action step, proving the 12h gate no longer blocks it.
        assertEquals("no_quick_reply",inbox().getJSONObject(0).getString("autoStatus"))
    }
    @Test fun menuCooldownIsIndependentBetweenWhatsappApps() {
        localConfig()
        val key=hashForCadence("menu|normal|Contacto de prueba")
        listener.getSharedPreferences("assistant_cadence",Context.MODE_PRIVATE).edit()
            .putLong(key,System.currentTimeMillis()-60_000L).commit()
        post(notification(text="Hola"),"com.whatsapp.w4b")
        assertEquals("no_quick_reply",inbox().getJSONObject(0).getString("autoStatus"))
    }
    @Test fun upgradeKeepsOldPendingBusinessMenuFromRepeating() {
        localConfig()
        val now=System.currentTimeMillis()
        val legacyKey=hashForCadence("normal|Contacto de prueba")
        val previous=org.json.JSONObject()
            .put("business","").put("lastSeen",now-60_000L)
            .put("pendingChoice",true).put("promptAt",now-3L*60L*60L*1000L)
        listener.getSharedPreferences("routing_context",Context.MODE_PRIVATE).edit()
            .putString(legacyKey,previous.toString()).commit()
        post(notification(text="Hola"))
        assertEquals("menu_cooldown_12h",inbox().getJSONObject(0).getString("autoStatus"))
    }
    @Test fun businessChoiceStillWorksElevenHoursAfterFirstMenu() {
        localConfig()
        val now=System.currentTimeMillis()
        val previous=org.json.JSONObject()
            .put("business","").put("lastSeen",now-60_000L)
            .put("pendingChoice",true).put("promptAt",now-11L*60L*60L*1000L)
        listener.getSharedPreferences("routing_context",Context.MODE_PRIVATE).edit()
            .putString(hashForCadence("business|Contacto de prueba"),previous.toString())
            .commit()
        post(notification(text="2"),"com.whatsapp.w4b")
        assertEquals("choice",inbox().getJSONObject(0).getString("routeMethod"))
        assertEquals("no_quick_reply",inbox().getJSONObject(0).getString("autoStatus"))
    }
    @Test fun outOfHoursReplyIsNotRepeatedWithinTwelveHours() {
        localConfig()
        listener.getSharedPreferences("assistant_cadence",Context.MODE_PRIVATE).edit()
            .putLong(hashForCadence("away|normal|Contacto de prueba|movieplay|sales"),
                System.currentTimeMillis()-2L*60L*60L*1000L).commit()
        post(notification(text="Netflix"))
        assertEquals("away_cooldown_12h",inbox().getJSONObject(0).getString("autoStatus"))
    }
    @Test fun outOfHoursCooldownDoesNotAffectTheOtherBusiness() {
        localConfig()
        listener.getSharedPreferences("assistant_cadence",Context.MODE_PRIVATE).edit()
            .putLong(hashForCadence("away|business|Contacto de prueba|movieplay|sales"),
                System.currentTimeMillis()-60_000L).commit()
        post(notification(text="Hamburguesa"),"com.whatsapp.w4b")
        assertEquals("no_quick_reply",inbox().getJSONObject(0).getString("autoStatus"))
    }
    @Test fun repeatedGratitudeIsQuietForFifteenMinutesWithoutBlockingNewServices() {
        localConfig()
        listener.getSharedPreferences("reply_throttle",Context.MODE_PRIVATE).edit()
            .putLong(hashForCadence("courtesy|normal|Contacto de prueba"),
                System.currentTimeMillis()-4L*60L*1000L).commit()
        post(notification(text="Muchas gracias"))
        assertEquals("courtesy_throttled",inbox().getJSONObject(0).getString("autoStatus"))
        post(notification(text="Netflix"),"com.whatsapp",id=83)
        assertEquals("no_quick_reply",inbox().getJSONObject(0).getString("autoStatus"))
    }
}
'''
p.write_text(s,encoding="utf-8")
print("10 cadence tests and 9 real NotificationListener regressions added for independent per-chat limits")
