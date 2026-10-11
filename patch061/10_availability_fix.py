from pathlib import Path
root=Path("source/autoresponder-pro")
p=root/"android/app/src/main/java/com/autoresponder/pro/LocalCatalog.kt"
s=p.read_text(encoding="utf-8")
a='data class Match(val text:String,val imageTag:String="",val count:Int=0)'
b='data class Match(val text:String,val imageTag:String="",val count:Int=0,val available:Boolean=false)'
assert s.count(a)==1
s=s.replace(a,b,1)
a='return if(result.length<=1600)Match(result,imageTag,chosen.size) else null'
b='return if(result.length<=1600)Match(result,imageTag,chosen.size,anythingAvailable) else null'
assert s.count(a)==1
p.write_text(s.replace(a,b,1),encoding="utf-8")
p=root/"android/app/src/main/java/com/autoresponder/pro/GuidedAssistant.kt"
s=p.read_text(encoding="utf-8")
assert s.count('quote.imageTag.isBlank()')==2
p.write_text(s.replace('quote.imageTag.isBlank()','!quote.available'),encoding="utf-8")
p=root/"web/app.js"
s=p.read_text(encoding="utf-8")
a='''return {reply:lines.join("\\n"),imageTag:firstActive?.imageTag||"",
      catalogId:items[0]?.id||""};'''
b='''return {reply:lines.join("\\n"),imageTag:firstActive?.imageTag||"",
      catalogId:items[0]?.id||"",available:!!firstActive};'''
assert s.count(a)==1
s=s.replace(a,b,1)
a='const active=!!quote?.imageTag;'
assert s.count(a)==1
s=s.replace(a,'const active=quote?.available===true;',1)
p.write_text(s,encoding="utf-8")
(root/"android/app/src/main/assets/app.js").write_text(s,encoding="utf-8")
print("Availability is independent of optional advertisement image tags (Android and web)")
