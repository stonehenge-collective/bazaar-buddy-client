import sys
import time
from pathlib import Path

import psutil
from window_manager import find_process_main_window_handle, capture_window, check_if_handle_is_foreground

import psutil

import sys
from pathlib import Path
from typing import Callable, Optional, TypeVar

T = TypeVar("T")

def bundle_dir() -> Path:
    """
    Return the folder that holds the running script or the frozen .exe.
    """
    if getattr(sys, 'frozen', False):          # PyInstaller sets this
        return Path(sys.executable).resolve().parent
    return Path(__file__).resolve().parent      # normal (un‑frozen) run

def get_process_by_name(process_name: str):
    return next(
            (p for p in psutil.process_iter(["name", "pid"]) if p.info["name"] == process_name),
            None,
        )

def poll_function(function: Callable[[], T], poll_frequency: int = .5, timeout: int = None):
    start = time.time()
    while True:
        result: T = function()
        if result:
            return result
        if timeout is not None and (time.time() - start) > timeout:
            return None
        time.sleep(poll_frequency)

def main() -> None:
    print("Getting Bazaar process...")
    bazaar_process = poll_function(lambda: get_process_by_name("TheBazaar.exe"))
    print(f"Got Bazaar process, {bazaar_process}, getting main window...")

    window_handle = find_process_main_window_handle(bazaar_process.pid)
    if not window_handle:
        sys.exit("Could not find a visible window for the process.")
    print(f"Got Bazaar window")

    print("Waiting for The Bazaar window to become the foreground window")
    if not poll_function(lambda: check_if_handle_is_foreground(window_handle)):
        sys.exit("Timed out waiting for window to become foreground.")

    print("Taking screenshot...")
    screenshot = capture_window(window_handle)
    print("Screenshot taken!")
    output_location = bundle_dir() / "screenshot.png"
    print(f"Saving screenshot to {output_location.resolve()}")
    screenshot.save(output_location)
    print(f"Screenshot saved to {output_location.resolve()}")
    time.sleep(30)

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("Aborted by user.")
