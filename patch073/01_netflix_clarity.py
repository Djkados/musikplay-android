from pathlib import Path

root=Path("source/autoresponder-pro")
native=root/"android/app/src/main/java/com/autoresponder/pro"
web=root/"web"
assets=root/"android/app/src/main/assets"

old=("En MoviePlay, Netflix Internacional identifica una cuenta de una región fuera de Colombia; "
     "Netflix habitual corresponde a la modalidad Colombia. Pueden cambiar las condiciones "
     "de acceso y verificación según el dispositivo y la cuenta. No significa automáticamente "
     "más calidad, más películas ni que no existan restricciones de hogar. Confirmamos la "
     "compatibilidad antes de la entrega.")
new=("Netflix Internacional es una cuenta destinada para usarse fuera de Colombia. "
     "No significa que incluya más películas, series ni contenido exclusivo; la diferencia "
     "es el país donde se utilizará la cuenta, no que sea un plan con contenido adicional.")

def replace(path, before, after, desc):
    content=path.read_text(encoding="utf-8")
    assert content.count(before)==1, (desc, content.count(before), str(path))
    path.write_text(content.replace(before,after,1),encoding="utf-8")

k=native/"NetflixInternationalInfo.kt"
replace(k,'const val DEFAULT = "'+old+'"',
        'const val DEFAULT = "'+new+'"\n    private const val LEGACY_DEFAULT = "'+old+'"',
        "Kotlin default and legacy")
replace(k,'''        val info=config.optString("netflixInternationalInfo").trim()
            .takeIf{it.length in 20..850} ?: DEFAULT''',
'''        val savedInfo=config.optString("netflixInternationalInfo").trim()
            .takeIf{it.length in 20..850} ?: DEFAULT
        // Migrate exactly the shipped v0.6.12 wording without changing
        // customer-edited descriptions.
        val info=if(savedInfo==LEGACY_DEFAULT) DEFAULT else savedInfo''',
        "Kotlin persisted legacy default migration")
replace(k,'💚 ¿Quieres cotizar el habitual o el Internacional?',
        '💚 ¿Lo utilizarás en Colombia o en otro país? Así te ayudo a elegir la opción adecuada.',
        "Kotlin next-step question")

j=web/"netflix-international.js"
replace(j,"const DEFAULT='"+old+"';",
        "const DEFAULT='"+new+"';\nconst OLD_DEFAULT='"+old+"';",
        "JavaScript shipped and previous description")
replace(j,'''    editable.trim():DEFAULT;''',
'''    (editable.trim()===OLD_DEFAULT?DEFAULT:editable.trim()):DEFAULT;''',
        "JavaScript preserved custom description and migrated default")
replace(j,'💚 ¿Quieres cotizar el habitual o el Internacional?',
        '💚 ¿Lo utilizarás en Colombia o en otro país? Así te ayudo a elegir la opción adecuada.',
        "JavaScript next-step question")
replace(j,'return {DEFAULT,question,answer};',
        'return {DEFAULT,OLD_DEFAULT,question,answer};',
        "Expose previous default for migration")

app=web/"app.js"
replace(app,'''  state.netflixInternationalInfo ||= window.NetflixInternationalInfo?.DEFAULT||"";''',
'''  state.netflixInternationalInfo ||= window.NetflixInternationalInfo?.DEFAULT||"";
  // Never overwrite manually edited explanations during upgrades.
  if(state.netflixInternationalInfo===window.NetflixInternationalInfo?.OLD_DEFAULT)
    state.netflixInternationalInfo=window.NetflixInternationalInfo.DEFAULT;''',
        "App existing configuration migration")
replace(app,'''    state.netflixInternationalInfo=state.netflixInternationalInfo||
      window.NetflixInternationalInfo?.DEFAULT||"";''',
'''    state.netflixInternationalInfo=state.netflixInternationalInfo||
      window.NetflixInternationalInfo?.DEFAULT||"";
    if(state.netflixInternationalInfo===window.NetflixInternationalInfo?.OLD_DEFAULT)
      state.netflixInternationalInfo=window.NetflixInternationalInfo.DEFAULT;''',
        "App imported backup migration")
