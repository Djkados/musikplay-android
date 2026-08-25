package com.movieplay.musikplay

import android.annotation.SuppressLint
import android.content.Intent
import android.graphics.Color
import android.net.Uri
import android.os.Bundle
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
import androidx.webkit.WebViewAssetLoader

class MainActivity : AppCompatActivity() {

    private lateinit var webView: WebView
    private lateinit var assetLoader: WebViewAssetLoader

    companion object {
        private const val APP_URL = "https://appassets.androidplatform.net/assets/web/index.html"
    }

    @SuppressLint("SetJavaScriptEnabled")
    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)

        window.statusBarColor = Color.BLACK
        window.navigationBarColor = Color.BLACK

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
            settings.userAgentString = settings.userAgentString + " MusikplayAndroid/2.0"

            CookieManager.getInstance().setAcceptCookie(true)
            CookieManager.getInstance().setAcceptThirdPartyCookies(this, true)

            addJavascriptInterface(MusikplayBridge(), "AndroidMusikplay")
            webChromeClient = WebChromeClient()
            webViewClient = MusikplayWebViewClient(assetLoader)
        }

        setContentView(webView)
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
        val callbackUrl = if (query.isNotBlank()) "$APP_URL?$query&native=1" else "$APP_URL?native=1"
        webView.loadUrl(callbackUrl)
        return true
    }

    private fun openExternal(uri: Uri) {
        runCatching {
            startActivity(Intent(Intent.ACTION_VIEW, uri))
        }
    }

    inner class MusikplayBridge {
        @JavascriptInterface
        fun isNative(): Boolean = true

        @JavascriptInterface
        fun getClientId(): String = BuildConfig.SPOTIFY_CLIENT_ID

        @JavascriptInterface
        fun getRedirectUri(): String = BuildConfig.SPOTIFY_REDIRECT_URI

        @JavascriptInterface
        fun openSpotify() {
            runOnUiThread {
                val launch = packageManager.getLaunchIntentForPackage("com.spotify.music")
                if (launch != null) {
                    startActivity(launch)
                } else {
                    openExternal(Uri.parse("https://play.google.com/store/apps/details?id=com.spotify.music"))
                }
            }
        }
    }

    inner class MusikplayWebViewClient(
        private val loader: WebViewAssetLoader
    ) : WebViewClient() {

        override fun shouldInterceptRequest(view: WebView?, request: WebResourceRequest): WebResourceResponse? {
            return loader.shouldInterceptRequest(request.url)
        }

        override fun shouldOverrideUrlLoading(view: WebView?, request: WebResourceRequest): Boolean {
            val uri = request.url
            val scheme = uri.scheme.orEmpty().lowercase()
            val host = uri.host.orEmpty().lowercase()

            if (scheme == "musikplay") {
                handleCallbackIntent(Intent(Intent.ACTION_VIEW, uri))
                return true
            }

            if (host == "appassets.androidplatform.net") return false

            // Spotify OAuth must happen in the system browser, not inside the embedded WebView.
            if (host == "accounts.spotify.com") {
                openExternal(uri)
                return true
            }

            // Open external services outside Musikplay.
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
