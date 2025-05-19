from logger import logger
from configuration import Configuration
from security import Security
from message_builder import MessageBuilder
from text_extractor import TextExtractor
from system_handler import WindowsSystemHandler, MacSystemHandler, BaseSystemHandler
from updater import TestUpdateSource, ProductionUpdateSource, BaseUpdater, WindowsUpdater, MacUpdater, BaseUpdateSource
from overlay import Overlay
from capture_controller import CaptureController
from capture_worker import BaseCaptureWorker, CaptureWorkerFactory
from bazaar_buddy import BazaarBuddy
from PyQt5.QtWidgets import QApplication
import sys


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

        if self.configuration.operating_system == "Windows":
            self.updater: BaseUpdater = WindowsUpdater(
                self.overlay, self.logger, self.configuration, self.update_source.latest_release
            )
        else:
            self.updater: BaseUpdater = MacUpdater(
                self.overlay, self.logger, self.configuration, self.update_source.latest_release
            )

        self.controller: CaptureController = CaptureController(
            self.overlay,
            self.logger,
            self.message_builder,
            self.text_extractor,
            self.configuration,
            self.capture_worker_factory,
        )

        self.bazaar_buddy: BazaarBuddy = BazaarBuddy(
            self.overlay,
            self.logger,
            self.controller,
            self.system_handler,
            self.configuration,
        )

    @property
    def capture_worker_factory(self) -> CaptureWorkerFactory:
        return CaptureWorkerFactory(self.configuration, self.message_builder, self.text_extractor, self.logger)


container = Container()
