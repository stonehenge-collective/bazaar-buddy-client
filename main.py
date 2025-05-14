import sys, traceback
from PyQt5.QtWidgets import QApplication
from PyQt5.QtGui import QIcon
from PyQt5.QtCore import QTimer

from security import Security
from configuration import Configuration
from capture_controller import CaptureController
from bazaar_buddy import BazaarBuddy
from updater import Updater
from container import container


def main() -> None:

    configuration: Configuration = container["Configuration"]

    # here we will take some steps to harden the application
    security: Security = container["Security"]
    security.randomize_process_name()

    if configuration.operating_system == "Windows":
        import ctypes

        ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID("StonehengeCollective.BazaarBuddy")

    app: QApplication = container["QApplication"]

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

    updater: Updater = container["Updater"]

    controller: CaptureController = None
    bazaar_buddy: BazaarBuddy = None

    def continue_startup() -> None:
        nonlocal controller, bazaar_buddy
        controller = container["CaptureController"]
        bazaar_buddy = container["BazaarBuddy"]
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

    try:
        main()
    except KeyboardInterrupt:
        print("Aborted by user.")
