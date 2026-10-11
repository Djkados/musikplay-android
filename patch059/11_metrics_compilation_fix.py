from pathlib import Path
p=Path("source/autoresponder-pro/android/app/src/main/java/com/autoresponder/pro/WhatsAppNotificationListener.kt")
s=p.read_text(encoding="utf-8")
a='''        val key=when(status){
            "submitted_unverified"->"submittedCount"'''
b='''        val metricKey=when(status){
            "submitted_unverified"->"submittedCount"'''
assert s.count(a)==1
s=s.replace(a,b)
a='''        if(key!=null)report.edit().putLong(key,report.getLong(key,0L)+1L).apply()'''
b='''        if(metricKey!=null)report.edit().putLong(metricKey,report.getLong(metricKey,0L)+1L).apply()'''
assert s.count(a)==1
p.write_text(s.replace(a,b),encoding="utf-8")
print("Resolved colliding notification fingerprint and activity metric local variables")
