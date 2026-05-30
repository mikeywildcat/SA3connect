# -*- mode: python ; coding: utf-8 -*-
"""
PyInstaller spec for SA3 NMEA Relay — Windows (single-file EXE)

Build (from an activated venv on Windows):
    cd "SA3 NMEA Relay"
    pyinstaller NMEARelay-Windows.spec --clean --noconfirm

The resulting EXE is in dist/SA3NMEARelay.exe.
"""

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
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name="SA3NMEARelay",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,           # No console window on Windows
    disable_windowed_traceback=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon="NMEARelay.ico",
    version_file=None,
)
