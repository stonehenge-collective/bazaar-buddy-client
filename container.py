import sys
from PyQt6.QtWidgets import QApplication
from pathlib import Path

from logger import logger
from configuration import Configuration
from security import Security
from message_builder import MessageBuilder
from system_handler import WindowsSystemHandler, MacSystemHandler, BaseSystemHandler
from updater import TestUpdateSource, ProductionUpdateSource, BaseUpdater, WindowsUpdater, MacUpdater, BaseUpdateSource
from overlay import Overlay
from capture_worker import MacCaptureWorker, WindowsCaptureWorkerV2
from bazaar_buddy import BazaarBuddy
from worker_framework import ThreadController
from timer_worker import TimerWorker
from text_extractor_worker import TextExtractor, TextExtractorWorkerFactory
from file_writer import BaseFileSystem, MacFileSystem, WindowsFileSystem, FileType


class Container:

    def __init__(self):

        self.app = QApplication(sys.argv)

        self.logger = logger
        self.configuration = Configuration()

        self.security = Security(self.configuration, self.logger)
        self.message_builder = MessageBuilder(self.configuration, self.logger)
        self.text_extractor = TextExtractor(self.configuration, self.logger)

        self.capture_worker = (
            MacCaptureWorker(
                self.logger,
                "The Bazaar",
            )
            if self.configuration.operating_system == "Darwin"
            else WindowsCaptureWorkerV2(
                self.logger,
                "The Bazaar",
            )
        )

        self.text_extractor_worker_factory = TextExtractorWorkerFactory(
            self.configuration,
            self.message_builder,
            self.text_extractor,
            self.capture_worker,
            self.logger,
        )

        self.system_handler: BaseSystemHandler = (
            WindowsSystemHandler() if self.configuration.operating_system == "Windows" else MacSystemHandler()
        )

        # File system handler for writing application data
        self.file_system: BaseFileSystem = (
            WindowsFileSystem(Path.home() / "AppData" / "Roaming" / "BazaarBuddy", self.configuration)
            if self.configuration.operating_system == "Windows"
            else MacFileSystem(Path.home() / "Library" / "Application Support" / "BazaarBuddy", self.configuration)
        )

        self.update_source: BaseUpdateSource = (
            TestUpdateSource(self.logger)
            if self.configuration.update_with_test_release
            else ProductionUpdateSource(self.logger)
        )

        self.overlay: Overlay = Overlay(
            "Checking for updates…",
            self.configuration,
            self.file_system.get_file_writer(FileType.CONFIG),
        )

        if self.configuration.operating_system == "Windows":
            self.updater: BaseUpdater = WindowsUpdater(
                self.overlay, self.logger, self.configuration, self.update_source.latest_release
            )
        else:
            self.updater: BaseUpdater = MacUpdater(
                self.overlay, self.logger, self.configuration, self.update_source.latest_release
            )

        self.one_second_timer = TimerWorker(self.logger, 1000, "one-second-timer")

        self.thread_controller = ThreadController(self.logger)

        self.bazaar_buddy: BazaarBuddy = BazaarBuddy(
            self.overlay,
            self.logger,
            self.thread_controller,
            self.text_extractor_worker_factory,
            self.one_second_timer,
            self.system_handler,
            self.configuration,
        )


container = Container()
