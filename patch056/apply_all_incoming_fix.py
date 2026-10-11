from pathlib import Path
root=Path("source/autoresponder-pro")
def rep(path, old, new):
    file=root/path
    s=file.read_text(encoding="utf-8")
    count=s.count(old)
    if count!=1: raise RuntimeError(f"{path}: expected one occurrence, got {count}: {old[:90]}")
    file.write_text(s.replace(old,new),encoding="utf-8")

native="android/app/src/main/java/com/autoresponder/pro/NativeAutoReplyEngine.kt"
rep(native,
  'if(!matches(config.optJSONArray("allowlist"),channel,c)) return Decision(reason="Contacto no autorizado para autoenvío")',
  '''if((config.optJSONObject("settings")?.optBoolean("requireAllowlist",true) ?: true) &&
            !matches(config.optJSONArray("allowlist"),channel,c))
            return Decision(reason="Contacto no autorizado para autoenvío")''')
rep(native,
  'val business=assignedBusiness(config,channel,c,m) ?: return Decision(reason="Negocio ambiguo: revisión manual")',
  '''val business=assignedBusiness(config,channel,c,m) ?: run {
            // Never guess a company's schedule for a neutral greeting.
            val allIncoming=config.optJSONObject("settings")?.optBoolean("requireAllowlist",true) == false
            val assistants=config.optJSONObject("assistants")
            if(allIncoming && assistants?.optJSONObject("movieplay")?.optBoolean("active",false)==true &&
                assistants.optJSONObject("tresm")?.optBoolean("active",false)==true)
                return Decision(text="¡Hola! 👋 ¿Tu consulta es para 🎬 MoviePlay o 🍔 Las Tres M? Así te compartimos la información correcta.",reason="Aclaración de negocio")
            return Decision(reason="Negocio ambiguo: revisión manual")
        }''')
rep(native,
  'if(unsafe.containsMatchIn(normalize(m))) return Decision(reason="Mensaje con posibles datos sensibles")',
  '''if(unsafe.containsMatchIn(normalize(m))) return Decision(reason="Mensaje con posibles datos sensibles")
        // Text descriptions of received media are never auto-replied to.
        val lower=normalize(m)
        if(lower.contains("envio una foto") || lower.contains("envio una imagen") ||
            lower.contains("envio un video") || lower.contains("envio un audio") ||
            lower.contains("envio un sticker"))
            return Decision(reason="Multimedia: revisión manual")''')
web="web/app.js"
rep(web,
 '/* AutoResponder Pro v0.5.4 — diagnóstico local de notificaciones y auto-respuestas. */',
 '/* AutoResponder Pro v0.5.6 — respuestas para todos los contactos entrantes. */')
rep(web,
 'settings:{requireAllowlist:true,blockGroups:true,reviewOnly:true,autoReplies:{normal:false,business:false}}',
 'settings:{requireAllowlist:false,blockGroups:true,reviewOnly:true,autoReplies:{normal:false,business:false}}')
rep(web,
 '  state.settings.autoReplies ||= {normal:false,business:false};',
 '''  state.settings.autoReplies ||= {normal:false,business:false};
  // The owner authorized replying to ALL new/saved inbound contacts.
  // One-time upgrade: only already-capturing channels are enabled for auto-text.
  // Thereafter, ordinary per-channel toggles always take precedence.
  const migration='autoresponder_pro_v056_all_incoming';
  if(native && !localStorage.getItem(migration)){
    state.settings.requireAllowlist=false;
    for(const ch of ['normal','business'])
      if(state.channel[ch]?.enabled)state.settings.autoReplies[ch]=true;
    localStorage.setItem(KEY,JSON.stringify(state));
    localStorage.setItem(migration,'done');
  }''')
rep(web,
  "    if (/\\b(otp|pin|clave|contrasena|password|codigo de acceso|verificacion bancaria)\\b/.test(msg)) return {reason:'Por seguridad no se generan respuestas a mensajes con claves o códigos.'};",
  "    if (/\\b(otp|pin|clave|contrasena|password|codigo de acceso|verificacion bancaria)\\b/.test(msg)) return {reason:'Por seguridad no se generan respuestas a mensajes con claves o códigos.'};\n    if (msg.includes('envio una foto')||msg.includes('envio una imagen')||msg.includes('envio un video')||msg.includes('envio un audio')||msg.includes('envio un sticker'))return {reason:'Multimedia: revisión manual.'};")
rep(web,
  '        if(!state.allowlist.some(x=>x.channel===ch)){notify(',
  '        if(state.settings.requireAllowlist && !state.allowlist.some(x=>x.channel===ch)){notify(')
rep(web,
  'Solo contactos autorizados · Sin imágenes automáticas',
  'Nuevos y guardados · sin imágenes automáticas')
rep(web,
  'La app prepara borradores para todos los contactos permitidos y solo responde automáticamente a quienes autorices explícitamente.',
  'La app responde a todos los contactos nuevos y guardados que escriban, con autoenvío activo en cada WhatsApp. Nunca inicia chats ni envía imágenes.')
rep(web,
  'La app prepara respuestas e imágenes. Si activas autoenvío, enviará solo textos con regla aprobada a contactos autorizados; las imágenes siempre se revisan.',
  'La app prepara respuestas a contactos nuevos o guardados. Con autoenvío activo, responde textos entrantes con horarios independientes; las imágenes se revisan.')
