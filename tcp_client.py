"""TCP client worker for receiving NMEA sentences from Sailaway 3 NMEA Gateway."""

from __future__ import annotations

import socket
from typing import List

from PyQt6.QtCore import QObject, pyqtSignal, pyqtSlot

TCP_READ_BUFFER_SIZE = 4096
_MAX_BUF_SIZE = 65536  # 64 KB — drop buffer if no newline found within this limit


class TcpWorker(QObject):
    """Connects to Sailaway 3 NMEA Gateway and emits each received line."""

    connected = pyqtSignal()
    disconnected = pyqtSignal()
    error = pyqtSignal(str)
    line = pyqtSignal(str)

    def __init__(self, host: str, port: int, parent=None):
        super().__init__(parent)
        self.host = host
        self.port = int(port)
        self._running = True
        self._sock = None

    @pyqtSlot()
    def run(self):
        try:
            self._sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self._sock.settimeout(5.0)
            self._sock.connect((self.host, self.port))
            self._sock.settimeout(1.0)
            self.connected.emit()
            buf = b""
            while self._running:
                try:
                    data = self._sock.recv(TCP_READ_BUFFER_SIZE)
                    if not data:
                        break
                    buf += data
                    if len(buf) > _MAX_BUF_SIZE:
                        import logging
                        logging.getLogger(__name__).warning(
                            "TCP receive buffer exceeded %d bytes without a newline; discarding",
                            _MAX_BUF_SIZE,
                        )
                        buf = b""
                        continue
                    while b"\n" in buf:
                        raw, buf = buf.split(b"\n", 1)
                        s = raw.strip().decode(errors="ignore")
                        if s:
                            self.line.emit(s)
                except socket.timeout:
                    continue
        except Exception as e:
            self.error.emit(str(e))
        finally:
            try:
                if self._sock:
                    self._sock.close()
            finally:
                self.disconnected.emit()

    def stop(self):
        self._running = False
        try:
            if self._sock:
                self._sock.shutdown(socket.SHUT_RDWR)
        except Exception:
            pass
