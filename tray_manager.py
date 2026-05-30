"""System tray icon (Windows) / menu bar icon (macOS) for SA3 NMEA Relay.

Responsibilities:
  - Show/hide the main window via tray icon click or context menu.
  - Provide a "Start at Login" toggle that is persisted via platform APIs:
      macOS   → ~/Library/LaunchAgents/com.sa3nmearelay.plist
      Windows → HKCU\\Software\\Microsoft\\Windows\\CurrentVersion\\Run
"""

from __future__ import annotations

import logging
import platform
import sys
from pathlib import Path

from PyQt6.QtCore import QCoreApplication, QSettings, Qt
from PyQt6.QtGui import QAction, QIcon, QPixmap
from PyQt6.QtWidgets import QMenu, QSystemTrayIcon

from translations import tr

_logger = logging.getLogger(__name__)

_APP_NAME = "SA3NMEARelay"
_DISPLAY_NAME = "SA3 NMEA Relay"
_PLIST_LABEL = "com.sa3nmearelay"


# ---------------------------------------------------------------------------
# Icon
# ---------------------------------------------------------------------------

def _icon_path() -> Path:
    """Return path to heelappicon.png, works from source and PyInstaller bundle."""
    if getattr(sys, "frozen", False):
        base = Path(sys._MEIPASS)  # type: ignore[attr-defined]
    else:
        base = Path(__file__).resolve().parent
    return base / "heelappicon.png"


def _make_icon() -> QIcon:
    path = _icon_path()
    if path.exists():
        return QIcon(str(path))
    # Fallback: simple coloured square
    px = QPixmap(22, 22)
    px.fill(Qt.GlobalColor.transparent)
    return QIcon(px)


def _set_dock_icon_visible(visible: bool) -> None:
    """Show or hide the macOS Dock icon dynamically (no-op on other platforms)."""
    if platform.system() != "Darwin":
        return
    try:
        import ctypes
        import ctypes.util
        libobjc = ctypes.cdll.LoadLibrary(ctypes.util.find_library("objc"))

        libobjc.objc_getClass.restype = ctypes.c_void_p
        libobjc.objc_getClass.argtypes = [ctypes.c_char_p]
        libobjc.sel_registerName.restype = ctypes.c_void_p
        libobjc.sel_registerName.argtypes = [ctypes.c_char_p]

        # Get NSApplication.sharedApplication (no extra args)
        libobjc.objc_msgSend.restype = ctypes.c_void_p
        libobjc.objc_msgSend.argtypes = [ctypes.c_void_p, ctypes.c_void_p]
        nsapp_cls = libobjc.objc_getClass(b"NSApplication")
        nsapp = libobjc.objc_msgSend(
            nsapp_cls, libobjc.sel_registerName(b"sharedApplication")
        )

        # setActivationPolicy: NSApplicationActivationPolicyRegular=0, Accessory=1
        SetPolicyFunc = ctypes.CFUNCTYPE(
            ctypes.c_bool, ctypes.c_void_p, ctypes.c_void_p, ctypes.c_long
        )
        set_policy = SetPolicyFunc(libobjc.objc_msgSend)
        set_policy(nsapp, libobjc.sel_registerName(b"setActivationPolicy:"),
                   0 if visible else 1)
    except Exception as exc:
        _logger.debug("Could not change Dock visibility: %s", exc)


# ---------------------------------------------------------------------------
# TrayManager
# ---------------------------------------------------------------------------

