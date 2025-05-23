import threading

from logging import Logger
from overlay import Overlay
from system_handler import BaseSystemHandler
from configuration import Configuration
from worker_framework import ThreadController
from timer_worker import TimerWorker
from text_extractor_worker import TextExtractorWorkerFactory


class BazaarBuddy:
    def __init__(
        self,
        overlay: Overlay,
        logger: Logger,
        thread_controller: ThreadController,
        text_extractor_worker_factory: TextExtractorWorkerFactory,
        one_second_timer: TimerWorker,
        system_handler: BaseSystemHandler,
        configuration: Configuration,
    ):
        self.overlay = overlay
        self.logger = logger
        self.thread_controller = thread_controller
        self.text_extractor_worker_factory = text_extractor_worker_factory
        self.text_extractor_worker = None
        self.one_second_timer = one_second_timer
        self.system_handler = system_handler
        self.configuration = configuration
        self.thread_name = threading.current_thread().name

    def start_polling(self):
        self.logger.info(f"[{self.thread_name}] Start Polling")
        self.overlay.set_message("Waiting for The Bazaar to start…")
        self.thread_controller.add_worker(self.one_second_timer)
        # saving connection so we can disconnect later
        self.attempt_start_connection = self.one_second_timer.timer_tick.connect(self._attempt_start)
        self.thread_controller.start_worker(self.one_second_timer.name)

    def restart_polling(self):
        self.logger.info(f"[{self.thread_name}] Restarting Polling")

        try:
            self.thread_controller.stop_worker(self.text_extractor_worker.name)
            self.text_extractor_worker.message_ready.disconnect()
            self.text_extractor_worker.window_closed.disconnect()
            self.text_extractor_worker = None
        except Exception as e:
            self.logger.warning(f"[{self.thread_name}] Error stopping text extractor: {e}")

        self.attempt_start_connection = self.one_second_timer.timer_tick.connect(self._attempt_start)

    def _attempt_start(self):

        self.logger.info(f"[{self.thread_name}] attempting to find the Bazaar process…")

        process_name = "TheBazaar.exe" if self.configuration.operating_system == "Windows" else "The Bazaar"
        bazaar_proc = self.system_handler.get_process_by_name(process_name)

        if not bazaar_proc:
            self.logger.info(f"[{self.thread_name}] could not find process with name: {process_name}")
            return

        self.logger.info(f"[{self.thread_name}] found Bazaar process with PID: {bazaar_proc.pid}")
        window_handle = self.system_handler.find_process_main_window_handle(bazaar_proc.pid)

        if not window_handle:
            self.logger.info(f"[{self.thread_name}] could not find main window handle for process")
            return

        self.logger.info(f"[{self.thread_name}] found window handle: {window_handle}")

        self.overlay.set_message("Bazaar process found, watching…")

        self.logger.info(f"[{self.thread_name}] Bazaar process found")

        self.logger.info(f"[{self.thread_name}] stopping trying to _attempt_start")
        self.one_second_timer.disconnect(self.attempt_start_connection)

        self.text_extractor_worker = self.text_extractor_worker_factory.create("text-extractor-worker")

        self.thread_controller.add_worker(self.text_extractor_worker)
        self.text_extractor_worker.message_ready.connect(self.overlay.set_message)
        self.text_extractor_worker.window_closed.connect(self.restart_polling)
        self.logger.info(f"[{self.thread_name}] starting text extractor worker")
        self.thread_controller.start_worker(self.text_extractor_worker.name)
