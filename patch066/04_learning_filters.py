from pathlib import Path
root=Path("source/autoresponder-pro")
p=root/"web/learning-engine.js"
s=p.read_text(encoding="utf-8")
def rep(a,b,why):
 global s
 assert s.count(a)==1,(why,s.count(a))
 s=s.replace(a,b,1)

rep('''  const secret=/\\b(comprobante|pago|pague|pagado|transferencia|consignacion|bancolombia|nequi|daviplata|llave|cuenta bancaria|recibo|foto|imagen|captura|adjunto|documento|sticker|video|audio|contraseña|contrasena|otp|codigo|clave|token|pin|cedula|direccion|domicilio|tarjeta|banco|clave dinamica)\\b/i;''',
'''  const secret=/\\b(comprobante|pague|pagado|transferencia realizada|consignacion realizada|ya transferi|ya pague|recibo|foto|imagen|captura|adjunto|documento|sticker|video|audio|contraseña|contrasena|otp|codigo|clave|token|pin|cedula|direccion|domicilio|tarjeta|clave dinamica)\\b/i;
  const evidence=/\\b(pago realizado|pago exitoso|soporte de pago|pago pedro|pago [a-zñ]+ [a-zñ]+|ya hice el pago|ya te pague|te consigne|me llego comprobante)\\b/i;''',
"separate safe payment questions from receipt evidence")
rep('''    if(secret.test(v) || /[<>$*]/.test(v) || v.split(' ').length>18)return null;''',
'''    if(secret.test(v) || evidence.test(v) || /[<>$*]/.test(v) ||
       v.split(' ').length>18)return null;''',
"exclude receipts while allowing harmless payment requests")
# Catalog/rule aliases must not inadvertently catch payment intents.
rep('''    if(!v||v.length<3||v.length>45 || /[0-9@/\\\\:#.$]/.test(v) || secret.test(v))return false;''',
'''    if(!v||v.length<3||v.length>45 || /[0-9@/\\\\:#.$]/.test(v) ||
        secret.test(v) || evidence.test(v) ||
        /\\b(pago|nequi|daviplata|bancolombia|llave|renovacion|renovar|gracias|transferir)\\b/.test(v))
      return false;''',
"catalog alias safety")
anchor="  function aliasFromPhrase(phrase) {"
extra='''  const intentKinds=new Set(["payment","payment_nequi","payment_bancolombia",
    "payment_daviplata","payment_llave","courtesy","renewal","human"]);
  function safeIntentAlias(raw,intent) {
    if(!intentKinds.has(intent))return false;
    const original=String(raw||"").trim(),v=normalize(original);
    if(original.length<4||original.length>100||v.length<4||v.length>90)return false;
    if(/[0-9@/\\\\:#.$]/.test(original)||/https?:|www\\./i.test(original) ||
       secret.test(v)||evidence.test(v))return false;
    if(!/^[\\p{L}\\s¿?¡!.,;\\-]+$/u.test(original))return false;
    if(new Set(["pago","cuenta","info","ok","hola","si","no","plata","dinero"]).has(v))
      return false;
    if(intent.startsWith("payment") && v.split(" ").length===1 &&
       !["nequi","daviplata","bancolombia","llave"].includes(v))
      return false;
    return true;
  }
'''
assert s.count(anchor)==1
s=s.replace(anchor,extra+anchor,1)
rep('''  return Object.freeze({normalize,safePhrase,safeAlias,aliasFromPhrase,absorb});''',
'''  return Object.freeze({normalize,safePhrase,safeAlias,safeIntentAlias,
    aliasFromPhrase,absorb});''',
"export safe intent alias")
p.write_text(s,encoding="utf-8")
(root/"android/app/src/main/assets/learning-engine.js").write_text(s,encoding="utf-8")
print("Learning engine now accepts harmless payment questions as suggestions while strictly excluding receipt proofs and phone/account data.")
