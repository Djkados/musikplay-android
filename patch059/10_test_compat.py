from pathlib import Path
p=Path("source/autoresponder-pro/tests/schedules.test.cjs")
s=p.read_text(encoding="utf-8")
a="assert.match(respond('business','Prueba','hamburguesa',false,local('2026-10-10T23:00')).reply,/sábados y domingos/);"
b="assert.match(respond('business','Prueba','hamburguesa',false,local('2026-10-10T23:00')).reply,/sábados y domingos/i);"
assert s.count(a)==1
s=s.replace(a,b)
assert s.count(",/Las Tres M/);")==1
s=s.replace(",/Las Tres M/);",",/Las Tres M/i);")
p.write_text(s,encoding="utf-8")
print("Schedule regression accepts professional uppercase headings")
