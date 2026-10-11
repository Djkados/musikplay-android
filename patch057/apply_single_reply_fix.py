from pathlib import Path

root = Path("source/autoresponder-pro")
listener = root / "android/app/src/main/java/com/autoresponder/pro/WhatsAppNotificationListener.kt"
s = listener.read_text(encoding="utf-8")

def replace_exact(original, new, label):
    global s
    matches=s.count(original)
    if matches != 1:
        raise AssertionError(f"{label}: expected once, got {matches}")
    s = s.replace(original,new)

replace_exact(
'''    private fun fingerprint(value: String): String = MessageDigest.getInstance("SHA-256")
        .digest(value.toByteArray()).take(12).joinToString("") { "%02x".format(it) }
''',
'''    private fun fingerprint(value: String): String = MessageDigest.getInstance("SHA-256")
        .digest(value.toByteArray()).take(12).joinToString("") { "%02x".format(it) }

    // Android/WhatsApp also publishes local notifications of our own sent messages.
    // These are not incoming customer messages and must never trigger a new reply.
    private fun isOwnNotification(title: String, sender: String, latest: Bundle?, extras: Bundle): Boolean {
        val selfNames = setOf("tu", "yo", "you", "me", "myself")
        if (NativeAutoReplyEngine.normalize(title).trimEnd(':') in selfNames ||
            NativeAutoReplyEngine.normalize(sender).trimEnd(':') in selfNames) return true

        val me = extras.getParcelable<android.app.Person>(Notification.EXTRA_MESSAGING_PERSON)
        val from = latest?.getParcelable<android.app.Person>("sender_person")
        if (me != null && from != null) {
            if (!me.key.isNullOrBlank() && me.key == from.key) return true
            if (!me.uri.isNullOrBlank() && me.uri == from.uri) return true
            if (!me.name.isNullOrBlank() && me.name.toString() == from.name?.toString()) return true
        }
        return false
    }

    // Extra protection for outgoing notifications that WhatsApp labels with a
    // different sender or omits Person metadata. We retain only a short hash.
    private fun outgoingEchoKey(channel: String, text: String): String =
        fingerprint("reply|$channel|$text")
''', "helper functions")

replace_exact(
'''        if (contact.isBlank() || message.isBlank() || contact.length > 140 || message.length > 1000) {
            trace(channel, "unreadable_message"); return
        }
''',
'''        if (isOwnNotification(title, structuredSender, latest, extras)) {
            trace(channel, "own_notification_skipped"); return
        }
        val echoedAt = getSharedPreferences("outgoing_echoes", Context.MODE_PRIVATE)
            .getLong(outgoingEchoKey(channel, message), 0L)
        if (echoedAt > 0L && System.currentTimeMillis() - echoedAt in 0L..120_000L) {
            trace(channel, "own_echo_skipped"); return
        }
        if (contact.isBlank() || message.isBlank() || contact.length > 140 || message.length > 1000) {
            trace(channel, "unreadable_message"); return
        }
''',"incoming guards")

replace_exact(
'''                            try {
                                val bundle = Bundle()
                                inputs.forEach { bundle.putCharSequence(it.resultKey,decision.text) }
                                val intent = Intent().addFlags(Intent.FLAG_RECEIVER_FOREGROUND)
                                RemoteInput.addResultsToIntent(inputs,intent,bundle)
                                action.actionIntent.send(this,0,intent)
''',
'''                            // Set echo suppression BEFORE notifying WhatsApp, because
                            // Android may synchronously publish the local sent notification.
                            val echoes = getSharedPreferences("outgoing_echoes", Context.MODE_PRIVATE)
                            val echoKey = outgoingEchoKey(channel, decision.text)
                            try {
                                val bundle = Bundle()
                                inputs.forEach { bundle.putCharSequence(it.resultKey,decision.text) }
                                val intent = Intent().addFlags(Intent.FLAG_RECEIVER_FOREGROUND)
                                RemoteInput.addResultsToIntent(inputs,intent,bundle)
                                echoes.edit().putLong(echoKey,now).commit()
                                action.actionIntent.send(this,0,intent)
''',"store echo before sending")

replace_exact(
'''                            } catch (_: PendingIntent.CanceledException) {
                                incoming.put("autoStatus","failed_canceled")
                            } catch (_: SecurityException) {
                                incoming.put("autoStatus","failed_permission")
                            } catch (_: Exception) {
                                incoming.put("autoStatus","failed")
                            }
''',
'''                            } catch (_: PendingIntent.CanceledException) {
                                echoes.edit().remove(echoKey).apply()
                                incoming.put("autoStatus","failed_canceled")
                            } catch (_: SecurityException) {
                                echoes.edit().remove(echoKey).apply()
                                incoming.put("autoStatus","failed_permission")
                            } catch (_: Exception) {
                                echoes.edit().remove(echoKey).apply()
                                incoming.put("autoStatus","failed")
                            }
''',"cleanup failed send")
listener.write_text(s,encoding="utf-8")

engine = root / "android/app/src/main/java/com/autoresponder/pro/NativeAutoReplyEngine.kt"
s=engine.read_text(encoding="utf-8")
old='''        val c=contact.trim(); val m=message.trim()
        if(c.isEmpty() || c.length>140 || m.length !in 1..1000) return Decision(reason="Datos de notificación no confiables")'''
