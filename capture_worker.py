from typing import Optional
from PIL import Image
import threading
from abc import ABC, abstractmethod
from logging import Logger
from configuration import Configuration


class FailedToFindWindowError(Exception):
    pass


class BaseCaptureWorker(ABC):

    def __init__(
        self,
        logger: Logger,
    ):
        self._logger = logger
        self._capture_lock = threading.Lock()

    @abstractmethod
    def capture_image_sync(self, timeout: float = 2.5) -> Image.Image | None:
        pass


class WindowsCaptureWorkerV2(BaseCaptureWorker):

    def __init__(
        self,
        logger: Logger,
        window_identifier: str,
    ):
        super().__init__(logger)
        from windows_capture import WindowsCapture, Frame, CaptureControl
        import sys

        major, minor, build, *_ = sys.getwindowsversion()

        supports_borderless = build >= 22000  # Win 11
        self._cap = WindowsCapture(
            window_name=window_identifier, cursor_capture=False, draw_border=False if supports_borderless else None
        )
        self._control: CaptureControl | None = None
        self._capture_event = threading.Event()
        self._capture_image: Image.Image | None = None
        self._capture_error: str | None = None

        @self._cap.event
        def on_frame_arrived(frame: Frame, control: CaptureControl):
            try:
                # BGRA -> RGB ndarray -> PIL.Image
                rgb = frame.convert_to_bgr().frame_buffer[..., ::-1].copy()
                image = Image.fromarray(rgb)
                self._capture_image = image
                self._logger.info(f"[{threading.current_thread().name}] Frame arrived, setting capture event")
            except Exception as exc:
                self._capture_error = str(exc)
            finally:
                self._capture_event.set()

        @self._cap.event  # type: ignore
        def on_closed():
            self._logger.info("Capture worker closed")
            self._control = None

    def capture_image_sync(self, timeout: float = 2.5) -> Image.Image | None:
        with self._capture_lock:
            self._logger.info(f"[{threading.current_thread().name}] Acquiring capture lock")
            if self._control is not None:
                # already capturing
                return None

            # reset state
            self._capture_event.clear()
            self._capture_error = None
            self._capture_image = None

            try:
                self._logger.info(f"[{threading.current_thread().name}] Starting capture event loop")
                self._control = self._cap.start_free_threaded()

                if self._capture_event.wait(timeout):
                    if self._capture_error is not None:
                        raise Exception(f"Capture failed: {self._capture_error}")
                    self._logger.info(
                        f"[{threading.current_thread().name}] Capture event loop completed, returning image"
                    )
                    if self._control:
                        self._control.stop()
                        self._control = None
                    return self._capture_image
                else:
                    self._logger.info(f"[{threading.current_thread().name}] Capture event loop timed out")
                    # timeout occurred
                    if self._control:
                        self._control.stop()
                        self._control = None
                    return None
            except Exception as exc:
                if self._control:
                    self._control.stop()
                    self._control = None
                if "Failed To Find Window" in str(exc):
                    self._logger.info(
                        f"[{threading.current_thread().name}] Failed to find window, raising FailedToFindWindowError"
                    )
                    raise FailedToFindWindowError()
                self._logger.error(f"[{threading.current_thread().name}] Capture failed: {exc}")
                raise exc


class MacCaptureWorker(BaseCaptureWorker):
    def __init__(
        self,
        logger: Logger,
        window_identifier: str,
    ):
        super().__init__(logger)
        self.window_identifier = window_identifier
        self._target_window_id = None

    def _find_target_window(self) -> Optional[int]:
        """Find the window matching our identifier using CoreGraphics."""
        try:
            from Quartz import CGWindowListCopyWindowInfo, kCGWindowListOptionOnScreenOnly, kCGNullWindowID  # type: ignore

            windows = CGWindowListCopyWindowInfo(kCGWindowListOptionOnScreenOnly, kCGNullWindowID)
            for window in windows:
                if window.get("kCGWindowIsOnscreen", False):
                    name = window.get("kCGWindowName", "")
                    owner = window.get("kCGWindowOwnerName", "")
                    if name == self.window_identifier or owner == self.window_identifier:
                        return window.get("kCGWindowNumber")
            return None
        except ImportError:
            raise Exception(
                f"[{threading.current_thread().name}] Could not import Quartz. Make sure pyobjc is installed"
            )

    def _capture_frame(self) -> Image.Image | None:
        """Capture a frame from the target window using CoreGraphics."""
        try:
            from Quartz import (  # type: ignore
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
            from CoreFoundation import CFDataGetBytes, CFDataGetLength  # type: ignore
            import numpy as np

            image = CGWindowListCreateImage(
                CGRectNull, kCGWindowListOptionIncludingWindow, self._target_window_id, kCGWindowImageDefault
            )

            if not image:
                return None

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
            return Image.fromarray(arr)
        except Exception as exc:
            raise Exception(f"[{threading.current_thread().name}] Capture error: {exc}")

    def capture_image_sync(self, timeout: float = 2.5) -> Image.Image | None:
        with self._capture_lock:
            self._logger.info(f"[{threading.current_thread().name}] Acquiring capture lock")

            try:
                self._target_window_id = self._find_target_window()
                if not self._target_window_id:
                    self._logger.info(
                        f"[{threading.current_thread().name}] Could not find window for identifier: {self.window_identifier}"
                    )
                    raise FailedToFindWindowError()

                self._logger.info(f"[{threading.current_thread().name}] Starting capture")
                return self._capture_frame()

            except Exception as exc:
                if "Failed to find window" in str(exc) or isinstance(exc, FailedToFindWindowError):
                    self._logger.info(
                        f"[{threading.current_thread().name}] Failed to find window, raising FailedToFindWindowError"
                    )
                    raise FailedToFindWindowError()
                self._logger.error(f"[{threading.current_thread().name}] Capture failed: {exc}")
                raise exc
