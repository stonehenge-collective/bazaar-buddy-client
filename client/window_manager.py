from PIL import Image
import win32process
from typing import Optional
import win32gui
from windows_capture import WindowsCapture, Frame

def capture_one_frame(window_name: str = None,
                      monitor_index: int = None,
                      include_cursor: bool = False) -> Image.Image:
    """
    Return a PIL.Image grabbed from a window (by title) or a monitor index.
    Blocks until the first frame arrives, then stops the capture thread.
    """
    if not window_name and monitor_index is None:
        raise ValueError("Provide either window_name or monitor_index")

    # 1. Holder for the frame we’ll receive from the callback
    frame_holder = {}

    # 2. Build the capture session
    cap = WindowsCapture(
        cursor_capture=include_cursor,
        draw_border=False,
        monitor_index=monitor_index,
        window_name=window_name,
    )

    # 3. Callback: copy the first frame and stop the session
    @cap.event
    def on_frame_arrived(frame: Frame, control):
        # frame.frame_buffer is BGRA; drop alpha & copy so buffer survives stop()
        bgr = frame.convert_to_bgr().frame_buffer.copy()
        frame_holder["img"] = Image.fromarray(bgr[..., ::-1])  # BGR→RGB
        control.stop()      # tells the internal thread to finish

    # 4. Mandatory on_closed handler (even if we do nothing)
    @cap.event
    def on_closed():
        pass

    # 5. Start the capture on its own thread and wait until it ends
    capture_control = cap.start_free_threaded()
    capture_control.wait()      # blocks until control.stop() is called

    if "img" not in frame_holder:
        raise RuntimeError("No frame arrived (window may be hidden?)")
    return frame_holder["img"]



def check_if_handle_is_foreground(window_handle: int) -> bool:
    return win32gui.GetForegroundWindow() == window_handle

def find_process_main_window_handle(process_id: int) -> Optional[int]:
    """
    Return the handle (HWND) of the first top‑level, visible window that
    belongs to the given process, or None if nothing is found.
    """
    result: Optional[int] = None            # what we'll eventually return

    def enum_callback(hwnd, _):
        nonlocal result                      # allow assignment to the outer var

        if not win32gui.IsWindowVisible(hwnd) or not win32gui.IsWindowEnabled(hwnd):
            return True                      # keep enumerating

        _, hwnd_pid = win32process.GetWindowThreadProcessId(hwnd)
        if hwnd_pid == process_id:
            result = hwnd                    # stash the handle
        return True                          # keep looking

    win32gui.EnumWindows(enum_callback, None)
    return result

if __name__ == "__main__":
    image = capture_one_frame("The Bazaar")
    image.save("./screenshot.png")
