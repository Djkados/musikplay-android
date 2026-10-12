from pathlib import Path
root=Path("source/autoresponder-pro")
p=root/"android/app/src/main/java/com/autoresponder/pro/ConversationFlow.kt"
s=p.read_text(encoding="utf-8")
old='''val pay=PaymentReplies.reply(config,business,"medios de pago")?:return null'''
new='''val pay=PaymentReplies.reply(config,business,"medios de pago",casual=true)?:return null'''
assert s.count(old)==1
p.write_text(s.replace(old,new,1),encoding="utf-8")
p=root/"android/app/build.gradle.kts"
s=p.read_text(encoding="utf-8")
assert s.count('versionCode = 19')==1 and s.count('versionName = "0.6.4"')==1
p.write_text(s.replace('versionCode = 19','versionCode = 20')
    .replace('versionName = "0.6.4"','versionName = "0.6.5"'),encoding="utf-8")
for fname in ["web/index.html","android/app/src/main/assets/index.html"]:
 p=root/fname
 p.write_text(p.read_text(encoding="utf-8").replace("Versión 0.6.4","Versión 0.6.5"),encoding="utf-8")
print("v0.6.5 signed upgrade versionCode 20; contextual payment menu uses the same short natural voice")
