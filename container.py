import sys
from PyQt5.QtWidgets import QApplication


from logger import logger
from configuration import Configuration
from security import Security
from message_builder import MessageBuilder
from text_extractor import TextExtractor
from system_handler import WindowsSystemHandler, MacSystemHandler, BaseSystemHandler
from updater import TestUpdateSource, ProductionUpdateSource, Updater, BaseUpdateSource
from overlay import Overlay
from capture_worker import MacCaptureWorker, WindowsCaptureWorkerV2
from bazaar_buddy import BazaarBuddy
from worker_framework import ThreadController
from timer_worker import TimerWorker


class Container:

    def __init__(self):

        self.app = QApplication(sys.argv)

        self.logger = logger
        self.configuration = Configuration()

        self.security = Security(self.configuration, self.logger)
        self.message_builder = MessageBuilder(self.configuration, self.logger)
        self.text_extractor = TextExtractor(self.configuration, self.logger)

        self.system_handler: BaseSystemHandler = (
            WindowsSystemHandler() if self.configuration.operating_system == "Windows" else MacSystemHandler()
        )

        self.update_source: BaseUpdateSource = (
            TestUpdateSource(self.logger)
            if self.configuration.update_with_test_release
            else ProductionUpdateSource(self.logger)
        )

        self.overlay: Overlay = Overlay("Checking for updates…", self.configuration)

        self.updater: Updater = Updater(
            self.overlay, self.logger, self.configuration, self.update_source.latest_release
        )

        self.capture_worker = (
            MacCaptureWorker(
                "Mac Capture Worker",
                self.logger,
                "The Bazaar",
                self.message_builder,
                self.text_extractor,
                self.configuration,
            )
            if self.configuration.operating_system == "Darwin"
            else WindowsCaptureWorkerV2(
                "Windows Capture Worker",
                self.logger,
                "The Bazaar",
                self.message_builder,
                self.text_extractor,
                self.configuration,
            )
        )

        self.timer_worker = TimerWorker(self.logger, 500, "bazaar-buddy-start-timer")

        self.thread_controller = ThreadController(self.logger)

        self.bazaar_buddy: BazaarBuddy = BazaarBuddy(
            self.overlay,
            self.logger,
            self.thread_controller,
            self.capture_worker,
            self.timer_worker,
            self.system_handler,
            self.configuration,
        )


container = Container()
