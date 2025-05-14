from lagom import Container, dependency_definition
from PyQt5.QtWidgets import QApplication
import sys


from logger import logger
from configuration import Configuration
from security import Security
from message_builder import MessageBuilder
from text_extractor import TextExtractor
from system_handler import BaseSystemHandler, WindowsSystemHandler, MacSystemHandler
from updater import BaseUpdateSource, ProductionUpdateSource, TestUpdateSource, Updater
from overlay import Overlay
from capture_controller import CaptureController
from bazaar_buddy import BazaarBuddy

container = Container(log_undefined_deps=True)

container["QApplication"] = QApplication(sys.argv)

container["Logger"] = logger

container["Configuration"] = Configuration()

container["Security"] = lambda c: Security(c["Configuration"], c["Logger"])

container["MessageBuilder"] = lambda c: MessageBuilder(c["Configuration"], c["Logger"])

container["TextExtractor"] = lambda c: TextExtractor(c["Configuration"], c["Logger"])


@dependency_definition(container)
def _system_handler_locader(c: Container) -> BaseSystemHandler:
    return WindowsSystemHandler() if c["Configuration"].operating_system == "Windows" else MacSystemHandler()


container["BaseSystemHandler"] = _system_handler_locader


@dependency_definition(container)
def _updater_loader(c: Container) -> BaseUpdateSource:
    return (
        TestUpdateSource(c["Logger"])
        if c["Configuration"].update_with_test_release
        else ProductionUpdateSource(c["Logger"])
    )


container["BaseUpdateSource"] = _updater_loader

container["Overlay"] = Overlay("Checking for updates…", container["Configuration"])


@dependency_definition(container)
def _updater_loader(c: Container) -> Updater:
    latest_release = c["BaseUpdateSource"].latest_release
    return Updater(c["Overlay"], c["Logger"], c["Configuration"], latest_release)


container["Updater"] = _updater_loader

container["CaptureController"] = lambda c: CaptureController(
    c["Overlay"], c["Logger"], c["MessageBuilder"], c["TextExtractor"], c["Configuration"]
)

container["BazaarBuddy"] = lambda c: BazaarBuddy(
    c["Overlay"], c["Logger"], c["CaptureController"], c["BaseSystemHandler"], c["Configuration"]
)
