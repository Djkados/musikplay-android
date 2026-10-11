from pathlib import Path
root=Path("source/autoresponder-pro")
js=r'''/*
 * Offline supervised learning for AutoResponder Pro.
 * Only sanitized, unrecognized plain-text expressions become suggestions.
 * Nothing is learned or added to outgoing rules without the owner's approval.
 */
(function(root,factory){
  const api=factory();
  if(typeof module!=='undefined' && module.exports)module.exports=api;
  if(root)root.LearningEngine=api;
})(typeof window!=='undefined'?window:null,function(){
  'use strict';
  const normalize=s=>String(s||'').toLowerCase().normalize('NFD')
    .replace(/[\u0300-\u036f]/g,'').replace(/\s+/g,' ').trim();
  const secret=/\b(comprobante|pago|pague|pagado|transferencia|consignacion|bancolombia|nequi|daviplata|llave|cuenta bancaria|recibo|foto|imagen|captura|adjunto|documento|sticker|video|audio|contraseña|contrasena|otp|codigo|clave|token|pin|cedula|direccion|domicilio|tarjeta|banco|clave dinamica)\b/i;
  const common=new Set('hola buenas buenos dias tardes noches gracias ok listo si no quiero quisiera saber cuanto vale cuesta precio precios que como cual cuales tienen disponible tienen para por favor de el la los las una un me tienen tienes en del'.split(' '));
  function safePhrase(raw) {
    const original=String(raw||'').trim();
    if(original.length<8||original.length>110 || /[0-9@/\\:#]|https?:|www\./i.test(original))
      return null;
    const v=normalize(original);
    if(secret.test(v) || /[<>$*]/.test(v) || v.split(' ').length>18)return null;
    if(!/^[\p{L}\s¿?¡!.,;-]+$/u.test(original))return null;
    if(v.split(' ').filter(t=>t.length>=4).length<1)return null;
    return v;
  }
  function safeAlias(raw) {
    const v=normalize(raw);
    if(!v||v.length<3||v.length>45 || /[0-9@/\\:#.$]/.test(v) || secret.test(v))return false;
    if(!/^[a-zñ\s\-]+$/i.test(v))return false;
    if(common.has(v) || v.split(' ').every(x=>common.has(x)))return false;
    return true;
  }
  function aliasFromPhrase(phrase) {
    const words=phrase.replace(/[¿?¡!.,;-]/g,' ').split(' ')
      .filter(w=>w.length>=4 && !common.has(w));
    const alias=words.slice(-2).join(' ').slice(0,45);
    return safeAlias(alias)?alias:'';
  }
  function idOf(business,phrase) {
    let h=2166136261;
    for(const c of business+'|'+phrase)h=Math.imul(h^c.charCodeAt(0),16777619)>>>0;
    return 'learn-'+h.toString(36);
  }
  function absorb(previous,inbox) {
    const all=Array.isArray(previous)?previous.map(s=>({...s})):[];
    for(const n of (Array.isArray(inbox)?inbox:[])) {
      if(!n || n.learnEligible!==true || n.hasAttachment || n.autoStatus==='manual_review')continue;
      if(n.autoStatus!=='skipped')continue;
      if(!['Consulta sin regla aprobada','Negocio ambiguo: revisión manual'].includes(n.autoReason))continue;
      const phrase=safePhrase(n.text);
      if(!phrase)continue;
      const business=['movieplay','tresm'].includes(n.assistant)?n.assistant:'none';
      const id=idOf(business,phrase);
      const existing=all.find(x=>x.id===id);
      if(existing){existing.count=Math.min(99,(existing.count||1)+1);continue;}
      all.unshift({id,phrase,alias:aliasFromPhrase(phrase),assistant:business,
        status:'pending',count:1,createdAt:Date.now()});
    }
    return all.slice(0,45);
  }
  return Object.freeze({normalize,safePhrase,safeAlias,aliasFromPhrase,absorb});
});
'''
(root/"web/learning-engine.js").write_text(js,encoding="utf-8")
(root/"android/app/src/main/assets/learning-engine.js").write_text(js,encoding="utf-8")
for f in ["web/index.html","android/app/src/main/assets/index.html"]:
  p=root/f;s=p.read_text(encoding="utf-8")
  old='  <script src="app.js"></script>'
  assert s.count(old)==1
  p.write_text(s.replace(old,'  <script src="learning-engine.js"></script>\n'+old,1),encoding="utf-8")
print("Local privacy-filtered supervised learning engine added to browser and APK")
