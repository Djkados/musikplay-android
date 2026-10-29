from pathlib import Path
root=Path("source/autoresponder-pro")
src=root/"android/app/src/main/java/com/autoresponder/pro"
def change(path,old,new,label):
 s=path.read_text(encoding="utf-8")
 assert s.count(old)==1,(label,s.count(old))
 path.write_text(s.replace(old,new,1),encoding="utf-8")

(src/"Sales360Store.kt").write_text(r'''package com.autoresponder.pro

import android.content.Context
import org.json.JSONArray
import org.json.JSONObject
import java.security.MessageDigest

/**
 * Local-only commercial opportunities. No chat transcripts, receipt images,
 * bank numbers or passwords are persisted. Never assumes a payment succeeded.
 * Delivery state is specifically "submitted_unverified", not delivered.
 */
internal object Sales360Store {
    private const val PREFS="sales_360_local"
    private const val KEY="leads"
    private const val LIMIT=120
    private const val TTL=30L*24L*60L*60L*1000L
    private val terminal=setOf("confirmed","lost","opt_out")
    private val valid=setOf("confirmed","lost","opt_out","reopen","delete")
    private fun identity(channel:String,contact:String):String =
        MessageDigest.getInstance("SHA-256")
            .digest((channel+"|"+contact.trim().lowercase()).toByteArray())
            .take(12).joinToString(""){"%02x".format(it)}
    private fun clean(raw:JSONArray,now:Long):JSONArray{
        val entries=(0 until raw.length()).mapNotNull{raw.optJSONObject(it)}
            .filter{it.optLong("updatedAt",0L) in (now-TTL)..(now+5L*60L*1000L)}
            .sortedByDescending{it.optLong("updatedAt",0L)}.take(LIMIT)
        return JSONArray().also { next-> entries.forEach{next.put(it)} }
    }
    private fun load(ctx:Context):JSONArray {
        val s=ctx.getSharedPreferences(PREFS,Context.MODE_PRIVATE)
            .getString(KEY,"[]")?:"[]"
        return runCatching{JSONArray(s)}.getOrDefault(JSONArray())
    }
    @Synchronized fun read(ctx:Context,now:Long=System.currentTimeMillis()):JSONArray {
        val result=clean(load(ctx),now)
        ctx.getSharedPreferences(PREFS,Context.MODE_PRIVATE)
            .edit().putString(KEY,result.toString()).apply()
        return result
    }
    private fun write(ctx:Context,rows:JSONArray){
        ctx.getSharedPreferences(PREFS,Context.MODE_PRIVATE)
            .edit().putString(KEY,rows.toString()).commit()
    }
    private fun find(rows:JSONArray,id:String):JSONObject?=(0 until rows.length())
        .mapNotNull{rows.optJSONObject(it)}.firstOrNull{it.optString("id")==id}
    private fun total(reply:String):Long =
        Regex("""TOTAL DEL COMBO:\s*\$([0-9.]+)""",RegexOption.IGNORE_CASE)
            .find(reply)?.groupValues?.get(1)?.replace(".","")?.toLongOrNull()?:0L

    @Synchronized fun observe(ctx:Context,channel:String,contact:String,
        decision:NativeAutoReplyEngine.Decision,now:Long,status:String){
        if(channel !in setOf("normal","business") || contact.isBlank() ||
            contact.length>140)return
        val route=decision.routeSource
        val quote=decision.business=="movieplay" &&
            (route=="combo_sale" || route=="guided" || route=="memory" ||
                decision.reason=="Catálogo aprobado") &&
            !decision.text.isNullOrBlank() &&
            decision.text.contains("$") &&
            !decision.paymentMenu
        val payment=route in setOf("payment_choice","payment_specific") ||
            decision.paymentMenu
        if(!quote && !payment)return
        val rows=read(ctx,now)
        val id=identity(channel,contact)
        val existing=find(rows,id)
        if(existing==null && !quote)return
        if(existing?.optString("stage") in terminal)return
        // Do not persist anything for bot responses blocked by safety or hours.
        val sent=status=="submitted_unverified"
        val stage=when {
            payment -> if(sent)"payment_requested" else "payment_prepared"
            quote -> if(sent)"quoted" else "quote_prepared"
            else -> return
        }
        val current=existing?:JSONObject().put("id",id)
            .put("channel",channel)
            .put("contact",contact.take(120))
            .put("createdAt",now)
            .put("stage","quote_prepared")
        // Preserve a previously submitted quote when a subsequent event fails.
        val oldStage=current.optString("stage")
        if(stage=="quote_prepared" && oldStage in setOf("quoted","payment_requested","payment_prepared"))return
        if(stage=="payment_prepared" && oldStage=="payment_requested")return
        current.put("stage",stage).put("updatedAt",now)
            .put("submittedUnverified",sent)
        if(quote){
            val safeReply=decision.text.orEmpty().take(1400)
            current.put("quote",safeReply)
                .put("total",total(safeReply))
                .put("quotedAt",now)
        }
        write(ctx,clean(JSONArray().put(current).also{a->
            for(i in 0 until rows.length()){
                val item=rows.optJSONObject(i)
                if(item!=null && item.optString("id")!=id)a.put(item)
            }
        },now))
    }
    @Synchronized fun evidence(ctx:Context,channel:String,contact:String,now:Long){
        val rows=read(ctx,now)
        val item=find(rows,identity(channel,contact))?:return
        if(item.optString("stage") in terminal)return
        item.put("stage","review").put("updatedAt",now)
            .put("needsManualPaymentCheck",true)
        write(ctx,clean(rows,now))
    }
    @Synchronized fun update(ctx:Context,id:String,action:String,
        now:Long=System.currentTimeMillis()):Boolean{
        if(action !in valid || !Regex("^[0-9a-f]{24}$").matches(id))return false
        val rows=read(ctx,now)
        val item=find(rows,id)?:return false
        if(action=="delete"){
            val next=JSONArray()
            for(i in 0 until rows.length()){
                val e=rows.optJSONObject(i)
                if(e!=null && e.optString("id")!=id)next.put(e)
            }
            write(ctx,next);return true
        }
        item.put("stage",if(action=="reopen")"quoted" else action)
            .put("updatedAt",now)
        if(action=="reopen")item.put("needsManualPaymentCheck",false)
        if(action=="confirmed")item.put("confirmedByHuman",true)
        write(ctx,clean(rows,now))
        return true
    }
}
''',encoding="utf-8")

