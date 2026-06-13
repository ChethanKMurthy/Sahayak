# Sahayak — Flutter Android app

Voice-first, camera-intake government-counter app. Capture documents (OCR'd and
PII-masked **on-device** via ML Kit), discover entitlements, fill the form, hear it
read back, consent, and get a submittable PDF + checklist.

## Prerequisites

- Flutter SDK 3.3+ (`flutter --version`)
- Android Studio + an emulator (or a real device with USB debugging)
- The backend running (see `../backend/README` or root README)

## One-time setup

This repo ships `lib/`, `pubspec.yaml`, `assets/`, `analysis_options.yaml`, and the
two Android config files below. Generate the rest of the Android platform scaffold
(Gradle, MainActivity, etc.) with:

```bash
cd mobile
flutter create --platforms=android --org com.sahayak .   # keeps existing lib/ & pubspec
bash ../scripts/sync-shared.sh                            # sync shared i18n strings
flutter pub get
```

Then apply the **three required edits** to `android/app/src/main/AndroidManifest.xml`:

1. Add these permissions **above** the `<application>` tag:
   ```xml
   <uses-permission android:name="android.permission.INTERNET"/>
   <uses-permission android:name="android.permission.CAMERA"/>
   <uses-permission android:name="android.permission.RECORD_AUDIO"/>
   ```
2. On the `<application>` tag, point it at the bundled network-security config (already
   in this repo at `android/app/src/main/res/xml/network_security_config.xml`):
   ```xml
   <application
       android:networkSecurityConfig="@xml/network_security_config"
       ... >
   ```
3. Ensure `minSdkVersion` is **≥ 21** in `android/app/build.gradle`
   (ML Kit, camera, and speech_to_text all require 21+). ML Kit text recognition
   works best at `minSdkVersion 21` with `multiDexEnabled true`.

## Run

```bash
# Emulator: the backend on your Mac is reachable at 10.0.2.2 (the default).
flutter run

# Real device on the same Wi-Fi: pass your machine's LAN IP.
flutter run --dart-define=API_BASE=http://192.168.1.50:8000
```

## What runs on-device (the privacy story)

- **Document classification + OCR**: `google_mlkit_text_recognition` (`lib/services/ocr.dart`)
- **PII masking**: Aadhaar → last-4 **before** anything leaves the phone (`lib/services/pii.dart`)
- **Voice**: `speech_to_text` (ASR) + `flutter_tts` (read-back) in the user's language
  (`lib/services/voice.dart`)

Only masked, structured fields are sent to the backend. The full 12-digit Aadhaar
number is never transmitted.

## Flow (mirrors the web app and the backend state machine)

welcome → capture (camera or demo persona) → consistency (mismatch resolution) →
eligibility (entitlement graph + "you also qualify" + dependency chains) → fill
(provenance + voice gap-fill) → teach-back (read-aloud + consent) → output
(PDF + checklist + fair-price + tracking).

## Building an APK

```bash
flutter build apk --release --dart-define=API_BASE=https://your-api.example.com
# → build/app/outputs/flutter-apk/app-release.apk
```

CI builds a debug APK automatically — see `.github/workflows/`.
