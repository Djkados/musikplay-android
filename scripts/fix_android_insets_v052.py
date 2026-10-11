from pathlib import Path

root = Path("source/autoresponder-pro")
activity = root / "android/app/src/main/java/com/autoresponder/pro/MainActivity.kt"
text = activity.read_text()

def replace_once(before, after):
    global text
    if text.count(before) != 1:
        raise RuntimeError("No se encontró el fragmento exacto; se detiene para evitar cambios incorrectos")
    text = text.replace(before, after, 1)

replace_once("import android.os.Bundle\n", "import android.os.Bundle\nimport android.graphics.Color\nimport android.view.ViewGroup\nimport android.view.WindowManager\nimport android.widget.FrameLayout\n")
replace_once("import androidx.core.view.ViewCompat\n", "import androidx.core.view.ViewCompat\nimport androidx.core.view.WindowCompat\n")
replace_once("""        webView = WebView(this)
""", """        // Android 15+ enforces edge-to-edge: the parent, not WebView, owns insets.
        WindowCompat.setDecorFitsSystemWindows(window, false)
        WindowCompat.getInsetsController(window, window.decorView).apply {
            isAppearanceLightStatusBars = false
            isAppearanceLightNavigationBars = false
        }
        window.setSoftInputMode(WindowManager.LayoutParams.SOFT_INPUT_ADJUST_RESIZE)
        val safeContainer = FrameLayout(this).apply {
            setBackgroundColor(Color.rgb(8, 13, 16))
            clipToPadding = true
        }
        webView = WebView(this).apply { setBackgroundColor(Color.rgb(8, 13, 16)) }
""")
replace_once("""        // Prevent Android 15+ status/navigation bars from covering dashboard controls.
        ViewCompat.setOnApplyWindowInsetsListener(webView) { view, insets ->
            val bars = insets.getInsets(WindowInsetsCompat.Type.systemBars())
            view.setPadding(bars.left, bars.top, bars.right, bars.bottom)
            insets
        }
        setContentView(webView)
        webView.loadUrl("https://appassets.androidplatform.net/assets/index.html")
""", """        // Keep the dashboard out of the status bar, display cutout, navigation
        // bar, and IME area, including when navigation mode or orientation changes.
        ViewCompat.setOnApplyWindowInsetsListener(safeContainer) { view, insets ->
            val bars = insets.getInsets(
                WindowInsetsCompat.Type.systemBars() or WindowInsetsCompat.Type.displayCutout()
            )
            val keyboard = insets.getInsets(WindowInsetsCompat.Type.ime())
            view.setPadding(bars.left, bars.top, bars.right, maxOf(bars.bottom, keyboard.bottom))
            WindowInsetsCompat.CONSUMED
        }
        safeContainer.addView(
            webView,
            FrameLayout.LayoutParams(
                ViewGroup.LayoutParams.MATCH_PARENT,
                ViewGroup.LayoutParams.MATCH_PARENT
            )
        )
        setContentView(safeContainer)
        ViewCompat.requestApplyInsets(safeContainer)
        webView.loadUrl("https://appassets.androidplatform.net/assets/index.html")
""")
activity.write_text(text)

manifest = root / "android/app/src/main/AndroidManifest.xml"
s = manifest.read_text()
before = '<activity android:name=".MainActivity" android:exported="true">'
assert s.count(before) == 1
manifest.write_text(s.replace(before, '<activity android:name=".MainActivity" android:exported="true" android:windowSoftInputMode="adjustResize">'))

gradle = root / "android/app/build.gradle.kts"
s = gradle.read_text()
assert 'versionCode = 6' in s and 'versionName = "0.5.1"' in s
gradle.write_text(s.replace('versionCode = 6','versionCode = 7').replace('versionName = "0.5.1"','versionName = "0.5.2"'))
print("Versión 0.5.2: inset de barras Android corregido")
