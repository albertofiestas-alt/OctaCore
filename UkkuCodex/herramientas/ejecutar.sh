#!/bin/bash
set -euo pipefail
cd "$(dirname "$0")/.."
UKKU_DERIVED="${UKKU_DERIVED_DATA:-$HOME/Library/Developer/Xcode/DerivedData/UkkuCodex}"
UKKU_DEVICE="${UKKU_SIMULATOR_UDID:-$(xcrun simctl list devices available -j | python3 -c 'import json,sys; ds=[d for v in json.load(sys.stdin)["devices"].values() for d in v if "iPhone" in d["name"]]; ds.sort(key=lambda d: (not d["name"].startswith("Ukku Codex"), d["state"] != "Booted")); print(ds[0]["udid"] if ds else "")')}"
if [ -z "$UKKU_DEVICE" ]; then echo 'Instala un simulador de iPhone en Xcode.'; exit 1; fi
mkdir -p evidencias
xcodegen generate
xcodebuild -project UkkuCodex.xcodeproj -scheme UkkuCodex -destination "id=$UKKU_DEVICE" -derivedDataPath "$UKKU_DERIVED" CODE_SIGNING_ALLOWED=NO build > evidencias/build.log 2>&1 || { tail -70 evidencias/build.log; exit 1; }
xcrun simctl boot "$UKKU_DEVICE" 2>/dev/null || true
xcrun simctl bootstatus "$UKKU_DEVICE" -b
if [ -d /Applications/Xcode.app/Contents/Applications/DeviceHub.app ]; then
    open /Applications/Xcode.app/Contents/Applications/DeviceHub.app
else
    open -a Simulator
fi
xcrun simctl terminate "$UKKU_DEVICE" com.hackathon.ukku.codex 2>/dev/null || true
xcrun simctl install "$UKKU_DEVICE" "$UKKU_DERIVED/Build/Products/Debug-iphonesimulator/UkkuCodex.app"
xcrun simctl launch "$UKKU_DEVICE" com.hackathon.ukku.codex "$@"
