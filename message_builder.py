# message_builder.py
from __future__ import annotations

import json
from logging import Logger
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence
import re

from configuration import Configuration

class MessageBuilder:
    """Identify entities in OCR text and build decorated display messages.

    Parameters
    ----------
    config
        A fully‑populated :class:`~configuration.configuration.Configuration`
        instance.  Only the values it exposes are used; the builder never reads
        files, environment variables, or `sys` directly.
    threshold
        Minimum fuzzy‑match score (0‑100) required for a keyword to be
        considered a hit.
    """

    def __init__(self, configuration: Configuration, logger: Logger, threshold: int = 90) -> None:
        self._configuration = configuration
        self._threshold = threshold
        self._logger = logger

        self._entities: List[Dict[str, Any]] = self._load_json(
            configuration.system_path / "entities.json",
            name="entities",
        )

        # Build a look‑up set once so we can match very quickly later
        self._keyword_set: set[str] = self._build_keyword_set(self._entities)

    # --------------------------------------------------------------------- #
    # Public interface
    # --------------------------------------------------------------------- #

    def match_keyword(self, text: str) -> Optional[str]:
        """Return the *first* keyword/phrase that appears in *text*.

        The search is **case‑insensitive** and only considers *whole* words or
        phrases.  A match is accepted only when the keyword is **not** embedded
        inside another word (i.e. the characters immediately before and after
        are *not* word characters).  Multi‑word phrases are fully supported.

        If several keywords are present, the one with the earliest start index
        is returned.  If none are found, ``None`` is returned.
        """
        hits: List[Tuple[int, str]] = []

        for kw in self._keyword_set:
            # (?<!\w)  → the char before is start‑of‑string OR a non‑word
            # (?!\w)   → the char after  is end‑of‑string   OR a non‑word
            pattern = re.compile(rf"(?<!\w){re.escape(kw)}(?!\w)", re.IGNORECASE)
            m = pattern.search(text)
            if m:
                hits.append((m.start(), kw))

        self._logger.debug("Found hits: %s", hits)

        if not hits:               # nothing matched at all
            self._logger.debug("No keyword found in OCR text")
            return None

        pos, kw = min(hits, key=lambda item: item[0])   # earliest occurrence wins
        self._logger.debug("Matched %r at position %d", kw, pos)
        return kw
    
    def match_entity(self, ocr_text: str) -> Optional[Dict[str, Any]]:
        self._logger.debug("Searching entities for OCR text %r", ocr_text)

        matched = self.match_keyword(ocr_text)
        if matched is None:
            self._logger.debug("No keyword cleared threshold")
            return None
        
        for entity in self._entities:
            if matched == entity.get("name") or matched in entity.get("alt_text", []):
                self._logger.debug("Found entity %r", entity.get("name"))
                return entity
        
        self._logger.warning("Matched keyword %r but no entity carried that name", matched)
        return None


    def get_message(self, ocr_text: str) -> Optional[str]:
        matched_entity = self.match_entity(ocr_text)

        if matched_entity:
            self._logger.debug("Found entity %r", matched_entity.get("name"))
            return matched_entity.get("display_message")

        return None

    # ------------------------------------------------------------------ #
    # Internal helpers
    # ------------------------------------------------------------------ #
    @staticmethod
    def _load_json(path: Path, *, name: str) -> List[Dict[str, Any]]:
        try:
            with path.open("r", encoding="utf-8") as fp:
                data: Any = json.load(fp)
        except FileNotFoundError as exc:
            raise FileNotFoundError(f"{name!s} file not found at {path!s}") from exc
        if not isinstance(data, list):
            raise ValueError(f"{name!s} JSON must contain a list, got {type(data).__name__}")
        return data  # type: ignore[return-value]

    @staticmethod
    def _build_keyword_set(entities: Sequence[Dict[str, Any]]) -> set[str]:
        kw: set[str] = {e.get("name") for e in entities if e.get("name")}
        for alt in (e.get("alt_text") for e in entities if e.get("alt_text")):
            kw.update(alt)
        return kw


# ------------------------------------------------------------------------- #
# Minimal demo – run `python -m message_builder` to test quickly
# ------------------------------------------------------------------------- #
if __name__ == "__main__":
    from pprint import pprint

    # Create configuration exactly once, then share it
    cfg = Configuration()
    import logging
    from logger import logger
    logger.setLevel(logging.DEBUG)

    builder = MessageBuilder(cfg, logger)

    examples = [
        "REPORT BUG SMALL AQUATIC TOOL APPAREL Dive Weights Se i Haste 1 items for 39 1 seconds. For each adjacent Aquatic item. reduce this item's Cooldown by 1 second. This has Multicast equal to its anil OW - lial 9 a he Hf 4 s lek o a Y4 yy - ww a Ze sy ZA 4 o vy Cz en t 4 ty a J S I A ae all - nN Version 1.0.434",
        "MEDIUM Toxic Calcinator Burn Poison equal to this item's Burn. 4 Crit 4 When you transform a this permanently gains Burn. At the start of each day spend 3 Gold to get a Chunk of Lead. Bank amount of gold you have."
    ]

    print(builder.match_keyword(examples[1]))
    # raw_message = builder.get_message(test_ocr)

    # print("Matched entity message:")
    # pprint(raw_message)
