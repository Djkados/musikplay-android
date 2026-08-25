package com.movieplay.musikplay

import android.annotation.SuppressLint
import android.content.Intent
import android.graphics.Color
import android.net.Uri
import android.os.Bundle
import android.view.ViewGroup
import android.widget.FrameLayout
import android.webkit.CookieManager
import android.webkit.JavascriptInterface
import android.webkit.WebChromeClient
import android.webkit.WebResourceRequest
import android.webkit.WebResourceResponse
import android.webkit.WebSettings
import android.webkit.WebView
import android.webkit.WebViewClient
import androidx.activity.OnBackPressedCallback
import androidx.appcompat.app.AppCompatActivity
import androidx.core.view.ViewCompat
import androidx.core.view.WindowCompat
import androidx.core.view.WindowInsetsCompat
import androidx.core.view.WindowInsetsControllerCompat
import androidx.webkit.WebViewAssetLoader

class MainActivity : AppCompatActivity() {

    private lateinit var webView: WebView
    private lateinit var assetLoader: WebViewAssetLoader
    private lateinit var root: FrameLayout

    companion object {
        private const val APP_URL = "https://appassets.androidplatform.net/assets/web/index.html"
        private const val SPOTIFY_PACKAGE = "com.spotify.music"
    }

    @SuppressLint("SetJavaScriptEnabled")
    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)

        // Android 15 forces edge-to-edge for targetSdk 35.
        // We keep the black system bars and explicitly inset the app content.
        WindowCompat.setDecorFitsSystemWindows(window, false)
        window.statusBarColor = Color.BLACK
        window.navigationBarColor = Color.BLACK
        WindowInsetsControllerCompat(window, window.decorView).apply {
            isAppearanceLightStatusBars = false
            isAppearanceLightNavigationBars = false
        }

        assetLoader = WebViewAssetLoader.Builder()
            .addPathHandler("/assets/", WebViewAssetLoader.AssetsPathHandler(this))
            .build()

        webView = WebView(this).apply {
            setBackgroundColor(Color.BLACK)
            settings.javaScriptEnabled = true
            settings.domStorageEnabled = true
            settings.databaseEnabled = true
            settings.cacheMode = WebSettings.LOAD_DEFAULT
            settings.mediaPlaybackRequiresUserGesture = false
            settings.mixedContentMode = WebSettings.MIXED_CONTENT_NEVER_ALLOW
            settings.setSupportMultipleWindows(false)
            settings.useWideViewPort = true
            settings.loadWithOverviewMode = false
            settings.textZoom = 100
            settings.userAgentString = settings.userAgentString + " MusikplayAndroid/2.2"

            CookieManager.getInstance().setAcceptCookie(true)
            CookieManager.getInstance().setAcceptThirdPartyCookies(this, true)

            addJavascriptInterface(MusikplayBridge(), "AndroidMusikplay")
            webChromeClient = WebChromeClient()
            webViewClient = MusikplayWebViewClient(assetLoader)
        }

        root = FrameLayout(this).apply {
            setBackgroundColor(Color.BLACK)
            addView(
                webView,
                FrameLayout.LayoutParams(
                    ViewGroup.LayoutParams.MATCH_PARENT,
                    ViewGroup.LayoutParams.MATCH_PARENT
                )
            )
        }
        setContentView(root)

        ViewCompat.setOnApplyWindowInsetsListener(root) { view, insets ->
            val bars = insets.getInsets(
                WindowInsetsCompat.Type.systemBars() or WindowInsetsCompat.Type.displayCutout()
            )
            view.setPadding(bars.left, bars.top, bars.right, bars.bottom)
            insets
        }
        ViewCompat.requestApplyInsets(root)

        WebView.setWebContentsDebuggingEnabled(BuildConfig.DEBUG)

        if (!handleCallbackIntent(intent)) {
            webView.loadUrl(APP_URL)
        }

        onBackPressedDispatcher.addCallback(this, object : OnBackPressedCallback(true) {
            override fun handleOnBackPressed() {
                if (webView.canGoBack()) webView.goBack() else finish()
            }
        })
    }

    override fun onNewIntent(intent: Intent) {
        super.onNewIntent(intent)
        setIntent(intent)
        handleCallbackIntent(intent)
    }

    override fun onResume() {
        super.onResume()
        webView.onResume()
        webView.postDelayed({
            webView.evaluateJavascript(
                "window.onMusikplayNativeResume && window.onMusikplayNativeResume();",
                null
            )
        }, 250)
    }

    override fun onPause() {
        webView.onPause()
        super.onPause()
    }

    override fun onDestroy() {
        webView.removeJavascriptInterface("AndroidMusikplay")
        webView.destroy()
        super.onDestroy()
    }

    private fun handleCallbackIntent(sourceIntent: Intent?): Boolean {
        val uri = sourceIntent?.data ?: return false
        if (uri.scheme != "musikplay" || uri.host != "callback") return false

        val query = uri.encodedQuery.orEmpty()
        val fragment = uri.encodedFragment.orEmpty()
        val suffix = buildString {
            if (query.isNotBlank()) append("?").append(query)
            if (fragment.isNotBlank()) append("#").append(fragment)
        }
        webView.loadUrl("$APP_URL$suffix")
        return true
    }

    private fun spotifyInstalled(): Boolean = runCatching {
        packageManager.getPackageInfo(SPOTIFY_PACKAGE, 0)
        true
    }.getOrDefault(false)

    private fun openExternal(uri: Uri, packageName: String? = null) {
        val intent = Intent(Intent.ACTION_VIEW, uri)
        if (!packageName.isNullOrBlank()) intent.setPackage(packageName)
        runCatching { startActivity(intent) }.onFailure {
            runCatching { startActivity(Intent(Intent.ACTION_VIEW, uri)) }
        }
    }

    private fun spotifyWebUrl(uri: String): String? {
        if (!uri.startsWith("spotify:")) return null
        val pieces = uri.split(":")
        if (pieces.size < 3) return null
        val type = pieces[1]
        val id = pieces[2]
        if (type !in setOf("track", "album", "artist", "playlist", "show", "episode")) return null
        return "https://open.spotify.com/$type/$id?utm_campaign=$packageName"
    }

    inner class MusikplayBridge {
        @JavascriptInterface
        fun isNative(): Boolean = true

        @JavascriptInterface
        fun getClientId(): String = BuildConfig.SPOTIFY_CLIENT_ID

        @JavascriptInterface
        fun getRedirectUri(): String = BuildConfig.SPOTIFY_REDIRECT_URI

        @JavascriptInterface
        fun isSpotifyInstalled(): Boolean = spotifyInstalled()

        @JavascriptInterface
        fun openSpotify() {
            runOnUiThread {
                val launch = packageManager.getLaunchIntentForPackage(SPOTIFY_PACKAGE)
                if (launch != null) startActivity(launch)
                else openExternal(Uri.parse("https://play.google.com/store/apps/details?id=$SPOTIFY_PACKAGE"))
            }
        }

        @JavascriptInterface
        fun openSpotifyContent(spotifyUri: String) {
            runOnUiThread {
                if (!spotifyInstalled()) {
                    openExternal(Uri.parse("https://play.google.com/store/apps/details?id=$SPOTIFY_PACKAGE"))
                    return@runOnUiThread
                }
                val direct = runCatching { Uri.parse(spotifyUri) }.getOrNull()
                if (direct != null) {
                    val ok = runCatching {
                        val intent = Intent(Intent.ACTION_VIEW, direct).apply {
                            setPackage(SPOTIFY_PACKAGE)
                            putExtra(Intent.EXTRA_REFERRER, Uri.parse("android-app://$packageName"))
                        }
                        startActivity(intent)
                    }.isSuccess
                    if (ok) return@runOnUiThread
                }
                spotifyWebUrl(spotifyUri)?.let { openExternal(Uri.parse(it), SPOTIFY_PACKAGE) }
                    ?: openSpotify()
            }
        }
    }

    inner class MusikplayWebViewClient(
        private val loader: WebViewAssetLoader
    ) : WebViewClient() {

        override fun shouldInterceptRequest(
            view: WebView?,
            request: WebResourceRequest
        ): WebResourceResponse? = loader.shouldInterceptRequest(request.url)

        override fun shouldOverrideUrlLoading(
            view: WebView?,
            request: WebResourceRequest
        ): Boolean {
            val uri = request.url
            val scheme = uri.scheme.orEmpty().lowercase()
            val host = uri.host.orEmpty().lowercase()

            if (scheme == "musikplay") {
                handleCallbackIntent(Intent(Intent.ACTION_VIEW, uri))
                return true
            }

            if (scheme == "spotify") {
                openExternal(uri, SPOTIFY_PACKAGE)
                return true
            }

            if (host == "appassets.androidplatform.net") return false

            if (host == "accounts.spotify.com") {
                openExternal(uri)
                return true
            }

            if (
                host.endsWith("spotify.com") ||
                host.endsWith("youtube.com") ||
                host.endsWith("music.youtube.com") ||
                host.endsWith("google.com")
            ) {
                openExternal(uri)
                return true
            }

            return false
        }
    }
}
