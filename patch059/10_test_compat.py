from pathlib import Path
p=Path("source/autoresponder-pro/tests/schedules.test.cjs")
s=p.read_text(encoding="utf-8")
a="assert.match(respond('business','Prueba','hamburguesa',false,local('2026-10-10T23:00')).reply,/sábados y domingos/);"
b="assert.match(respond('business','Prueba','hamburguesa',false,local('2026-10-10T23:00')).reply,/sábados y domingos/i);"
assert s.count(a)==1
p.write_text(s.replace(a,b),encoding="utf-8")
print("Schedule regression accepts professional uppercase headings")
