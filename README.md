# SA3 NMEA Relay

A lightweight, standalone bridge app for **Sailaway 3** that:

1. Connects to the Sailaway 3 NMEA Gateway (TCP client)
2. Corrects proprietary Sailaway sentences into standard NMEA 0183
3. Relays the corrected stream via a TCP server to navigation apps (OpenCPN, qtVlm, etc.)

Cross-platform — runs on **macOS** and **Windows**.  Apple Hardened Runtime entitlements are included for notarization.

---

## Sentence corrections

| Received from Sailaway | Relayed as | Notes |
|---|---|---|
| `$SLCLI,<heel>` | `$IIXDR,A,<heel>,D,ROLL*XX` | Sign inverted (Sailaway +port → NMEA −port) |
| `$RIRSA,<angle>,<status>,...` | `$IIRSA,<angle>,<status>,,V*XX` | Standard RSA format |
| `$WIMWV` / `$IIMWV` with angle > 180° | Same sentence, angle rewritten as negative | ±180° signed convention |
| Own-boat `!AIVDM`/`!AIVDO` | *dropped* | Detected via `$SLBID` boat-ID matching |
| All other sentences | Passed through unchanged | Checksum preserved |

---

## Requirements

- Python 3.11+
- `PyQt6 >= 6.5`
- `PyInstaller` (for building distributable binaries)

Install into a virtual environment:

```bash
python -m venv .venv
source .venv/bin/activate        # macOS / Linux
# .venv\Scripts\activate.bat     # Windows
pip install PyQt6 pyinstaller
```

---

## Running from source

```bash
cd "SA3 NMEA Relay"
python main.py
```

---

## Building a distributable

### macOS — signed & notarized DMG

```bash
# Set environment variables
export DEVELOPER_ID="Developer ID Application: Your Name (TEAMID)"
export APPLE_ID="you@example.com"
export APP_PASSWORD="xxxx-xxxx-xxxx-xxxx"   # app-specific password from appleid.apple.com
export TEAM_ID="YOURTEAMID"

chmod +x build_signed.sh
./build_signed.sh
```

The script:
1. Runs PyInstaller with `NMEARelay.spec`
2. Deep-signs the `.app` with Hardened Runtime + entitlements
3. Wraps it in a compressed DMG
4. Submits to Apple notarization and staples the ticket

If you skip the environment variables, you get an unsigned `.app` / DMG that runs locally.

### Windows — single EXE

```bat
build_windows.bat
```

Output: `dist\SA3NMEARelay.exe`

---

## Entitlements (macOS)

`entitlements.plist` grants:

| Key | Reason |
|---|---|
| `network.client` | TCP connection to Sailaway NMEA Gateway |
| `network.server` | TCP relay server for navigation apps |
| `files.user-selected.read-write` | Future config import/export |
| `cs.allow-jit` | PyQt6 requires JIT under Hardened Runtime |
| `cs.disable-library-validation` | PyInstaller bundles third-party dylibs |

---

## Project layout

```
SA3 NMEA Relay/
├── main.py               Entry point
├── app.py                QMainWindow — wires everything together
├── connection_panel.py   PyQt6 GUI panel (Connection + TCP Relay tabs)
├── tcp_client.py         TcpWorker — connects to Sailaway NMEA Gateway
├── tcp_relay.py          TCPRelay — listens for nav-app connections, broadcasts
├── nmea_corrector.py     Sentence correction + own-boat AIS filtering
├── NMEARelay.spec        PyInstaller spec (macOS .app)
├── NMEARelay-Windows.spec  PyInstaller spec (Windows .exe)
├── entitlements.plist    Apple Hardened Runtime entitlements
├── build_signed.sh       macOS build + sign + notarize script
├── build_windows.bat     Windows build script
└── pyproject.toml        Package metadata
```
