#!/usr/bin/env python3
"""
build_entities.py

• Reads:  events.json, items.json, monsters.json
• Writes: entities.json
          tools/tesseract/tessdata/eng.bazaar_terms
          tools/tesseract/tessdata/configs/bazaar_terms

The output schema for entities.json is:

[
  {
    "name": "<entity-name>",
    "type": "event" | "item" | "monster",
    "display_message": null | "<pre-formatted message>",
    "alt_text": "<alt text>"              # ← only present for monsters that have it
  },
  ...
]
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List, Optional
import re

_CLEANUP_REGEXES: list[tuple[str, str]] = [
    (r" \.", "."),   # " ." → "."
    (r" \)", ")"),   # " )" → ")"
    (r"\( ", "("),   # "( " → "("
    (r"\+ ", "+"),   # "+ " → "+"
    (r" :", ":"),    # " :" → ":"
    (r" %", "%"),    # " %" → "%"
]


def cleanup_display_message(text: str) -> str:
    """Apply small whitespace/mark-up fixes required by OCR output."""
    for pattern, replacement in _CLEANUP_REGEXES:
        text = re.sub(pattern, replacement, text)
    return text

# --------------------------------------------------------------------------- #
#                            ---- constants ----                              #
# --------------------------------------------------------------------------- #

# Hard-coded mapping of names → alternative OCR spellings
ALT_TEXT_MAP: Dict[str, str] = {
    "Frost Street Champion": "Frost Street Champiox",
    "Tempest Flamedancer": "Tempest Flamedancex",
}

DO_NOT_DISPLAY: Dict[str] = [
    "Aerodrome",
    "Armory",
    "B1&B2",
    "Battlefield",
    "Bladeborn Badlands",
    "Block Party",
    "Borrow",
    "Botanical Gardens",
    "Burning Caldera",
    "Cabin Fishing",
    "Cache of Riches",
    "Candy Stash",
    "Celestial Conduit",
    "Cinder Chase",
    "Deadly Duel",
    "Deep Sea Fishing",
    "Dooley's Workshop (Start Run)",
    "Dooley’s Workshop",
    "Epic Battle",
    "Extract Extract",
    "Forja",
    "Freezer",
    "Frozen Tomb",
    "Furnace",
    "Guard Locker",
    "Guardian's Gorge",
    "Haddy",
    "Hospital",
    "House Party",
    "Invest in Yourself",
    "Languid Dunes",
    "Look for Spare Change",
    "Lost and Found",
    "Mak's Laboratory (Start Run)",
    "Medicine Cabinet",
    "Monster Ranch",
    "Murkwood Bayou",
    "Mysterious Portal",
    "Obstacle Course",
    "Pearl's Dig Site",
    "Procure Medkit",
    "Pygmalien's Loft (Start Run)",
    "Pyre",
    "Racetrack",
    "Recycling Center",
    "Regenerative Tincture",
    "Relax",
    "Sanguine Valley",
    "Scrap Salvage",
    "Security Center",
    "Sharpening Kit",
    "Sirocco Steppe",
    "Snack Time",
    "Study",
    "The Artist",
    "Tranquil Spring",
    "Utility Box",
    "Vanessa's Quarters (Start Run)",
    "Workshop",
    "Start of Run"
]

#                      Directory layout                          #
CURRENT_DIR = Path(__file__).resolve().parent         # client/data
ROOT_DIR = Path(__file__).resolve().parent.parent

EVENTS_PATH          = CURRENT_DIR / "events.json"
ITEMS_PATH           = CURRENT_DIR / "items.json"
MONSTERS_PATH    = CURRENT_DIR / "monsters.json"

ENTITY_OUT_PATH      = ROOT_DIR / "entities.json"
DECORATOR_PATH = ROOT_DIR / "decorate.json"

WINDOWS_TESSDATA_PATH = ROOT_DIR / "tools" / "windows_tesseract" / "tessdata"
MAC_TESSDATA_PATH = ROOT_DIR / "tools" / "mac_tesseract" / "share" / "tessdata"
WINDOWS_TERMS_PATH   = WINDOWS_TESSDATA_PATH / "eng.bazaar_terms"
MAC_TERMS_PATH = MAC_TESSDATA_PATH / "eng.bazaar_terms"
WINDOWS_CHAR_SET_PATH = WINDOWS_TESSDATA_PATH / "configs" / "bazaar_terms"
MAC_CHAR_SET_PATH = MAC_TESSDATA_PATH / "configs" / "bazaar_terms"


# --------------------------------------------------------------------------- #
#                          ---- helper functions ----                         #
# --------------------------------------------------------------------------- #
def build_item_name(tier: str, base_name: str, enchantment: Optional[str]) -> str:
    """Compose '[enchantment ]tier base_name' and remove extra spaces."""
    parts: List[str] = []
    if enchantment:
        parts.append(enchantment)
    if tier:
        parts.append(tier)
    parts.append(base_name)
    return " ".join(parts)


def collect_item_tooltips(card: Dict[str, Any], enchantment: Optional[str]) -> List[str]:
    """Card unifiedTooltips + matching enchantment's tooltips (if any)."""
    tips: List[str] = list(card.get("unifiedTooltips", []))
    if enchantment:
        for ench in card.get("enchantments", []):
            if ench.get("type") == enchantment:
                tips.extend(ench.get("tooltips", []))
                break
    return tips

