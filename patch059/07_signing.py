from pathlib import Path
root=Path("source/autoresponder-pro")
p=root/"android/app/build.gradle.kts"
s=p.read_text(encoding="utf-8")
assert 'versionCode = 13' in s and 'versionName = "0.5.8"' in s
s=s.replace('versionCode = 13','versionCode = 14').replace('versionName = "0.5.8"','versionName = "0.5.9"')
old='''    buildTypes { release { isMinifyEnabled = false } }'''
new='''    // Reuse a dedicated fixed development signing certificate across releases.
    // Debug APKs no longer use a random GitHub Actions runner keystore.
    // Production deployments must migrate to a privately stored signing key.
    signingConfigs {
        create("devStable") {
            storeFile = file("keystore/autoresponder-dev.jks")
            storePassword = "musikplaydev"
            keyAlias = "musikplaydev"
            keyPassword = "musikplaydev"
        }
    }
    buildTypes {
        getByName("debug") {
            signingConfig = signingConfigs.getByName("devStable")
        }
        getByName("release") {
            isMinifyEnabled = false
            signingConfig = signingConfigs.getByName("devStable")
        }
    }'''
assert s.count(old)==1
p.write_text(s.replace(old,new),encoding="utf-8")
print("Version 0.5.9 code 14, repeatable development signing enabled")
