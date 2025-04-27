#!/usr/bin/env python3
"""
Re-format “monsterEncounterDays” JSON into a flat list:

[
  {
    "name": <monster cardName>,
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
import argparse
from pathlib import Path
from typing import Any, Dict, List


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
    """Card unifiedTooltips + (matching enchantment’s tooltips, if any)."""
    tips: List[str] = list(card.get("unifiedTooltips", []))
    if enchantment:
        for ench in card.get("enchantments", []):
            if ench.get("type") == enchantment:
                tips.extend(ench.get("tooltips", []))
                break
    return tips


def reformat(data: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Transform entire input structure into the flattened list."""
    result: List[Dict[str, Any]] = []

    for day in data.get("monsterEncounterDays", []):
        for group in day.get("groups", []):
            for monster in group:
                m: Dict[str, Any] = {
                    "name": monster.get("cardName", ""),
                    "health": monster.get("health", ""),
                    "items": [],
                    "skills": [],
                }

                # ---- items --------------------------------------------------
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

                # ---- skills -------------------------------------------------
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
    with open("monsters_raw.json") as fp:
        raw = json.load(fp)

    formatted = reformat(raw)

    with open("monsters.json", "w") as fp:
        json.dump(formatted, fp, indent=2)


if __name__ == "__main__":
    main()
