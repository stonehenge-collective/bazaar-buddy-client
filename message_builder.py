# message_builder.py
from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence

from rapidfuzz import fuzz, process

from configuration import Configuration

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


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

    def __init__(self, configuration: Configuration, *, threshold: int = 80) -> None:
        self._configuration = configuration
        self._threshold = threshold

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
        """Return the best‑matched keyword in *text*, or ``None`` if nothing
        clears :pyattr:`_threshold`."""
        result = process.extractOne(
            query=text,
            choices=list(self._keyword_set),
            scorer=fuzz.token_set_ratio,
            processor=str.lower,
            score_cutoff=self._threshold,
        )
        if result is None:
            return None

        word, score, _ = result
        logger.debug("Matched %r with score %d", word, score)
        return word

    def get_message(self, ocr_text: str) -> Optional[str]:
        """Look up and return the *display_message* for the entity referenced
        somewhere in *ocr_text*.  Returns ``None`` if no entity matches."""
        logger.debug("Searching entities for OCR text %r", ocr_text)

        matched = self.match_keyword(ocr_text)
        if matched is None:
            logger.debug("No keyword cleared threshold")
            return None

        for entity in self._entities:
            if matched in {entity.get("name"), entity.get("alt_text")}:
                logger.debug("Found entity %r", entity.get("name"))
                return entity.get("display_message")

        logger.warning("Matched keyword %r but no entity carried that name", matched)
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

    builder = MessageBuilder(cfg)

    test_ocr = "The cult of personality strikes again."  # ← OCR text
    raw_message = builder.get_message(test_ocr)

    print("Matched entity message:")
    pprint(raw_message)
