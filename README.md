# Musikplay Android V2

Versión Android instalable de Musikplay, con diseño negro + verde limón y la misma experiencia ya validada en la PWA.

## Qué hace

- Inicio con recomendaciones basadas en tu Spotify.
- Búsqueda del catálogo de Spotify.
- Tus playlists, guardados e historial.
- Reproductor y controles desde Musikplay.
- Spotify Connect como motor de audio para mantener la reproducción al bloquear el celular o cambiar de app.
- Cola, anterior, play/pausa y siguiente.
- Acceso a YouTube Music como complemento.
- OAuth Authorization Code + PKCE. No usa ni guarda Client Secret.

> Nota técnica: Spotify no ofrece actualmente un SDK móvil de terceros que entregue el audio crudo a Musikplay. El APK controla la reproducción autorizada de Spotify; Spotify mantiene el audio, caché, integración con llamadas y reproducción de sistema.

## Datos ya configurados

- Spotify Client ID: ya incluido (es un identificador público, no un secreto).
- Redirect URI Android: `https://djkados.github.io/musikplay/android-callback.html`
- Package Android: `com.movieplay.musikplay`

## Paso 1 — parche mínimo en el GitHub Pages actual

En el repositorio `Djkados/musikplay`, sube SOLO este archivo a la raíz:

`github-pages-patch/android-callback.html`

Luego comprueba que abra:

`https://djkados.github.io/musikplay/android-callback.html`

## Paso 2 — Spotify Developer Dashboard

En la app Spotify Developer **Musikplay** que ya existe:

1. Entra a Edit/Settings.
2. En Redirect URIs agrega exactamente:
   `https://djkados.github.io/musikplay/android-callback.html`
3. Conserva también el URI web existente:
   `https://djkados.github.io/musikplay/`
4. Guarda.

No hace falta Client Secret.

## Paso 3 — compilar el APK con GitHub Actions

Recomendado: crea un repositorio separado llamado `musikplay-android` y sube TODO el contenido de esta carpeta a la raíz del nuevo repositorio.

El archivo `.github/workflows/build-apk.yml` compila automáticamente el APK.

Después:

1. GitHub > Actions.
2. Abre `Build Musikplay APK`.
3. Espera a que termine en verde.
4. Abre la ejecución terminada.
5. En Artifacts descarga `Musikplay-Android-V2`.
6. Dentro está `app-debug.apk`.
7. Instálalo en el celular.

## Primera prueba

1. Ten Spotify oficial instalado y conectado con tu Premium.
2. Abre Musikplay Android.
3. Pulsa Conectar Spotify.
4. Autoriza en el navegador.
5. Volverás automáticamente a Musikplay.
6. Si el celular no aparece como dispositivo, abre Spotify una vez, reproduce/pausa y vuelve a Musikplay.
7. Reproduce desde Musikplay, bloquea el teléfono y valida que el audio continúe.

## Firma del APK

La Action actual genera un APK de prueba (debug), adecuado para validar Musikplay V2. Cuando la versión esté estable, conviene crear una firma release permanente para que todas las actualizaciones se instalen sobre la anterior sin desinstalar.
