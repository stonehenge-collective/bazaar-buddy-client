from datetime import datetime
from typing import Optional
from PIL import Image
from windows_capture import WindowsCapture, Frame, CaptureControl
from PyQt5.QtCore import QObject, pyqtSignal
from text_extractor import extract_text
from message_builder import build_message

class CaptureWorker(QObject):
    """Runs a single WindowsCapture session and pipes out parsed messages."""
    message_ready = pyqtSignal(str)           # emitted on every new message
    error        = pyqtSignal(str)

    def __init__(self, window_title: str):
        super().__init__()
        self._cap = WindowsCapture(
            window_name=window_title,
            cursor_capture=False,
            draw_border=False,
        )
        self._control: Optional[CaptureControl] = None
        self._busy = False

        @self._cap.event
        def on_frame_arrived(frame: Frame, control):
            if self._busy:   # ② basic throttle
                return
            try:
                self._busy = True
                # BGRA -> RGB ndarray -> PIL.Image
                rgb = frame.convert_to_bgr().frame_buffer[..., ::-1].copy()
                image = Image.fromarray(rgb)
                # timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                # filename = f"frame_{timestamp}.png"
                # image.save(filename)
                try:
                    text = extract_text(image)
                    print(text)
                except (AttributeError, PermissionError):
                    self._busy = False
                    return
                if message := build_message(text):
                    self.message_ready.emit(message)
                self._busy = False
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