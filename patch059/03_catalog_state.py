from pathlib import Path
root=Path("source/autoresponder-pro")
p=root/"web/app.js"
s=p.read_text(encoding="utf-8")
def change(a,b):
 global s
 assert s.count(a)==1,(a[:70],s.count(a))
 s=s.replace(a,b,1)
catalogSeed='''  const catalogDefaults=()=>[
    {id:"nf26",assistant:"movieplay",name:"Netflix Premium 4K",type:"service",duration:"26 días",price:14000,salePrice:0,offerUntil:"",keywords:"netflix,neflis,netflis",imageTag:"netflix",active:true},
    {id:"nf28",assistant:"movieplay",name:"Netflix Premium 4K",type:"service",duration:"28 días",price:16000,salePrice:0,offerUntil:"",keywords:"netflix,neflis,netflis",imageTag:"netflix",active:true},
    {id:"nf30",assistant:"movieplay",name:"Netflix Premium 4K",type:"service",duration:"30 días",price:18000,salePrice:0,offerUntil:"",keywords:"netflix,neflis,netflis",imageTag:"netflix",active:true},
    {id:"dp30",assistant:"movieplay",name:"Disney Premium",type:"service",duration:"30 días",price:0,salePrice:0,offerUntil:"",keywords:"disney,disney plus",imageTag:"disney",active:true},
    {id:"pv30",assistant:"movieplay",name:"Prime Video",type:"service",duration:"30 días",price:0,salePrice:0,offerUntil:"",keywords:"prime video,prime",imageTag:"prime",active:true},
    {id:"mp30",assistant:"movieplay",name:"Max Premium",type:"service",duration:"30 días",price:0,salePrice:0,offerUntil:"",keywords:"max premium,max",imageTag:"max",active:true},
    {id:"ham",assistant:"tresm",name:"Hamburguesa sencilla",type:"food",duration:"",price:0,salePrice:0,offerUntil:"",keywords:"hamburguesa,amburguesa",imageTag:"hamburguesa",active:true},
    {id:"hame",assistant:"tresm",name:"Hamburguesa especial",type:"food",duration:"",price:0,salePrice:0,offerUntil:"",keywords:"hamburguesa,amburguesa",imageTag:"hamburguesa",active:true},
    {id:"perro",assistant:"tresm",name:"Perro caliente",type:"food",duration:"",price:0,salePrice:0,offerUntil:"",keywords:"perro caliente,perro",imageTag:"perro",active:true},
    {id:"chuzo",assistant:"tresm",name:"Chuzo",type:"food",duration:"",price:0,salePrice:0,offerUntil:"",keywords:"chuzo",imageTag:"chuzo",active:true},
    {id:"patacon",assistant:"tresm",name:"Patacón",type:"food",duration:"",price:0,salePrice:0,offerUntil:"",keywords:"patacon",imageTag:"patacon",active:true}
  ];
'''
change("  const defaults = () => ({",catalogSeed+"  const defaults = () => ({")
change("],images:[],schedules:SE.defaultSchedules()", "],images:[],catalog:catalogDefaults(),schedules:SE.defaultSchedules()")
change("  let state = readConfig();", "  let state = readConfig();\n  state.catalog ||= catalogDefaults();")
change("migrateScheduleConfig();save();setRoute", "migrateScheduleConfig();state.catalog ||= catalogDefaults();save();setRoute")
change("const {channel,assistants,exceptions,allowlist,blocked,paused,rules,schedules,scheduleOverrides,settings}=state;",
       "const {channel,assistants,exceptions,allowlist,blocked,paused,rules,catalog,schedules,scheduleOverrides,settings}=state;")
change("JSON.stringify({version:1,channel,assistants,exceptions,allowlist,blocked,paused,rules,schedules,scheduleOverrides,settings})",
       "JSON.stringify({version:1,channel,assistants,exceptions,allowlist,blocked,paused,rules,catalog,schedules,scheduleOverrides,settings})")
