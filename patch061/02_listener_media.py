from pathlib import Path
p=Path("source/autoresponder-pro/android/app/src/main/java/com/autoresponder/pro/WhatsAppNotificationListener.kt")
s=p.read_text(encoding="utf-8")
a='''        val latest = messages.lastOrNull { !it.getCharSequence("text").isNullOrBlank() }'''
b='''        // Never fall back to an earlier text when the newest message is media.
        val latest = messages.lastOrNull()'''
assert s.count(a)==1
s=s.replace(a,b,1)
a='''        // Prevent retaining messages that may contain secrets or authentication codes.
        val normalized = NativeAutoReplyEngine.normalize(message)'''
b='''        // A payment image may include a perfectly readable caption. Never
        // interpret that caption as a fresh text request for payment details.
        val unsafeIncoming=IncomingSafety.blockReason(extras,latest,message)
        if(unsafeIncoming!=null) {
            val now=System.currentTimeMillis()
            val seen=getSharedPreferences("recent_notifications",Context.MODE_PRIVATE)
            val safeKey=fingerprint("review|$channel|$contact|$messageTime|$unsafeIncoming")
            if(now-seen.getLong(safeKey,0L)<5L*60L*1000L) {
                trace(channel,"duplicate_review_skipped");return
            }
            seen.edit().putLong(safeKey,now).apply()
            val inbox=getSharedPreferences("private_inbox",Context.MODE_PRIVATE)
            val before=try {JSONArray(inbox.getString("items","[]"))} catch (_:Exception){JSONArray()}
            // Do not persist OCR, sensitive captions or document bytes.
            val item=JSONObject().put("id",fingerprint("$safeKey|$now"))
                .put("channel",channel).put("contact",contact).put("time",now)
                .put("text","📎 Archivo o comprobante recibido; revisar en WhatsApp")
                .put("autoStatus","manual_review")
                .put("autoReason",if(unsafeIncoming=="adjunto_revision_manual")
                    "Adjunto con o sin texto: revisión humana, sin respuesta automática"
                    else "Pago o comprobante reportado: verificar manualmente")
                .put("hasAttachment",unsafeIncoming=="adjunto_revision_manual")
                .put("learnEligible",false)
            val items=JSONArray().put(item)
            for(i in 0 until minOf(49,before.length()))items.put(before.get(i))
            inbox.edit().putString("items",items.toString()).apply()
            val counters=getSharedPreferences("listener_status",Context.MODE_PRIVATE)
            counters.edit().putLong("needsReviewCount",
                counters.getLong("needsReviewCount",0L)+1L).apply()
            trace(channel,unsafeIncoming)
            return
        }
        // Prevent retaining messages that may contain secrets or authentication codes.
        val normalized = NativeAutoReplyEngine.normalize(message)'''
assert s.count(a)==1
s=s.replace(a,b,1)
a='''                    .put("imageTag",decision.imageTag)'''
b='''                    .put("imageTag",decision.imageTag)
                    .put("learnEligible",decision.reason=="Consulta sin regla aprobada" ||
                        decision.reason=="Negocio ambiguo: revisión manual")'''
assert s.count(a)==1
s=s.replace(a,b,1)
p.write_text(s,encoding="utf-8")
print("Android listener now quarantines captioned media and payment receipts; no reply, no learning, no caption persisted")
