from pathlib import Path

p=Path("source/autoresponder-pro/android/app/src/main/java/com/autoresponder/pro/WhatsAppNotificationListener.kt")
s=p.read_text(encoding="utf-8")
def change(old,new):
 global s
 assert s.count(old)==1,("Listener not as expected",old[:95],s.count(old))
 s=s.replace(old,new,1)

change('''            val alias=NativeAutoReplyEngine.normalize(title)
            if(alias.isNotBlank() && alias !in selfNames &&
                !alias.startsWith("whatsapp") &&
                (echoedAt<=0L || now-echoedAt !in 0L..120_000L)){
                val pauseKey=fingerprint("$channel|$title")
                val active=getSharedPreferences("human_pauses",Context.MODE_PRIVATE)
                active.edit().putLong(pauseKey,now+60*60*1000L).apply()''',
'''            val peer=title.takeUnless{NativeAutoReplyEngine.normalize(it) in selfNames}
                ?: extras.getCharSequence(Notification.EXTRA_CONVERSATION_TITLE)
                    ?.toString()?.trim().orEmpty()
            val alias=NativeAutoReplyEngine.normalize(peer)
            val status=getSharedPreferences("listener_status",Context.MODE_PRIVATE)
            val recentBot=status.getLong("lastBotSubmit_"+channel,0L)
            val likelyBot=echoedAt>0L && now-echoedAt in 0L..120_000L ||
                (recentBot>0L && now-recentBot in 0L..8_000L)
            if(alias.isNotBlank() && alias !in selfNames &&
                !alias.startsWith("whatsapp") && !likelyBot){
                val configJson=getSharedPreferences("automation_rules",Context.MODE_PRIVATE)
                    .getString("config","{}")
                val settings=try {JSONObject(configJson?:"{}").optJSONObject("settings")}
                    catch (_:Exception){null}
                val minutes=when(settings?.optInt("humanReplyPauseMinutes",180)){120->120;else->180}
                val pauseKey=fingerprint("$channel|$peer")
                val active=getSharedPreferences("human_pauses",Context.MODE_PRIVATE)
                active.edit().putLong(pauseKey,now+minutes*60L*1000L).apply()''')
change('''                val decision=if(now<humanPauseUntil)
                    NativeAutoReplyEngine.Decision(reason="Atención humana pausada",
                        routeSource="human_pause")
                else NativeAutoReplyEngine.decide(config,channel,contact,message,''',
'''                val sellerBusiness=NativeAutoReplyEngine.sellerBusiness(config,channel,contact)
                // Seller mode is permanently quiet except thanks/payments, even
                // while the chat is under the temporary human-takeover timer.
                val decision=if(now<humanPauseUntil && sellerBusiness==null)
                    NativeAutoReplyEngine.Decision(reason="Atención humana pausada",
                        routeSource="human_pause")
                else NativeAutoReplyEngine.decide(config,channel,contact,message,''')
change('''                                action.actionIntent.send(this,0,intent)''',
'''                                getSharedPreferences("listener_status",Context.MODE_PRIVATE)
                                    .edit().putLong("lastBotSubmit_"+channel,now).apply()
                                action.actionIntent.send(this,0,intent)''')
p.write_text(s,encoding="utf-8")
print("Manual replies trigger configurable 2/3-hour pause where notifications allow; sellers can still receive only gratitude or bank details. Own auto replies are ignored.")
