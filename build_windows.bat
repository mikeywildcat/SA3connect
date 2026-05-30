@echo off
:: =============================================================================
:: build_windows.bat — Build SA3 NMEA Relay for Windows using PyInstaller
::
:: Prerequisites
::   • Python venv with PyQt6 + PyInstaller installed
::   • Run from the "SA3 NMEA Relay" directory inside an activated venv
::
:: Usage
::   cd "SA3 NMEA Relay"
::   .\build_windows.bat
:: =============================================================================

echo Building SA3 NMEA Relay (Windows)...
pyinstaller NMEARelay-Windows.spec --clean --noconfirm

if not exist "dist\SA3NMEARelay.exe" (
    echo Error: EXE not found in dist\
    exit /b 1
)

echo.
echo Done!  Distributable: dist\SA3NMEARelay.exe
