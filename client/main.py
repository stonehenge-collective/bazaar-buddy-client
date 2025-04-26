import sys
import time
import logging
from pathlib import Path
from logging.handlers import RotatingFileHandler
from typing import Callable, TypeVar, Optional

import psutil
from window_manager import (
    find_process_main_window_handle,
    capture_one_frame,
    check_if_handle_is_foreground,
)
from text_extractor import extract_text
from ui import QApplication, Overlay
from PyQt5.QtCore import QTimer

import json

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

def poll_function(function: Callable[[], T], poll_frequency: float = 0.5, timeout: Optional[float] = None) -> Optional[T]:
    start = time.time()
    while True:
        result: T = function()
        if result:
            return result
        if timeout is not None and (time.time() - start) > timeout:
            return None
        time.sleep(poll_frequency)

def take_screenshot(process_name: str):
    print(f"Getting {process_name} process...")
    bazaar_process = poll_function(lambda: get_process_by_name(process_name))
    print(f"Got {process_name} process, {bazaar_process}, getting main window...")

    if bazaar_process is None:
        print("Process not found.")
        return None

    window_handle = find_process_main_window_handle(bazaar_process.pid)
    if not window_handle:
        print("Could not find a visible window for the process.")
        return None
    print(f"Got {process_name} window.")

    print(f"Waiting for {process_name} window to become the foreground window")
    if not check_if_handle_is_foreground(window_handle):
        print("Window not in foreground")
        return None

    print("Taking screenshot...")
    return capture_one_frame("The Bazaar")

def build_message(screenshot_text: str):
    for event in events:
        if event.get("name") in screenshot_text:
            print(f"found event! {event}")
            if event.get("display", True):
                return "\n\n".join(event.get("options"))
        
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

def main() -> None:
    app = QApplication(sys.argv)
    overlay = Overlay("Welcome")

    attempt = 0                     # capture in an outer-scope var

    def poll():
        nonlocal attempt
        try:
            screenshot = take_screenshot("TheBazaar.exe")
            if not screenshot:
                print("Could not take screenshot")
                attempt += 1
                return

            output_location = bundle_dir() / f"screenshot_{attempt}.png"
            print(f"Saving screenshot to {output_location.resolve()}")
            screenshot.save(output_location)
            print(f"Screenshot saved to {output_location.resolve()}")

            screenshot_text = extract_text(screenshot)
            print(screenshot_text)

            message = build_message(screenshot_text)
            
            if message:
                overlay.set_message(message)

            attempt += 1
        except Exception:                 # catches *everything* except SystemExit/KeyboardInterrupt
            logger.exception("Unhandled exception in poll()")

    # call `poll()` every 1 000 ms
    timer = QTimer()
    timer.timeout.connect(poll)
    timer.start(1000)

    sys.exit(app.exec_())

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("Aborted by user.")
