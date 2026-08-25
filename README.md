# Musikplay Android V2.2

Versión Android de Musikplay optimizada para móvil y Spotify Premium.

## Cambios V2.2

- Spotify App Remote SDK 0.8.0 para reproducir, pausar, siguiente y anterior desde Musikplay.
- La música continúa al bloquear el celular porque Spotify mantiene el servicio de audio en segundo plano.
- PlayerState nativo sincronizado con la interfaz de Musikplay.
- Controles y tipografías más grandes para Android.
- Mini reproductor y pantalla "Reproduciendo ahora" redimensionados.
- Ajustes simplificados: ya no depende de que el celular aparezca manualmente como dispositivo Spotify Connect.
- Icono Android adaptativo nuevo, negro + verde limón.
- Firma de desarrollo estable para que Spotify reconozca siempre el mismo SHA-1.

## Configuración requerida en Spotify Developers

En la aplicación **Musikplay** del Dashboard de Spotify:

1. Mantén estos Redirect URIs:
   - `https://djkados.github.io/musikplay/`
   - `https://djkados.github.io/musikplay/android-callback.html`
2. Edita la app y habilita **Android** además de Web API / Web Playback SDK.
3. Agrega el paquete Android:
   - `com.movieplay.musikplay`
4. Agrega el SHA-1 de la firma de desarrollo:
   - `3C:B9:C0:C0:3C:58:8E:FC:15:06:11:23:C7:FA:AF:E2:FE:FE:F1:D1`

La app usa el Client ID ya configurado en el proyecto. No usa ni necesita el Client Secret dentro del APK.

## Compilar con GitHub Actions

El workflow `.github/workflows/build-apk.yml` descarga el SDK oficial Spotify App Remote 0.8.0 directamente desde el release oficial y compila el APK.

El artifact final se llama:

`Musikplay-Android-V2.2`

## Firma

La V2.2 usa `app/keystore/musikplay-dev.jks` únicamente como firma de desarrollo/pruebas para mantener un SHA-1 fijo. Antes de publicar en Play Store debe sustituirse por una firma privada de producción.

> Si instalaste V2.0 creada con la firma debug efímera de GitHub, probablemente tendrás que desinstalar V2.0 antes de instalar V2.2 una sola vez.


## V2.2
- Corrige solapamiento con barra de estado en Android 15.
- Corrige avisos/toasts que se salían de la pantalla.
- Reproducción Android usa Spotify Connect/Web API, sin depender del auth popup inestable de App Remote.
- Spotify oficial mantiene el audio en segundo plano.
