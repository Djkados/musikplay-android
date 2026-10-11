from pathlib import Path
root=Path("source/autoresponder-pro")
p=root/"android/app/build.gradle.kts"
s=p.read_text(encoding="utf-8")
assert s.count('versionCode = 14')==1 and s.count('versionName = "0.5.9"')==1
p.write_text(s.replace('versionCode = 14','versionCode = 15')
              .replace('versionName = "0.5.9"','versionName = "0.6.0"'),encoding="utf-8")
p=root/"web/app.js";s=p.read_text(encoding="utf-8")
s=s.replace("AutoResponder Pro v0.5.9","AutoResponder Pro v0.6.0",1)
p.write_text(s,encoding="utf-8")
(root/"android/app/src/main/assets/app.js").write_text(s,encoding="utf-8")
p=root/"web/index.html";s=p.read_text(encoding="utf-8")
s=s.replace('Versión 0.5.9 ·','Versión 0.6.0 ·',1)
p.write_text(s,encoding="utf-8")
(root/"android/app/src/main/assets/index.html").write_text(s,encoding="utf-8")
print("v0.6.0 / versionCode 15 with same persistent signing certificate")
