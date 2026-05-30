"""Connection + TCP Relay control panel.

Contains two tabs:
  Connection  — configure Sailaway NMEA Gateway host/port and connect/disconnect.
  TCP Relay   — configure and start/stop the outbound relay server.
"""

from __future__ import annotations

import json

from PyQt6.QtCore import QSettings, Qt, pyqtSignal
from PyQt6.QtWidgets import (
    QComboBox,
    QFormLayout,
    QGridLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QSizePolicy,
    QSpinBox,
    QTabWidget,
    QVBoxLayout,
    QWidget,
)

from translations import LANGUAGE_NAMES, get_language, set_language, tr

_SETTINGS_ORG = "SA3NMEARelay"
_SETTINGS_APP = "SA3NMEARelay"


class ConnectionPanel(QWidget):
    """Control panel with Connection and TCP Relay tabs."""

    connect_clicked = pyqtSignal(str, int)           # host, port
    disconnect_clicked = pyqtSignal()
    tcp_relay_toggle = pyqtSignal(str, int)          # host, port
    tcp_relay_settings_changed = pyqtSignal(str, int)
    language_changed = pyqtSignal(str)               # lang code

    def __init__(self, parent=None):
        super().__init__(parent)

        self.tabs = QTabWidget(self)

        self.tabs.addTab(self._create_connection_tab(), tr("tab_connection"))
        self.tabs.addTab(self._create_relay_tab(), tr("tab_tcp_relay"))

        # Language selector row at the bottom
        lang_row = QHBoxLayout()
        lang_lbl = QLabel(tr("language_label") + ":")
        lang_lbl.setStyleSheet("color: #888; font-size: 9pt;")
        self._lang_combo = QComboBox()
        for code, name in LANGUAGE_NAMES.items():
            self._lang_combo.addItem(name, code)
        cur_idx = self._lang_combo.findData(get_language())
        if cur_idx >= 0:
            self._lang_combo.setCurrentIndex(cur_idx)
        self._lang_combo.currentIndexChanged.connect(self._on_language_changed)
        lang_row.addWidget(lang_lbl)
        lang_row.addWidget(self._lang_combo)
        lang_row.addStretch()

        layout = QVBoxLayout(self)
        layout.addWidget(self.tabs)
        layout.addLayout(lang_row)
        layout.setContentsMargins(0, 0, 0, 4)

        self._apply_styles()
        self._load_settings()
        self._refresh_toggle_texts()

        self.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Preferred)
        self.setMinimumWidth(260)
        self.setMaximumHeight(590)

    # ------------------------------------------------------------------
    # Tab builders
    # ------------------------------------------------------------------

    def _create_connection_tab(self) -> QWidget:
        tab = QWidget()

        # Host combo (editable, with history)
        self.host = QComboBox()
        self.host.setEditable(True)
        try:
            self.host.setInsertPolicy(QComboBox.InsertPolicy.NoInsert)
        except Exception:
            pass

        # Port combo (editable, with history)
        self.port = QComboBox()
        self.port.setEditable(True)
        try:
            self.port.setInsertPolicy(QComboBox.InsertPolicy.NoInsert)
        except Exception:
            pass

        # Auto-connect toggle
        self.chk_auto = QPushButton(tr("auto_connect"))
        self.chk_auto.setCheckable(True)
        self.chk_auto.setProperty("pill", "true")
        self.chk_auto.setToolTip(tr("auto_connect_tooltip"))

        # Action buttons
        self.btn_connect = QPushButton(tr("btn_connect"))
        self.btn_connect.setProperty("primary", "true")
        self.btn_disconnect = QPushButton(tr("btn_disconnect"))
        self.btn_clear_history = QPushButton(tr("btn_clear_history"))

        for btn in (self.btn_connect, self.btn_disconnect):
            btn.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)

        self._btn_grid = QGridLayout()
        self._last_cols = None
        self._btns = [self.btn_connect, self.btn_disconnect]

        # Histories (loaded later)
        self._hosts_history: list = []
        self._ports_history: list = []

        # Form
        form = QFormLayout(tab)
        form.addRow(tr("host_label"), self.host)
        form.addRow(tr("port_label"), self.port)
        form.addRow("", self.chk_auto)
        form.addRow("", self._btn_grid)
        form.addRow("", self.btn_clear_history)

        # Help text
        self._conn_help_lbl = QLabel()
        try:
            self._conn_help_lbl.setTextFormat(Qt.TextFormat.RichText)
        except Exception:
            pass
        self._conn_help_lbl.setWordWrap(True)
        try:
            self._conn_help_lbl.setAlignment(Qt.AlignmentFlag.AlignHCenter)
        except Exception:
            pass
        self._conn_help_lbl.setText(tr("connection_help"))
        form.addRow("", self._conn_help_lbl)

        self._rebuild_button_grid(force=True)

        # Signals
        self.btn_connect.clicked.connect(self._on_connect)
        self.btn_disconnect.clicked.connect(self.disconnect_clicked.emit)
        self.btn_clear_history.clicked.connect(self._on_clear_history)
        self.chk_auto.toggled.connect(self._on_auto_toggled)

        return tab

    def _create_relay_tab(self) -> QWidget:
        tab = QWidget()

        self._relay_group = QGroupBox(tr("relay_group"))
        g_layout = QVBoxLayout()

        settings_form = QFormLayout()

        self.tcp_host_input = QLineEdit("0.0.0.0")
        self.tcp_host_input.setPlaceholderText("0.0.0.0  (all interfaces)")
        settings_form.addRow(tr("relay_listen_host"), self.tcp_host_input)

        self.tcp_port_input = QSpinBox()
        self.tcp_port_input.setRange(1024, 65535)
        self.tcp_port_input.setValue(10111)
        settings_form.addRow(tr("relay_port"), self.tcp_port_input)

        g_layout.addLayout(settings_form)

        self.chk_auto_relay = QPushButton(tr("auto_relay"))
        self.chk_auto_relay.setCheckable(True)
        self.chk_auto_relay.setProperty("pill", "true")
        self.chk_auto_relay.setToolTip(tr("auto_relay_tooltip"))
        self.chk_auto_relay.toggled.connect(self._on_auto_relay_toggled)
        g_layout.addWidget(self.chk_auto_relay)

        self.tcp_relay_btn = QPushButton(tr("btn_start_relay"))
        self.tcp_relay_btn.setProperty("primary", "true")
        self.tcp_relay_btn.clicked.connect(self._on_tcp_relay_toggle)
        g_layout.addWidget(self.tcp_relay_btn)

        self.tcp_status_label = QLabel(tr("relay_inactive"))
        self.tcp_status_label.setStyleSheet("color: #888; font-size: 9pt;")
        g_layout.addWidget(self.tcp_status_label)

        self.tcp_clients_label = QLabel(tr("relay_clients", n=0))
        g_layout.addWidget(self.tcp_clients_label)

        self._relay_help_lbl = QLabel()
        try:
            self._relay_help_lbl.setTextFormat(Qt.TextFormat.RichText)
        except Exception:
            pass
        self._relay_help_lbl.setWordWrap(True)
        try:
            self._relay_help_lbl.setAlignment(Qt.AlignmentFlag.AlignHCenter)
        except Exception:
            pass
        self._relay_help_lbl.setText(tr("relay_help"))
        g_layout.addWidget(self._relay_help_lbl)
        g_layout.addStretch()

        self._relay_group.setLayout(g_layout)
        tab_layout = QVBoxLayout(tab)
        tab_layout.addWidget(self._relay_group)
        tab_layout.addStretch()
        return tab

    # ------------------------------------------------------------------
    # Relay tab public update methods (called from main window)
    # ------------------------------------------------------------------

    def update_tcp_relay_status(self, active: bool, message: str = ""):
        if active:
            self.tcp_relay_btn.setText(tr("btn_stop_relay"))
            self.tcp_relay_btn.setStyleSheet("background-color: #51cf66;")
            self.tcp_host_input.setEnabled(False)
            self.tcp_port_input.setEnabled(False)
            if message:
                self.tcp_status_label.setText(message)
                self.tcp_status_label.setStyleSheet("color: #51cf66; font-size: 9pt;")
        else:
            self.tcp_relay_btn.setText(tr("btn_start_relay"))
            self.tcp_relay_btn.setStyleSheet("")
            self.tcp_host_input.setEnabled(True)
            self.tcp_port_input.setEnabled(True)
            self.tcp_status_label.setText(message or tr("relay_inactive"))
            self.tcp_status_label.setStyleSheet("color: #888; font-size: 9pt;")

    def update_tcp_relay_error(self, error_msg: str):
        self.tcp_status_label.setText(f"Error: {error_msg}")
        self.tcp_status_label.setStyleSheet("color: #ff6b6b; font-size: 9pt;")

    def update_tcp_client_count(self, count: int):
        self.tcp_clients_label.setText(tr("relay_clients", n=count))

    def update_connection_status(self, connected: bool):
        self.btn_connect.setEnabled(not connected)
        self.btn_disconnect.setEnabled(connected)

    # ------------------------------------------------------------------
    # Internal event handlers
    # ------------------------------------------------------------------

    def _on_tcp_relay_toggle(self):
        host = self.tcp_host_input.text().strip() or "0.0.0.0"
        port = self.tcp_port_input.value()
        self.tcp_relay_toggle.emit(host, port)

    def _on_connect(self):
        self._save_settings()
        self.connect_clicked.emit(self._current_host(), self._current_port())

    def _on_clear_history(self):
        self._hosts_history.clear()
        self._ports_history.clear()
        s = QSettings(_SETTINGS_ORG, _SETTINGS_APP)
        s.remove("network/hostsHistory")
        s.remove("network/portsHistory")
        self._rebuild_host_combo()
        self._rebuild_port_combo()

    def _on_language_changed(self, idx: int):
        code = self._lang_combo.itemData(idx)
        if code and code != get_language():
            set_language(code)
            s = QSettings(_SETTINGS_ORG, _SETTINGS_APP)
            s.setValue("app/language", code)
            self._retranslate_ui()
            self.language_changed.emit(code)

    def _retranslate_ui(self):
        """Update all visible strings after a language change."""
        self.tabs.setTabText(0, tr("tab_connection"))
        self.tabs.setTabText(1, tr("tab_tcp_relay"))
        self.chk_auto.setToolTip(tr("auto_connect_tooltip"))
        self.btn_connect.setText(tr("btn_connect"))
        self.btn_disconnect.setText(tr("btn_disconnect"))
        self.btn_clear_history.setText(tr("btn_clear_history"))
        self._conn_help_lbl.setText(tr("connection_help"))
        self._relay_group.setTitle(tr("relay_group"))
        self.chk_auto_relay.setToolTip(tr("auto_relay_tooltip"))
        self.tcp_status_label.setText(tr("relay_inactive"))
        self._relay_help_lbl.setText(tr("relay_help"))
        self._refresh_toggle_texts()
        # Relay button text depends on current relay state — preserve it
        is_running = not self.tcp_relay_btn.isEnabled() or \
            self.tcp_relay_btn.text() not in (tr("btn_start_relay"), "Start TCP Relay",
                                               "Démarrer le relais TCP",
                                               "TCP-Weiterleitung starten",
                                               "TCP-doorstuur starten")
        # Simpler: check stylesheet to determine active state
        if self.tcp_relay_btn.styleSheet():
            self.tcp_relay_btn.setText(tr("btn_stop_relay"))
        else:
            self.tcp_relay_btn.setText(tr("btn_start_relay"))

    def _on_auto_toggled(self, checked: bool):
        self.chk_auto.setText(tr("auto_connect_on") if checked else tr("auto_connect"))

    def _on_auto_relay_toggled(self, checked: bool):
        self.chk_auto_relay.setText(tr("auto_relay_on") if checked else tr("auto_relay"))
        s = QSettings(_SETTINGS_ORG, _SETTINGS_APP)
        s.setValue("relay/autoRelay", "true" if checked else "false")

    def _refresh_toggle_texts(self):
        self.chk_auto.setText(
            tr("auto_connect_on") if self.chk_auto.isChecked() else tr("auto_connect")
        )
        self.chk_auto_relay.setText(
            tr("auto_relay_on") if self.chk_auto_relay.isChecked() else tr("auto_relay")
        )

    # ------------------------------------------------------------------
    # Current value helpers
    # ------------------------------------------------------------------

    def _current_host(self) -> str:
        try:
            return self.host.currentText().strip() or "127.0.0.1"
        except Exception:
            return "127.0.0.1"

    def _current_port(self) -> int:
        try:
            return max(1, min(65535, int(self.port.currentText().strip())))
        except Exception:
            return 10110

    def is_auto_connect(self) -> bool:
        return self.chk_auto.isChecked()

    def is_auto_relay(self) -> bool:
        return self.chk_auto_relay.isChecked()

    # ------------------------------------------------------------------
    # Combo rebuilders
    # ------------------------------------------------------------------

    def _rebuild_host_combo(self):
        cur = self._current_host()
        self.host.blockSignals(True)
        self.host.clear()
        self.host.addItems(self._hosts_history or ["127.0.0.1"])
        try:
            self.host.setCurrentText(cur)
        except Exception:
            pass
        self.host.blockSignals(False)

    def _rebuild_port_combo(self):
        cur = self.port.currentText()
        self.port.blockSignals(True)
        self.port.clear()
        self.port.addItems(
            [str(p) for p in self._ports_history] if self._ports_history else ["10110"]
        )
        try:
            self.port.setCurrentText(cur)
        except Exception:
            pass
        self.port.blockSignals(False)

    def record_success_host(self, host: str):
        if not host:
            return
        try:
            self._hosts_history.remove(host)
        except ValueError:
            pass
        self._hosts_history.insert(0, host)
        self._hosts_history = self._hosts_history[:10]
        self._rebuild_host_combo()
        self.host.setCurrentText(host)
        s = QSettings(_SETTINGS_ORG, _SETTINGS_APP)
        s.setValue("network/hostsHistory", json.dumps(self._hosts_history))

    def record_success_port(self, port: int):
        if not isinstance(port, int) or not (1 <= port <= 65535):
            return
        try:
            self._ports_history.remove(port)
        except ValueError:
            pass
        self._ports_history.insert(0, port)
        self._ports_history = self._ports_history[:10]
        self._rebuild_port_combo()
        self.port.setCurrentText(str(port))
        s = QSettings(_SETTINGS_ORG, _SETTINGS_APP)
        s.setValue("network/portsHistory", json.dumps(self._ports_history))

    # ------------------------------------------------------------------
    # Button grid (responsive 1 or 2 columns)
    # ------------------------------------------------------------------

    def _rebuild_button_grid(self, force: bool = False):
        w = self.width() if self.width() > 0 else 400
        cols = 1 if w < 280 else 2
        if not force and cols == self._last_cols:
            return
        self._last_cols = cols
        while self._btn_grid.count():
            self._btn_grid.takeAt(0)
        for i, btn in enumerate(self._btns):
            r, c = divmod(i, cols)
            self._btn_grid.addWidget(btn, r, c)
        for c in range(cols):
            self._btn_grid.setColumnStretch(c, 1)

    def resizeEvent(self, event):
        try:
            self._rebuild_button_grid()
        except Exception:
            pass
        super().resizeEvent(event)

    # ------------------------------------------------------------------
    # Persist / restore settings
    # ------------------------------------------------------------------

    def _load_settings(self):
        s = QSettings(_SETTINGS_ORG, _SETTINGS_APP)

        # Language — load first so all subsequent tr() calls use the right language
        saved_lang = str(s.value("app/language", "en"))
        set_language(saved_lang)
        idx = self._lang_combo.findData(saved_lang)
        if idx >= 0:
            self._lang_combo.blockSignals(True)
            self._lang_combo.setCurrentIndex(idx)
            self._lang_combo.blockSignals(False)

        saved_host = str(s.value("network/host", "127.0.0.1"))
        try:
            raw = s.value("network/hostsHistory", "[]")
            self._hosts_history = json.loads(raw) if isinstance(raw, str) else []
        except Exception:
            self._hosts_history = []
        self._rebuild_host_combo()
        self.host.setCurrentText(saved_host)

        saved_port = str(s.value("network/port", "10110"))
        try:
            raw = s.value("network/portsHistory", "[]")
            self._ports_history = json.loads(raw) if isinstance(raw, str) else []
        except Exception:
            self._ports_history = []
        self._rebuild_port_combo()
        self.port.setCurrentText(saved_port)

        val = str(s.value("network/autoConnect", "false")).strip().lower()
        self.chk_auto.setChecked(val in ("true", "1", "yes", "on"))

        # TCP relay settings
        self.tcp_host_input.setText(str(s.value("relay/host", "0.0.0.0")))
        try:
            self.tcp_port_input.setValue(int(s.value("relay/port", 10111)))
        except Exception:
            self.tcp_port_input.setValue(10111)

        val = str(s.value("relay/autoRelay", "false")).strip().lower()
        self.chk_auto_relay.setChecked(val in ("true", "1", "yes", "on"))

    def _save_settings(self):
        s = QSettings(_SETTINGS_ORG, _SETTINGS_APP)
        s.setValue("network/host", self._current_host())
        s.setValue("network/port", self._current_port())
        s.setValue("network/autoConnect", "true" if self.chk_auto.isChecked() else "false")
        s.setValue("relay/host", self.tcp_host_input.text().strip() or "0.0.0.0")
        s.setValue("relay/port", self.tcp_port_input.value())

    def save_relay_settings(self):
        """Persist relay host/port (call after relay starts successfully)."""
        s = QSettings(_SETTINGS_ORG, _SETTINGS_APP)
        s.setValue("relay/host", self.tcp_host_input.text().strip() or "0.0.0.0")
        s.setValue("relay/port", self.tcp_port_input.value())

    # ------------------------------------------------------------------
    # Styles
    # ------------------------------------------------------------------

    def _apply_styles(self):
        self.setStyleSheet(
            """
            QWidget {
                background-color: #1e1e2e;
                color: #cdd6f4;
                font-family: "Helvetica Neue", Arial, sans-serif;
                font-size: 10pt;
            }
            QTabWidget::pane {
                border: 1px solid #45475a;
                border-radius: 4px;
            }
            QTabBar::tab {
                background: #313244;
                color: #bac2de;
                padding: 6px 14px;
                border-radius: 4px 4px 0 0;
                margin-right: 2px;
            }
            QTabBar::tab:selected {
                background: #1e1e2e;
                color: #cba6f7;
            }
            QComboBox, QLineEdit, QSpinBox {
                background-color: #313244;
                border: 1px solid #45475a;
                border-radius: 4px;
                padding: 4px 8px;
                color: #cdd6f4;
            }
            QComboBox:focus, QLineEdit:focus, QSpinBox:focus {
                border-color: #cba6f7;
            }
            QPushButton {
                background-color: #45475a;
                border: 1px solid #585b70;
                border-radius: 6px;
                padding: 5px 10px;
                color: #cdd6f4;
            }
            QPushButton:hover { background-color: #585b70; }
            QPushButton:pressed { background-color: #313244; }
            QPushButton[primary="true"] {
                background-color: #89b4fa;
                color: #1e1e2e;
                font-weight: bold;
                border: none;
            }
            QPushButton[primary="true"]:hover { background-color: #b4befe; }
            QPushButton[pill="true"] {
                border-radius: 10px;
                padding: 4px 14px;
            }
            QPushButton[pill="true"]:checked {
                background-color: #a6e3a1;
                color: #1e1e2e;
                border: none;
            }
            QGroupBox {
                border: 1px solid #45475a;
                border-radius: 6px;
                margin-top: 10px;
                padding-top: 6px;
                font-weight: bold;
                color: #a6adc8;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 4px;
            }
            QLabel { color: #cdd6f4; }
            """
        )
