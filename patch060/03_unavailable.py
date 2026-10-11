from pathlib import Path
root=Path("source/autoresponder-pro")
p=root/"android/app/src/main/java/com/autoresponder/pro/LocalCatalog.kt"
s=p.read_text(encoding="utf-8")
def change(a,b):
 global s
 assert s.count(a)==1,(a[:70],s.count(a))
 s=s.replace(a,b,1)
change('.map {norm(it)}.filter {it.length>=4}', '.map {norm(it)}.filter {it.length>=3}')
change('if(item.optBoolean("active",false) && item.optString("assistant")==business &&',
       'if(item.optString("assistant")==business &&')
change('if(item.optBoolean("active",false) && item.optString("assistant")==business &&',
       'if(item.optString("assistant")==business &&')
change('''        val requested=Regex("\\\\b(26|28|30|60|90|180|365)\\\\s*(dias|dia|d)\\\\b")
            .find(normalized)?.groupValues?.get(1)
        val selected=if(requested!=null){
            hits.filter {Regex("\\\\b"+requested+"\\\\b").containsMatchIn(norm(it.optString("duration")))}
                .ifEmpty {hits}
        } else hits''',
'''        val requested=Regex("\\\\b(26|28|30|60|90|180|365)\\\\s*(dias|dia|d)\\\\b|\\\\b(2|3|6|12)\\\\s*(meses|mes)\\\\b")
            .find(normalized)?.value
        val selected=if(requested!=null){
            hits.filter {norm(it.optString("duration"))==requested}.ifEmpty {hits}
        } else hits''')
change('''        val imageTag=chosen.first().optString("imageTag","")''',
'''        val firstAvailable=chosen.firstOrNull {it.optBoolean("active",false)}
        val imageTag=firstAvailable?.optString("imageTag","") ?: ""
        val anythingAvailable=firstAvailable!=null''')
change('''            lines.add("  💵 $amount"+if(validOffer)" (oferta hasta $until)" else "")''',
'''            lines.add("  💵 $amount"+if(validOffer && item.optBoolean("active",false))
                " (oferta hasta $until)" else "")
            if(!item.optBoolean("active",false))
                lines.add("  🚫 *NO DISPONIBLE POR EL MOMENTO*")''')
change('''        if(business=="tresm"){
            lines.add("📲 *Menú completo y pedidos:*")''',
'''        if(!anythingAvailable){
            lines.add("Este producto está temporalmente fuera de venta. El precio es solo informativo.")
            lines.add("Si deseas, te contamos las opciones disponibles. 😊")
        } else if(business=="tresm"){
            lines.add("📲 *Menú completo y pedidos:*")''')
change('''        } else {
            lines.add("¿Cuál opción te interesa? 😊")
        }''',
'''        } else {
            lines.add("¿Cuál opción disponible te interesa? 😊")
        }''')
p.write_text(s,encoding="utf-8")

p=root/"web/app.js";s=p.read_text(encoding="utf-8")
def rep(a,b):
 global s
 assert s.count(a)==1,(a[:80],s.count(a))
 s=s.replace(a,b,1)
rep('''    return state.catalog.filter(i=>i.active&&i.assistant===business&&''',
    '''    return state.catalog.filter(i=>i.assistant===business&&''')
rep('''return alias.length>=4 &&''','''return alias.length>=3 &&''')
rep('''const plan=normalize(message).match(/\\b(26|28|30|60|90|180|365)\\s*(d[ií]as?|d)\\b/);
    const scoped=plan?matching.filter(i=>String(i.duration||"").includes(plan[1])):matching;''',
'''const plan=normalize(message).match(/\\b(?:26|28|30|60|90|180|365)\\s*(?:dias?|d)\\b|\\b(?:2|3|6|12)\\s*(?:meses|mes)\\b/);
    const scoped=plan?matching.filter(i=>normalize(i.duration||"")===plan[0]):matching;''')
rep('''const items=(scoped.length?scoped:matching).slice(0,7);''',
'''const items=(scoped.length?scoped:matching).slice(0,7);
    const firstActive=items.find(i=>i.active);''')
rep('''lines.push("  💵 "+(amount>0?"$"+amount.toLocaleString("es-CO"):
        business==="tresm"?"Consultar en el menú":"Precio por confirmar")+
        (valid?" (oferta hasta "+item.offerUntil+")":""));''',
'''lines.push("  💵 "+(amount>0?"$"+amount.toLocaleString("es-CO"):
        business==="tresm"?"Consultar en el menú":"Precio por confirmar")+
        (valid&&item.active?" (oferta hasta "+item.offerUntil+")":""));
      if(!item.active)lines.push("  🚫 *NO DISPONIBLE POR EL MOMENTO*");''')
rep('''    if(business==="tresm")lines.push("📲 *Menú completo y pedidos:*",
      "https://lastresm.netlify.app","","¿Qué se te antoja? 😊");
    else lines.push("¿Cuál opción te interesa? 😊");
    return {reply:lines.join("\\n"),imageTag:items[0]?.imageTag||"",catalogId:items[0]?.id||""};''',
'''    if(!firstActive){
      lines.push("Este producto está temporalmente fuera de venta. El precio es solo informativo.",
        "Si deseas, te contamos las opciones disponibles. 😊");
    } else if(business==="tresm")lines.push("📲 *Menú completo y pedidos:*",
      "https://lastresm.netlify.app","","¿Qué se te antoja? 😊");
    else lines.push("¿Cuál opción disponible te interesa? 😊");
    return {reply:lines.join("\\n"),imageTag:firstActive?.imageTag||"",
      catalogId:items[0]?.id||""};''')
# More useful availability badge in price card and clear toggle labelling.
rep(''''<input type="checkbox" class="toggle" data-catalog-toggle="'+safe(i.id)+'"'+(i.active?' checked':'')+'></div>'+''',
''' '<span class="pill '+(i.active?'':'off')+'">'+(i.active?'Disponible':'🚫 No disponible')+'</span>'+
      '<input type="checkbox" class="toggle" aria-label="Disponible" data-catalog-toggle="'+safe(i.id)+'"'+(i.active?' checked':'')+'></div>'+''')
rep('''      '<p class="tiny muted">'+safe(i.notes||'')+'</p><p class="tiny muted">Palabras clave: '+safe(i.keywords)+'</p><div class="row">'+''',
'''      '<p class="tiny muted">'+safe(i.notes||'')+'</p>'+
      (!i.active?'<p class="small muted">El precio seguirá visible, marcado como no disponible.</p>':'')+
      '<p class="tiny muted">Palabras clave: '+safe(i.keywords)+'</p><div class="row">'+''')
p.write_text(s,encoding="utf-8")
(root/"android/app/src/main/assets/app.js").write_text(s,encoding="utf-8")
print("Unavailable products now preserve informational prices and status; excluded from automatic images")
