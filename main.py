import sys, traceback
from PyQt5.QtWidgets import QApplication
from PyQt5.QtGui import QIcon
from PyQt5.QtCore import QTimer

from logger import logger
from system_handler import WindowsSystemHandler, MacSystemHandler
from overlay import Overlay
from capture_controller import CaptureController
from updater import MockUpdater, Updater
from bazaar_buddy import BazaarBuddy
from configuration import Configuration
from message_builder import MessageBuilder
from text_extractor import TextExtractor
from security import Security


def main() -> None:

    configuration = Configuration()

    # here we will take some steps to harden the application
    security = Security(configuration, logger)
    security.randomize_process_name()

    # remove this once testing is done
    configuration.is_local = False

    message_builder = MessageBuilder(configuration, logger)
    text_extractor = TextExtractor(configuration, logger)
    system_handler = WindowsSystemHandler() if configuration.operating_system == "Windows" else MacSystemHandler()

    if configuration.operating_system == "Windows":
        import ctypes

        ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID("StonehengeCollective.BazaarBuddy")

    def excepthook(exc_type, exc_value, tb):
        # 1 – show the traceback (or log it)
        traceback.print_exception(exc_type, exc_value, tb)

        # 2 – tell Qt to leave the event‑loop
        if QApplication is not None:          # qApp is None before QApplication is created
            QApplication.exit(1)              # value returned by app.exec_()

        # 3 – make the *process* exit with the same non‑zero code
        #     (this also prevents your finally‑block running if that is desirable)
        sys.exit(1)
    sys.excepthook = excepthook

    app = QApplication(sys.argv)
    app.setWindowIcon(QIcon(str(configuration.system_path / "assets" / "brand_icon.ico")))

    overlay = Overlay("Checking for updates…", configuration)
    updater = Updater(overlay, logger, configuration)

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
    QApplication.processEvents()
    QTimer.singleShot(0, updater.check_and_prompt)

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

    try:
        main()
    except KeyboardInterrupt:
        print("Aborted by user.")
