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
        versionCode = 2
        versionName = "2.0.0"

        buildConfigField("String", "SPOTIFY_CLIENT_ID", "\"024afdd700ef406c9845f7d9e27e3a92\"")
        buildConfigField("String", "SPOTIFY_REDIRECT_URI", "\"https://djkados.github.io/musikplay/android-callback.html\"")
    }

    buildFeatures {
        buildConfig = true
    }

    buildTypes {
        debug {
            // Debug APK is installable as com.movieplay.musikplay.
        }
        release {
            isMinifyEnabled = false
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
}

dependencies {
    implementation("androidx.core:core-ktx:1.15.0")
    implementation("androidx.appcompat:appcompat:1.7.0")
    implementation("androidx.webkit:webkit:1.12.1")
}
