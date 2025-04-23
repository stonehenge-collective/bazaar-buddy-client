
import win32gui
import win32process
from PIL import ImageGrab, Image
from typing import Optional

def capture_window(window_handle: int) -> Image:
    left, top, right, bottom = win32gui.GetWindowRect(window_handle)
    return ImageGrab.grab(bbox=(left, top, right, bottom))

def check_if_handle_is_foreground(window_handle: int) -> bool:
    return win32gui.GetForegroundWindow() == window_handle

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