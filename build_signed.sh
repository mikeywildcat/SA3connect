#!/bin/bash
# =============================================================================
# build_signed.sh — Build, code-sign, package (DMG), and notarize
#                   SA3 NMEA Relay for macOS.
#
# Prerequisites
#   • Xcode Command Line Tools (xcode-select --install)
#   • Python venv with PyQt6 + PyInstaller installed
#   • A valid Developer ID Application certificate in your keychain
#   • An Apple Developer account with an app-specific password
#
# Usage
#   cd "SA3 NMEA Relay"
#   chmod +x build_signed.sh
#   ./build_signed.sh
# =============================================================================

set -euo pipefail

# ---- CONFIGURATION --------------------------------------------------------
APP_NAME="SA3NMEARelay"
BUNDLE_ID="com.sa3companion.nmea-relay"
DIST_DIR="dist"
APP_PATH="${DIST_DIR}/${APP_NAME}.app"
DMG_PATH="${DIST_DIR}/${APP_NAME}.dmg"
ENTITLEMENTS="entitlements.plist"

# Code-signing identity — from: security find-identity -v -p codesigning
DEVELOPER_ID="${DEVELOPER_ID:-Developer ID Application: MICHAEL JOHN WHITEHOUSE (TX9XVTF5T6)}"
APPLE_ID="${APPLE_ID:-mikey.whitehouse@alethiamedia.co.uk}"
APP_PASSWORD="${APP_PASSWORD:-}"           # app-specific password from appleid.apple.com
TEAM_ID="${TEAM_ID:-TX9XVTF5T6}"          # your 10-char Team ID

# ---- BUILD ----------------------------------------------------------------
echo "==> Building ${APP_NAME}..."
pyinstaller NMEARelay.spec --clean --noconfirm

if [ ! -d "${APP_PATH}" ]; then
    echo "Error: app bundle not found at ${APP_PATH}"
    exit 1
fi

echo "==> Build complete: ${APP_PATH}"

# ---- CODE SIGN ------------------------------------------------------------
if [ -n "${DEVELOPER_ID}" ]; then
    echo "==> Code-signing with: ${DEVELOPER_ID}"

    # Sign all nested binaries / frameworks / dylibs first
    find "${APP_PATH}/Contents/Frameworks" -name "*.dylib" -o -name "*.so" 2>/dev/null \
    | while read -r lib; do
        codesign --force --sign "${DEVELOPER_ID}" \
            --options runtime \
            --entitlements "${ENTITLEMENTS}" \
            "${lib}" 2>/dev/null || true
    done

    # Sign the main executable
    codesign --force --sign "${DEVELOPER_ID}" \
        --options runtime \
        --entitlements "${ENTITLEMENTS}" \
        "${APP_PATH}/Contents/MacOS/${APP_NAME}"

    # Sign the entire .app bundle (deep)
    codesign --force --deep --sign "${DEVELOPER_ID}" \
        --options runtime \
        --entitlements "${ENTITLEMENTS}" \
        "${APP_PATH}"

    echo "==> Code-signing complete."
    codesign --verify --deep --strict "${APP_PATH}" && echo "   Verification: OK"
else
    echo "WARNING: DEVELOPER_ID not set — skipping code-signing."
    echo "         The app will not pass Gatekeeper on other Macs."
fi

# ---- CREATE DMG -----------------------------------------------------------
echo "==> Creating DMG..."
rm -f "${DMG_PATH}"
hdiutil create \
    -volname "SA3 NMEA Relay" \
    -srcfolder "${APP_PATH}" \
    -ov -format UDZO \
    "${DMG_PATH}"
echo "==> DMG created: ${DMG_PATH}"

# ---- NOTARIZE (requires credentials) -------------------------------------
if [ -n "${DEVELOPER_ID}" ] && [ -n "${APPLE_ID}" ] && [ -n "${APP_PASSWORD}" ]; then
    echo "==> Submitting for notarization..."
    xcrun notarytool submit "${DMG_PATH}" \
        --apple-id "${APPLE_ID}" \
        --password "${APP_PASSWORD}" \
        --team-id "${TEAM_ID}" \
        --wait

    echo "==> Stapling notarization ticket..."
    xcrun stapler staple "${DMG_PATH}"
    echo "==> Notarization complete."
else
    echo ""
    echo "NOTE: Notarization skipped (APPLE_ID / APP_PASSWORD not set)."
    echo "      To notarize, export APPLE_ID, APP_PASSWORD, and DEVELOPER_ID"
    echo "      before running this script."
fi

echo ""
echo "Done!  Distributable: ${DMG_PATH}"
