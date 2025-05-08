import sys
from PyQt5.QtWidgets import QApplication
from PyQt5.QtGui import QIcon
from PyQt5.QtCore import QTimer

from logger import logger
from system_handler import get_system_handler
from overlay import Overlay
from capture_controller import CaptureController
from updater import Updater
from bazaar_buddy import BazaarBuddy
from configuration.configuration import get_configuration


def main() -> None:
    config = get_configuration()

    if config.operating_system == "Windows":
        import ctypes

        ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID("StonehengeCollective.BazaarBuddy")

    app = QApplication(sys.argv)
    app.setWindowIcon(QIcon(str(config.system_path / "assets" / "brand_icon.ico")))

    overlay = Overlay("Checking for updates…")
    updater = Updater(overlay, logger, config)

    controller = None
    bazaar_buddy = None

    def continue_startup() -> None:
        nonlocal controller, bazaar_buddy
        controller = CaptureController(overlay, logger)
        system_handler = get_system_handler()
        bazaar_buddy = BazaarBuddy(overlay, logger, controller, system_handler, config)
        bazaar_buddy.start_polling()

    updater.update_completed.connect(continue_startup)

    # Kick off the check once the event loop is running so the overlay
    # repaints before the (blocking) HTTP call.
    QTimer.singleShot(0, updater.check_and_prompt)

    try:
        sys.exit(app.exec_())
    finally:
        # If continue_startup never ran, controller isn't defined—guard it.
        try:
            bazaar_buddy.controller.stop()
        except NameError:
            pass


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("Aborted by user.")