rep(web,
  'Solo los contactos autorizados pueden recibir auto-respuestas si activas esta opción.',
  'Esta lista es opcional: se usa solo si activas el modo restringido de contactos.')
rep(web,
  'Exigir contacto autorizado</span>',
  'Restringir respuestas a contactos autorizados (apagar para todos)</span>')
rep(web,
  '<div class="notice">Imágenes siempre con confirmación manual. El texto puede enviarse solo a contactos autorizados mediante activación expresa por WhatsApp. No hay mensajes masivos.</div>',
  '<div class="notice">Sin lista restrictiva, la app puede responder a todos los contactos que escriban. Solo mensajes entrantes, sin envíos masivos, grupos ni imágenes automáticas.</div>')
rep(web,
  '!authorized(i.channel,i.contact)?',
  'state.settings.requireAllowlist&&!authorized(i.channel,i.contact)?')
rep(web,
  'contacto(s) de prueba</p>',
  'contacto(s) en lista opcional</p>')
rep(web,
  'Solo contactos autorizados</span>',
  'Modo lista restrictiva</span>')
rep(web,
  '1. Autoriza un contacto de prueba con su nombre exacto de notificación y el canal. 2. Prueba la consulta en el simulador. 3. Da permiso de acceso a notificaciones desde Android. 4. Habilita autoenvío en ese WhatsApp.',
  '1. Revisa reglas y horarios. 2. Concede permiso de notificaciones. 3. Habilita captura y autoenvío para cada WhatsApp. 4. Envía un mensaje desde otro teléfono.')
rep(web,
  'Se responderán automáticamente mensajes de texto de contactos autorizados en ',
  'Se responderán automáticamente mensajes entrantes de contactos nuevos y guardados en ')
# The bundled WebView loads the APK assets, not the top-level web folder.
(root/"android/app/src/main/assets/app.js").write_text((root/web).read_text(encoding="utf-8"),encoding="utf-8")
rep("android/app/build.gradle.kts",'versionCode = 10','versionCode = 11')
rep("android/app/build.gradle.kts",'versionName = "0.5.5"','versionName = "0.5.6"')
# Existing web test fixtures explicitly exercise the old restricted mode.
rep("tests/workflow.test.cjs",
 "const storage = new Map([['autoresponder_pro_v1', JSON.stringify(config)]]);",
 "const storage = new Map([['autoresponder_pro_v1', JSON.stringify(config)],['autoresponder_pro_v056_all_incoming','done']]);")
rep("tests/smoke.test.cjs",'c.channel.normal.enabled=true;',
 'c.channel.normal.enabled=true;\nc.settings.requireAllowlist=true;')
for fn in ["tests/workflow.test.cjs","tests/smoke.test.cjs"]:
 rep(fn,"Date,Math,URL,Blob",
 "Date:class StableDate extends Date{constructor(...v){super(...(v.length?v:['2026-10-10T20:00:00-05:00']));}static now(){return new Date('2026-10-10T20:00:00-05:00').getTime();}},Math,URL,Blob")
# Native test coverage uses the existing fixture; no contact must be in allowlist.
t=root/"android/app/src/test/java/com/autoresponder/pro/NativeAutoReplyEngineTest.kt"
s=t.read_text();assert s.rstrip().endswith("}")
s=s.rstrip()[:-1]+'''
    @Test fun anyNewOrSavedContactMayReceiveInboundRepliesWithOptIn() {
        val c=config(); val at=clock("2026-10-10","19:00")
        c.getJSONObject("settings").put("requireAllowlist",false)
            .getJSONObject("autoReplies").put("normal",true)
        c.put("allowlist",JSONArray())
        assertEquals("Precios MoviePlay",NativeAutoReplyEngine.decide(c,"normal","Cliente nuevo","netflix",at).text)
        assertEquals("Precios MoviePlay",NativeAutoReplyEngine.decide(c,"business","Guardado","netflix",at).text)
        assertEquals("Menú Las Tres M",NativeAutoReplyEngine.decide(c,"business","Cliente nuevo","hamburguesa",at).text)
        assertEquals("Menú Las Tres M",NativeAutoReplyEngine.decide(c,"normal","Guardado","hamburguesa",at).text)
    }
    @Test fun allIncomingClarifiesAmbiguityButProtectsMediaAndExclusions() {
        val c=config(); val at=clock("2026-10-10","19:00")
        c.getJSONObject("settings").put("requireAllowlist",false)
        c.put("allowlist",JSONArray())
        val d=NativeAutoReplyEngine.decide(c,"business","Nuevo","hola",at)
        assert(d.text?.contains("MoviePlay")==true && d.text.contains("Las Tres M"))
        assertNull(d.business)
        assertNull(NativeAutoReplyEngine.decide(c,"business","Nuevo","📷 Envió una foto.",at).text)
        c.getJSONArray("blocked").put(JSONObject().put("channel","business").put("contact","Nuevo"))
        assertNull(NativeAutoReplyEngine.decide(c,"business","Nuevo","netflix",at).text)
    }
}
'''
t.write_text(s)
print("AutoResponder 0.5.6 all-incoming patch applied successfully")