new='''        val c=contact.trim(); val m=message.trim()
        // Defense in depth: never create auto-replies for local outgoing messages.
        if(normalize(c) in setOf("tu","yo","you","me","myself"))
            return Decision(reason="Mensaje propio: no responder")
        if(c.isEmpty() || c.length>140 || m.length !in 1..1000) return Decision(reason="Datos de notificación no confiables")'''
assert s.count(old)==1
engine.write_text(s.replace(old,new),encoding="utf-8")

tests=root/"android/app/src/test/java/com/autoresponder/pro/NotificationCaptureRegressionTest.kt"
t=tests.read_text(encoding="utf-8")
old='''"automation_rules", "reply_throttle"'''
assert old in t
t=t.replace(old,'''"automation_rules", "reply_throttle", "outgoing_echoes"''')
assert t.rstrip().endswith("}")
t=t.rstrip()[:-1]+'''
    private fun ownNotification(name: String): Notification {
        val self = Person.Builder().setName(name).setKey("self-person").build()
        return NotificationCompat.Builder(listener,"messages")
            .setSmallIcon(android.R.drawable.ic_dialog_info)
            .setCategory(Notification.CATEGORY_MESSAGE)
            .setContentTitle(name)
            .setStyle(NotificationCompat.MessagingStyle(self)
                .addMessage("¡Hola! Gracias por escribir a MoviePlay.", System.currentTimeMillis(), self))
            .build()
    }

    @Test fun sentMessagesWithTuSenderAreNotRecapturedOrReplied() {
        post(ownNotification("Tú"), "com.whatsapp.w4b")
        assertEquals(0,inbox().length())
        val status = listener.getSharedPreferences("listener_status",Context.MODE_PRIVATE)
        assertEquals("own_notification_skipped",status.getString("lastReason",""))
    }

    @Test fun selfMessagingPersonMustNotBeHandledAsAnIncomingCustomer() {
        post(ownNotification("Agente"))
        assertEquals(0,inbox().length())
    }

    @Test fun outgoingEchoFingerprintPreventsLoopEvenWithAlternateSenderName() {
        val reply = "¡Hola! Gracias por escribir a MoviePlay."
        val key=java.security.MessageDigest.getInstance("SHA-256")
            .digest("reply|business|$reply".toByteArray()).take(12)
            .joinToString("") { "%02x".format(it) }
        listener.getSharedPreferences("outgoing_echoes",Context.MODE_PRIVATE)
            .edit().putLong(key,System.currentTimeMillis()).commit()
        post(notification(text=reply),"com.whatsapp.w4b")
        assertEquals(0,inbox().length())
        assertEquals("own_echo_skipped", listener.getSharedPreferences("listener_status",Context.MODE_PRIVATE)
            .getString("lastReason",""))
    }

    @Test fun ordinaryCustomerStillEntersInboxAfterOwnSentNotification() {
        post(ownNotification("Tú"),"com.whatsapp.w4b")
        post(notification(text="Netflix por 30 días"),"com.whatsapp.w4b",id=3)
        assertEquals(1,inbox().length())
        assertEquals("Netflix por 30 días",inbox().getJSONObject(0).getString("text"))
    }

    @Test fun channelHashesAreIndependent() {
        val reply="Mensaje de prueba"
        val key=java.security.MessageDigest.getInstance("SHA-256")
            .digest("reply|business|$reply".toByteArray()).take(12)
            .joinToString("") { "%02x".format(it) }
        listener.getSharedPreferences("outgoing_echoes",Context.MODE_PRIVATE)
            .edit().putLong(key,System.currentTimeMillis()).commit()
        post(notification(text=reply),"com.whatsapp",id=4)
        assertEquals(1,inbox().length())
    }
}
'''
tests.write_text(t,encoding="utf-8")

nativeTest=root/"android/app/src/test/java/com/autoresponder/pro/NativeAutoReplyEngineTest.kt"
s=nativeTest.read_text(encoding="utf-8")
assert s.rstrip().endswith("}")
s=s.rstrip()[:-1]+'''
    @Test fun localOutgoingSenderNeverTriggersAnswer() {
        val c=config()
        c.getJSONObject("settings").put("requireAllowlist",false)
        val at=clock("2026-10-10","23:18")
        assertNull(NativeAutoReplyEngine.decide(c,"business","Tú",
            "¡Hola! Gracias por escribir a MoviePlay.",at).text)
        assertNull(NativeAutoReplyEngine.decide(c,"normal","Yo",
            "¡Hola! Gracias por escribir a MoviePlay.",at).text)
    }
}
'''
nativeTest.write_text(s,encoding="utf-8")

build=root/"android/app/build.gradle.kts"
s=build.read_text(encoding="utf-8")
assert 'versionCode = 11' in s and 'versionName = "0.5.6"' in s
build.write_text(s.replace('versionCode = 11','versionCode = 12')
                  .replace('versionName = "0.5.6"','versionName = "0.5.7"'),encoding="utf-8")
print("AutoResponder 0.5.7: own message and echo loop protection applied")
