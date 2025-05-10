from typing import Optional
import platform
from capture_worker import WindowsCaptureWorker, MacCaptureWorker, BaseCaptureWorker
from overlay import Overlay
from PyQt5.QtCore import QThread, Qt, QObject, pyqtSignal
from logging import Logger
from message_builder import MessageBuilder
from text_extractor import TextExtractor


class CaptureController(QObject):
    """Manages a CaptureWorker and signals when capture stops."""

    stopped = pyqtSignal()  # emitted whenever capture ends (graceful or on error)

    def __init__(self, overlay: Overlay, logger: Logger, message_builder: MessageBuilder, text_extractor: TextExtractor, window_identifier: str = "The Bazaar"):
        super().__init__()
        self._overlay = overlay
        self._window_identifier = window_identifier
        self._logger = logger
        self._thread: Optional[QThread] = None
        self._worker: Optional[BaseCaptureWorker] = None
        self._message_builder: MessageBuilder = message_builder
        self._text_extractor: TextExtractor = text_extractor

    # ---------------------------- public API ------------------------------
    def running(self) -> bool:
        return self._worker is not None

    def start(self):
        if self._worker is not None:
            return  # already running
        self._logger.info("Starting CaptureWorker …")
        self._thread = QThread()

        # Create platform-specific worker
        if platform.system() == "Windows":
            self._worker = WindowsCaptureWorker(self._window_identifier, self._message_builder, self._text_extractor)
        else:  # macOS
            self._worker = MacCaptureWorker(self._window_identifier, self._message_builder, self._text_extractor)

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
        except Exception:
            self._logger.exception("Error while stopping CaptureWorker")
        self._thread.quit()
        self._thread.wait(3_000)
        self._thread = None
        self._worker = None
        self.stopped.emit()

    # ------------------------ internal helpers ----------------------------
    def _on_worker_error(self, msg: str):
        self._logger.error("Capture error: %s", msg)
        self.stop()

    def _display_text(self, text: str):
        self._overlay.set_message(text)
