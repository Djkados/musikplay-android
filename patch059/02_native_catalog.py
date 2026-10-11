from pathlib import Path
root=Path("source/autoresponder-pro/android/app/src/main/java/com/autoresponder/pro")
catalog=r'''package com.autoresponder.pro

import org.json.JSONArray
import org.json.JSONObject
import java.text.Normalizer
import java.time.LocalDate
import java.util.Locale

/** Approved, on-device prices. No network access and no invented price. */
internal object LocalCatalog {
    data class Match(val text:String,val imageTag:String="",val count:Int=0)
    private fun norm(s:String):String=Normalizer.normalize(s.lowercase(Locale.ROOT),Normalizer.Form.NFD)
        .replace(Regex("\\p{M}+"),"").replace(Regex("[^a-z0-9]+")," ").trim()
    private fun tokens(item:JSONObject):List<String> =
        (item.optString("keywords").split(",")+item.optString("name"))
            .map {norm(it)}.filter {it.length>=4}
    private fun contains(haystack:String,needle:String):Boolean =
        (" $haystack ").contains(" $needle ")
    private fun distanceOne(a:String,b:String):Boolean {
        if(kotlin.math.abs(a.length-b.length)>1)return false
        var i=0;var j=0;var edits=0
        while(i<a.length && j<b.length){
            if(a[i]==b[j]){i++;j++;continue}
            if(++edits>1)return false
            when {
                a.length>b.length -> i++
                b.length>a.length -> j++
                else -> {i++;j++}
            }
        }
        return edits+a.length-i+b.length-j<=1
    }
    private fun matches(item:JSONObject,message:String):Boolean {
        val input=norm(message)
        val words=input.split(" ")
        return tokens(item).any { alias ->
            contains(input,alias) ||
                (alias.length>=5 && !alias.contains(" ") &&
                    words.any { it.length>=4 && distanceOne(it,alias) })
        }
    }
    fun detects(config:JSONObject,business:String,message:String):Boolean {
        val items=config.optJSONArray("catalog") ?: return false
        for(i in 0 until items.length()){
            val item=items.optJSONObject(i) ?: continue
            if(item.optBoolean("active",false) && item.optString("assistant")==business &&
                matches(item,message))return true
        }
        return false
    }
    fun reply(config:JSONObject,business:String,message:String,today:LocalDate):Match? {
        val items=config.optJSONArray("catalog") ?: return null
        val hits=ArrayList<JSONObject>()
        for(i in 0 until items.length()){
            val item=items.optJSONObject(i) ?: continue
            if(item.optBoolean("active",false) && item.optString("assistant")==business &&
                matches(item,message))hits.add(item)
        }
        if(hits.isEmpty())return null
        // If a plan length was explicitly given, don't quote other durations.
        val normalized=norm(message)
        val requested=Regex("\\b(26|28|30|60|90|180|365)\\s*(dias|dia|d)\\b")
            .find(normalized)?.groupValues?.get(1)
        val selected=if(requested!=null){
            hits.filter {Regex("\\b"+requested+"\\b").containsMatchIn(norm(it.optString("duration")))}
                .ifEmpty {hits}
        } else hits
        val chosen=selected.take(7)
        val lines=mutableListOf(if(business=="tresm")"🍔 *LAS TRES M*" else "🎬 *MOVIEPLAY*",
            "",if(business=="tresm")"📋 *Consulta de nuestro menú*" else "📺 *Planes y precios disponibles*","")
        val imageTag=chosen.first().optString("imageTag","")
        for(item in chosen){
            val name=item.optString("name").trim().take(90)
            val duration=item.optString("duration").trim()
            val base=item.optLong("price",0L)
            val offer=item.optLong("salePrice",0L)
            val until=item.optString("offerUntil","")
            val validOffer=offer>0 && offer<base && runCatching {
                !LocalDate.parse(until).isBefore(today)
            }.getOrDefault(false)
            val price=if(validOffer)offer else base
            val details=if(duration.isNotBlank())" · $duration" else ""
            val amount=if(price>0)"$"+String.format(Locale.GERMANY,"%,d",price)
                else if(business=="tresm")"Consultar en el menú" else "Precio por confirmar"
            lines.add("• *$name*"+details)
            lines.add("  💵 $amount"+if(validOffer)" (oferta hasta $until)" else "")
        }
        lines.add("")
        if(business=="tresm"){
            lines.add("📲 *Menú completo y pedidos:*")
            lines.add("https://lastresm.netlify.app")
            lines.add("")
            lines.add("¿Qué se te antoja? 😊")
        } else {
            lines.add("¿Cuál opción te interesa? 😊")
        }
        val result=lines.joinToString("\n")
        return if(result.length<=1600)Match(result,imageTag,chosen.size) else null
    }
}
'''
(root/"LocalCatalog.kt").write_text(catalog,encoding="utf-8")
p=root/"NativeAutoReplyEngine.kt"
s=p.read_text(encoding="utf-8")
def change(old,new):
 global s
 assert s.count(old)==1,(old[:80],s.count(old))
 s=s.replace(old,new,1)
change('val m=movie.any { normalized.contains(it) }',
       'val m=movie.any { normalized.contains(it) } || LocalCatalog.detects(config,"movieplay",message)')
change('val f=food.any { normalized.contains(it) }',
       'val f=food.any { normalized.contains(it) } || LocalCatalog.detects(config,"tresm",message)')
change('''        val rules=config.optJSONArray("rules") ?: return Decision(reason="Sin reglas")''',
'''        LocalCatalog.reply(config,business,m,now.toLocalDate())?.let {
            return Decision(text=it.text,business=business,department=unit,
                reason="Catálogo aprobado",routeSource=route.source)
        }
        val rules=config.optJSONArray("rules") ?: return Decision(reason="Sin reglas")''')
p.write_text(s,encoding="utf-8")
print("Native local catalog and common typo tolerance enabled")
