import sys
import logging
from pathlib import Path
from logging.handlers import RotatingFileHandler
from typing import TypeVar, Optional
import psutil
from capture_worker import (
    CaptureWorker,
)
from text_extractor import extract_text
from ui import QApplication, Overlay
from PyQt5.QtCore import QThread, Qt, QTimer, QObject, pyqtSignal
import win32gui
import win32process

T = TypeVar("T")

def bundle_dir() -> Path:
    """
    Return the folder that holds the running script or the frozen .exe.
    """
    if getattr(sys, 'frozen', False):          # PyInstaller sets this
        return Path(sys.executable).resolve().parent
    return Path(__file__).resolve().parent      # normal (un-frozen) run

# === Logging configuration ===

# where to put the log file
LOG_FILE = bundle_dir() / "app.log"

# create logger
logger = logging.getLogger()
logger.setLevel(logging.INFO)

# file handler with rotation (max 5 MB per file, keep 3 backups)
file_handler = RotatingFileHandler(
    filename=str(LOG_FILE),
    maxBytes=5 * 1024 * 1024,
    backupCount=3,
    encoding='utf-8'
)
file_fmt = logging.Formatter("%(asctime)s %(levelname)-8s %(message)s")
file_handler.setFormatter(file_fmt)
logger.addHandler(file_handler)

# console handler (writes to the original stdout)
console_handler = logging.StreamHandler(stream=sys.__stdout__)
console_handler.setFormatter(file_fmt)
logger.addHandler(console_handler)

# helper to redirect print → logger.info
class LoggerWriter:
    def __init__(self, level: int):
        self.level = level
    def write(self, message):
        msg = message.rstrip('\n')
        if msg:
            logger.log(self.level, msg)
    def flush(self):
        pass

# redirect stdout/stderr
sys.stdout = LoggerWriter(logging.INFO)
sys.stderr = LoggerWriter(logging.ERROR)
# === end logging config ===

def get_process_by_name(process_name: str):
    return next(
        (p for p in psutil.process_iter(["name", "pid"]) if p.info["name"] == process_name),
        None,
    )

def find_process_main_window_handle(process_id: int) -> Optional[int]:
    """
    Return the handle (HWND) of the first top‑level, visible window that
    belongs to the given process, or None if nothing is found.
    """
    result: Optional[int] = None            # what we'll eventually return

    def enum_callback(hwnd, _):
        nonlocal result                      # allow assignment to the outer var

        if not win32gui.IsWindowVisible(hwnd) or not win32gui.IsWindowEnabled(hwnd):
            return True                      # keep enumerating

        _, hwnd_pid = win32process.GetWindowThreadProcessId(hwnd)
        if hwnd_pid == process_id:
            result = hwnd                    # stash the handle
        return True                          # keep looking

    win32gui.EnumWindows(enum_callback, None)
    return result

class CaptureController(QObject):
    """Manages a CaptureWorker and signals when capture stops."""

    stopped = pyqtSignal()  # emitted whenever capture ends (graceful or on error)

    def __init__(self, overlay: Overlay, window_title: str = "The Bazaar"):
        super().__init__()
        self._overlay       = overlay
        self._window_title  = window_title
        self._thread:  Optional[QThread]  = None
        self._worker:  Optional[CaptureWorker] = None

    # ---------------------------- public API ------------------------------
    def running(self) -> bool:
        return self._worker is not None

    def start(self):
        if self._worker is not None:
            return  # already running
        logger.info("Starting CaptureWorker …")
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
        logger.info("Stopping CaptureWorker …")
        try:
            self._worker.stop()
        except Exception:  # noqa: BLE001
            logger.exception("Error while stopping CaptureWorker")
        self._thread.quit()
        self._thread.wait(3_000)
        self._thread  = None
        self._worker  = None
        self.stopped.emit()  # let the outside world know we've stopped

    # ------------------------ internal helpers ----------------------------
    def _on_worker_error(self, msg: str):
        logger.error("Capture error: %s", msg)
        # treat any error as a signal to shut down and restart later
        self.stop()

    def _display_text(self, text: str):
        self._overlay.set_message(text)

def _attempt_start_capture(controller: "CaptureController", overlay: Overlay) -> bool:
    """Return True if capture launched successfully."""
    bazaar_proc = get_process_by_name("TheBazaar.exe")
    if not bazaar_proc:
        return False

    if find_process_main_window_handle(bazaar_proc.pid):
        overlay.set_message("Bazaar process found, watching…")
        controller.start()
        return True

    return False

def main() -> None:
    app      = QApplication(sys.argv)
    overlay  = Overlay("Waiting for The Bazaar to start…")
    controller = CaptureController(overlay)

    # --- stateful timer: only active while NOT capturing ------------------
    poll_timer = QTimer()
    poll_timer.setInterval(1000)  # 1 s

    def _tick():
        overlay.set_message("Waiting for The Bazaar to start…")
        if controller.running():
            return  # already capturing – skip heavy checks
        if _attempt_start_capture(controller, overlay):
            poll_timer.stop()  # stop polling once capture starts

    poll_timer.timeout.connect(_tick)
    poll_timer.start()

    # Restart polling whenever capture ends
    controller.stopped.connect(lambda: poll_timer.start())

    # Immediate attempt on startup (no 1 s delay for the first check)
    _tick()

    # -------------------------------------------------------------------
    try:
        sys.exit(app.exec_())
    finally:
        controller.stop()

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("Aborted by user.")