def decorate_display_message(text: str, rules: list[dict]) -> str:
    """Apply decorators so Rich Text can parse and add color to certain keywords"""
    decorated_message = text
    def _get_replacer(decorateSpan):
        def _replacer(match): 
            original = match.group(0)
            return decorateSpan.format(word=original)
        
        return _replacer
    for rule in rules: 
        decorated_message = re.sub(rule.get("word"), _get_replacer(rule.get("decorate")), decorated_message, flags=re.IGNORECASE)

    return decorated_message


# ------------------------------ Monsters ----------------------------------- #
def reformat_monsters(raw: Dict[str, Any]) -> List[Dict[str, Any]]:
    """
    Flatten monsters.json into the format expected by the original runtime.
    Returns the list that used to go into monsters.json.
    """
    result: List[Dict[str, Any]] = []

    for day in raw.get("monsterEncounterDays", []):
        for group in day.get("groups", []):
            for monster in group:
                name: str = monster.get("cardName", "")
                m: Dict[str, Any] = {
                    "name": name,
                    "health": monster.get("health", ""),
                    "items": [],
                    "skills": [],
                }

                # ---- items ----
                for itm in monster.get("items", []):
                    card = itm["card"]
                    tier: str = itm.get("tierType", "").strip()
                    enchantment: Optional[str] = itm.get("enchantmentType")

                    m["items"].append(
                        {
                            "name": build_item_name(tier, card["name"], enchantment),
                            "tooltips": collect_item_tooltips(card, enchantment),
                        }
                    )

                # ---- skills ----
                for skl in monster.get("skills", []):
                    card = skl["card"]
                    tier: str = skl.get("tierType", "").strip()
                    m["skills"].append(
                        {
                            "name": f"{tier} {card['name']}".strip(),
                            "tooltips": list(card.get("unifiedTooltips", [])),
                        }
                    )

                result.append(m)

    return result


# --------------------------- Message builders ------------------------------ #
def build_monster_message(m: Dict[str, Any]) -> str:
    msg: List[str] = [f"{m['name']}", f"Health: {m['health']}"]

    if m["items"]:
        msg.append("")        # blank line
        msg.append("Items")
        for item in m["items"]:
            msg.append(f"{item['name']}")
            msg.extend(item["tooltips"])
            msg.append("")

    if m["skills"]:
        msg.append("Skills")
        for i, skill in enumerate(m["skills"]):
            msg.append(f"{skill['name']}")
            msg.extend(skill["tooltips"])
            if i < len(m["skills"]) - 1:
                msg.append("")
    # Strip any trailing blank lines
    while msg and msg[-1] == "":
        msg.pop()
    return "<br>".join(msg)