listener=src/"WhatsAppNotificationListener.kt"
change(listener,'''            inbox.edit().putString("items",items.toString()).apply()
            val counters=getSharedPreferences("listener_status",Context.MODE_PRIVATE)''',
'''            inbox.edit().putString("items",items.toString()).apply()
            // An attachment is NOT a verified payment. Only an existing
            // commercial opportunity is moved to manual review.
            Sales360Store.evidence(this,channel,contact,now)
            val counters=getSharedPreferences("listener_status",Context.MODE_PRIVATE)''',
"manual receipt review tracking")
change(listener,'''                } else incoming.put("autoStatus","skipped")
            } catch (_: Exception) {
                incoming.put("autoStatus","failed_config")
            }
''',
'''                } else incoming.put("autoStatus","skipped")
                // Track real notification outcomes, not simulated or assumed
                // deliveries. Store no payment credentials and no media.
                Sales360Store.observe(this,channel,contact,decision,now,
                    incoming.optString("autoStatus","skipped"))
            } catch (_: Exception) {
                incoming.put("autoStatus","failed_config")
            }
''',"observe sales decision outcomes")

activity=src/"MainActivity.kt"
change(activity,'''        @JavascriptInterface
        fun getInbox(): String = getSharedPreferences("private_inbox", MODE_PRIVATE)
            .getString("items", "[]") ?: "[]"
''',
'''        @JavascriptInterface
        fun getInbox(): String = getSharedPreferences("private_inbox", MODE_PRIVATE)
            .getString("items", "[]") ?: "[]"

        /** Native, on-device lead list. Never synchronized to cloud/config backup. */
        @JavascriptInterface
        fun getSales360(): String = Sales360Store.read(this@MainActivity).toString()

        /** Payment confirmation ALWAYS requires an explicit human click. */
        @JavascriptInterface
        fun setSales360Status(id:String,action:String):Boolean =
            Sales360Store.update(this@MainActivity,id,action)
''',"native bridge leads and manual status")
print("0.6.12 native sales pipeline: quote/payment/review, manual confirmation, retention 30 days.")