replace(app,"AutoResponder Pro v0.6.12","AutoResponder Pro v0.6.13",
        "App code version marker")

idx=web/"index.html"
replace(idx,"Versión 0.6.12 · Ventas 360",
        "Versión 0.6.13 · Ventas 360",
        "App visible version marker")

t=root/"android/app/src/test/java/com/autoresponder/pro/Sales360AndNetflixInfoTest.kt"
replace(t,'''        assertTrue(a.contains("restricciones de hogar"))''',
'''        assertTrue(a.contains("fuera de Colombia"))
        assertTrue(a.contains("contenido exclusivo"))
        assertTrue(a.contains("país donde se utilizará"))
        // Existing users must get corrected copy unless they edited it.
        val older=infoConfig().put("netflixInternationalInfo",NetflixInternationalInfo.LEGACY_DEFAULT_FOR_TEST)
        assertTrue(NetflixInternationalInfo.answer(older,
            "¿Qué diferencia tiene Netflix Internacional?")!!.contains("contenido exclusivo"))
        val custom=infoConfig().put("netflixInternationalInfo",
            "Esta es una explicación propia que sí se debe conservar.")
        assertTrue(NetflixInternationalInfo.answer(custom,
            "¿Qué es Netflix Internacional?")!!.contains("explicación propia"))''',
        "Kotlin regression check")
# Make the legacy description testable without modifying visibility of internal logic.
replace(k,'''    private const val LEGACY_DEFAULT = "'''+old+'''"''',
        '''    internal const val LEGACY_DEFAULT_FOR_TEST = "'''+old+'''"
    private const val LEGACY_DEFAULT = LEGACY_DEFAULT_FOR_TEST''',
        "Kotlin legacy constant test bridge")

(root/"tests/netflix_clarity_073.test.cjs").write_text(r''' 'use strict';
const assert = require('node:assert/strict');
const N = require('../web/netflix-international.js');
const catalog = [
  {assistant:'movieplay',name:'Netflix Internacional',duration:'30 días',price:18000,active:true},
  {assistant:'movieplay',name:'Netflix Premium',duration:'30 días',price:18000,active:true}
];
const queries=[
  '¿Qué es eso de Netflix Internacional?',
  '¿Cuál es la diferencia entre Netflix normal y Netflix Internacional?',
  'Explícame Netflix internacional'
];
for(const q of queries){
 const answer=N.answer(catalog,q);
 assert.ok(answer,'must explain: '+q);
 assert.match(answer,/fuera de Colombia/i);
 assert.match(answer,/no significa que incluya más películas/i);
 assert.match(answer,/contenido exclusivo/i);
 assert.match(answer,/país donde se utilizará/i);
 assert.match(answer,/\$18\.000/);
 assert.match(answer,/en Colombia o en otro país/i);
}
assert.ok(N.OLD_DEFAULT.includes('restricciones de hogar'));
const migrated=N.answer(catalog,queries[0],N.OLD_DEFAULT);
assert.match(migrated,/contenido exclusivo/);
assert.doesNotMatch(migrated,/restricciones de hogar/);
const userEdited='Es la descripción personalizada y aprobada por el administrador.';
assert.match(N.answer(catalog,queries[0],userEdited),/descripción personalizada/);
assert.doesNotMatch(N.answer(catalog,queries[0],userEdited),/No significa que incluya más películas/);
assert.equal(N.answer(catalog,'¿Cuánto cuesta Netflix Internacional?'),null);
assert.match(N.answer(catalog.map(x=>({...x,active:false})),queries[0]),/por confirmar/);
console.log('v0.6.13: Netflix Internacional - wording, previous default and custom text verified.');
''',encoding="utf-8")

gradle=root/"android/app/build.gradle.kts"
replace(gradle,"versionCode = 27","versionCode = 28","Android version code")
replace(gradle,'versionName = "0.6.12"','versionName = "0.6.13"',"Android version name")
for name in ["app.js","index.html","netflix-international.js"]:
    (assets/name).write_text((web/name).read_text(encoding="utf-8"),encoding="utf-8")

print("v0.6.13: Netflix Internacional wording clarified; old stored default migrated, custom text retained.")
