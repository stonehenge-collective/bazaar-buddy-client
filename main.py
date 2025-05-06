import sys
from PyQt5.QtWidgets import QApplication
from PyQt5.QtGui import QIcon
from logger import logger

from bazaar_monitor import BazaarMonitor
from system_handler import OPERATING_SYSTEM, SYSTEM_PATH


def main() -> None:
    if OPERATING_SYSTEM == "Windows":
        import ctypes

        ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID("StonehengeCollective.BazaarBuddy")

    app = QApplication(sys.argv)
    app.setWindowIcon(QIcon(str(SYSTEM_PATH / "assets" / "brand_icon.ico")))

    bazaar_monitor = BazaarMonitor(logger)
    bazaar_monitor.updater.check_and_prompt()

    try:
        sys.exit(app.exec_())
    finally:
        bazaar_monitor.controller.stop()


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("Aborted by user.")
