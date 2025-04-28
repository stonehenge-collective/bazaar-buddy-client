import json
from pathlib import Path
import sys
from word_matcher import match_word

if getattr(sys, 'frozen', False):        # running inside the .exe
    system_path = Path(sys._MEIPASS)           # type: ignore[attr-defined]
else:                                    # running from source
    system_path = Path(__file__).resolve().parent

# -------------------------------------------------------------------
# Load data files
# -------------------------------------------------------------------

events_file_path = system_path / "data/events.json"
with events_file_path.open("r", encoding="utf-8") as fp:
    events = json.load(fp)

items_file_path = system_path / "data/items.json"
with items_file_path.open("r", encoding="utf-8") as fp:
    items = json.load(fp).get("items")

monsters_file_path = system_path / "data/monsters.json"
with monsters_file_path.open("r", encoding="utf-8") as fp:
    monsters = json.load(fp)

# -------------------------------------------------------------------
# Build message based on OCR text
# -------------------------------------------------------------------

def build_message(screenshot_text: str):
    matched_word = match_word(screenshot_text)

    if not matched_word:
        return None

    # ----------------- Monsters -----------------
    for monster in monsters:
        name = monster.get("name")
        alt_text = monster.get("alt_text", None)
        if name == matched_word or alt_text == matched_word:
            print(f"found monster! {name}")
            message = f"{name}\nHealth: {monster.get('health')}\n\n"

            if monster.get("items"):
                message += "Items\n"
                for item in monster["items"]:
                    message += f"{item['name']}\n" + "\n".join(item["tooltips"]) + "\n\n"

            if monster.get("skills"):
                message += "Skills\n"
                for i, skill in enumerate(monster["skills"]):
                    message += f"{skill['name']}\n" + "\n".join(skill["tooltips"])
                    if i < len(monster["skills"]) - 1:
                        message += "\n\n"
            return message

    # ----------------- Events -----------------
    for event in events:
        name = event.get("name")
        if name == matched_word:
            print(f"found event! {name}")
            if event.get("display", True):
                return f"{name}\n" + "\n\n".join(event["options"])

    # ----------------- Items -----------------
    for item in items:
        name = item.get("name")
        if name == matched_word:
            print(f"found item! {name}")
            message = f"{name}\n" + "\n".join(item["unifiedTooltips"]) + "\n\n"
            for i, ench in enumerate(item["enchantments"]):
                message += ench["type"] + "\n" + "\n\n".join(ench["tooltips"])
                if i < len(item["enchantments"]) - 1:
                    message += "\n\n"
            return message

    return None
