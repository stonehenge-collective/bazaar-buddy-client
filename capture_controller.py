from typing import Optional
from capture_worker import BaseCaptureWorker, CaptureWorkerFactory
from overlay import Overlay
from PyQt5.QtCore import QThread, Qt, QObject, pyqtSignal
from logging import Logger
from message_builder import MessageBuilder
from text_extractor import TextExtractor
from configuration import Configuration


class CaptureController(QObject):
    """Manages a CaptureWorker and signals when capture stops."""

    stopped = pyqtSignal()  # emitted whenever capture ends (graceful or on error)

    def __init__(
        self,
        overlay: Overlay,
        logger: Logger,
        message_builder: MessageBuilder,
        text_extractor: TextExtractor,
        configuration: Configuration,
        capture_worker_factory: CaptureWorkerFactory,
    ):
        super().__init__()
        self._overlay = overlay
        self._logger = logger
        self._thread: Optional[QThread] = None
        self._capture_worker_factory: CaptureWorkerFactory = capture_worker_factory
        self._current_worker: Optional[BaseCaptureWorker] = None
        self._message_builder: MessageBuilder = message_builder
        self._text_extractor: TextExtractor = text_extractor
        self._configuration = configuration

    # ---------------------------- public API ------------------------------
    def running(self) -> bool:
        return self._current_worker is not None

    def start(self):
        if self._current_worker is not None:
            return  # already running
        self._logger.info("Starting CaptureWorker …")
        self._thread = QThread()
        self._current_worker = self._capture_worker_factory.create()
        self._current_worker.moveToThread(self._thread)

        # wire signals
        self._thread.started.connect(self._current_worker.start)
        self._current_worker.message_ready.connect(self._display_text, Qt.QueuedConnection)
        self._current_worker.error.connect(self._on_worker_error)

        self._thread.start()

    def stop(self):
        if self._current_worker is None or self._thread is None:
            return
        self._logger.info("Stopping CaptureWorker …")
        try:
            self._current_worker.stop()
        except Exception:
            self._logger.exception("Error while stopping CaptureWorker")
        self._thread.quit()
        self._thread.wait(3_000)
        self._thread = None
        self._current_worker = None
        self.stopped.emit()

    # ------------------------ internal helpers ----------------------------
    def _on_worker_error(self, msg: str):
        self._logger.error("Capture error: %s", msg)
        self.stop()

    def _display_text(self, text: str):
        self._overlay.set_message(text)
