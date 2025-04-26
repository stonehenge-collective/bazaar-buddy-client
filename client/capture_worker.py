import time
from typing import Optional
from PIL import Image
from windows_capture import WindowsCapture, Frame, CaptureControl
from PyQt5.QtCore import QObject, pyqtSignal

class CaptureWorker(QObject):
    """Runs a single WindowsCapture session and pipes out parsed messages."""
    message_ready = pyqtSignal(object)           # emitted on every new message
    error        = pyqtSignal(str)

    def __init__(self, window_title: str):
        super().__init__()
        self._cap = WindowsCapture(
            window_name=window_title,
            cursor_capture=False,
            draw_border=False,
        )
        self._control: Optional[CaptureControl] = None
        self._last_emit = time.monotonic()

        @self._cap.event
        def on_frame_arrived(frame: Frame, control):
            now = time.monotonic()
            if now - self._last_emit >= 1.0:
                self._last_emit = now
                try:
                    # BGRA -> RGB ndarray -> PIL.Image
                    rgb = frame.convert_to_bgr().frame_buffer[..., ::-1].copy()
                    image = Image.fromarray(rgb)
                    self.message_ready.emit(image)
                except Exception as exc:                  # noqa: BLE001
                    self.error.emit(str(exc))

        @self._cap.event
        def on_closed():
            # Window disappeared -> tell the GUI to shut down gracefully
            self.error.emit("Capture window closed")

    # Public API ---------------------------------------------------------
    def start(self):
        """Start streaming — runs inside the worker thread."""
        try:
            self._control = self._cap.start_free_threaded()
        except Exception as exc:               # ← catches “window not found”
            self.error.emit(f"Capture failed: {exc}")

    def stop(self):  # type: ignore[override]
        """Ask WindowsCapture to stop & wait for its thread."""
        try:
            if self._control:
                self._control.stop()
                self._control.wait()
                self._control = None
        except Exception as exc:  # noqa: BLE001
            self.error.emit(f"Failed to stop: {exc}")