# Improve recognition for common typographical variants without network AI.
change("    return SE.resolveAssignment(channel,contact,message,state.channel,state.exceptions);",
'''    const initial=SE.resolveAssignment(channel,contact,message,state.channel,state.exceptions);
    if(initial.method!=="clarify" || SE.detectBusiness(message).confidence==="mixed")return initial;
    const found=["movieplay","tresm"].filter(b=>catalogMatches(b,message).length>0);
    return found.length===1?{assistant:found[0],method:"catalog",confidence:"high"}:initial;''')
before="  function respond(channel,contact,text,group=false,at=new Date()){"
matcher='''  function catalogMatches(business,message) {
    const normalized=normalize(message).replace(/[^a-z0-9]+/g," ").trim();
    const words=normalized.split(" ");
    const oneEdit=(a,b)=>{
      if(Math.abs(a.length-b.length)>1)return false;
      let i=0,j=0,d=0;
      while(i<a.length&&j<b.length){
        if(a[i]===b[j]){i++;j++;continue;}
        if(++d>1)return false;
        if(a.length>b.length)i++;
        else if(b.length>a.length)j++;
        else{i++;j++;}
      }
      return d+a.length-i+b.length-j<=1;
    };
    return state.catalog.filter(i=>i.active&&i.assistant===business&&
      (String(i.keywords||"").split(",").concat(i.name||"")).some(term=>{
        const alias=normalize(term).replace(/[^a-z0-9]+/g," ").trim();
        return alias.length>=4 &&
          ((" "+normalized+" ").includes(" "+alias+" ") ||
           (alias.length>=5&&!alias.includes(" ")&&words.some(w=>w.length>=4&&oneEdit(w,alias))));
      }));
  }
  function catalogAnswer(business,message,at) {
    const matching=catalogMatches(business,message);
    if(!matching.length)return null;
    const plan=normalize(message).match(/\\b(26|28|30|60|90|180|365)\\s*(d[ií]as?|d)\\b/);
    const scoped=plan?matching.filter(i=>String(i.duration||"").includes(plan[1])):matching;
    const items=(scoped.length?scoped:matching).slice(0,7);
    const lines=[business==="tresm"?"🍔 *LAS TRES M*":"🎬 *MOVIEPLAY*",
       "",business==="tresm"?"📋 *Consulta de nuestro menú*":"📺 *Planes y precios disponibles*",""];
    const today=SE.bogotaParts(at).date;
    for(const item of items) {
      const price=Number(item.price)||0,offer=Number(item.salePrice)||0;
      const valid=price>0&&offer>0&&offer<price&&item.offerUntil&&item.offerUntil>=today;
      const amount=valid?offer:price;
      lines.push("• *"+item.name+"*"+(item.duration?" · "+item.duration:""));
      lines.push("  💵 "+(amount>0?"$"+amount.toLocaleString("es-CO"):
        business==="tresm"?"Consultar en el menú":"Precio por confirmar")+
        (valid?" (oferta hasta "+item.offerUntil+")":""));
    }
    lines.push("");
    if(business==="tresm")lines.push("📲 *Menú completo y pedidos:*",
      "https://lastresm.netlify.app","","¿Qué se te antoja? 😊");
    else lines.push("¿Cuál opción te interesa? 😊");
    return {reply:lines.join("\\n"),imageTag:items[0]?.imageTag||"",catalogId:items[0]?.id||""};
  }
'''
assert s.count(before)==1
s=s.replace(before,matcher+before,1)
change("    const rules=state.rules.filter(r=>r.active && r.assistant===assistant);",
'''    const offer=catalogAnswer(assistant,text,at);
    if(offer)return {...offer,assistant,unit,method:assign.method,status:"open",
      image:pickImage(assistant,offer.imageTag,SE.bogotaParts(at).date)};
    const rules=state.rules.filter(r=>r.active && r.assistant===assistant);''')
p.write_text(s,encoding="utf-8")
(root/"android/app/src/main/assets/app.js").write_text(s,encoding="utf-8")
print("Native-synchronized local catalog and typo-tolerant browser simulation installed")
