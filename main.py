import sys, traceback
from PyQt5.QtWidgets import QApplication
from PyQt5.QtGui import QIcon
from PyQt5.QtCore import QTimer

from logger import logger
from system_handler import WindowsSystemHandler, MacSystemHandler
from overlay import Overlay
from capture_controller import CaptureController
from bazaar_buddy import BazaarBuddy
from configuration import Configuration
from message_builder import MessageBuilder
from text_extractor import TextExtractor
from security import Security
from updater import TestUpdateSource, ProductionUpdateSource, Updater

from container import Container
from dependency_injector.wiring import inject, Provide


@inject
def main(
    configuration: Configuration = Provide[Container.configuration],
    security: Security = Provide[Container.security],
    message_builder: MessageBuilder = Provide[Container.message_builder],
    text_extractor: TextExtractor = Provide[Container.text_extractor],
) -> None:

    print(configuration)

    # here we will take some steps to harden the application
    security.randomize_process_name()

    system_handler = WindowsSystemHandler() if configuration.operating_system == "Windows" else MacSystemHandler()
    update_source = (
        TestUpdateSource(logger) if configuration.update_with_test_release else ProductionUpdateSource(logger)
    )

    if configuration.operating_system == "Windows":
        import ctypes

        ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID("StonehengeCollective.BazaarBuddy")

    app = QApplication(sys.argv)

    def excepthook(exc_type, exc_value, tb):
        nonlocal app
        # 1 – show the traceback (or log it)
        traceback.print_exception(exc_type, exc_value, tb)

        # 2 – tell Qt to leave the event‑loop
        if app is not None:  # qApp is None before QApplication is created
            app.exit(1)  # value returned by app.exec_()

        # 3 – make the *process* exit with the same non‑zero code
        #     (this also prevents your finally‑block running if that is desirable)
        sys.exit(1)

    sys.excepthook = excepthook

    app.setWindowIcon(QIcon(str(configuration.system_path / "assets" / "brand_icon.ico")))

    overlay = Overlay("Checking for updates…", configuration)
    updater = Updater(overlay, logger, configuration, update_source.latest_release)

    controller = None
    bazaar_buddy = None

    def continue_startup() -> None:
        nonlocal controller, bazaar_buddy
        controller = CaptureController(overlay, logger, message_builder, text_extractor, configuration)
        bazaar_buddy = BazaarBuddy(overlay, logger, controller, system_handler, configuration)
        bazaar_buddy.start_polling()

    updater.update_completed.connect(continue_startup)

    # Kick off the check once the event loop is running so the overlay
    # repaints before the (blocking) HTTP call.

    app.processEvents()
    QTimer.singleShot(0, updater.check_for_update)

    try:
        sys.exit(app.exec_())
    finally:
        # If continue_startup never ran, controller isn't defined—guard it.
        try:
            if bazaar_buddy:
                bazaar_buddy.controller.stop()
        except NameError:
            pass


if __name__ == "__main__":
    container = Container()
    container.wire(modules=[__name__])

    try:
        main()
    except KeyboardInterrupt:
        print("Aborted by user.")
