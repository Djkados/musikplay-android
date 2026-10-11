from pathlib import Path
p=Path("source/autoresponder-pro/android/app/src/main/java/com/autoresponder/pro/NativeAutoReplyEngine.kt")
s=p.read_text()
def change(a,b):
 global s
 assert s.count(a)==1, "Unexpected engine version: "+a[:80]
 s=s.replace(a,b)
change('data class Decision(val text: String? = null, val business: String? = null, val department: String? = null, val reason: String = "")',
'''data class Decision(val text: String? = null, val business: String? = null,
        val department: String? = null, val reason: String = "",
        val routeSource: String = "none", val needsChoice: Boolean = false)
    private data class Route(val business:String?,val source:String)''')
a=s.index("    private fun assignedBusiness(");b=s.index("    private fun easter(",a)
s=s[:a]+'''    private fun assignedBusiness(config:JSONObject,channel:String,contact:String,
        message:String,rememberedBusiness:String?,awaitingChoice:Boolean):Route {
        val exceptions=config.optJSONArray("exceptions")
        if(exceptions!=null)for(i in 0 until exceptions.length()){
            val item=exceptions.optJSONObject(i) ?: continue
            if(item.optString("channel")==channel && matchContact(item,contact)){
                val assistant=item.optString("assistant")
                if(assistant!="auto")return Route(assistant,"exception")
                break
            }
        }
        val channelAssistant=config.optJSONObject("channel")?.optJSONObject(channel)
            ?.optString("assistant","none") ?: "none"
        if(channelAssistant!="auto")return Route(channelAssistant,"channel")
        val normalized=normalize(message)
        val m=movie.any { normalized.contains(it) }
        val f=food.any { normalized.contains(it) }
        if(m && f)return Route(null,"mixed")
        if(m)return Route("movieplay","detected")
        if(f)return Route("tresm","detected")
        if(awaitingChoice){
            if(normalized in setOf("1","opcion 1","la primera","primera"))
                return Route("movieplay","choice")
            if(normalized in setOf("2","opcion 2","la segunda","segunda"))
                return Route("tresm","choice")
        }
        if(rememberedBusiness in setOf("movieplay","tresm"))
            return Route(rememberedBusiness,"context")
        return Route(null,"clarify")
    }

'''+s[b:]
change('fun decide(config: JSONObject, channel: String, contact: String, message: String, now: ZonedDateTime = ZonedDateTime.now(colombia)): Decision {',
'''fun decide(config:JSONObject,channel:String,contact:String,message:String,
        now:ZonedDateTime=ZonedDateTime.now(colombia),
        rememberedBusiness:String?=null,awaitingChoice:Boolean=false):Decision {''')
a=s.index("        val business=assignedBusiness(");b=s.index('        if(business=="none"',a)
s=s[:a]+'''        val route=assignedBusiness(config,channel,c,m,rememberedBusiness,awaitingChoice)
        val business=route.business ?: run {
            val unrestricted=config.optJSONObject("settings")?.optBoolean("requireAllowlist",true)==false
            val assistants=config.optJSONObject("assistants")
            if(unrestricted && assistants?.optJSONObject("movieplay")?.optBoolean("active",false)==true &&
                assistants.optJSONObject("tresm")?.optBoolean("active",false)==true)
                return Decision(text="¡Hola! 👋 ¿Tu consulta es para 🎬 MoviePlay (1) o 🍔 Las Tres M (2)? Así te damos la información y el horario correctos.",
                    reason="Aclaración de negocio",routeSource=route.source,needsChoice=true)
            return Decision(reason="Negocio ambiguo: revisión manual",routeSource=route.source)
        }
'''+s[b:]
change('if(unit.isNotEmpty())scheduledReply(config,business,unit,now)?.let {return it}',
       'if(unit.isNotEmpty())scheduledReply(config,business,unit,now)?.let {return it.copy(routeSource=route.source)}')
change('if(best==null)return Decision(reason="Consulta sin regla aprobada")',
'''if(best==null) {
            val n=normalize(m)
            val selected=route.source=="choice" || (route.source=="detected" &&
                n in setOf("movieplay","las tres m"))
            val greeting=n in setOf("hola","buenas","buenos dias","buenas tardes",
                "buenas noches","gracias","ok","listo","si")
            val price=n.contains("precio") || n.contains("cuanto") ||
                n.contains("cuesta") || n.contains("vale")
            if(selected || (route.source=="context" && (greeting || price))) {
                val answer=when(business){
                    "movieplay" -> "🎬 ¡Bienvenido a MoviePlay! ¿Qué plataforma deseas consultar? Te ayudamos con planes, precios y soporte."
                    "tresm" -> "🍔 ¡Bienvenido a Las Tres M! Mira el menú y los precios en https://lastresm.netlify.app. ¿Qué comida te interesa?"
                    else -> null
                }
                if(answer!=null)return Decision(text=answer,business=business,
                    department=unit,reason="Consulta en contexto",routeSource=route.source)
            }
            return Decision(reason="Consulta sin regla aprobada",business=business,
                department=unit,routeSource=route.source)
        }''')
change('return Decision(text=reply,business=business,department=unit,reason="Regla configurada")',
       'return Decision(text=reply,business=business,department=unit,reason="Regla configurada",routeSource=route.source)')
p.write_text(s)
print("Engine routes each business independently")
