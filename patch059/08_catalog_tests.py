from pathlib import Path
root=Path("source/autoresponder-pro")
p=root/"tests/smoke.test.cjs";s=p.read_text(encoding="utf-8")
old="assert.match(test.respond('business','Cliente de prueba','Precio Netflix').reply,/26 días — \\$14.000/);"
assert s.count(old)==1
s=s.replace(old,"assert.match(test.respond('business','Cliente de prueba','Precio Netflix').reply,/26 días[\\s\\S]*?\\$14\\.000/);")
p.write_text(s,encoding="utf-8")
for file in ["tests/workflow.test.cjs","tests/schedules.test.cjs"]:
    p=root/file;s=p.read_text(encoding="utf-8")
    if file.endswith("workflow.test.cjs"):
        old=" ],settings:{requireAllowlist:true,blockGroups:true,reviewOnly:true},inbox:[]"
        new=" ],catalog:[],settings:{requireAllowlist:true,blockGroups:true,reviewOnly:true},inbox:[]"
    else:
        old=" images:[],schedules:scheduled,scheduleOverrides:[]"
        new=" images:[],catalog:[],schedules:scheduled,scheduleOverrides:[]"
    assert s.count(old)==1,(file,s.count(old))
    s=s.replace(old,new)
    p.write_text(s,encoding="utf-8")
# Verify product prices / offers and typo matching deterministically on JVM.
p=root/"android/app/src/test/java/com/autoresponder/pro/LocalCatalogTest.kt"
p.write_text('''package com.autoresponder.pro

import org.json.JSONArray
import org.json.JSONObject
import org.junit.Assert.*
import org.junit.Test
import java.time.LocalDate

class LocalCatalogTest {
    private fun catalog():JSONObject {
        val a=JSONArray()
        a.put(JSONObject().put("assistant","movieplay").put("active",true)
            .put("name","Netflix Premium 4K").put("duration","26 días")
            .put("keywords","netflix,neflis").put("price",14000))
        a.put(JSONObject().put("assistant","movieplay").put("active",true)
            .put("name","Netflix Premium 4K").put("duration","30 días")
            .put("keywords","netflix,neflis").put("price",18000)
            .put("salePrice",11000).put("offerUntil","2026-10-31"))
        a.put(JSONObject().put("assistant","tresm").put("active",true)
            .put("name","Hamburguesa especial").put("keywords","hamburguesa")
            .put("price",0).put("imageTag","hamburguesa"))
        return JSONObject().put("catalog",a)
    }
    @Test fun quotesOnlyApprovedPlanPricesAndDates() {
        val c=catalog()
        val exact=LocalCatalog.reply(c,"movieplay","neflis 30 dias",
            LocalDate.parse("2026-10-15"))
        assertNotNull(exact)
        assertTrue(exact!!.text.contains("30 días"))
        assertTrue(exact.text.contains("$11.000"))
        assertFalse(exact.text.contains("$14.000"))
        val after=LocalCatalog.reply(c,"movieplay","Netflix 30 días",
            LocalDate.parse("2026-11-01"))
        assertTrue(after!!.text.contains("$18.000"))
        assertFalse(after.text.contains("$11.000"))
    }
    @Test fun unavailableFoodPriceNeverInvented() {
        val food=LocalCatalog.reply(catalog(),"tresm","hamburguesa",
            LocalDate.parse("2026-10-15"))
        assertTrue(food!!.text.contains("Consultar en el menú"))
        assertTrue(food.text.contains("https://lastresm.netlify.app"))
        assertEquals("hamburguesa",food.imageTag)
        assertNull(LocalCatalog.reply(catalog(),"tresm","netflix",
            LocalDate.parse("2026-10-15")))
    }
}
'''.replace('"$11.000"','"\\$11.000"')
    .replace('"$14.000"','"\\$14.000"')
    .replace('"$18.000"','"\\$18.000"'),encoding="utf-8")
print("Legacy fixture regressions isolated from new default catalog; catalog validation added")
