import sys
import time
from pathlib import Path

import psutil
from window_manager import find_process_main_window_handle, capture_window, check_if_handle_is_foreground

import psutil

import sys
from pathlib import Path
from typing import Callable, Optional, TypeVar
from text_extractor import extract_text

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

def take_screenshot(process_name: str):
    print(f"Getting {process_name} process...")
    bazaar_process = poll_function(lambda: get_process_by_name(process_name))
    print(f"Got {process_name} process, {bazaar_process}, getting main window...")

    window_handle = find_process_main_window_handle(bazaar_process.pid)
    if not window_handle:
        print("Could not find a visible window for the process.")
        return None
    print(f"Got {process_name} window")

    print(f"Waiting for {process_name} window to become the foreground window")
    if not check_if_handle_is_foreground(window_handle):
        print("Window not in foreground")
        return None

    print("Taking screenshot...")
    return capture_window(window_handle)


def main() -> None:
    try:
        attempt = 0
        while True:
            screenshot = take_screenshot("TheBazaar.exe")
            if screenshot:
                output_location = bundle_dir() / f"screenshot_{attempt}.png"
                print(f"Saving screenshot to {output_location.resolve()}")
                screenshot.save(output_location)
                print(f"Screenshot saved to {output_location.resolve()}")
                print(extract_text(screenshot))
            else:
                print("Could not take screenshot")
            attempt += 1
            time.sleep(1)
    except Exception as e:
        

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("Aborted by user.")
