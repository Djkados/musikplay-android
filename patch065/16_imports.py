from pathlib import Path
p=Path("source/autoresponder-pro/android/app/src/test/java/com/autoresponder/pro/NativeAutoReplyEngineTest.kt")
s=p.read_text(encoding="utf-8")
anchor="import org.junit.Assert.assertTrue\n"
assert s.count(anchor)==1
s=s.replace(anchor,anchor+"import org.junit.Assert.assertFalse\nimport org.junit.Assert.assertNotEquals\n",1)
p.write_text(s,encoding="utf-8")
print("New seller/renewal tests import JUnit assertFalse and assertNotEquals")

