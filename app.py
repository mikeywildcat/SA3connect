"""Main application window for SA3 NMEA Relay.

Wires together:
  - ConnectionPanel (left dock)
  - NMEA sentence log (centre)
  - Status bar
  - TcpWorker (Sailaway inbound)
  - TCPRelay (outbound relay server)
  - NMEACorrector (sentence correction / filtering)
"""

from __future__ import annotations

import logging
import time
from collections import deque
from typing import Optional

from PyQt6.QtCore import QCoreApplication, QSettings, QThread, Qt, QTimer, QUrl
from PyQt6.QtGui import QDesktopServices
from PyQt6.QtWidgets import (
    QHBoxLayout,
    QLabel,
    QMainWindow,
    QMenu,
    QMenuBar,
    QMessageBox,
    QPlainTextEdit,
    QSizePolicy,
    QSplitter,
    QStatusBar,
    QVBoxLayout,
    QWidget,
)

from connection_panel import ConnectionPanel, _SETTINGS_ORG, _SETTINGS_APP
from nmea_corrector import correct_sentence
from tcp_client import TcpWorker
from tcp_relay import TCPRelay
from tray_manager import TrayManager
from translations import tr

_logger = logging.getLogger(__name__)

# Rolling log window: keep the last N seconds of sentences
_LOG_WINDOW_SECONDS = 30
_LOG_MAX_LINES = 500


