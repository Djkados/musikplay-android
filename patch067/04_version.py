from pathlib import Path
root=Path("source/autoresponder-pro")
p=root/"android/app/build.gradle.kts"
s=p.read_text(encoding="utf-8")
assert s.count("versionCode = 21")==1 and s.count('versionName = "0.6.6"')==1
p.write_text(s.replace("versionCode = 21","versionCode = 22")
              .replace('versionName = "0.6.6"','versionName = "0.6.7"'),
              encoding="utf-8")
p=root/"web/app.js"
s=p.read_text(encoding="utf-8")
assert s.count("AutoResponder Pro v0.6.6")==1
p.write_text(s.replace("AutoResponder Pro v0.6.6","AutoResponder Pro v0.6.7",1),encoding="utf-8")
(root/"android/app/src/main/assets/app.js").write_text(p.read_text(encoding="utf-8"),encoding="utf-8")
for filename in ("web/index.html","android/app/src/main/assets/index.html"):
 p=root/filename;s=p.read_text(encoding="utf-8")
 assert s.count("Versión 0.6.6")==1
 p.write_text(s.replace("Versión 0.6.6","Versión 0.6.7"),encoding="utf-8")
print("AutoResponder Pro v0.6.7 / versionCode 22, identical package and stable signing key")