class TrayManager:
    """Creates and manages the system tray / menu bar icon."""

    def __init__(self, window):
        self._window = window
        self._tray: QSystemTrayIcon | None = None

        # Load tray-only preference
        _s = QSettings(_APP_NAME, _APP_NAME)
        self._tray_only: bool = str(_s.value("app/trayOnlyMode", "false")).lower() in ("true", "1", "yes")

        if not QSystemTrayIcon.isSystemTrayAvailable():
            _logger.warning("System tray is not available on this platform.")
            return

        self._tray = QSystemTrayIcon(_make_icon())
        self._tray.setToolTip(_DISPLAY_NAME)

        menu = QMenu()

        # Show / Hide
        self._act_show = QAction(tr("tray_hide"))
        self._act_show.triggered.connect(self._on_show_hide)
        menu.addAction(self._act_show)

        menu.addSeparator()

        # Menu Bar / Tray Only
        self._act_tray_only = QAction(tr("tray_only_mode"))
        self._act_tray_only.setCheckable(True)
        self._act_tray_only.setChecked(self._tray_only)
        self._act_tray_only.triggered.connect(self._on_toggle_tray_only)
        menu.addAction(self._act_tray_only)

        # Start at Login
        self._act_login = QAction(tr("tray_start_at_login"))
        self._act_login.setCheckable(True)
        self._act_login.setChecked(self._is_start_at_login_enabled())
        self._act_login.triggered.connect(self._on_toggle_login)
        menu.addAction(self._act_login)

        menu.addSeparator()

        # Help
        self._act_help = QAction(tr("tray_help"))
        self._act_help.triggered.connect(self._on_help)
        menu.addAction(self._act_help)

        menu.addSeparator()

        # Quit
        act_quit = QAction(tr("tray_quit", app=_DISPLAY_NAME))
        act_quit.triggered.connect(QCoreApplication.quit)
        menu.addAction(act_quit)

        self._tray.setContextMenu(menu)
        self._tray.activated.connect(self._on_activated)
        self._tray.show()

        # Apply tray-only dock policy immediately if set
        if self._tray_only:
            _set_dock_icon_visible(False)

    # ------------------------------------------------------------------
    # Public helpers
    # ------------------------------------------------------------------

    def is_available(self) -> bool:
        return self._tray is not None

    def is_tray_only(self) -> bool:
        return self._tray_only

    def show_notification(self, title: str, msg: str) -> None:
        """Show a system notification if the tray is available."""
        if self._tray:
            self._tray.showMessage(
                title, msg,
                QSystemTrayIcon.MessageIcon.Information,
                4000,
            )

    def on_window_shown(self):
        """Call when the main window becomes visible."""
        if self._tray:
            self._act_show.setText(tr("tray_hide"))
        if not self._tray_only:
            _set_dock_icon_visible(True)

    def on_window_hidden(self):
        """Call when the main window is hidden to tray."""
        if self._tray:
            self._act_show.setText(tr("tray_show"))
        if not self._tray_only:
            _set_dock_icon_visible(False)

    def on_window_visibility_changed(self, visible: bool):
        """Legacy helper — delegates to on_window_shown/on_window_hidden."""
        if visible:
            self.on_window_shown()
        else:
            self.on_window_hidden()

    # ------------------------------------------------------------------
    # Tray interaction
    # ------------------------------------------------------------------

    def _on_activated(self, reason: QSystemTrayIcon.ActivationReason):
        # Single click on Windows / double-click toggle
        if reason in (
            QSystemTrayIcon.ActivationReason.Trigger,
            QSystemTrayIcon.ActivationReason.DoubleClick,
        ):
            self._on_show_hide()

    def _on_show_hide(self):
        win = self._window
        if win.isVisible() and not win.isMinimized():
            win.hide()
        else:
            win.show()
            win.setWindowState(
                win.windowState() & ~Qt.WindowState.WindowMinimized
            )
            win.raise_()
            win.activateWindow()

    def _on_help(self):
        self._window.open_help()

    # ------------------------------------------------------------------
    # Start at Login
    # ------------------------------------------------------------------

    def _on_toggle_tray_only(self, checked: bool):
        self._tray_only = checked
        s = QSettings(_APP_NAME, _APP_NAME)
        s.setValue("app/trayOnlyMode", "true" if checked else "false")
        if checked:
            _set_dock_icon_visible(False)
        else:
            if self._window.isVisible():
                _set_dock_icon_visible(True)

    def _on_toggle_login(self, checked: bool):
        try:
            if checked:
                self._enable_login()
            else:
                self._disable_login()
        except Exception as exc:
            _logger.error("Failed to toggle Start at Login: %s", exc)
            # Revert the checkbox so the UI reflects actual state
            self._act_login.setChecked(not checked)

    def _is_start_at_login_enabled(self) -> bool:
        try:
            if platform.system() == "Darwin":
                return self._macos_plist_path().exists()
            if platform.system() == "Windows":
                return self._win_reg_exists()
        except Exception:
            pass
        return False

    def _enable_login(self):
        if platform.system() == "Darwin":
            self._macos_write_plist()
        elif platform.system() == "Windows":
            self._win_reg_write()

    def _disable_login(self):
        if platform.system() == "Darwin":
            p = self._macos_plist_path()
            if p.exists():
                p.unlink()
                _logger.info("LaunchAgent removed: %s", p)
        elif platform.system() == "Windows":
            self._win_reg_delete()

    # -- macOS LaunchAgent -------------------------------------------------

    def _macos_plist_path(self) -> Path:
        return Path.home() / "Library" / "LaunchAgents" / f"{_PLIST_LABEL}.plist"

    def _macos_write_plist(self):
        if getattr(sys, "frozen", False):
            # PyInstaller .app bundle — point to the bundle executable
            program_args = f"        <string>{sys.executable}</string>"
        else:
            # Running from source
            python = sys.executable
            script = Path(__file__).resolve().parent / "main.py"
            program_args = (
                f"        <string>{python}</string>\n"
                f"        <string>{script}</string>"
            )

        log_file = Path.home() / "Library" / "Logs" / "SA3NMEARelay.log"
        plist = (
            '<?xml version="1.0" encoding="UTF-8"?>\n'
            '<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN"\n'
            '    "http://www.apple.com/DTDs/PropertyList-1.0.dtd">\n'
            '<plist version="1.0">\n'
            "<dict>\n"
            "    <key>Label</key>\n"
            f"    <string>{_PLIST_LABEL}</string>\n"
            "    <key>ProgramArguments</key>\n"
            "    <array>\n"
            f"{program_args}\n"
            "    </array>\n"
            "    <key>RunAtLoad</key>\n"
            "    <true/>\n"
            "    <key>KeepAlive</key>\n"
            "    <false/>\n"
            "    <key>StandardOutPath</key>\n"
            f"    <string>{log_file}</string>\n"
            "    <key>StandardErrorPath</key>\n"
            f"    <string>{log_file}</string>\n"
            "</dict>\n"
            "</plist>\n"
        )

        path = self._macos_plist_path()
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(plist, encoding="utf-8")
        _logger.info("LaunchAgent written: %s", path)

    # -- Windows Registry --------------------------------------------------

    def _win_exe_cmd(self) -> str:
        if getattr(sys, "frozen", False):
            return f'"{sys.executable}"'
        python_dir = Path(sys.executable).parent
        pythonw = python_dir / "pythonw.exe"
        if not pythonw.exists():
            pythonw = Path(sys.executable)
        script = Path(__file__).resolve().parent / "main.py"
        return f'"{pythonw}" "{script}"'

    def _win_reg_exists(self) -> bool:
        try:
            import winreg
            key = winreg.OpenKey(
                winreg.HKEY_CURRENT_USER,
                r"Software\Microsoft\Windows\CurrentVersion\Run",
                0,
                winreg.KEY_QUERY_VALUE,
            )
            winreg.QueryValueEx(key, _APP_NAME)
            winreg.CloseKey(key)
            return True
        except Exception:
            return False

    def _win_reg_write(self):
        import winreg
        key = winreg.OpenKey(
            winreg.HKEY_CURRENT_USER,
            r"Software\Microsoft\Windows\CurrentVersion\Run",
            0,
            winreg.KEY_SET_VALUE,
        )
        winreg.SetValueEx(key, _APP_NAME, 0, winreg.REG_SZ, self._win_exe_cmd())
        winreg.CloseKey(key)
        _logger.info("Registry run key written for start at login.")

    def _win_reg_delete(self):
        try:
            import winreg
            key = winreg.OpenKey(
                winreg.HKEY_CURRENT_USER,
                r"Software\Microsoft\Windows\CurrentVersion\Run",
                0,
                winreg.KEY_SET_VALUE,
            )
            winreg.DeleteValue(key, _APP_NAME)
            winreg.CloseKey(key)
            _logger.info("Registry run key removed.")
        except FileNotFoundError:
            pass
