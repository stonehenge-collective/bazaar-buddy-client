import sys
from overlay import Overlay
from PyQt5.QtWidgets import QApplication
from PyQt5.QtGui import QIcon
from PyQt5.QtCore import QTimer
from capture_controller import CaptureController
from logger import logger

from system_handler import get_system_handler, OPERATING_SYSTEM, SYSTEM_PATH

def attempt_start_capture(controller: "CaptureController", overlay: Overlay) -> bool:
    """Return True if capture launched successfully."""
    system_handler = get_system_handler()
    logger.info("Looking for Bazaar process...")

    # On macOS, the process name is different
    process_name = "TheBazaar.exe" if OPERATING_SYSTEM == "Windows" else "The Bazaar"
    bazaar_proc = system_handler.get_process_by_name(process_name)

    if not bazaar_proc:
        logger.info(f"Could not find process with name: {process_name}")
        return False

    logger.info(f"Found Bazaar process with PID: {bazaar_proc.pid}")
    window_handle = system_handler.find_process_main_window_handle(bazaar_proc.pid)

    if not window_handle:
        logger.info("Could not find main window handle for process")
        return False

    logger.info(f"Found window handle: {window_handle}")
    overlay.set_message("Bazaar process found, watching…")
    controller.start()
    return True


def main() -> None:
    if OPERATING_SYSTEM == "Windows":
        import ctypes
        ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(
            u"StonehengeCollective.BazaarBuddy")
        
    app = QApplication(sys.argv)
    app.setWindowIcon(QIcon(str(SYSTEM_PATH / "assets" / "brand_icon.ico")))
    overlay = Overlay("Waiting for The Bazaar to start…")
    controller = CaptureController(overlay, logger)

    poll_timer = QTimer()
    poll_timer.setInterval(1000)  # 1 s

    def _tick():
        overlay.set_message("Waiting for The Bazaar to start…")
        if controller.running():
            return  # already capturing – skip heavy checks
        if attempt_start_capture(controller, overlay):
            poll_timer.stop()  # stop polling once capture starts

    poll_timer.timeout.connect(_tick)
    poll_timer.start()

    # Restart polling whenever capture ends
    controller.stopped.connect(lambda: poll_timer.start())

    # Immediate attempt on startup (no 1 s delay for the first check)
    _tick()

    # -------------------------------------------------------------------
    try:
        sys.exit(app.exec_())
    finally:
        controller.stop()


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("Aborted by user.")
