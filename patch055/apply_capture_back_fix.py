from pathlib import Path
import re
root = Path("source/autoresponder-pro/android/app/src/main/java/com/autoresponder/pro")
main = root/"MainActivity.kt"
s = main.read_text()
old = '''    @Deprecated("Uses legacy Android back navigation")
    override fun onBackPressed() {
        if (webView.canGoBack()) webView.goBack() else super.onBackPressed()
    }'''
new = '''    private var lastBackAt = 0L

    @Deprecated("Uses legacy Android back navigation")
    override fun onBackPressed() {
        // The dashboard is a single-page app, so WebView history is usually empty.
        // Dismiss visible overlays before navigating or considering an exit.
        webView.evaluateJavascript("""
            (function() {
              const visible = el => !!(el && el.getClientRects().length &&
                getComputedStyle(el).visibility !== 'hidden');
              const overlay = document.querySelector(
                '[role="dialog"]:not([hidden]), dialog[open], .modal.show, .modal.open, .sidebar.open, .drawer.open, [aria-modal="true"]'
              );
              if (visible(overlay)) {
                const close = overlay.querySelector('[aria-label="Cerrar"], [aria-label="Close"], .close, .btn-close, [data-close]');
                if (close) close.click();
                else document.dispatchEvent(new KeyboardEvent('keydown', {key:'Escape', bubbles:true}));
                return true;
              }
              document.dispatchEvent(new KeyboardEvent('keydown', {key:'Escape', bubbles:true}));
              return false;
            })();
        """.trimIndent()) { result ->
            if (result == "true") return@evaluateJavascript
            if (webView.canGoBack()) {
                webView.goBack()
            } else {
                val now = System.currentTimeMillis()
                if (now - lastBackAt < 2200L) {
                    lastBackAt = 0L
                    finish()
                } else {
                    lastBackAt = now
                    toast("Pulsa Atrás nuevamente para salir de AutoResponder Pro.")
                }
            }
        }
    }'''
assert old in s, "MainActivity back handler changed: inspect manually"
main.write_text(s.replace(old,new))
listener = root/"WhatsAppNotificationListener.kt"
s = listener.read_text()
old = '''        getSharedPreferences("listener_status", Context.MODE_PRIVATE).edit()
            .putString("lastChannel", channel).putString("lastReason", code)
            .putLong("lastEventAt", System.currentTimeMillis()).apply()'''
new = '''        val prefs = getSharedPreferences("listener_status", Context.MODE_PRIVATE)
        val previous = try { JSONArray(prefs.getString("recentEvents", "[]")) } catch (_: Exception) { JSONArray() }
        val events = JSONArray().put(JSONObject()
            .put("channel", channel).put("reason", code).put("at", System.currentTimeMillis()))
        for (i in 0 until minOf(previous.length(), 19)) events.put(previous.get(i))
        prefs.edit().putString("lastChannel", channel).putString("lastReason", code)
            .putString("recentEvents", events.toString())
            .putLong("lastEventAt", System.currentTimeMillis()).apply()'''
assert old in s
s=s.replace(old,new)
old = '''        if (notification.category != Notification.CATEGORY_MESSAGE) {
            trace(channel, "not_message_category"); return
        }
        val extras = notification.extras
        // Fail closed on group or summary notifications.
        if (extras.getBoolean("android.isGroupConversation", false)) {
            trace(channel, "group_skipped"); return
        }
        if (!extras.getCharSequence(Notification.EXTRA_CONVERSATION_TITLE).isNullOrBlank()) {
            trace(channel, "group_skipped"); return
        }
        val contact = extras.getCharSequence(Notification.EXTRA_TITLE)?.toString()?.trim().orEmpty()
        val message = extras.getCharSequence(Notification.EXTRA_TEXT)?.toString()?.trim().orEmpty()'''
new = '''        val extras = notification.extras
        val messages = extras.getParcelableArray(Notification.EXTRA_MESSAGES)
            ?.mapNotNull { it as? Bundle }.orEmpty()
        // WhatsApp may omit CATEGORY_MESSAGE for valid MessagingStyle notifications.
        if (notification.category != Notification.CATEGORY_MESSAGE && messages.isEmpty()) {
            trace(channel, "not_message_category"); return
        }
        // A conversation title alone does not prove the notification is a group.
        if (extras.getBoolean("android.isGroupConversation", false)) {
            trace(channel, "group_skipped"); return
        }
        val latest = messages.lastOrNull { !it.getCharSequence("text").isNullOrBlank() }
        val structuredSender = latest?.getCharSequence("sender")?.toString()?.trim().orEmpty()
        val title = extras.getCharSequence(Notification.EXTRA_TITLE)?.toString()?.trim().orEmpty()
        val contact = structuredSender.ifBlank { title }
        val message = latest?.getCharSequence("text")?.toString()?.trim()
            ?: extras.getCharSequence(Notification.EXTRA_TEXT)?.toString()?.trim().orEmpty()'''
assert old in s, "listener extraction changed: inspect manually"
s=s.replace(old,new)
# A renewed WhatsApp notification can carry an older MessagingStyle message.
# Check that message timestamp rather than only the notification posting time.
old = '''        if (System.currentTimeMillis() - sbn.postTime > 2 * 60 * 1000L) {
            trace(channel, "stale_skipped"); return
        }'''
new = '''        val messageTime = latest?.getLong("time", sbn.postTime) ?: sbn.postTime
        if (messageTime <= 0L || kotlin.math.abs(System.currentTimeMillis() - messageTime) > 2 * 60 * 1000L) {
            trace(channel, "stale_skipped"); return
        }'''
assert old in s, "stale logic not found"
s = s.replace(old, new)
listener.write_text(s)
# Increment the installed app version so Android identifies this as v0.5.5.
build = Path("source/autoresponder-pro/android/app/build.gradle.kts")
gradle_text = build.read_text()
assert 'versionCode = 9' in gradle_text and 'versionName = "0.5.4"' in gradle_text
build.write_text(gradle_text.replace('versionCode = 9','versionCode = 10').replace('versionName = "0.5.4"','versionName = "0.5.5"'))
print("Patched v0.5.5 Android back, capture, timestamp, and version")
