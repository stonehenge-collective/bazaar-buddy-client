import sys, traceback
from PyQt5.QtGui import QIcon
from PyQt5.QtCore import QTimer
from container import container as c


def main() -> None:

    # here we will take some steps to harden the application
    c.security.randomize_process_name()

    if c.configuration.operating_system == "Windows":
        import ctypes

        ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID("StonehengeCollective.BazaarBuddy")

    def excepthook(exc_type, exc_value, tb):
        # 1 – show the traceback (or log it)
        traceback.print_exception(exc_type, exc_value, tb)

        # 2 – tell Qt to leave the event‑loop
        if c.app is not None:  # qApp is None before QApplication is created
            c.app.exit(1)  # value returned by app.exec_()

        # 3 – make the *process* exit with the same non‑zero code
        #     (this also prevents your finally‑block running if that is desirable)
        sys.exit(1)

    sys.excepthook = excepthook

    c.app.setWindowIcon(QIcon(str(c.configuration.system_path / "assets" / "brand_icon.ico")))

    def continue_startup() -> None:
        c.bazaar_buddy.start_polling()

    c.updater.update_completed.connect(continue_startup)

    # Kick off the check once the event loop is running so the overlay
    # repaints before the (blocking) HTTP call.

    c.app.processEvents()
    QTimer.singleShot(0, c.updater.check_for_update)

    try:
        sys.exit(c.app.exec_())
    finally:
        # If continue_startup never ran, controller isn't defined—guard it.
        try:
            if c.bazaar_buddy:
                c.bazaar_buddy.controller.stop()
        except NameError:
            pass


if __name__ == "__main__":

    try:
        main()
    except KeyboardInterrupt:
        print("Aborted by user.")
