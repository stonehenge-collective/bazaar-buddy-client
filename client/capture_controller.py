from typing import Optional
from capture_worker import (
    CaptureWorker,
)
from overlay import Overlay
from PyQt5.QtCore import QThread, Qt, QObject, pyqtSignal
from logging import Logger

class CaptureController(QObject):
    """Manages a CaptureWorker and signals when capture stops."""

    stopped = pyqtSignal()  # emitted whenever capture ends (graceful or on error)

    def __init__(self, overlay: Overlay, logger: Logger, window_title: str = "The Bazaar"):
        super().__init__()
        self._overlay       = overlay
        self._window_title  = window_title
        self._logger = logger
        self._thread:  Optional[QThread]  = None
        self._worker:  Optional[CaptureWorker] = None

    # ---------------------------- public API ------------------------------
    def running(self) -> bool:
        return self._worker is not None

    def start(self):
        if self._worker is not None:
            return  # already running
        self._logger.info("Starting CaptureWorker …")
        self._thread = QThread()
        self._worker = CaptureWorker(self._window_title)
        self._worker.moveToThread(self._thread)

        # wire signals
        self._thread.started.connect(self._worker.start)
        self._worker.message_ready.connect(self._display_text, Qt.QueuedConnection)
        self._worker.error.connect(self._on_worker_error)

        self._thread.start()

    def stop(self):
        if self._worker is None or self._thread is None:
            return
        self._logger.info("Stopping CaptureWorker …")
        try:
            self._worker.stop()
        except Exception:  # noqa: BLE001
            self._logger.exception("Error while stopping CaptureWorker")
        self._thread.quit()
        self._thread.wait(3_000)
        self._thread  = None
        self._worker  = None
        self.stopped.emit()  # let the outside world know we've stopped

    # ------------------------ internal helpers ----------------------------
    def _on_worker_error(self, msg: str):
        self._logger.error("Capture error: %s", msg)
        # treat any error as a signal to shut down and restart later
        self.stop()

    def _display_text(self, text: str):
        self._overlay.set_message(text)