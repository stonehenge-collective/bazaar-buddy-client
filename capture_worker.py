from typing import Optional
from PIL import Image
from PyQt5.QtCore import QObject, pyqtSignal, QTimer
from text_extractor import TextExtractor
from message_builder import MessageBuilder
from logging import Logger
from configuration import Configuration


class BaseCaptureWorker(QObject):
    """Base class for capture workers."""

    message_ready = pyqtSignal(str)
    error = pyqtSignal(str)

    def __init__(
        self,
        message_builder: MessageBuilder,
        text_extractor: TextExtractor,
        logger: Logger,
        configuration: Configuration,
    ):
        super().__init__()
        self._busy = False
        self._message_builder = message_builder
        self._text_extractor = text_extractor
        self._logger = logger
        self._configuration = configuration

    def start(self) -> None:
        """Start the capture process."""
        raise NotImplementedError("Subclasses must implement start()")

    def stop(self) -> None:
        """Stop the capture process."""
        raise NotImplementedError("Subclasses must implement stop()")

    def _process_frame(self, image: Image.Image) -> None:
        """Process a captured frame and emit messages."""
        if self._busy:
            return
        try:
            self._busy = True
            if self._configuration.save_images:
                from datetime import datetime

                filename = datetime.now().strftime("%Y%m%d_%H%M%S_%f") + ".png"
                image.save(self._configuration.system_path / filename)
            text = self._text_extractor.extract_text(image)
            self._logger.info(f"parsed text: {text}")
            if message := self._message_builder.get_message(text):
                self._logger.info(f"built message: {message}")
                self.message_ready.emit(message)
        except (AttributeError, PermissionError):
            pass
        finally:
            self._busy = False


class WindowsCaptureWorker(BaseCaptureWorker):
    """Windows-specific capture implementation."""

    def __init__(
        self,
        window_identifier: str,
        message_builder: MessageBuilder,
        text_extractor: TextExtractor,
        logger: Logger,
        configuration: Configuration,
    ):
        super().__init__(message_builder, text_extractor, logger, configuration)
        from windows_capture import WindowsCapture, Frame, CaptureControl
        import sys, platform

        major, minor, build, *_ = sys.getwindowsversion()

        supports_borderless = build >= 22000  # Win 11
        self._cap = WindowsCapture(
            window_name=window_identifier, cursor_capture=False, draw_border=False if supports_borderless else None
        )
        self._control: Optional[CaptureControl] = None

        @self._cap.event
        def on_frame_arrived(frame: Frame, control):
            try:
                # BGRA -> RGB ndarray -> PIL.Image
                rgb = frame.convert_to_bgr().frame_buffer[..., ::-1].copy()
                image = Image.fromarray(rgb)
                self._process_frame(image)
            except Exception as exc:
                self.error.emit(str(exc))

        @self._cap.event
        def on_closed():
            self.error.emit("Capture window closed")

    def start(self) -> None:
        try:
            self._control = self._cap.start_free_threaded()
        except Exception as exc:
            self.error.emit(f"Capture failed: {exc}")

    def stop(self) -> None:
        try:
            if self._control:
                self._control.stop()
                self._control.wait()
                self._control = None
        except Exception as exc:
            self.error.emit(f"Failed to stop: {exc}")


class MacCaptureWorker(BaseCaptureWorker):
    """Mac-specific capture implementation using CoreGraphics."""

    def __init__(
        self,
        window_identifier: str,
        message_builder: MessageBuilder,
        text_extractor: TextExtractor,
        logger: Logger,
        configuration: Configuration,
    ):
        super().__init__(message_builder, text_extractor, logger, configuration)
        self.window_identifier = window_identifier
        self._target_window_id = None
        self._running = False

    def _find_target_window(self) -> Optional[int]:
        """Find the window matching our identifier using CoreGraphics."""
        try:
            from Quartz import CGWindowListCopyWindowInfo, kCGWindowListOptionOnScreenOnly, kCGNullWindowID

            windows = CGWindowListCopyWindowInfo(kCGWindowListOptionOnScreenOnly, kCGNullWindowID)
            for window in windows:
                if window.get("kCGWindowIsOnscreen", False):
                    name = window.get("kCGWindowName", "")
                    owner = window.get("kCGWindowOwnerName", "")
                    if name == self.window_identifier or owner == self.window_identifier:
                        return window.get("kCGWindowNumber")
            return None
        except ImportError:
            print("Could not import Quartz. Make sure pyobjc is installed")
            return None

    def _capture_frame(self) -> None:
        """Capture a frame from the target window using CoreGraphics."""
        if not self._target_window_id or not self._running:
            return

        try:
            from Quartz import (
                CGWindowListCreateImage,
                CGRectNull,
                kCGWindowImageDefault,
                kCGWindowListOptionIncludingWindow,
                CGImageGetWidth,
                CGImageGetHeight,
                CGImageGetDataProvider,
                CGDataProviderCopyData,
                CGImageGetBytesPerRow,
                CGImageGetBitsPerPixel,
            )
            from CoreFoundation import CFDataGetBytes, CFDataGetLength
            import numpy as np

            image = CGWindowListCreateImage(
                CGRectNull, kCGWindowListOptionIncludingWindow, self._target_window_id, kCGWindowImageDefault
            )

            if not image:
                return

            # Get image dimensions
            width = CGImageGetWidth(image)
            height = CGImageGetHeight(image)
            bytes_per_row = CGImageGetBytesPerRow(image)
            bits_per_pixel = CGImageGetBitsPerPixel(image)

            # Get raw pixel data
            provider = CGImageGetDataProvider(image)
            data = CGDataProviderCopyData(provider)
            buffer = CFDataGetBytes(data, (0, CFDataGetLength(data)), None)

            # Convert to numpy array
            arr = np.frombuffer(buffer, dtype=np.uint8)
            arr = arr.reshape((height, bytes_per_row // 4, 4))
            arr = arr[:, :width, :3]  # Keep only RGB channels

            # Convert to PIL Image
            pil_image = Image.fromarray(arr)
            self._process_frame(pil_image)

            # Schedule next capture
            if self._running:
                QTimer.singleShot(0, self._capture_frame)

        except Exception as exc:
            print(f"Capture error: {exc}")
            self.error.emit(str(exc))

    def start(self) -> None:
        """Start the capture process."""
        try:
            self._target_window_id = self._find_target_window()
            if not self._target_window_id:
                self.error.emit(f"Could not find window for identifier: {self.window_identifier}")
                return

            self._running = True
            self._capture_frame()

        except Exception as exc:
            self.error.emit(f"Capture failed: {exc}")

    def stop(self) -> None:
        """Stop the capture process."""
        self._running = False
        self._target_window_id = None
