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
import com.spotify.android.appremote.api.ConnectionParams
import com.spotify.android.appremote.api.Connector
import com.spotify.android.appremote.api.SpotifyAppRemote
import org.json.JSONObject

class MainActivity : AppCompatActivity() {

    private lateinit var webView: WebView
    private lateinit var assetLoader: WebViewAssetLoader
    private var spotifyAppRemote: SpotifyAppRemote? = null
    private var remoteConnecting = false
    private var pendingSpotifyUri: String? = null

    companion object {
        private const val APP_URL = "https://appassets.androidplatform.net/assets/web/index.html"
        private const val SPOTIFY_PACKAGE = "com.spotify.music"
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
            settings.useWideViewPort = true
            settings.loadWithOverviewMode = false
            settings.textZoom = 100
            settings.userAgentString = settings.userAgentString + " MusikplayAndroid/2.1"

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

    override fun onStart() {
        super.onStart()
        // Connect in the foreground. Spotify itself keeps audio alive in background.
        connectSpotifyRemote(showAuthView = false)
    }

    override fun onNewIntent(intent: Intent) {
        super.onNewIntent(intent)
        setIntent(intent)
        handleCallbackIntent(intent)
    }

    override fun onResume() {
        super.onResume()
        webView.onResume()
        if (spotifyAppRemote?.isConnected != true) {
            connectSpotifyRemote(showAuthView = false)
        }
    }

    override fun onPause() {
        webView.onPause()
        super.onPause()
    }

    override fun onStop() {
        spotifyAppRemote?.let {
            runCatching { SpotifyAppRemote.disconnect(it) }
        }
        spotifyAppRemote = null
        remoteConnecting = false
        sendRemoteState(false, "Spotify sigue reproduciendo en segundo plano")
        super.onStop()
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
        runCatching { startActivity(Intent(Intent.ACTION_VIEW, uri)) }
    }

    private fun spotifyInstalled(): Boolean = runCatching {
        packageManager.getPackageInfo(SPOTIFY_PACKAGE, 0)
        true
    }.getOrDefault(false)

    private fun connectSpotifyRemote(showAuthView: Boolean) {
        if (!spotifyInstalled()) {
            sendRemoteState(false, "Instala Spotify para activar la reproducción")
            return
        }
        if (spotifyAppRemote?.isConnected == true || remoteConnecting) return

        remoteConnecting = true
        sendRemoteState(false, "Conectando con Spotify…")

        val params = ConnectionParams.Builder(BuildConfig.SPOTIFY_CLIENT_ID)
            .setRedirectUri(BuildConfig.SPOTIFY_REDIRECT_URI)
            .showAuthView(showAuthView)
            .build()

        SpotifyAppRemote.connect(this, params, object : Connector.ConnectionListener {
            override fun onConnected(appRemote: SpotifyAppRemote) {
                remoteConnecting = false
                spotifyAppRemote = appRemote
                sendRemoteState(true, "Musikplay listo para reproducir")
                subscribeToNativePlayerState()

                pendingSpotifyUri?.let { uri ->
                    pendingSpotifyUri = null
                    playNativeUri(uri)
                }
            }

            override fun onFailure(throwable: Throwable) {
                remoteConnecting = false
                spotifyAppRemote = null
                val raw = throwable.message.orEmpty()
                val friendly = when {
                    raw.contains("not_authorized", true) || raw.contains("authorization", true) ->
                        "Autoriza Musikplay para controlar Spotify"
                    raw.contains("INVALID_APP_ID", true) || raw.contains("identifier", true) ->
                        "Falta registrar Android + SHA-1 en Spotify Developers"
                    else -> raw.ifBlank { "No se pudo conectar con Spotify" }
                }
                sendRemoteState(false, friendly)
            }
        })
    }

    private fun subscribeToNativePlayerState() {
        val remote = spotifyAppRemote ?: return
        remote.playerApi.subscribeToPlayerState()
            .setEventCallback { playerState ->
                val track = playerState.track
                val payload = JSONObject().apply {
                    put("paused", playerState.isPaused)
                    put("position", playerState.playbackPosition)
                    if (track != null) {
                        put("uri", track.uri)
                        put("name", track.name)
                        put("artist", track.artist?.name.orEmpty())
                        put("duration", track.duration)
                        put("imageUri", track.imageUri?.raw.orEmpty())
                    }
                }
                runJs("window.onMusikplayNativePlayerState && window.onMusikplayNativePlayerState(${payload});")
            }
            .setErrorCallback { error ->
                sendRemoteError(error.message ?: "No pude leer el estado de Spotify")
            }
    }

    private fun playNativeUri(uri: String) {
        val remote = spotifyAppRemote
        if (remote?.isConnected != true) {
            pendingSpotifyUri = uri
            connectSpotifyRemote(showAuthView = true)
            return
        }
        remote.playerApi.play(uri)
            .setResultCallback {
                sendRemoteState(true, "Reproduciendo desde Musikplay")
            }
            .setErrorCallback { error -> sendRemoteError(error.message ?: "Spotify no pudo reproducir esta canción") }
    }

    private fun runPlayerCommand(command: String) {
        val remote = spotifyAppRemote
        if (remote?.isConnected != true) {
            connectSpotifyRemote(showAuthView = true)
            sendRemoteError("Conectando con Spotify. Intenta nuevamente en un momento.")
            return
        }
        val result = when (command) {
            "pause" -> remote.playerApi.pause()
            "resume" -> remote.playerApi.resume()
            "next" -> remote.playerApi.skipNext()
            "previous" -> remote.playerApi.skipPrevious()
            else -> null
        } ?: return
        result.setErrorCallback { error -> sendRemoteError(error.message ?: "No se pudo controlar Spotify") }
    }

    private fun requestNativePlayerState() {
        val remote = spotifyAppRemote ?: return
        remote.playerApi.playerState
            .setResultCallback { playerState ->
                val track = playerState.track
                val payload = JSONObject().apply {
                    put("paused", playerState.isPaused)
                    put("position", playerState.playbackPosition)
                    if (track != null) {
                        put("uri", track.uri)
                        put("name", track.name)
                        put("artist", track.artist?.name.orEmpty())
                        put("duration", track.duration)
                        put("imageUri", track.imageUri?.raw.orEmpty())
                    }
                }
                runJs("window.onMusikplayNativePlayerState && window.onMusikplayNativePlayerState(${payload});")
            }
            .setErrorCallback { error -> sendRemoteError(error.message ?: "No pude leer Spotify") }
    }

    private fun sendRemoteState(ready: Boolean, message: String) {
        runJs(
            "window.onMusikplayNativeRemoteState && window.onMusikplayNativeRemoteState(" +
                ready + "," + JSONObject.quote(message) + ");"
        )
    }

    private fun sendRemoteError(message: String) {
        runJs("window.onMusikplayNativeRemoteError && window.onMusikplayNativeRemoteError(${JSONObject.quote(message)});")
    }

    private fun runJs(script: String) {
        if (!::webView.isInitialized) return
        runOnUiThread { webView.evaluateJavascript(script, null) }
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
        fun isSpotifyRemoteReady(): Boolean = spotifyAppRemote?.isConnected == true

        @JavascriptInterface
        fun connectSpotifyRemote() {
            runOnUiThread { connectSpotifyRemote(showAuthView = true) }
        }

        @JavascriptInterface
        fun requestSpotifyPlayerState() {
            runOnUiThread { requestNativePlayerState() }
        }

        @JavascriptInterface
        fun playSpotifyUri(uri: String): Boolean {
            runOnUiThread { playNativeUri(uri) }
            return true
        }

        @JavascriptInterface
        fun pauseSpotify() {
            runOnUiThread { runPlayerCommand("pause") }
        }

        @JavascriptInterface
        fun resumeSpotify() {
            runOnUiThread { runPlayerCommand("resume") }
        }

        @JavascriptInterface
        fun nextSpotify() {
            runOnUiThread { runPlayerCommand("next") }
        }

        @JavascriptInterface
        fun previousSpotify() {
            runOnUiThread { runPlayerCommand("previous") }
        }

        @JavascriptInterface
        fun openSpotify() {
            runOnUiThread {
                val launch = packageManager.getLaunchIntentForPackage(SPOTIFY_PACKAGE)
                if (launch != null) startActivity(launch)
                else openExternal(Uri.parse("https://play.google.com/store/apps/details?id=$SPOTIFY_PACKAGE"))
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
