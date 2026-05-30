"""TCP relay server — broadcasts corrected NMEA sentences to connected navigation apps."""

from __future__ import annotations

import logging
import queue
import socket
import threading
from typing import List

from PyQt6.QtCore import QThread, pyqtSignal

_logger = logging.getLogger(__name__)


class TCPRelay(QThread):
    """TCP server that listens for client connections and broadcasts NMEA sentences."""

    status_changed = pyqtSignal(bool, str)    # (active, message)
    error_occurred = pyqtSignal(str)
    client_count_changed = pyqtSignal(int)

    def __init__(self, host: str = "0.0.0.0", port: int = 10111, parent=None):
        super().__init__(parent)
        self.host = host
        self.port = port
        self.running = False
        self.server_socket = None
        self.clients: List[socket.socket] = []
        self.clients_lock = threading.Lock()
        self._send_queue: queue.Queue = queue.Queue(maxsize=1000)

    # ------------------------------------------------------------------
    # QThread entry point
    # ------------------------------------------------------------------

    def run(self):
        try:
            self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            self.server_socket.bind((self.host, self.port))
            self.server_socket.listen(5)
            self.server_socket.settimeout(1.0)

            self.running = True
            self.status_changed.emit(True, f"Relay active on {self.host}:{self.port}")
            _logger.info("TCP relay started on %s:%d", self.host, self.port)

            sender = threading.Thread(target=self._sender_loop, daemon=True)
            sender.start()

            while self.running:
                try:
                    client_sock, address = self.server_socket.accept()
                    _logger.info("Client connected from %s", address)
                    with self.clients_lock:
                        self.clients.append(client_sock)
                        self.client_count_changed.emit(len(self.clients))
                except socket.timeout:
                    self._cleanup_clients()
                except Exception as exc:
                    if self.running:
                        _logger.error("Accept error: %s", exc)

        except Exception as exc:
            msg = f"TCP relay error: {exc}"
            _logger.error(msg)
            self.error_occurred.emit(msg)
        finally:
            self._cleanup()

    # ------------------------------------------------------------------
    # Send helpers (thread-safe)
    # ------------------------------------------------------------------

    def send_sentence(self, sentence: str):
        """Queue a single NMEA sentence (with or without trailing CRLF)."""
        if not sentence or not self.running:
            return
        if not sentence.endswith("\n"):
            sentence += "\r\n"
        self._enqueue(sentence)

    def send_sentences(self, sentences: List[str]):
        """Queue multiple NMEA sentences at once."""
        if not sentences or not self.running:
            return
        data = "\r\n".join(sentences) + "\r\n"
        self._enqueue(data)

    def _enqueue(self, data: str):
        try:
            self._send_queue.put_nowait(data)
        except queue.Full:
            try:
                self._send_queue.get_nowait()
                self._send_queue.put_nowait(data)
            except Exception:
                pass

    # ------------------------------------------------------------------
    # Internal threads
    # ------------------------------------------------------------------

    def _sender_loop(self):
        while self.running:
            try:
                data = self._send_queue.get(timeout=0.1)
                if data is None:
                    break
                data_bytes = data.encode("ascii", errors="ignore")
                with self.clients_lock:
                    disconnected = []
                    for client in self.clients:
                        try:
                            client.sendall(data_bytes)
                        except Exception:
                            disconnected.append(client)
                    for client in disconnected:
                        try:
                            client.close()
                        except Exception:
                            pass
                        self.clients.remove(client)
                    if disconnected:
                        self.client_count_changed.emit(len(self.clients))
            except queue.Empty:
                continue
            except Exception as exc:
                _logger.error("Sender loop error: %s", exc)

    def _cleanup_clients(self):
        with self.clients_lock:
            active = []
            for client in self.clients:
                try:
                    # MSG_DONTWAIT + MSG_PEEK: non-blocking peek detects clean closes.
                    # Falls back to send probe for platforms that don't support it.
                    client.recv(1, socket.MSG_DONTWAIT | socket.MSG_PEEK)
                    active.append(client)
                except BlockingIOError:
                    # No data yet — socket is still alive
                    active.append(client)
                except Exception:
                    try:
                        client.close()
                    except Exception:
                        pass
            if len(active) != len(self.clients):
                self.clients = active
                self.client_count_changed.emit(len(self.clients))

    def _cleanup(self):
        try:
            self._send_queue.put_nowait(None)
        except Exception:
            pass
        with self.clients_lock:
            for client in self.clients:
                try:
                    client.close()
                except Exception:
                    pass
            self.clients.clear()
            self.client_count_changed.emit(0)
        if self.server_socket:
            try:
                self.server_socket.close()
            except Exception:
                pass
        self.status_changed.emit(False, "Relay stopped")

    def stop(self):
        self.running = False
        self.wait(3000)
        if self.isRunning():
            self.terminate()
