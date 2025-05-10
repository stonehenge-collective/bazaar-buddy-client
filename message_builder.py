# message_builder.py
from __future__ import annotations

import json
from logging import Logger
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence


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
        """Return the *first* keyword appearing in *text*.

        The search is **case‑insensitive** and looks for *substring* matches.
        If multiple keywords are present, the one that appears earliest in the
        string is returned (based on its starting index).  If no keyword is
        found, ``None`` is returned.
        """
        text_lower = text.lower()
        # Collect all hits as (position, keyword) pairs
        hits: List[tuple[int, str]] = []
        for kw in self._keyword_set:
            pos = text_lower.find(kw.lower())
            if pos != -1:
                hits.append((pos, kw))

        self._logger.debug(f"Found hits: {hits}")

        if not hits:  # Nothing matched at all
            self._logger.debug("No keyword found in OCR text")
            return None

        # Choose the keyword with the earliest position in the text
        pos, kw = min(hits, key=lambda item: item[0])
        self._logger.debug("Matched %r at position %d", kw, pos)
        return kw

    def get_message(self, ocr_text: str) -> Optional[str]:
        """Look up and return the *display_message* for the entity referenced
        somewhere in *ocr_text*.  Returns ``None`` if no entity matches."""
        self._logger.debug("Searching entities for OCR text %r", ocr_text)

        matched = self.match_keyword(ocr_text)
        if matched is None:
            self._logger.debug("No keyword cleared threshold")
            return None

        for entity in self._entities:
            if matched in {entity.get("name"), entity.get("alt_text")}:
                self._logger.debug("Found entity %r", entity.get("name"))
                return entity.get("display_message")

        self._logger.warning("Matched keyword %r but no entity carried that name", matched)
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
