from pathlib import Path
p=Path("source/autoresponder-pro/android/app/src/main/java/com/autoresponder/pro/MainActivity.kt")
s=p.read_text(encoding="utf-8")

old='''                        val payload = JSONObject().put("name", name).put("phone", phone)
                        webView.evaluateJavascript("window.onAndroidContactSelected(${payload});", null)'''
new='''                        // Android can resume WebView and redraw the HTML
                        // *after* the contact callback. Retain only the
                        // user-selected phone/name for up to ten minutes.
                        val payload = JSONObject().put("name", name)
                            .put("phone", phone)
                            .put("pickedAt", System.currentTimeMillis())
                        getSharedPreferences("selected_android_contact", MODE_PRIVATE)
                            .edit().putString("pending",payload.toString()).apply()
                        webView.post {
                            webView.evaluateJavascript(
                                "if(typeof window.onAndroidContactSelected==='function')"+
                                "window.onAndroidContactSelected("+
                                JSONObject.quote(payload.toString())+");",null)
                        }'''
assert s.count(old)==1,("onActivityResult expected",s.count(old))
s=s.replace(old,new,1)

old='''        @JavascriptInterface
        fun pickPhoneContact() {'''
new='''        /** Recover one chosen contact after WebView resume/reload. */
        @JavascriptInterface
        fun takeSelectedPhoneContact():String {
            val prefs=getSharedPreferences("selected_android_contact",MODE_PRIVATE)
            val raw=prefs.getString("pending","").orEmpty()
            if(raw.isBlank())return ""
            prefs.edit().remove("pending").apply()
            return try {
                val item=JSONObject(raw)
                val pickedAt=item.optLong("pickedAt",0L)
                val age=System.currentTimeMillis()-pickedAt
                if(age !in 0L..600_000L) "" else item.toString()
            }catch (_:Exception){""}
        }

        @JavascriptInterface
        fun pickPhoneContact() {'''
assert s.count(old)==1,("android bridge anchor",s.count(old))
s=s.replace(old,new,1)

old='''        fun pickPhoneContact() {
            runOnUiThread {
                val intent = Intent(Intent.ACTION_PICK, ContactsContract.CommonDataKinds.Phone.CONTENT_URI)'''
new='''        fun pickPhoneContact() {
            runOnUiThread {
                getSharedPreferences("selected_android_contact",MODE_PRIVATE)
                    .edit().remove("pending").apply()
                val intent = Intent(Intent.ACTION_PICK, ContactsContract.CommonDataKinds.Phone.CONTENT_URI)'''
assert s.count(old)==1,("picker open anchor",s.count(old))
s=s.replace(old,new,1)

p.write_text(s,encoding="utf-8")
print("Android stages the chosen name/phone across app resume, then exposes one-shot retrieval with ten-minute expiration")
