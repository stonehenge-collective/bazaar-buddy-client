from abc import ABC, abstractmethod
from typing import Optional
import platform
import sys
from pathlib import Path

# Define SYSTEM_PATH based on whether we're running as a frozen executable or not
if getattr(sys, "frozen", False):
    # When frozen, we need to look in the _internal directory
    SYSTEM_PATH = Path(sys._MEIPASS)
else:
    SYSTEM_PATH = Path(__file__).parent


class BaseSystemHandler(ABC):
    """Base class for system-specific process and window handling."""

    @abstractmethod
    def get_process_by_name(self, process_name: str) -> Optional[dict]:
        """Find a process by its name."""
        pass

    @abstractmethod
    def find_process_main_window_handle(self, process_id: int) -> Optional[int]:
        """Find the main window handle for a given process."""
        pass


class WindowsSystemHandler(BaseSystemHandler):
    """Windows-specific system handler."""

    def __init__(self):
        import psutil
        import win32gui
        import win32process

        self.psutil = psutil
        self.win32gui = win32gui
        self.win32process = win32process

    def get_process_by_name(self, process_name: str) -> Optional[dict]:
        return next(
            (p for p in self.psutil.process_iter(["name", "pid"]) if p.info["name"] == process_name),
            None,
        )

    def find_process_main_window_handle(self, process_id: int) -> Optional[int]:
        result: Optional[int] = None

        def enum_callback(hwnd, _):
            nonlocal result
            if not self.win32gui.IsWindowVisible(hwnd) or not self.win32gui.IsWindowEnabled(hwnd):
                return True
            _, hwnd_pid = self.win32process.GetWindowThreadProcessId(hwnd)
            if hwnd_pid == process_id:
                result = hwnd
            return True

        self.win32gui.EnumWindows(enum_callback, None)
        return result


class MacSystemHandler(BaseSystemHandler):
    """Mac-specific system handler."""

    def __init__(self):
        import psutil

        self.psutil = psutil

    def get_process_by_name(self, process_name: str) -> Optional[dict]:
        # On macOS, we can use bundle ID or process name
        return next(
            (p for p in self.psutil.process_iter(["name", "pid"]) if p.info["name"] == process_name),
            None,
        )

    def find_process_main_window_handle(self, process_id: int) -> Optional[int]:
        # On macOS, we return the process ID itself as the "handle"
        # since we'll use it with Qt's window management
        return process_id


def get_system_handler() -> BaseSystemHandler:
    """Factory function to get the appropriate system handler for the current platform."""
    if platform.system() == "Windows":
        return WindowsSystemHandler()
    else:
        return MacSystemHandler()
