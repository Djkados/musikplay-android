from pathlib import Path
root=Path("source/autoresponder-pro/android/app/src/main/java/com/autoresponder/pro")
source=r'''package com.autoresponder.pro

import android.app.Notification
import android.os.Bundle
import java.text.Normalizer
import java.util.Locale

/**
 * Strict incoming-only gate. Media attachments (even when captioned), receipts,
 * transfer confirmations and reported payments never trigger auto-send or learning.
 * Metadata can vary with WhatsApp/Android, so uncertain messages fail closed.
 */
internal object IncomingSafety {
    private fun clean(raw:String):String =
        Normalizer.normalize(raw.lowercase(Locale.ROOT),Normalizer.Form.NFD)
            .replace(Regex("\\p{M}+"),"").replace(Regex("\\s+")," ").trim()

    fun isPaymentEvidence(text:String):Boolean {
        val t=clean(text)
        if(t.isEmpty())return false
        if(Regex("\\b(comprobante|capture de pago|captura de pago|pago realizado|pago exitoso|"+
            "ya pague|acabo de pagar|ya hice el pago|te pague|te consigne|consignacion realizada|"+
            "transferencia realizada|transferencia exitosa|te transferi|te envie el pago|"+
            "te mando el pago|envio el soporte|soporte de pago|adjunto recibo|recibo de pago|"+
            "ya transferi|confirmo que pague|enviado el comprobante)\\b").containsMatchIn(t))return true
        // Captions such as "Pago Pedro Páez" or "Pago 18.000": don't interpret
        // them as a request for bank details. Legitimate "medios de pago",
        // "pago con Nequi", etc. are handled by PaymentReplies.
        if(t.startsWith("pago ") &&
            !Regex("^pago (con|por|en|mediante|con llave|nequi|daviplata|bancolombia|de que forma|donde|como)\\b")
                .containsMatchIn(t) &&
            t.split(" ").size in 2..7)return true
        return false
    }

    private fun mediaMarker(text:String):Boolean {
        val t=text.trim()
        if(t.isEmpty())return false
        return Regex("(?is)^\\s*(?:📷|📸|🖼|🎥|📎|📄|🎙|🎤|🎧|"+
            "\\[(?:foto|imagen|video|documento|archivo|audio|sticker|gif)\\]|"+
            "(?:foto|imagen|photo|image|documento|document|archivo adjunto|"+
            "video|sticker|gif|nota de voz)(?:\\s*[:\\-\\n]|\\s+adjunt[oa]))")
            .containsMatchIn(t)
    }
    fun hasMedia(extras:Bundle,latest:Bundle?,text:String):Boolean {
        if(latest!=null){
            val type=latest.getString("type")
                ?:latest.getString("dataMimeType")?:latest.getString("mimeType")
            if(!type.isNullOrBlank() && !type.equals("text/plain",ignoreCase=true))
                return true
            if(latest.containsKey("uri") && latest.get("uri")!=null)return true
            if(latest.containsKey("dataUri") && latest.get("dataUri")!=null)return true
        }
        if(extras.containsKey(Notification.EXTRA_PICTURE) ||
            extras.containsKey(Notification.EXTRA_PICTURE_ICON))return true
        if(mediaMarker(text))return true
        val notificationText=extras.getCharSequence(Notification.EXTRA_TEXT)?.toString().orEmpty()
        return mediaMarker(notificationText)
    }
    fun blockReason(extras:Bundle,latest:Bundle?,text:String):String?=when {
        hasMedia(extras,latest,text)->"adjunto_revision_manual"
        isPaymentEvidence(text)->"comprobante_revision_manual"
        else->null
    }
}
'''
(root/"IncomingSafety.kt").write_text(source,encoding="utf-8")
p=root/"NativeAutoReplyEngine.kt";s=p.read_text(encoding="utf-8")
old='''        if(unsafe.containsMatchIn(normalize(m))) return Decision(reason="Mensaje con posibles datos sensibles")'''
new='''        if(IncomingSafety.isPaymentEvidence(m))
            return Decision(reason="Comprobante o pago reportado: verificar manualmente",
                routeSource="manual_review")
        if(unsafe.containsMatchIn(normalize(m))) return Decision(reason="Mensaje con posibles datos sensibles")'''
assert s.count(old)==1
p.write_text(s.replace(old,new),encoding="utf-8")
p=root/"PaymentReplies.kt";s=p.read_text(encoding="utf-8")
old='''        val clean=normalize(message)
        val shortcut='''
new='''        if(IncomingSafety.isPaymentEvidence(message))return null
        val clean=normalize(message)
        val shortcut='''
assert s.count(old)==1
p.write_text(s.replace(old,new),encoding="utf-8")
print("Incoming attachment + evidence safety classifiers and payment guard installed")
