"""Entry point for SA3 NMEA Relay.

Run directly:   python main.py
Or via package: nmea-relay
"""

from __future__ import annotations

import logging
import sys

# Ensure we can resolve our own modules whether running from source or bundled.
import os
if getattr(sys, "frozen", False):
    # PyInstaller bundle: _MEIPASS is the extraction directory
    _base = sys._MEIPASS  # type: ignore[attr-defined]
else:
    _base = os.path.dirname(os.path.abspath(__file__))

if _base not in sys.path:
    sys.path.insert(0, _base)


def _pick_language_on_first_run(app, icon_file: str) -> None:
    """Show a language-selection dialog on the very first launch."""
    from PyQt6.QtCore import QSettings, Qt
    from PyQt6.QtGui import QIcon, QPixmap
    from PyQt6.QtWidgets import (
        QDialog, QVBoxLayout, QHBoxLayout, QGridLayout, QLabel, QPushButton, QButtonGroup,
    )
    from translations import LANGUAGE_NAMES, set_language

    dialog = QDialog()
    dialog.setWindowTitle("SA3 NMEA Relay")
    dialog.setWindowFlags(dialog.windowFlags() & ~Qt.WindowType.WindowContextHelpButtonHint)
    dialog.setFixedWidth(380)
    dialog.setModal(True)

    if icon_file and __import__("os").path.exists(icon_file):
        dialog.setWindowIcon(QIcon(icon_file))

    layout = QVBoxLayout(dialog)
    layout.setSpacing(16)
    layout.setContentsMargins(24, 24, 24, 24)

    # Icon + heading row
    heading_row = QHBoxLayout()
    if icon_file and __import__("os").path.exists(icon_file):
        pix = QPixmap(icon_file).scaled(48, 48,
            Qt.AspectRatioMode.KeepAspectRatio,
            Qt.TransformationMode.SmoothTransformation)
        icon_lbl = QLabel()
        icon_lbl.setPixmap(pix)
        icon_lbl.setFixedSize(48, 48)
        heading_row.addWidget(icon_lbl)
    heading_row.addSpacing(12)
    title_lbl = QLabel("SA3 NMEA Relay")
    title_lbl.setStyleSheet("font-size: 16pt; font-weight: bold; color: #cdd6f4;")
    heading_row.addWidget(title_lbl)
    heading_row.addStretch()
    layout.addLayout(heading_row)

    sub_lbl = QLabel("Select your language / Sélectionnez votre langue\n"
                      "Sprache wählen / Selecteer uw taal")
    sub_lbl.setStyleSheet("color: #a6adc8; font-size: 9pt;")
    sub_lbl.setWordWrap(True)
    layout.addWidget(sub_lbl)

    # Language buttons — 2×2 grid so labels are never truncated
    btn_group = QButtonGroup(dialog)
    btn_group.setExclusive(True)
    lang_buttons: dict[str, QPushButton] = {}

    grid = QGridLayout()
    grid.setSpacing(8)
    btn_style = (
        "QPushButton { background:#313244; color:#cdd6f4; border:1px solid #45475a;"
        " border-radius:6px; font-size:10pt; padding:6px 12px; }"
        "QPushButton:checked { background:#89b4fa; color:#1e1e2e; border:1px solid #89b4fa; }"
        "QPushButton:hover:!checked { background:#45475a; }"
    )
    for i, (code, name) in enumerate(LANGUAGE_NAMES.items()):
        btn = QPushButton(name)
        btn.setCheckable(True)
        btn.setMinimumHeight(38)
        btn.setStyleSheet(btn_style)
        if code == "en":
            btn.setChecked(True)
        btn_group.addButton(btn)
        lang_buttons[code] = btn
        grid.addWidget(btn, i // 2, i % 2)
    layout.addLayout(grid)

    # Confirm button
    ok_btn = QPushButton("OK")
    ok_btn.setFixedHeight(38)
    ok_btn.setStyleSheet(
        "QPushButton { background:#89b4fa; color:#1e1e2e; border-radius:6px;"
        " font-size:11pt; font-weight:bold; }"
        "QPushButton:hover { background:#b4befe; }"
    )
    ok_btn.clicked.connect(dialog.accept)
    layout.addWidget(ok_btn)

    dialog.setStyleSheet("QDialog { background-color: #1e1e2e; }")

    dialog.exec()

    # Determine selected language
    chosen = "en"
    for code, btn in lang_buttons.items():
        if btn.isChecked():
            chosen = code
            break

    # Persist and activate
    set_language(chosen)
    s = QSettings("SA3NMEARelay", "SA3NMEARelay")
    s.setValue("app/language", chosen)


def main():
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s  %(levelname)-8s  %(name)s: %(message)s",
        datefmt="%H:%M:%S",
    )

    from PyQt6.QtCore import QCoreApplication
    from PyQt6.QtWidgets import QApplication

    # Required for QSettings to resolve org/app name correctly
    QCoreApplication.setOrganizationName("SA3NMEARelay")
    QCoreApplication.setApplicationName("SA3NMEARelay")

    app = QApplication(sys.argv)
    app.setApplicationDisplayName("SA3 NMEA Relay")

    # Keep running when the window is closed (lives in the tray/menu bar)
    app.setQuitOnLastWindowClosed(False)

    from app import MainWindow

    # Set app-wide window / taskbar icon
    import os
    from PyQt6.QtGui import QIcon
    _icon_file = os.path.join(_base, "heelappicon.png")
    if os.path.exists(_icon_file):
        app.setWindowIcon(QIcon(_icon_file))

    # First-run language picker — only shown when no language has been saved yet
    from PyQt6.QtCore import QSettings
    _s = QSettings("SA3NMEARelay", "SA3NMEARelay")
    if _s.value("app/language") is None:
        _pick_language_on_first_run(app, _icon_file)

    window = MainWindow()

    # In tray-only mode the window starts hidden; tray icon is the only entry point
    _tray_only = str(_s.value("app/trayOnlyMode", "false")).lower() in ("true", "1", "yes")
    if not _tray_only:
        window.show()

    # Clean up workers/threads when the user quits from the tray menu
    app.aboutToQuit.connect(window._do_cleanup)

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
