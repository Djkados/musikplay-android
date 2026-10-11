from pathlib import Path
root=Path("source/autoresponder-pro")
native=root/"android/app/src/main/java/com/autoresponder/pro"
p=native/"NativeAutoReplyEngine.kt";s=p.read_text(encoding="utf-8")
def rep(old,new):
 global s
 assert s.count(old)==1,(old[:70],s.count(old))
 s=s.replace(old,new,1)
rep('val routeSource: String = "none", val needsChoice: Boolean = false)',
    'val routeSource: String = "none", val needsChoice: Boolean = false, val imageTag:String = "")')
rep('reason="Catálogo aprobado",routeSource=route.source)',
    'reason="Catálogo aprobado",routeSource=route.source,imageTag=it.imageTag)')
rep('return Decision(text=reply,business=business,department=unit,reason="Regla configurada",routeSource=route.source)',
    'return Decision(text=reply,business=business,department=unit,reason="Regla configurada",routeSource=route.source,imageTag=best.optString("imageTag",""))')
p.write_text(s,encoding="utf-8")
p=native/"WhatsAppNotificationListener.kt";s=p.read_text(encoding="utf-8")
def rep(old,new):
 global s
 assert s.count(old)==1,(old[:70],s.count(old))
 s=s.replace(old,new,1)
rep('''        if (isOwnNotification(title, structuredSender, latest, extras)) {
            trace(channel, "own_notification_skipped"); return
        }
        val echoedAt = getSharedPreferences("outgoing_echoes", Context.MODE_PRIVATE)
            .getLong(outgoingEchoKey(channel, message), 0L)''',
'''        val echoedAt = getSharedPreferences("outgoing_echoes", Context.MODE_PRIVATE)
            .getLong(outgoingEchoKey(channel, message), 0L)
        if (isOwnNotification(title, structuredSender, latest, extras)) {
            val now=System.currentTimeMillis()
            // Never treat our own automated answer as human intervention.
            val selfNames=setOf("tu","yo","you","me","myself")
            val alias=NativeAutoReplyEngine.normalize(title)
            if(alias.isNotBlank() && alias !in selfNames &&
                !alias.startsWith("whatsapp") &&
                (echoedAt<=0L || now-echoedAt !in 0L..120_000L)){
                val pauseKey=fingerprint("$channel|$title")
                val active=getSharedPreferences("human_pauses",Context.MODE_PRIVATE)
                active.edit().putLong(pauseKey,now+60*60*1000L).apply()
                val stats=getSharedPreferences("listener_status",Context.MODE_PRIVATE)
                stats.edit().putLong("humanPauses",stats.getLong("humanPauses",0L)+1L)
                    .putLong("lastHumanPauseAt",now).apply()
                trace(channel,"human_reply_paused")
            } else trace(channel,"own_notification_skipped")
            return
        }''')
rep('''                val decision=NativeAutoReplyEngine.decide(config,channel,contact,message,
                    rememberedBusiness=remembered,awaitingChoice=pending)''',
'''                val humanPauseUntil=getSharedPreferences("human_pauses",Context.MODE_PRIVATE)
                    .getLong(fingerprint("$channel|$contact"),0L)
                val decision=if(now<humanPauseUntil)
                    NativeAutoReplyEngine.Decision(reason="Atención humana pausada",
                        routeSource="human_pause")
                else NativeAutoReplyEngine.decide(config,channel,contact,message,
                    rememberedBusiness=remembered,awaitingChoice=pending)''')
rep('''                    .put("preparedText",decision.text ?: JSONObject.NULL)''',
'''                    .put("preparedText",decision.text ?: JSONObject.NULL)
                    .put("imageTag",decision.imageTag)''')
rep('''        trace(channel, incoming.optString("autoStatus", "captured"))
''',
'''        val report=getSharedPreferences("listener_status",Context.MODE_PRIVATE)
        val status=incoming.optString("autoStatus","captured")
        val key=when(status){
            "submitted_unverified"->"submittedCount"
            "no_quick_reply"->"noQuickReplyCount"
            "skipped"->"needsReviewCount"
            "failed","failed_permission","failed_canceled","failed_storage","failed_config"->"failedCount"
            else->null
        }
        if(key!=null)report.edit().putLong(key,report.getLong(key,0L)+1L).apply()
        if(status=="submitted_unverified" && incoming.optString("autoReason")=="Catálogo aprobado")
            report.edit().putLong("catalogReplies",report.getLong("catalogReplies",0L)+1L).apply()
        trace(channel,status)
''')
p.write_text(s,encoding="utf-8")
p=native/"MainActivity.kt";s=p.read_text(encoding="utf-8")
anchor='''                .put("rulesSynchronized", config.optInt("version") == 1)
                .toString()'''
assert s.count(anchor)==1
s=s.replace(anchor,'''                .put("rulesSynchronized", config.optInt("version") == 1)
                .put("submittedCount",status.getLong("submittedCount",0L))
                .put("noQuickReplyCount",status.getLong("noQuickReplyCount",0L))
                .put("needsReviewCount",status.getLong("needsReviewCount",0L))
                .put("failedCount",status.getLong("failedCount",0L))
                .put("catalogReplies",status.getLong("catalogReplies",0L))
                .put("humanPauses",status.getLong("humanPauses",0L))
                .put("lastHumanPauseAt",status.getLong("lastHumanPauseAt",0L))
                .toString()''',1)
p.write_text(s,encoding="utf-8")
print("Human takeover pauses (without own-auto loops), native catalog metadata and activity counters added")
