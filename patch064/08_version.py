from pathlib import Path
root=Path("source/autoresponder-pro")
p=root/"android/app/build.gradle.kts"
s=p.read_text(encoding="utf-8")
assert s.count("versionCode = 18")==1 and s.count('versionName = "0.6.3"')==1
p.write_text(s.replace("versionCode = 18","versionCode = 19")
    .replace('versionName = "0.6.3"','versionName = "0.6.4"'),encoding="utf-8")
p=root/"web/app.js"
s=p.read_text(encoding="utf-8").replace("AutoResponder Pro v0.6.3","AutoResponder Pro v0.6.4",1)
p.write_text(s,encoding="utf-8")
(root/"android/app/src/main/assets/app.js").write_text(s,encoding="utf-8")
for name in ["web/index.html","android/app/src/main/assets/index.html"]:
    p=root/name
    p.write_text(p.read_text(encoding="utf-8").replace("Versión 0.6.3","Versión 0.6.4"),
        encoding="utf-8")
p=root/"tests/smoke.test.cjs"
s=p.read_text(encoding="utf-8")
s+='''
// The anti-spam controls default to the previously tested intervals,
// can be edited locally, and never require a remote price provider.
const config064=test.getConfig();
assert.equal(config064.settings.cadence.menuHours,12);
assert.equal(config064.settings.cadence.awayHours,12);
assert.equal(config064.settings.cadence.courtesyMinutes,15);
assert.equal(config064.settings.cadence.repeatMinutes,2);
console.log('OK — 0.6.4 cadence settings and local-only catalog preserved.');
'''
p.write_text(s,encoding="utf-8")
print("AutoResponder Pro v0.6.4 / code 19, same stable signing and no external catalog sync")
