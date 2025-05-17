from typing import Optional
from PIL import Image
from PyQt5.QtCore import pyqtSignal
import threading

from text_extractor import TextExtractor
from message_builder import MessageBuilder
from logging import Logger
from configuration import Configuration
from worker_framework import Worker


class BaseCaptureWorker(Worker):

    message_ready = pyqtSignal(str)

    def __init__(
        self,
        name: str,
        logger: Logger,
        message_builder: MessageBuilder,
        text_extractor: TextExtractor,
        configuration: Configuration,
    ):
        super().__init__(logger, name)
        self._message_builder = message_builder
        self._text_extractor = text_extractor
        self._configuration = configuration

    def _process_frame(self, image: Image.Image) -> None:
        """Process a captured frame and emit messages."""
        try:
            if self._configuration.save_images:
                from datetime import datetime

                filename = datetime.now().strftime("%Y%m%d_%H%M%S_%f") + ".png"
                image.save(self._configuration.system_path / filename)
            text = self._text_extractor.extract_text(image)
            self._logger.info(f"[{threading.current_thread().name}] parsed text: {text}")
            if message := self._message_builder.get_message(text):
                self._logger.info(f"[{threading.current_thread().name}] built message: {message}")
                self.message_ready.emit(message)
        except (AttributeError, PermissionError):
            pass


class WindowsCaptureWorkerV2(BaseCaptureWorker):

    def __init__(
        self,
        worker_name: str,
        logger: Logger,
        window_identifier: str,
        message_builder: MessageBuilder,
        text_extractor: TextExtractor,
        configuration: Configuration,
    ):
        super().__init__(worker_name, logger, message_builder, text_extractor, configuration)
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

    def _run(self):
        try:
            self._control = self._cap.start_free_threaded()
        except Exception as exc:
            self.error.emit(f"Capture failed: {exc}")

    def _on_stop_requested(self):
        try:
            if self._control:
                self._control.stop()
                self._control.wait()
                self._control = None
        except Exception as exc:
            self.error.emit(f"Failed to stop: {exc}")


class MacCaptureWorker(BaseCaptureWorker):
    def __init__(
        self,
        worker_name: str,
        logger: Logger,
        window_identifier: str,
        message_builder: MessageBuilder,
        text_extractor: TextExtractor,
        configuration: Configuration,
    ):
        super().__init__(worker_name, logger, message_builder, text_extractor, configuration)
        self.window_identifier = window_identifier
        self._target_window_id = None

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
            self.error.emit(
                f"[{threading.current_thread().name}] Could not import Quartz. Make sure pyobjc is installed"
            )
            return None

    def _capture_frame(self) -> None:
        """Capture a frame from the target window using CoreGraphics."""
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

        except Exception as exc:
            self.error.emit(f"[{threading.current_thread().name}] Capture error: {exc}")

    def _run(self):
        try:
            self._target_window_id = self._find_target_window()
            if not self._target_window_id:
                self.logger.info(
                    f"[{threading.current_thread().name}] Could not find window for identifier: {self.window_identifier}"
                )
                return

            self._capture_frame()

        except Exception as exc:
            self.logger.error(f"[{threading.current_thread().name}] Capture failed: {exc}")

    def _on_stop_requested(self):
        self._target_window_id = None
