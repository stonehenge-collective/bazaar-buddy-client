# ocr_text_extractor.py
from __future__ import annotations

import os
from pathlib import Path

from PIL import Image
import pytesseract
from pytesseract import Output

from configuration import Configuration
from logging import Logger

class TextExtractor:
    """Thin wrapper around *pytesseract* that sets the correct runtime paths
    based on :class:`~configuration.configuration.Configuration`.

    Parameters
    ----------
    config
        Runtime configuration (already initialised elsewhere).
    lang
        Tesseract language(s) to load; default is ``"eng"``.
    tess_config
        Extra `--psm`, `--oem`, or user‑defined config string(s) passed straight
        to Tesseract.  The original code hard‑coded ``"bazaar_terms"``; keep
        that as the default for backwards compatibility.
    """

    def __init__(
        self,
        configuration: Configuration,
        logger: Logger,
        *,
        lang: str = "eng",
        tess_config: str = "bazaar_terms",
    ) -> None:
        self._configuration = configuration
        self._logger = logger
        self._lang = lang
        self._tess_config = tess_config

        self._prepare_tesseract_paths()

    # ------------------------------------------------------------------ #
    # Public API
    # ------------------------------------------------------------------ #
    def extract_text(self, image: Image.Image, confidence_treshold = 80) -> str:
        """Run OCR directly on a :pyclass:`PIL.Image.Image` instance."""
        self._logger.debug("Extracting text from in‑memory image")
        tesser_data = pytesseract.image_to_data(
            image,
            lang=self._lang,
            config=self._tess_config,
            output_type=Output.DICT
        )
        keep = [
            text for text, conf in zip(tesser_data["text"], tesser_data["conf"])
            if text.strip() and int(conf) >= confidence_treshold
        ]

        return " ".join(keep)

    def extract_text_from_file(self, image_path: Path | str) -> str:
        """Open *image_path* and return the extracted text."""
        path = Path(image_path)
        self._logger.debug("Opening image file %s", path)
        with Image.open(path) as img:
            return self.extract_text(img)

    def _prepare_tesseract_paths(self) -> None:
        """Point *pytesseract* at the bundled Tesseract binaries and data."""
        if self._configuration.operating_system == "Windows":
            tess_dir = self._configuration.system_path / "tools" / "windows_tesseract"
            pytesseract.pytesseract.tesseract_cmd = str(tess_dir / "tesseract.exe")
            os.environ["TESSDATA_PREFIX"] = str(tess_dir / "tessdata")
        else:
            tess_dir = self._configuration.system_path / "tools" / "mac_tesseract"
            pytesseract.pytesseract.tesseract_cmd = str(tess_dir / "bin" / "tesseract")
            os.environ["DYLD_LIBRARY_PATH"] = str(tess_dir / "lib")
            os.environ["TESSDATA_PREFIX"] = str(tess_dir / "share" / "tessdata")

        self._logger.debug("Configured Tesseract paths: %s", pytesseract.pytesseract.tesseract_cmd)


# ------------------------------------------------------------------------- #
# Quick self‑test — run `python -m ocr_text_extractor` to verify
# ------------------------------------------------------------------------- #
if __name__ == "__main__":  # pragma: no cover
    from pprint import pprint
    from logger import logger

    cfg = Configuration()
    extractor = TextExtractor(cfg, logger)

    sample_file = Path("ocr_tests/fire_claw.png")
    text = extractor.extract_text_from_file(sample_file)
    print(text)
