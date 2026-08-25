plugins {
    id("com.android.application")
    id("org.jetbrains.kotlin.android")
}

android {
    namespace = "com.movieplay.musikplay"
    compileSdk = 35

    defaultConfig {
        applicationId = "com.movieplay.musikplay"
        minSdk = 26
        targetSdk = 35
        versionCode = 3
        versionName = "2.1.0"

        buildConfigField("String", "SPOTIFY_CLIENT_ID", "\"024afdd700ef406c9845f7d9e27e3a92\"")
        buildConfigField("String", "SPOTIFY_REDIRECT_URI", "\"https://djkados.github.io/musikplay/android-callback.html\"")
    }

    signingConfigs {
        create("musikplayDev") {
            storeFile = file("keystore/musikplay-dev.jks")
            storePassword = "musikplaydev"
            keyAlias = "musikplaydev"
            keyPassword = "musikplaydev"
        }
    }

    buildFeatures {
        buildConfig = true
    }

    buildTypes {
        debug {
            signingConfig = signingConfigs.getByName("musikplayDev")
        }
        release {
            isMinifyEnabled = false
            signingConfig = signingConfigs.getByName("musikplayDev")
            proguardFiles(
                getDefaultProguardFile("proguard-android-optimize.txt"),
                "proguard-rules.pro"
            )
        }
    }

    compileOptions {
        sourceCompatibility = JavaVersion.VERSION_17
        targetCompatibility = JavaVersion.VERSION_17
    }

    kotlinOptions {
        jvmTarget = "17"
    }

    packaging {
        resources {
            pickFirsts += setOf("META-INF/LICENSE", "META-INF/NOTICE")
        }
    }
}

dependencies {
    implementation("androidx.core:core-ktx:1.15.0")
    implementation("androidx.appcompat:appcompat:1.7.0")
    implementation("androidx.webkit:webkit:1.12.1")
    implementation("com.google.code.gson:gson:2.11.0")
    implementation(files("libs/spotify-app-remote-release-0.8.0.aar"))
}
