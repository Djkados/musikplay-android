from pathlib import Path
p=Path("source/autoresponder-pro/android/app/src/test/java/com/autoresponder/pro/NativeAutoReplyEngineTest.kt")
s=p.read_text(encoding="utf-8")
a="import org.junit.Assert.assertEquals\n"
assert s.count(a)==1
p.write_text(s.replace(a,a+"import org.junit.Assert.assertTrue\n",1),encoding="utf-8")
print("Imported JUnit assertTrue for formatted selector tests")
