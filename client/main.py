from datetime import datetime
import sys
import time
import logging
from pathlib import Path
from logging.handlers import RotatingFileHandler
from typing import Callable, TypeVar, Optional
import psutil
from capture_worker import (
    CaptureWorker,
)
from text_extractor import extract_text
from ui import QApplication, Overlay
from PyQt5.QtCore import QThread, Qt, QTimer
from PIL import Image
import json
import time
import win32gui
import win32process

if getattr(sys, 'frozen', False):        # running inside the .exe
    system_path = Path(sys._MEIPASS)           # type: ignore[attr-defined]
else:                                    # running from source
    system_path = Path(__file__).resolve().parent

events_file_path = system_path / "data/events.json"

with events_file_path.open("r", encoding="utf-8") as fp:
    events = json.load(fp)

items_file_path = system_path / "data/items.json"

with items_file_path.open("r", encoding="utf-8") as fp:
    items = json.load(fp).get("items")

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

def build_message(screenshot_text: str):
    for event in events:
        if event.get("name") in screenshot_text:
            print(f"found event! {event}")
            message = event.get("name")+"\n"
            if event.get("display", True):
                message += "\n\n".join(event.get("options"))
            return message
        
    for item in items:
        if item.get("name") in screenshot_text:
            print(f"found item! {item.get("name")}")
            message = item.get("name")+"\n"
            message += "\n".join(item.get("unifiedTooltips"))
            message += "\n\n"
            enchantments = item.get("enchantments")
            for i, enchantment in enumerate(enchantments):
                message += enchantment.get("type") + "\n"
                message += "\n\n".join(enchantment.get("tooltips"))
                if i < len(enchantments) - 1:
                    message += "\n\n"
            return message
    
    return None

class CaptureController:
    """Manages *one* CaptureWorker and restarts it while the app is running."""

    def __init__(self, overlay: Overlay, window_title: str = "The Bazaar"):
        self._overlay = overlay
        self._window_title = window_title
        self._thread: Optional[QThread] = None
        self._worker: Optional[CaptureWorker] = None

    # ---------------------------------------------------------------------
    #  Public API
    # ---------------------------------------------------------------------
    def start(self):
        """Ensure a worker is active (if not already)."""
        if self._worker is not None:
            return  # already running

        logger.info("Starting CaptureWorker …")
        self._thread = QThread()
        self._worker = CaptureWorker(self._window_title)
        self._worker.moveToThread(self._thread)

        # Wire up signals before booting the thread
        self._thread.started.connect(self._worker.start)
        self._worker.message_ready.connect(self._process_image, Qt.QueuedConnection)
        self._worker.error.connect(self._on_worker_error)

        self._thread.start()

    def stop(self):
        """Terminate and clean‑up the running worker (if any)."""
        if self._worker is None or self._thread is None:
            return

        logger.info("Stopping CaptureWorker …")
        try:
            self._worker.stop()  # custom method added below
        except Exception:
            logger.exception("Error while stopping CaptureWorker")

        self._thread.quit()
        self._thread.wait(3_000)  # wait up to 3 s for a graceful shutdown
        self._thread = None
        self._worker = None

    # ------------------------------------------------------------------
    #  Internal helpers & slots
    # ------------------------------------------------------------------
    def _on_worker_error(self, msg: str):
        logger.error("Capture error: %s", msg)
        if "closed" in msg.lower():
            # Window vanished while streaming — treat as process exit
            self.stop()

    def _process_image(self, image: Image.Image):
        try:
            # Persist a copy for troubleshooting
            ts = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
            # Disabled by default — uncomment if you need raw dumps
            # image.save(bundle_dir() / f"screenshot_{ts}.png")

            try:
                screenshot_text = extract_text(image)
            except (AttributeError, PermissionError):
                logger.debug("Transient OCR failure – frame skipped")
                return
            logger.info("OCR result: %s", screenshot_text)
            message = build_message(screenshot_text)
            if message:
                self._overlay.set_message(message)
        except Exception:
            logger.exception("Unhandled exception while processing frame")

def main() -> None:  # noqa: C901
    # 1. Start the GUI right away
    app = QApplication(sys.argv)
    overlay = Overlay("Waiting for The Bazaar to start...")

    # 2. Build the controller that spins workers up/down
    controller = CaptureController(overlay, window_title="The Bazaar")

    # 3. Poll timer — runs on the Qt event‑loop every second
    poll_timer = QTimer()
    poll_timer.setInterval(1_000)  # 1 s

    def _tick():
        # Called inside the GUI thread — cheap checks only!
        bazaar_process = get_process_by_name("TheBazaar.exe")
        if bazaar_process:
            window_handle = find_process_main_window_handle(bazaar_process.pid)
            if window_handle:
                overlay.set_message("Bazaar process found, watching...")
                controller.start()
                return
        controller.stop()
        overlay.set_message("Waiting for The Bazaar to start...")

    poll_timer.timeout.connect(_tick)
    poll_timer.start()

    # Run!
    try:
        sys.exit(app.exec_())
    finally:
        controller.stop()  # Ensure clean shutdown on Ctrl‑C

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("Aborted by user.")
