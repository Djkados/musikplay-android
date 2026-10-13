from pathlib import Path
root=Path("source/autoresponder-pro")
p=root/"android/app/build.gradle.kts"
s=p.read_text(encoding="utf-8")
assert s.count("versionCode = 24")==1 and s.count('versionName = "0.6.9"')==1
p.write_text(s.replace("versionCode = 24","versionCode = 25")
             .replace('versionName = "0.6.9"','versionName = "0.6.10"'),
             encoding="utf-8")
p=root/"web/app.js"
s=p.read_text(encoding="utf-8")
assert s.count("AutoResponder Pro v0.6.9")==1
p.write_text(s.replace("AutoResponder Pro v0.6.9","AutoResponder Pro v0.6.10",1),
             encoding="utf-8")
(root/"android/app/src/main/assets/app.js").write_text(p.read_text(encoding="utf-8"),
             encoding="utf-8")
for file in ["web/index.html","android/app/src/main/assets/index.html"]:
    p=root/file
    html=p.read_text(encoding="utf-8")
    assert html.count("Versión 0.6.9")==1
    p.write_text(html.replace("Versión 0.6.9","Versión 0.6.10"),encoding="utf-8")
print("AutoResponder Pro v0.6.10 / versionCode 25; same package, catalog and developer signing certificate")
