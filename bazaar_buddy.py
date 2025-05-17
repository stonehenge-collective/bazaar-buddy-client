import threading

from logging import Logger
from overlay import Overlay
from system_handler import BaseSystemHandler
from configuration import Configuration
from worker_framework import ThreadController
from capture_worker import CaptureWorker
from timer_worker import TimerWorker


class BazaarBuddy:
    def __init__(
        self,
        overlay: Overlay,
        logger: Logger,
        thread_controller: ThreadController,
        capture_worker: CaptureWorker,
        timer_worker: TimerWorker,
        system_handler: BaseSystemHandler,
        configuration: Configuration,
    ):
        self.overlay = overlay
        self.logger = logger
        self.thread_controller = thread_controller
        self.capture_worker = capture_worker
        self.timer_worker = timer_worker
        self.system_handler = system_handler
        self.configuration = configuration
        self.thread_name = threading.current_thread().name

    def start_polling(self):
        self.overlay.set_message("Waiting for The Bazaar to start…")
        self.thread_controller.add_worker(self.timer_worker)
        # saving connection so we can disconnect later
        self.attempt_start_connection = self.timer_worker.timer_tick.connect(self._attempt_start)
        self.thread_controller.start_worker(self.timer_worker.name)

    def _attempt_start(self):

        self.logger.info(f"[{self.thread_name}] Attempting to find the Bazaar process…")

        process_name = "TheBazaar.exe" if self.configuration.operating_system == "Windows" else "The Bazaar"
        bazaar_proc = self.system_handler.get_process_by_name(process_name)

        if not bazaar_proc:
            self.logger.info(f"[{self.thread_name}] Could not find process with name: {process_name}")
            return

        self.logger.info(f"[{self.thread_name}] Found Bazaar process with PID: {bazaar_proc.pid}")
        window_handle = self.system_handler.find_process_main_window_handle(bazaar_proc.pid)

        if not window_handle:
            self.logger.info(f"[{self.thread_name}] Could not find main window handle for process")
            return

        self.logger.info(f"[{self.thread_name}] Found window handle: {window_handle}")

        self.overlay.set_message("Bazaar process found, watching…")

        self.logger.info(f"[{self.thread_name}] Bazaar process found")

        self.logger.info(f"[{self.thread_name}] stopping trying to _attempt_start")
        self.timer_worker.disconnect(self.attempt_start_connection)

        self.logger.info(f"[{self.thread_name}] Starting capture worker…")
        self.thread_controller.add_worker(self.capture_worker)
        self.timer_worker.timer_tick.connect(self.capture_worker._run)
        self.capture_worker.message_ready.connect(self.overlay.set_message)
        self.capture_worker.error.connect(self.logger.error)
        self.logger.info(f"[{self.thread_name}] starting capture worker")
        self.thread_controller.start_worker(self.capture_worker.name)
