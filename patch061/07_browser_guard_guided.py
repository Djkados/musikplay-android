from pathlib import Path
p=Path("source/autoresponder-pro/web/app.js");s=p.read_text(encoding="utf-8")
def rep(a,b):
 global s
 assert s.count(a)==1,(a[:105],s.count(a))
 s=s.replace(a,b,1)
anchor="  function respond(channel,contact,text,group=false,at=new Date()){"
extra='''  function isEvidenceText(text){
    const t=normalize(text);
    if(/\\b(comprobante|captura de pago|pago realizado|pago exitoso|ya pague|ya hice el pago|te pague|te consigne|consignacion realizada|transferencia realizada|te transferi|te mande el pago|te envie el pago|recibo de pago|soporte de pago)\\b/.test(t))
      return true;
    if(t.startsWith("pago ") && !/^pago (con|por|en|mediante|nequi|daviplata|bancolombia|donde|como)\\b/.test(t) &&
      t.split(" ").length<=7)return true;
    return false;
  }
  function isMediaText(text){
    return /^(?:📷|📸|🖼|📎|📄|🎙|🎤|🎧|foto[: -]|imagen[: -]|documento[: -]|video[: -]|archivo adjunto|nota de voz)/i
      .test(String(text||"").trim());
  }
  function guidePurchase(business,text,at){
    const t=normalize(text);
    if(!/\\b(quiero comprar|quiero contratar|me interesa|quiero adquirir|como compro|como comprar|quiero renovar|quiero pedir|hacer un pedido|quiero un domicilio|me lo llevo|lo quiero comprar|para comprar|para pedir)\\b/.test(t))
      return null;
    const quote=catalogAnswer(business,text,at);
    const active=!!quote?.imageTag;
    const title=business==="movieplay"?"🎬 *MOVIEPLAY*":"🍔 *LAS TRES M*";
    const intro=quote?.reply||title+"\\n\\n"+(business==="movieplay"?
      "🛒 *Solicitud de compra*":"🍟 *Preparar tu pedido*");
    if(quote && !active)return {reply:intro+"\\n\\nEste producto figura temporalmente no disponible. ¿Quieres consultar otra opción?",image:null};
    const steps=business==="movieplay"?
      "📌 *Para continuar:*\\n1️⃣ Indica la plataforma y duración.\\n2️⃣ Confirma el plan que te interesa.\\n3️⃣ Solicita el medio de pago de tu preferencia.\\n\\n"+
      "🔐 La disponibilidad, el pago y la entrega se verifican antes de activar el servicio.":
      "📝 *Para preparar tu solicitud:*\\n1️⃣ Dinos los productos y cantidades.\\n2️⃣ Indica adiciones o cambios.\\n3️⃣ Confirma si es para recoger o a domicilio.\\n\\n"+
      "📍 Para domicilio comparte la dirección por WhatsApp.\\n✅ El pedido y valor final se confirman al revisarlo.";
    return {reply:intro+"\\n\\n"+steps,image:null};
  }
'''
assert s.count(anchor)==1
s=s.replace(anchor,extra+anchor,1)
a='''    const msg=normalize(text);
    if (/\\b(otp|pin|clave|contrasena|password|codigo de acceso|verificacion bancaria)\\b/.test(msg))'''
b='''    const msg=normalize(text);
    if(isMediaText(text)||isEvidenceText(text))
      return {reason:"Comprobante o adjunto: revisar directamente en WhatsApp, sin respuesta automática."};
    if(/\\b(asesor humano|persona real|hablar con alguien|hablar con asesor|atencion personal|necesito un asesor)\\b/.test(msg))
      return {reason:"El cliente pidió atención humana; no responder automáticamente."};
    if (/\\b(otp|pin|clave|contrasena|password|codigo de acceso|verificacion bancaria)\\b/.test(msg))'''
rep(a,b)
a='''    const offer=catalogAnswer(assistant,text,at);'''
b='''    const guided=guidePurchase(assistant,text,at);
    if(guided)return {...guided,assistant,unit,method:"guided",status:"open"};
    const offer=catalogAnswer(assistant,text,at);'''
rep(a,b)
rep("No se automatizan imágenes ni grupos. Si el teléfono identifica una respuesta manual tuya, intenta pausar ese chat 1 hora; revisa las pruebas en tu dispositivo.",
    "No se automatizan imágenes, comprobantes, confirmaciones bancarias ni grupos. Cuando detecta atención humana intenta pausar la conversación 1 hora.")
# Keep inbox text anonymous and avoid implying a receipt has been read or verified.
p.write_text(s,encoding="utf-8")
Path("source/autoresponder-pro/android/app/src/main/assets/app.js").write_text(s,encoding="utf-8")
print("Browser simulator respects media/payment evidence safety and reproduces guided presales")
