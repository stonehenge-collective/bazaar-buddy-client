from PyQt5.QtCore import QTimer
from logging import Logger
from overlay import Overlay
from capture_controller import CaptureController
from system_handler import BaseSystemHandler
from configuration import Configuration


class BazaarBuddy:
    def __init__(
        self,
        overlay: Overlay,
        logger: Logger,
        controller: CaptureController,
        system_handler: BaseSystemHandler,
        configuration: Configuration,
    ):
        self.overlay = overlay
        self.logger = logger
        self.controller = controller
        self.system_handler = system_handler
        self.configuration = configuration

        self.poll_timer = QTimer()
        self.poll_timer.setInterval(1000)
        self.poll_timer.timeout.connect(self._tick)
        self.controller.stopped.connect(self.start_polling)

    def attempt_start_capture(self) -> bool:
        """Return True if capture launched successfully."""
        self.logger.info("Looking for Bazaar process...")

        # On macOS, the process name is different
        process_name = "TheBazaar.exe" if self.configuration.operating_system == "Windows" else "The Bazaar"
        bazaar_proc = self.system_handler.get_process_by_name(process_name)

        if not bazaar_proc:
            self.logger.info(f"Could not find process with name: {process_name}")
            return False

        self.logger.info(f"Found Bazaar process with PID: {bazaar_proc.pid}")
        window_handle = self.system_handler.find_process_main_window_handle(bazaar_proc.pid)

        if not window_handle:
            self.logger.info("Could not find main window handle for process")
            return False

        self.logger.info(f"Found window handle: {window_handle}")
        self.overlay.set_message("Bazaar process found, watching…")
        self.controller.start()
        return True

    def _tick(self):
        self.overlay.set_message("Waiting for The Bazaar to start from updated client…")
        if self.controller.running():
            return  # already capturing – skip heavy checks
        if self.attempt_start_capture():
            self.stop_polling()  # stop polling once capture starts

    def start_polling(self):
        self.poll_timer.start()

    def stop_polling(self):
        self.poll_timer.stop()