def build_item_message(item: Dict[str, Any]) -> str:
    msg: List[str] = [item["name"], *item["unifiedTooltips"], ""]
    for i, ench in enumerate(item.get("enchantments", [])):
        msg.append(ench["type"])
        msg.extend(ench["tooltips"])
        if i < len(item["enchantments"]) - 1:
            msg.append("")
    # Remove trailing blank lines
    while msg and msg[-1] == "":
        msg.pop()
    return "<br>".join(msg)


def build_event_message(event: Dict[str, Any]) -> Optional[str]:
    if not event.get("display", True):
        return None
    return f"{event['name']}<br>" + "<br><br>".join(event["options"])


# --------------------------------------------------------------------------- #
#                            ---- main routine ----                           #
# --------------------------------------------------------------------------- #
def main() -> None:
    # ─── Ensure output dirs exist ───────────────────────────────────────────
    ENTITY_OUT_PATH.parent.mkdir(parents=True, exist_ok=True)

    # ─── Load input JSON ────────────────────────────────────────────────────
    with EVENTS_PATH.open(encoding="utf-8") as fp:
        events = json.load(fp)

    with ITEMS_PATH.open(encoding="utf-8") as fp:
        items = json.load(fp).get("items", [])

    with MONSTERS_PATH.open(encoding="utf-8") as fp:
        monsters = json.load(fp)

    with DECORATOR_PATH.open(encoding="utf-8") as fp:
        decorate_rules = json.load(fp)

    monsters: List[Dict[str, Any]] = reformat_monsters(monsters)

    # ─── Build combined entities list ───────────────────────────────────────
    entities: List[Dict[str, Any]] = []

    # Events
    for ev in events:
        entities.append(
            {
                "name": ev["name"],
                "type": "event",
                "display_message": build_event_message(ev),
            }
        )

    # Items
    for itm in items:
        entities.append(
            {
                "name": itm["name"],
                "type": "item",
                "display_message": build_item_message(itm),
            }
        )

    # Monsters
    for mon in monsters:
        ent: Dict[str, Any] = {
            "name": mon["name"],
            "type": "monster",
            "display_message": build_monster_message(mon),
        }
        entities.append(ent)

    for entity in entities:
        msg = cleanup_display_message(entity["display_message"])

        entity["display_message"] = decorate_display_message(msg, decorate_rules)
        
        entity_name = entity.get("name")
        if entity_name in ALT_TEXT_MAP:
            entity["alt_text"] = ALT_TEXT_MAP[entity_name]
        
        if entity_name in DO_NOT_DISPLAY:
            entity.pop("display_message")

    # ─── Write entities.json ────────────────────────────────────────────────
    with ENTITY_OUT_PATH.open("w", encoding="utf-8") as fp:
        json.dump(entities, fp, indent=2, ensure_ascii=False)

    # ─── Build OCR term files (word set & char whitelist) ───────────────────
    word_set = set()

    for e in entities:
        word_set.add(e["name"])
        if e.get("alt_text"):
            word_set.add(e["alt_text"])

    # eng.bazaar_terms  (newline-separated words)
    with WINDOWS_TERMS_PATH.open("w", encoding="utf-8") as fp:
        fp.write("\n".join(sorted(word_set)))

    with MAC_TERMS_PATH.open("w", encoding="utf-8") as fp:
        fp.write("\n".join(sorted(word_set)))

    # bazaar_terms config  (whitelisted characters)
    char_set = set("".join(word_set))
    whitelist = "".join(sorted(char_set))

    config_body = (
        "load_system_dawg     F\n"
        "load_freq_dawg       F\n"
        "user_words_suffix    bazaar_terms\n"
        f"tessedit_char_whitelist {whitelist} \n"
        "tessedit_pageseg_mode 11"
    )
    with WINDOWS_CHAR_SET_PATH.open("w", encoding="utf-8") as fp:
        fp.write(config_body)

    with MAC_CHAR_SET_PATH.open("w", encoding="utf-8") as fp:
        fp.write(config_body)

    print("✔ entities.json, eng.bazaar_terms, and bazaar_terms created.")


if __name__ == "__main__":
    main()
