from pathlib import Path
p=Path("source/autoresponder-pro/tests/schedules.test.cjs")
s=p.read_text(encoding="utf-8")
old="assert.equal(respond('normal','Prueba','Netflix',false,local('2026-10-11T18:00')).reply,'Respuesta exclusiva MoviePlay');"
new="""const movieResult=respond('normal','Prueba','Netflix',false,local('2026-10-11T18:00'));
assert.match(movieResult.reply,/MOVIEPLAY|MoviePlay/);
assert.doesNotMatch(movieResult.reply,/Las Tres M/);
assert.match(movieResult.reply,/26 días[\\\\s\\\\S]*?\\\\$14\\\\.000/);"""
assert s.count(old)==1
p.write_text(s.replace(old,new),encoding="utf-8")
print("Updated multi-business integration test to check current catalog reply without old hardcoded response")
