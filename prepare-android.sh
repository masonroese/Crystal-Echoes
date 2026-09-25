#!/usr/bin/env bash
# Customises the Android project that `npx cap add android` generates:
# landscape only, full screen, dark background, and the Crystal Echoes icon + splash.
set -euo pipefail
cd "$(dirname "$0")/.."

MAIN=android/app/src/main
[ -f "$MAIN/AndroidManifest.xml" ] || { echo "Run 'npx cap add android' first."; exit 1; }

# Landscape only (either way up).
if ! grep -q 'screenOrientation' "$MAIN/AndroidManifest.xml"; then
  sed -i.bak 's|android:name=".MainActivity"|android:name=".MainActivity"\n            android:screenOrientation="sensorLandscape"|' "$MAIN/AndroidManifest.xml"
  rm -f "$MAIN/AndroidManifest.xml.bak"
fi

# Full-screen activity.
cp resources/android/MainActivity.java "$MAIN/java/com/crystalechoes/game/MainActivity.java"

# Icons and splash screens.
cp -R resources/android/res/. "$MAIN/res/"

# Dark icon background (behind the adaptive icon) and dark launch screen.
cat > "$MAIN/res/values/ic_launcher_background.xml" <<'XML'
<?xml version="1.0" encoding="utf-8"?>
<resources>
    <color name="ic_launcher_background">#0D1315</color>
</resources>
XML

echo "Android project prepared: landscape, full screen, Crystal Echoes icon."
