from pathlib import Path
root=Path("source/autoresponder-pro")
p=root/"android/app/build.gradle.kts"
s=p.read_text(encoding="utf-8")
assert s.count('versionCode = 20')==1 and s.count('versionName = "0.6.5"')==1
p.write_text(s.replace('versionCode = 20','versionCode = 21')
              .replace('versionName = "0.6.5"','versionName = "0.6.6"'),
              encoding="utf-8")
p=root/"web/app.js";s=p.read_text(encoding="utf-8")
assert s.count("AutoResponder Pro v0.6.5")==1
s=s.replace("AutoResponder Pro v0.6.5","AutoResponder Pro v0.6.6",1)
p.write_text(s,encoding="utf-8")
(root/"android/app/src/main/assets/app.js").write_text(s,encoding="utf-8")
for filename in ["web/index.html","android/app/src/main/assets/index.html"]:
 p=root/filename;s=p.read_text(encoding="utf-8")
 assert s.count("Versión 0.6.5")==1
 p.write_text(s.replace("Versión 0.6.5","Versión 0.6.6"),encoding="utf-8")
print("AutoResponder v0.6.6: Android versionCode 21, same installed-package and stable signing")
