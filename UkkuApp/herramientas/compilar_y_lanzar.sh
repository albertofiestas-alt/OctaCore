#!/bin/sh
# Compila Ukku para el simulador, la instala y la abre. Argumentos extra van a la app (p. ej. --pestana 2).
set -e
cd "$(dirname "$0")/.."
D=E2064532-A568-4F32-A8F3-9343A9E431FB
DD="${UKKU_DERIVED:-$HOME/Library/Developer/Xcode/DerivedData/Ukku-demo}"
xcodegen generate >/dev/null
xcodebuild -project Ukku.xcodeproj -scheme Ukku -destination "id=$D" -derivedDataPath "$DD" build 2>&1 | grep -E "error:|BUILD" | sort -u
xcrun simctl terminate $D com.hackathon.ukku 2>/dev/null || true
xcrun simctl install $D "$DD/Build/Products/Debug-iphonesimulator/Ukku.app"
xcrun simctl launch $D com.hackathon.ukku "$@"
