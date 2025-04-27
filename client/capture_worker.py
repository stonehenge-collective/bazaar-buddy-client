import time
from typing import Optional
from PIL import Image
from windows_capture import WindowsCapture, Frame, CaptureControl
from PyQt5.QtCore import QObject, pyqtSignal
from text_extractor import extract_text
import json
from pathlib import Path
import sys

if getattr(sys, 'frozen', False):        # running inside the .exe
    system_path = Path(sys._MEIPASS)           # type: ignore[attr-defined]
else:                                    # running from source
    system_path = Path(__file__).resolve().parent

events_file_path = system_path / "data/events.json"

with events_file_path.open("r", encoding="utf-8") as fp:
    events = json.load(fp)

items_file_path = system_path / "data/items.json"

with items_file_path.open("r", encoding="utf-8") as fp:
    items = json.load(fp).get("items")

monsters_file_path = system_path / "data/monsters.json"

with monsters_file_path.open("r", encoding="utf-8") as fp:
    monsters = json.load(fp)

def build_message(screenshot_text: str):
    for monster in monsters:
        if monster.get("name") in screenshot_text:
            print(f"found monster! {monster.get("name")}")
            message = monster.get("name")+"\n"
            message += f"Health: {monster.get("health")}\n\n"
            if monster.get("items"):
                message += "Items\n"
                for item in monster.get("items"):
                    message += item.get("name")+"\n"
                    message += "\n".join(item.get("tooltips"))
                    message += "\n\n"
            if monster.get("skills"):
                message += "Skills\n"
                for i, skill in enumerate(monster.get("skills")):
                    message += skill.get("name")+"\n"
                    message += "\n".join(skill.get("tooltips"))
                    if i < len(monster.get("skills")) - 1:
                        message += "\n\n"
            return message
        
    for event in events:
        if event.get("name") in screenshot_text:
            print(f"found event! {event}")
            if event.get("display", True):
                message = event.get("name")+"\n"
                message += "\n\n".join(event.get("options"))
                return message
        
    for item in items:
        if item.get("name") in screenshot_text:
            print(f"found item! {item.get("name")}")
            message = item.get("name")+"\n"
            message += "\n".join(item.get("unifiedTooltips"))
            message += "\n\n"
            enchantments = item.get("enchantments")
            for i, enchantment in enumerate(enchantments):
                message += enchantment.get("type") + "\n"
                message += "\n\n".join(enchantment.get("tooltips"))
                if i < len(enchantments) - 1:
                    message += "\n\n"
            return message
        
    
    
    return None

class CaptureWorker(QObject):
    """Runs a single WindowsCapture session and pipes out parsed messages."""
    message_ready = pyqtSignal(str)           # emitted on every new message
    error        = pyqtSignal(str)

    def __init__(self, window_title: str):
        super().__init__()
        self._cap = WindowsCapture(
            window_name=window_title,
            cursor_capture=False,
            draw_border=False,
        )
        self._control: Optional[CaptureControl] = None
        self._busy = False

        @self._cap.event
        def on_frame_arrived(frame: Frame, control):
            if self._busy:   # ② basic throttle
                return
            try:
                self._busy = True
                # BGRA -> RGB ndarray -> PIL.Image
                rgb = frame.convert_to_bgr().frame_buffer[..., ::-1].copy()
                image = Image.fromarray(rgb)
                try:
                    text = extract_text(image)
                    print(text)
                except (AttributeError, PermissionError):
                    self._busy = False
                    return
                if message := build_message(text):
                    self.message_ready.emit(message)
                self._busy = False
            except Exception as exc:                  # noqa: BLE001
                self.error.emit(str(exc))

        @self._cap.event
        def on_closed():
            # Window disappeared -> tell the GUI to shut down gracefully
            self.error.emit("Capture window closed")

    # Public API ---------------------------------------------------------
    def start(self):
        """Start streaming — runs inside the worker thread."""
        try:
            self._control = self._cap.start_free_threaded()
        except Exception as exc:               # ← catches “window not found”
            self.error.emit(f"Capture failed: {exc}")

    def stop(self):  # type: ignore[override]
        """Ask WindowsCapture to stop & wait for its thread."""
        try:
            if self._control:
                self._control.stop()
                self._control.wait()
                self._control = None
        except Exception as exc:  # noqa: BLE001
            self.error.emit(f"Failed to stop: {exc}")