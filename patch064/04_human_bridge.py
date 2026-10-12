from pathlib import Path
root=Path("source/autoresponder-pro")
p=root/"android/app/src/main/java/com/autoresponder/pro/MainActivity.kt"
s=p.read_text(encoding="utf-8")
def rep(a,b):
 global s
 assert s.count(a)==1,(a[:100],s.count(a))
 s=s.replace(a,b,1)
rep('''import android.content.ComponentName''','''import android.content.ComponentName
import android.content.Context
import android.os.PowerManager
import java.security.MessageDigest''')
rep('''    inner class Bridge {''','''    private fun contactKey(channel:String,contact:String):String? {
        if(channel !in setOf("normal","business") ||
            contact.isBlank() || contact.length>140)return null
        return MessageDigest.getInstance("SHA-256")
            .digest("$channel|$contact".toByteArray())
            .take(12).joinToString(""){"%02x".format(it)}
    }

    inner class Bridge {''')
rep('''        @JavascriptInterface
        fun getInbox(): String = getSharedPreferences("private_inbox", MODE_PRIVATE)''',
'''        /** User-only controls. No outgoing message is sent or chat is opened. */
        @JavascriptInterface
        fun setConversationPause(channel:String,contact:String,minutes:Int):Boolean {
            val key=contactKey(channel,contact)?:return false
            if(minutes !in setOf(0,30,60,120,-1))return false
            val prefs=getSharedPreferences("human_pauses",Context.MODE_PRIVATE)
            val until=when(minutes){
                0->0L
                -1->Long.MAX_VALUE
                else->System.currentTimeMillis()+minutes*60_000L
            }
            if(minutes==0)prefs.edit().remove(key).commit()
            else prefs.edit().putLong(key,until).commit()
            val stats=getSharedPreferences("listener_status",Context.MODE_PRIVATE)
            stats.edit().putLong("lastManualControlAt",System.currentTimeMillis())
                .putLong("manualControlCount",stats.getLong("manualControlCount",0L)+1L)
                .apply()
            return true
        }

        @JavascriptInterface
        fun getConversationPause(channel:String,contact:String):String {
            val key=contactKey(channel,contact)?:return """{"active":false}"""
            val until=getSharedPreferences("human_pauses",Context.MODE_PRIVATE)
                .getLong(key,0L)
            val active=until>System.currentTimeMillis()
            return JSONObject().put("active",active)
                .put("until",if(active)until else 0L)
                .put("indefinite",until==Long.MAX_VALUE).toString()
        }

        @JavascriptInterface
        fun clearConversationMemory(channel:String,contact:String):Boolean {
            val key=contactKey(channel,contact)?:return false
            // Clear the business selector/product flow without unpausing an
            // intentionally suspended conversation.
            getSharedPreferences("routing_context",Context.MODE_PRIVATE)
                .edit().remove(key).commit()
            return true
        }

        @JavascriptInterface
        fun openBatteryOptimizationSettings() {
            runOnUiThread {
                try {startActivity(Intent(Settings.ACTION_IGNORE_BATTERY_OPTIMIZATION_SETTINGS))}
                catch (_:Exception) {
                    startActivity(Intent(Settings.ACTION_APPLICATION_DETAILS_SETTINGS,
                        Uri.parse("package:$packageName")))
                }
            }
        }

        @JavascriptInterface
        fun getInbox(): String = getSharedPreferences("private_inbox", MODE_PRIVATE)''')
rep('''                .put("lastHumanPauseAt",status.getLong("lastHumanPauseAt",0L))
                .toString()''',
'''                .put("lastHumanPauseAt",status.getLong("lastHumanPauseAt",0L))
                .put("lastSubmittedAt",status.getLong("lastSubmittedAt",0L))
                .put("lastManualControlAt",status.getLong("lastManualControlAt",0L))
                .put("manualControlCount",status.getLong("manualControlCount",0L))
                .put("appVersion",runCatching { packageManager.getPackageInfo(
                    packageName,0).versionName }.getOrNull())
                .put("batteryOptimizationIgnored",
                    (getSystemService(Context.POWER_SERVICE) as? PowerManager)
                        ?.isIgnoringBatteryOptimizations(packageName) ?: false)
                .toString()''')
p.write_text(s,encoding="utf-8")

p=root/"android/app/src/main/java/com/autoresponder/pro/WhatsAppNotificationListener.kt"
s=p.read_text(encoding="utf-8")
a='''        if(status=="submitted_unverified" && incoming.optString("autoReason")=="Catálogo aprobado")'''
b='''        if(status=="submitted_unverified")
            report.edit().putLong("lastSubmittedAt",now).apply()
        if(status=="submitted_unverified" && incoming.optString("autoReason")=="Catálogo aprobado")'''
assert s.count(a)==1
p.write_text(s.replace(a,b,1),encoding="utf-8")
# No new permissions: Android only opens the system optimization settings.
print("Add native pause 30/60/120/minutes/until-resumed, reset chat context and passive battery/connection diagnostics")