class MainWindow(QMainWindow):

    def __init__(self):
        super().__init__()
        self.setWindowTitle("SA3 NMEA Relay")
        self.resize(760, 520)

        # Runtime state
        self._tcp_worker: Optional[TcpWorker] = None
        self._tcp_thread: Optional[QThread] = None
        self._relay: Optional[TCPRelay] = None
        self._own_boat_id: Optional[str] = None  # detected from $SLBID
        self._sentence_count = 0
        self._relayed_count = 0
        self._log_lines: deque = deque(maxlen=_LOG_MAX_LINES)  # (timestamp, text)
        self._was_connected = False      # True once a session is established
        self._manual_disconnect = False  # True when user clicks Disconnect
        self._auto_retry_timer: Optional[QTimer] = None  # retries during startup auto-connect

        self._build_ui()
        self._connect_signals()

        # System tray / menu bar icon
        self._tray = TrayManager(self)

        # Startup notification (delayed so tray icon is fully ready)
        QTimer.singleShot(800, self._show_startup_notification)

        # Status refresh timer
        self._status_timer = QTimer(self)
        self._status_timer.timeout.connect(self._refresh_status_bar)
        self._status_timer.start(1000)

        # Auto-connect on startup if configured
        if self.conn_panel.is_auto_connect():
            QTimer.singleShot(400, self.conn_panel.btn_connect.click)
            # Arm the retry timer — will keep retrying until connected
            self._auto_retry_timer = QTimer(self)
            self._auto_retry_timer.setInterval(10_000)  # retry every 10 s
            self._auto_retry_timer.timeout.connect(self._auto_retry_connect)
            self._auto_retry_timer.start()

        # Auto-relay on startup if configured
        if self.conn_panel.is_auto_relay():
            QTimer.singleShot(600, self.conn_panel.tcp_relay_btn.click)

    # ------------------------------------------------------------------
    # UI construction
    # ------------------------------------------------------------------

    def _build_ui(self):
        central = QWidget()
        self.setCentralWidget(central)
        root = QHBoxLayout(central)
        root.setContentsMargins(6, 6, 6, 6)
        root.setSpacing(6)

        # ---- Left panel: ConnectionPanel ----
        self.conn_panel = ConnectionPanel()
        self.conn_panel.setSizePolicy(
            QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Expanding
        )

        # ---- Right panel: log + stats ----
        right = QWidget()
        right_layout = QVBoxLayout(right)
        right_layout.setContentsMargins(0, 0, 0, 0)
        right_layout.setSpacing(4)

        # Stats bar
        stats_row = QHBoxLayout()
        self.lbl_rx = QLabel(tr("stat_received", n=0))
        self.lbl_relayed = QLabel(tr("stat_relayed", n=0))
        self.lbl_boat_id = QLabel(tr("stat_boat_id_none"))
        for lbl in (self.lbl_rx, self.lbl_relayed, self.lbl_boat_id):
            lbl.setStyleSheet("color: #888; font-size: 9pt;")
            stats_row.addWidget(lbl)
        stats_row.addStretch()
        right_layout.addLayout(stats_row)

        # NMEA log viewer
        self.log_viewer = QPlainTextEdit()
        self.log_viewer.setReadOnly(True)
        self.log_viewer.setMaximumBlockCount(_LOG_MAX_LINES)
        self.log_viewer.setStyleSheet(
            "background-color: #11111b; color: #a6e3a1; "
            "font-family: 'Menlo', 'Consolas', 'Courier New', monospace; "
            "font-size: 9pt; border: 1px solid #45475a; border-radius: 4px;"
        )
        right_layout.addWidget(self.log_viewer)

        # Splitter
        splitter = QSplitter(Qt.Orientation.Horizontal)
        splitter.addWidget(self.conn_panel)
        splitter.addWidget(right)
        splitter.setStretchFactor(0, 0)
        splitter.setStretchFactor(1, 1)
        splitter.setSizes([280, 460])

        root.addWidget(splitter)

        # Status bar
        self.setStatusBar(QStatusBar())
        self.lbl_conn_status = QLabel(tr("status_disconnected"))
        self.lbl_conn_status.setStyleSheet("color: #f38ba8;")
        self.statusBar().addWidget(self.lbl_conn_status)

        self.setStyleSheet(
            "QMainWindow { background-color: #1e1e2e; }"
            "QSplitter::handle { background-color: #45475a; width: 2px; }"
            "QStatusBar { background-color: #181825; color: #a6adc8; font-size: 9pt; }"
        )

        # Menu bar – File menu
        menu_bar = self.menuBar()
        file_menu = menu_bar.addMenu(tr("menu_file"))
        act_quit = file_menu.addAction(tr("menu_quit"))
        act_quit.triggered.connect(QCoreApplication.quit)

        # Menu bar – Help menu
        help_menu = menu_bar.addMenu(tr("menu_help"))
        act_manual = help_menu.addAction(tr("menu_help_manual"))
        act_manual.triggered.connect(self.open_help)

    # ------------------------------------------------------------------
    # Signal wiring
    # ------------------------------------------------------------------

    def _connect_signals(self):
        self.conn_panel.connect_clicked.connect(self._on_connect)
        self.conn_panel.disconnect_clicked.connect(self._on_disconnect)
        self.conn_panel.tcp_relay_toggle.connect(self._on_relay_toggle)
        self.conn_panel.language_changed.connect(self._on_language_changed)

    # ------------------------------------------------------------------
    # Connection management
    # ------------------------------------------------------------------

    def _on_connect(self, host: str, port: int):
        if self._tcp_worker is not None:
            return  # already connected

        self._tcp_thread = QThread()
        self._tcp_worker = TcpWorker(host, port)
        self._tcp_worker.moveToThread(self._tcp_thread)

        self._tcp_thread.started.connect(self._tcp_worker.run)
        self._tcp_worker.connected.connect(lambda: self._on_connected(host, port))
        self._tcp_worker.disconnected.connect(self._on_disconnected)
        self._tcp_worker.error.connect(self._on_connect_error)
        self._tcp_worker.line.connect(self._on_nmea_line)

        self._tcp_thread.start()
        self.lbl_conn_status.setText(tr("status_connecting", host=host, port=port))
        self.lbl_conn_status.setStyleSheet("color: #f9e2af;")
        self.conn_panel.update_connection_status(False)

    def _auto_retry_connect(self):
        """Retry connect automatically — only while not yet connected."""
        if self._tcp_worker is None and not self._manual_disconnect:
            self.conn_panel.btn_connect.click()

    def _stop_auto_retry(self):
        if self._auto_retry_timer is not None:
            self._auto_retry_timer.stop()
            self._auto_retry_timer = None

    def _show_startup_notification(self):
        if self._tray.is_available():
            self._tray.show_notification(
                tr("notif_running_title"),
                tr("notif_running_msg"),
            )

    def _on_connected(self, host: str, port: int):
        self._was_connected = True
        self._manual_disconnect = False
        self._stop_auto_retry()  # successfully connected — no more retries
        self.lbl_conn_status.setText(tr("status_connected", host=host, port=port))
        self.lbl_conn_status.setStyleSheet("color: #a6e3a1;")
        self.conn_panel.update_connection_status(True)
        self.conn_panel.record_success_host(host)
        self.conn_panel.record_success_port(port)
        self._log(tr("log_connected", host=host, port=port))
        if self._tray.is_available():
            self._tray.show_notification(
                tr("notif_connected_title"),
                tr("notif_connected_msg", host=host, port=port),
            )

    def _on_disconnect(self):
        if self._tcp_worker:
            self._manual_disconnect = True
            self._stop_auto_retry()  # user clicked Disconnect — cancel retries
            self._tcp_worker.stop()

    def _on_disconnected(self):
        was_connected = self._was_connected
        manual = self._manual_disconnect
        self._was_connected = False
        self._manual_disconnect = False

        self.lbl_conn_status.setText(tr("status_disconnected"))
        self.lbl_conn_status.setStyleSheet("color: #f38ba8;")
        self.conn_panel.update_connection_status(False)
        if self._tcp_thread:
            self._tcp_thread.quit()
            self._tcp_thread.wait(2000)
        self._tcp_worker = None
        self._tcp_thread = None
        self._log(tr("log_disconnected"))

        if was_connected and not manual:
            self._show_connection_lost_popup()

    def _show_connection_lost_popup(self):
        dlg = QMessageBox(self)
        dlg.setWindowTitle(tr("conn_lost_title"))
        dlg.setIcon(QMessageBox.Icon.Warning)
        dlg.setText(tr("conn_lost_msg"))
        dlg.setStandardButtons(QMessageBox.StandardButton.Ok)
        dlg.setStyleSheet(
            "QMessageBox { background-color: #1e1e2e; color: #cdd6f4; }"
            "QLabel { color: #cdd6f4; font-size: 10pt; }"
            "QPushButton { background:#89b4fa; color:#1e1e2e; border-radius:5px;"
            " padding:5px 20px; font-weight:bold; }"
            "QPushButton:hover { background:#b4befe; }"
        )
        dlg.exec()

    def _on_connect_error(self, msg: str):
        self.lbl_conn_status.setText(tr("status_error", msg=msg[:60]))
        self.lbl_conn_status.setStyleSheet("color: #f38ba8;")
        self.conn_panel.update_connection_status(False)
        self._log(tr("log_error", msg=msg))

    # ------------------------------------------------------------------
    # NMEA sentence processing
    # ------------------------------------------------------------------

    def _on_nmea_line(self, text: str):
        self._sentence_count += 1

        # Detect Sailaway boat ID from $SLBID sentences
        stripped = text.strip()
        if stripped.startswith("$SLBID"):
            try:
                bid = stripped.split(",")[1].split("*")[0].strip()
                if bid and bid != self._own_boat_id:
                    self._own_boat_id = bid
                    self.lbl_boat_id.setText(tr("stat_boat_id", bid=bid))
                    self._log(tr("log_boat_id", bid=bid))
            except Exception:
                pass

        # Correct and optionally relay
        corrected = correct_sentence(stripped, self._own_boat_id)
        if corrected is not None:
            if self._relay and self._relay.running:
                self._relay.send_sentence(corrected)
                self._relayed_count += 1

        # Append to log viewer (show original with possible conversion note)
        self._log(stripped)

    def _log(self, text: str):
        now = time.time()
        self._log_lines.append((now, text))
        # Trim old lines outside window
        cutoff = now - _LOG_WINDOW_SECONDS
        while self._log_lines and self._log_lines[0][0] < cutoff:
            self._log_lines.popleft()
        self.log_viewer.appendPlainText(text)

    def _refresh_status_bar(self):
        self.lbl_rx.setText(tr("stat_received", n=self._sentence_count))
        self.lbl_relayed.setText(tr("stat_relayed", n=self._relayed_count))

    def open_help(self):
        """Open the language-appropriate help file in the system default browser."""
        import os, sys
        from translations import get_language
        if getattr(sys, "frozen", False):
            base = sys._MEIPASS  # type: ignore[attr-defined]
        else:
            base = os.path.dirname(os.path.abspath(__file__))
        lang = get_language()
        candidate = f"help_{lang}.html" if lang != "en" else "help.html"
        path = os.path.join(base, candidate)
        if not os.path.exists(path):
            path = os.path.join(base, "help.html")
        QDesktopServices.openUrl(QUrl.fromLocalFile(path))

    def _on_language_changed(self, _lang: str):
        """Refresh any main-window strings that aren't in ConnectionPanel."""
        self.lbl_rx.setText(tr("stat_received", n=self._sentence_count))
        self.lbl_relayed.setText(tr("stat_relayed", n=self._relayed_count))
        if self._own_boat_id:
            self.lbl_boat_id.setText(tr("stat_boat_id", bid=self._own_boat_id))
        else:
            self.lbl_boat_id.setText(tr("stat_boat_id_none"))
        # Retranslate Help menu
        mb = self.menuBar()
        if mb.actions():
            mb.actions()[0].setText(tr("menu_help"))
            if mb.actions()[0].menu() and mb.actions()[0].menu().actions():
                mb.actions()[0].menu().actions()[0].setText(tr("menu_help_manual"))

    # ------------------------------------------------------------------
    # TCP relay management
    # ------------------------------------------------------------------

    def _on_relay_toggle(self, host: str, port: int):
        # Use `is not None` — not `.running` — so the check is correct even
        # during the brief window after start() before the thread sets running=True.
        if self._relay is not None:
            self._relay.finished.disconnect(self._on_relay_thread_finished)
            self._relay.stop()
            self._relay = None
            self.conn_panel.update_tcp_relay_status(False, "Relay stopped")
            self.conn_panel.save_relay_settings()
            return

        self._relay = TCPRelay(host, port)
        self._relay.status_changed.connect(self.conn_panel.update_tcp_relay_status)
        self._relay.error_occurred.connect(self._on_relay_error)
        self._relay.client_count_changed.connect(self.conn_panel.update_tcp_client_count)
        # Track unexpected exits so self._relay is always cleared when the thread dies.
        self._relay.finished.connect(self._on_relay_thread_finished)
        self._relay.start()
        self.conn_panel.save_relay_settings()

    def _on_relay_thread_finished(self):
        """Called whenever the relay QThread exits (normally or due to an error).
        Clears self._relay so the toggle button is always in sync with reality.
        The TCPRelay._cleanup() already emits status_changed(False) which resets
        the button text, so we only need to clear the object reference here.
        """
        if self._relay is not None:
            self._relay = None
            self.conn_panel.update_tcp_client_count(0)

    def _on_relay_error(self, msg: str):
        self.conn_panel.update_tcp_relay_error(msg)
        # Do NOT stop/clear here — the thread is already winding down and
        # _on_relay_thread_finished will clear self._relay when it finishes.

    # ------------------------------------------------------------------
    # Lifecycle
    # ------------------------------------------------------------------

    def closeEvent(self, event):
        """Hide to tray instead of closing, if tray is available."""
        if self._tray.is_available():
            event.ignore()
            self.hide()
        else:
            self._do_cleanup()
            event.accept()

    def showEvent(self, event):
        super().showEvent(event)
        if hasattr(self, "_tray") and self._tray.is_available():
            self._tray.on_window_shown()

    def hideEvent(self, event):
        super().hideEvent(event)
        if hasattr(self, "_tray") and self._tray.is_available():
            self._tray.on_window_hidden()

    def _do_cleanup(self):
        self._status_timer.stop()
        if self._tcp_worker:
            self._tcp_worker.stop()
        if self._relay:
            try:
                self._relay.finished.disconnect(self._on_relay_thread_finished)
            except Exception:
                pass
            self._relay.stop()
        if self._tcp_thread:
            self._tcp_thread.quit()
            self._tcp_thread.wait(2000)
