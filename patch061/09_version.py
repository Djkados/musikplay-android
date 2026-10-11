from pathlib import Path
root=Path("source/autoresponder-pro")
p=root/"android/app/build.gradle.kts"
s=p.read_text(encoding="utf-8")
assert s.count('versionCode = 15')==1 and s.count('versionName = "0.6.0"')==1
p.write_text(s.replace('versionCode = 15','versionCode = 16')
              .replace('versionName = "0.6.0"','versionName = "0.6.1'),encoding="utf-8")
# The version name above is checked and repaired explicitly to ensure valid gradle syntax.
gradle=p.read_text(encoding="utf-8")
gradle=gradle.replace('versionName = "0.6.1','versionName = "0.6.1"')
p.write_text(gradle,encoding="utf-8")
p=root/"web/app.js";s=p.read_text(encoding="utf-8")
s=s.replace("AutoResponder Pro v0.6.0","AutoResponder Pro v0.6.1",1)
p.write_text(s,encoding="utf-8")
(root/"android/app/src/main/assets/app.js").write_text(s,encoding="utf-8")
for name in ["web/index.html","android/app/src/main/assets/index.html"]:
  p=root/name;s=p.read_text(encoding="utf-8")
  p.write_text(s.replace("Versión 0.6.0","Versión 0.6.1"),encoding="utf-8")
print("AutoResponder Pro 0.6.1 / versionCode 16 / persistent debug signature retained")
