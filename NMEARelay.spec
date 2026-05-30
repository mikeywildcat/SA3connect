# -*- mode: python ; coding: utf-8 -*-
"""
PyInstaller spec for SA3 NMEA Relay — macOS (one-dir .app bundle)

Build:
    cd "SA3 NMEA Relay"
    pyinstaller NMEARelay.spec --clean --noconfirm

The resulting .app is in dist/SA3NMEARelay.app.
Run build_signed.sh to code-sign, create DMG, and notarize.
"""

import sys
from pathlib import Path

block_cipher = None
base_path = Path.cwd()

a = Analysis(
    ["main.py"],
    pathex=[str(base_path)],
    binaries=[],
    datas=[("heelappicon.png", "."), ("help.html", "."), ("help_fr.html", "."), ("help_de.html", "."), ("help_nl.html", ".")],
    hiddenimports=[
        "PyQt6.QtCore",
        "PyQt6.QtGui",
        "PyQt6.QtWidgets",
        "PyQt6.sip",
        "tray_manager",
        "translations",
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        # Exclude heavy packages not needed here
        "PyQt6.QtWebEngine",
        "PyQt6.QtWebEngineCore",
        "PyQt6.QtWebEngineWidgets",
        "numpy",
        "scipy",
        "xarray",
        "cfgrib",
        "eccodes",
        "psutil",
        "timezonefinder",
        "pyqtgraph",
        "websocket",
    ],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name="SA3NMEARelay",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    console=False,
    disable_windowed_traceback=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=False,
    upx_exclude=[],
    name="SA3NMEARelay",
)

app = BUNDLE(
    coll,
    name="SA3NMEARelay.app",
    icon="NMEARelay.icns",
    bundle_identifier="com.sa3companion.nmea-relay",
    version="1.0.0",
    info_plist={
        "CFBundleName": "SA3 NMEA Relay",
        "CFBundleDisplayName": "SA3 NMEA Relay",
        "CFBundleShortVersionString": "1.0.0",
        "CFBundleVersion": "1.0.0",
        "NSPrincipalClass": "NSApplication",
        "NSHighResolutionCapable": True,
        "LSMinimumSystemVersion": "11.0",
        # Network usage descriptions (required for Hardened Runtime)
        "NSLocalNetworkUsageDescription":
            "SA3 NMEA Relay connects to the Sailaway 3 NMEA Gateway and "
            "relays corrected sentences to navigation apps on your network.",
    },
)
