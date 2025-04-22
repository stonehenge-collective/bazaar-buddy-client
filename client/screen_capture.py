import sys
import time
from pathlib import Path

import psutil
import win32con  # noqa: F401  # kept in case you later need window constants
import win32gui
import win32process
from PIL import ImageGrab


TARGET_PROCESS = "TheBazaar.exe"
OUT_FILE = Path(__file__).with_suffix(".png")  # screenshot next to the exe
POLL_INTERVAL = 0.5  # seconds between foreground checks
TIMEOUT = None  # seconds; set to an int/float to avoid waiting forever

def find_main_hwnd(pid: int) -> int | None:
    """Return the first top‑level window handle belonging to *pid*."""

    def callback(hwnd, hwnds):
        # Skip invisible/minimized windows
        if win32gui.IsWindowVisible(hwnd) and win32gui.IsWindowEnabled(hwnd):
            _, win_pid = win32process.GetWindowThreadProcessId(hwnd)
            if win_pid == pid:
                hwnds.append(hwnd)
                return False  # Stop enumeration
        return True

    hwnds: list[int] = []
    win32gui.EnumWindows(callback, hwnds)
    return hwnds[0] if hwnds else None


def wait_until_foreground(hwnd: int, poll: float = POLL_INTERVAL, timeout: float | None = TIMEOUT) -> bool:
    """Poll until *hwnd* is the active (foreground) window.

    Returns True if the window became foreground within *timeout*,
    otherwise False. ``timeout=None`` means wait indefinitely.
    """
    start = time.time()
    while True:
        print(win32gui.GetForegroundWindow())
        if win32gui.GetForegroundWindow() == hwnd:
            return True
        if timeout is not None and (time.time() - start) > timeout:
            return False
        time.sleep(poll)


def capture_window(hwnd: int, outfile: Path) -> None:
    left, top, right, bottom = win32gui.GetWindowRect(hwnd)
    img = ImageGrab.grab(bbox=(left, top, right, bottom))
    img.save(outfile)
    print(f"Screenshot saved to {outfile.resolve()}")


def main() -> None:
    # 1. Locate the process
    target = next(
        (p for p in psutil.process_iter(["name", "pid"]) if p.info["name"] == TARGET_PROCESS),
        None,
    )
    if not target:
        sys.exit(f"{TARGET_PROCESS} is not running.")

    # 2. Grab the window handle
    _, win_pid = win32process.GetWindowThreadProcessId(target.pid)
    # hwnd = find_main_hwnd(target.pid)
    # if not hwnd:
    #     sys.exit("Could not find a visible window for the process.")

    # 3. Wait for the user to bring the window forward
    print("Waiting for The Bazaar window to become the foreground window … (Ctrl+C to abort)")
    if not wait_until_foreground(win_pid):
        sys.exit("Timed out waiting for window to become foreground.")

    # 4. Capture the screenshot once the window is foreground
    capture_window(win_pid, OUT_FILE)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("Aborted by user.")
