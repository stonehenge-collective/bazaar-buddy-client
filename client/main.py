import sys
from overlay import QApplication, Overlay
from PyQt5.QtCore import QTimer
from capture_controller import CaptureController
from logger import logger
from system_handler import get_process_by_name, find_process_main_window_handle


def attempt_start_capture(controller: "CaptureController", overlay: Overlay) -> bool:
    """Return True if capture launched successfully."""
    bazaar_proc = get_process_by_name("TheBazaar.exe")
    if not bazaar_proc:
        return False

    if find_process_main_window_handle(bazaar_proc.pid):
        overlay.set_message("Bazaar process found, watching…")
        controller.start()
        return True

    return False


def main() -> None:
    app = QApplication(sys.argv)
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
