from pathlib import Path
p=Path("source/autoresponder-pro/web/app.js")
s=p.read_text(encoding="utf-8")
def rep(a,b):
 global s
 assert s.count(a)==1,(a[:100],s.count(a))
 s=s.replace(a,b,1)

rep("  function paymentAnswer(assistant,text){",
    "  function paymentAnswer(assistant,text,casual=false){")

old='''|\\ba donde transfiero\\b|\\bpagar el servicio\\b/.test(n)'''
new='''|\\ba donde transfiero\\b|\\bpagar el servicio\\b|\\b(?:donde|a donde|por donde|en donde) (?:te |le |les |puedo )?(?:transfiero|transferir|consigno|deposito)\\b|\\b(?:a que|a cual) (?:cuenta|numero|llave) (?:te )?(?:transfiero|transfieren|transfiera|puedo transferir)?\\b|\\b(?:pasame|mandame|enviame|me pasas|me mandas|me compartes) (?:las? )?(?:cuentas?|datos? (?:de|para) pago|medios? de pago|numero|llave)\\b|\\b(?:quiero|voy a|puedo) (?:transferirte|transferir|pagarte)\\b/.test(n)'''
rep(old,new)

anchor='''    const holder=pay.holder?"👤 *Titular:* "+pay.holder+"\\n\\n":"";'''
insert='''    const holder=pay.holder?"👤 *Titular:* "+pay.holder+"\\n\\n":"";
    if(casual){
      if(type==="menu")return "Claro 😊 ¿Por cuál medio te queda más fácil?\\n\\n"+
        "1️⃣ Nequi\\n2️⃣ Bancolombia\\n3️⃣ DaviPlata\\n4️⃣ Llave\\n\\n"+
        "Dime el número o el medio y te paso los datos.";
      if(type==="llaves"){
        const keys=names.map(k=>pay[k]?.key?
          (k==="bancolombia"?"Bancolombia":k==="daviplata"?"DaviPlata":"Nequi")+
          ": "+pay[k].key:null).filter(Boolean);
        return "Claro 🙌 Estas son las llaves que manejo:\\n\\n"+keys.join("\\n")+
          "\\n\\nCuando transfieras, me envías el comprobante y lo reviso.";
      }
      const name=type==="nequi"?"Nequi":type==="bancolombia"?"Bancolombia":"DaviPlata";
      const detail=pay[type]||{};
      if(!detail.number&&!detail.key)
        return "Por ahora no tengo configurados los datos de "+name+
          " para este negocio. Te confirmo por aquí. 🙌";
      return "Claro 😊 Te paso los datos de "+name+":\\n\\n"+
        (pay.holder?"👤 "+pay.holder+"\\n":"")+
        (detail.number?(type==="bancolombia"?"🏦 Cuenta de ahorros: ":"📲 Número: ")+
          detail.number+"\\n":"")+
        (detail.key?"🔑 Llave: "+detail.key:"")+
        "\\n\\nCuando transfieras, me envías el comprobante y lo reviso. 🙌";
    }'''
rep(anchor,insert)
p.write_text(s,encoding="utf-8")
Path("source/autoresponder-pro/android/app/src/main/assets/app.js").write_text(s,encoding="utf-8")
print("Browser simulator now recognizes 'donde te transfiero' and shows short first-person seller payment responses.")
