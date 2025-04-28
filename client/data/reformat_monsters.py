#!/usr/bin/env python3
"""
Re-format "monsterEncounterDays" JSON into a flat list and optionally attach
hard‑coded alternative names ("alt_text") for selected monsters.

Output structure:
[
  {
    "name": <monster cardName>,
    "alt_text": <alternative text>  # only when available
    "health": <monster health>,
    "items": [
      {
        "name": "<[enchantmentType ]tierType card.name>",
        "tooltips": [ <card.unifiedTooltips …> + <matching-enchantment.tooltips …> ]
      },
      …
    ],
    "skills": [
      {
        "name": "<tierType card.name>",
        "tooltips": [ <card.unifiedTooltips …> ]
      },
      …
    ]
  },
  …
]
"""

import json
from typing import Any, Dict, List

# ---------------------------------------------------------------------------
# Hard‑coded mapping of monster names to alternative texts. Expand as needed.
# ---------------------------------------------------------------------------
ALT_TEXT_MAP: Dict[str, str] = {
    "Frost Street Champion": "Frost Street Champiox",
    # "Some Other Monster": "Alternative name here",
}


def build_item_name(tier: str, base_name: str, enchantment: str | None) -> str:
    """Compose '[enchantment ]tier base_name' (remove extra spaces)."""
    parts: List[str] = []
    if enchantment:
        parts.append(enchantment)
    if tier:
        parts.append(tier)
    parts.append(base_name)
    return " ".join(parts)


def collect_item_tooltips(card: Dict[str, Any], enchantment: str | None) -> List[str]:
    """Card unifiedTooltips + matching enchantment's tooltips (if any)."""
    tips: List[str] = list(card.get("unifiedTooltips", []))
    if enchantment:
        for ench in card.get("enchantments", []):
            if ench.get("type") == enchantment:
                tips.extend(ench.get("tooltips", []))
                break
    return tips


def reformat(data: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Transform the entire input structure into the flattened list."""
    result: List[Dict[str, Any]] = []

    for day in data.get("monsterEncounterDays", []):
        for group in day.get("groups", []):
            for monster in group:
                name: str = monster.get("cardName", "")
                m: Dict[str, Any] = {
                    "name": name,
                    "health": monster.get("health", ""),
                    "items": [],
                    "skills": [],
                }

                # Optional alt text ---------------------------------------------------
                if name in ALT_TEXT_MAP:
                    m["alt_text"] = ALT_TEXT_MAP[name]

                # ---- items ----------------------------------------------------------
                for itm in monster.get("items", []):
                    card = itm["card"]
                    tier: str = itm.get("tierType", "").strip()
                    enchantment: str | None = itm.get("enchantmentType")

                    m["items"].append(
                        {
                            "name": build_item_name(tier, card["name"], enchantment),
                            "tooltips": collect_item_tooltips(card, enchantment),
                        }
                    )

                # ---- skills ---------------------------------------------------------
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


def main() -> None:
    with open("monsters_raw.json", "r", encoding="utf-8") as fp:
        raw = json.load(fp)

    formatted = reformat(raw)

    with open("monsters.json", "w", encoding="utf-8") as fp:
        json.dump(formatted, fp, indent=2, ensure_ascii=False)


if __name__ == "__main__":
    main()
