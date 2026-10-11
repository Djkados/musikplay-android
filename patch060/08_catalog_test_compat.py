from pathlib import Path
p=Path("source/autoresponder-pro/tests/smoke.test.cjs")
s=p.read_text(encoding="utf-8")
old="assert.equal(test.respond('business','Cliente de prueba','quiero una cuenta canva').requiresSelection,true);"
new="""const canva=test.respond('business','Cliente de prueba','quiero una cuenta canva');
assert.equal(canva.assistant,'movieplay');
assert.match(canva.reply,/Canva/);
assert.match(canva.reply,/30 días[\\s\\S]*?\\$8\\.000/);"""
assert s.count(old)==1
p.write_text(s.replace(old,new),encoding="utf-8")
print("Adapted legacy unknown-service test: Canva is now recognized with approved flyer price")
