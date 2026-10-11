package com.autoresponder.pro

import android.app.Notification
import android.content.Context
import android.os.UserHandle
import android.service.notification.StatusBarNotification
import androidx.core.app.NotificationCompat
import androidx.core.app.Person
import org.json.JSONArray
import org.junit.Assert.*
import org.junit.Before
import org.junit.Test
import org.junit.runner.RunWith
import org.robolectric.Robolectric
import org.robolectric.RobolectricTestRunner
import org.robolectric.annotation.Config

@RunWith(RobolectricTestRunner::class)
@Config(sdk = [28])
class NotificationCaptureRegressionTest {
    private lateinit var listener: WhatsAppNotificationListener
    @Before fun prepare() {
        listener = Robolectric.buildService(WhatsAppNotificationListener::class.java).create().get()
        for (key in listOf("capture_config", "private_inbox", "recent_notifications", "listener_status", "automation_rules", "reply_throttle")) {
            listener.getSharedPreferences(key, Context.MODE_PRIVATE).edit().clear().commit()
        }
        listener.getSharedPreferences("capture_config", Context.MODE_PRIVATE).edit()
            .putBoolean("normal", true).putBoolean("business", true).commit()
    }
    private fun notification(group: Boolean = false, text: String = "Precio Netflix", age: Long = 0): Notification {
        val sender = Person.Builder().setName("Contacto de prueba").setKey("remote-person").build()
        return NotificationCompat.Builder(listener, "messages")
            .setSmallIcon(android.R.drawable.ic_dialog_info)
            .setCategory(Notification.CATEGORY_MESSAGE)
            .setStyle(NotificationCompat.MessagingStyle(Person.Builder().setName("Yo").setKey("self-person").build())
                .setConversationTitle("Contacto de prueba").setGroupConversation(group)
                .addMessage(text, System.currentTimeMillis() - age, sender))
            .build()
    }
    private fun post(n: Notification, pkg: String = "com.whatsapp", id: Int = 1) {
        listener.onNotificationPosted(StatusBarNotification(pkg, pkg, id, "chat-$id", 10001, 0, n, UserHandle.of(0), null, System.currentTimeMillis()))
    }
    private fun inbox() = JSONArray(listener.getSharedPreferences("private_inbox", Context.MODE_PRIVATE).getString("items", "[]"))
    @Test fun individualWithConversationTitleIsNotAGroup() {
        post(notification())
        assertEquals("Explicit non-group conversation was incorrectly discarded", 1, inbox().length())
        assertEquals("Contacto de prueba", inbox().getJSONObject(0).getString("contact"))
    }
    @Test fun latestStructuredMessageWinsOverSummaryPresentation() {
        val n = notification()
        n.extras.putCharSequence(Notification.EXTRA_TITLE, "WhatsApp")
        n.extras.putCharSequence(Notification.EXTRA_TEXT, "2 mensajes nuevos")
        post(n)
        assertEquals(1, inbox().length())
        assertEquals("Precio Netflix", inbox().getJSONObject(0).getString("text"))
    }
    @Test fun messagingStyleDoesNotRequireOptionalCategory() {
        val n = notification(); n.category = null; post(n, "com.whatsapp.w4b")
        assertEquals(1, inbox().length())
        assertEquals("business", inbox().getJSONObject(0).getString("channel"))
    }
    @Test fun trueGroupsAndSummaryNotificationsRemainExcluded() {
        post(notification(group = true))
        val n = notification(); n.flags = n.flags or Notification.FLAG_GROUP_SUMMARY; post(n)
        assertEquals(0, inbox().length())
    }
    @Test fun sensitiveTextIsNeverRetained() {
        post(notification(text = "codigo de verificacion 123456"))
        assertEquals(0, inbox().length())
    }
    @Test fun disabledChannelsDoNotCapture() {
        listener.getSharedPreferences("capture_config", Context.MODE_PRIVATE).edit().putBoolean("normal", false).commit()
        post(notification()); assertEquals(0, inbox().length())
    }
    @Test fun duplicateStructuredMessagesAreNotInsertedTwice() {
        val n = notification(); post(n); post(n)
        assertEquals(1, inbox().length())
    }
    @Test fun refreshedNotificationDoesNotReplayOldMessage() {
        post(notification(age = 300_000)); assertEquals(0, inbox().length())
    }
    @Test fun summaryDoesNotEraseIndividualDiagnosticAndTraceContainsNoChat() {
        post(notification())
        val n = notification(); n.flags = n.flags or Notification.FLAG_GROUP_SUMMARY; post(n)
        val prefs = listener.getSharedPreferences("listener_status", Context.MODE_PRIVATE)
        val events = JSONArray(prefs.getString("recentEvents", "[]"))
        assertEquals(2, events.length())
        assertEquals("notification_summary", events.getJSONObject(0).getString("reason"))
        assertEquals("no_rules_config", events.getJSONObject(1).getString("reason"))
        assertFalse(events.toString().contains("Contacto de prueba"))
        assertFalse(events.toString().contains("Netflix"))
    }
}
