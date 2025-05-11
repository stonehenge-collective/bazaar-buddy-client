from __future__ import annotations

"""A minimal OCR helper around **EasyOCR** (CPU‑only).

This re‑implementation replaces *pytesseract* with *EasyOCR* while retaining
exactly the same public interface so it can be dropped into existing code.

EasyOCR's neural network models run on either CPU or GPU; we explicitly force
**cpu‑only** mode by passing ``gpu=False`` to the reader.

If you need image pre‑processing, do it upstream and feed the cleaned bitmap
into the extractor just like before.
"""

from pathlib import Path
from typing import List

import numpy as np
from PIL import Image
import easyocr

from configuration import Configuration
from logging import Logger

__all__ = ["TextExtractor"]


class TextExtractor:
    """Thin wrapper around *EasyOCR*.

    Parameters
    ----------
    configuration
        Runtime configuration (already initialised elsewhere).
    logger
        App‑wide logger instance.
    lang
        ISO‑639‑1 language code(s) understood by EasyOCR — **comma‑separated**
        (e.g. ``"en,fr,de"``).  Default is ``"en"``.
    model_storage_dir
        Optional override for the directory where EasyOCR stores its downloaded
        model files. If *None*, the library default is used.
    """

    def __init__(
        self,
        configuration: Configuration,
        logger: Logger,
        *,
        lang: str = "en",
        model_storage_dir: str | Path | None = None,
    ) -> None:
        self._configuration = configuration
        self._logger = logger

        langs = [code.strip() for code in lang.split(",") if code.strip()]
        self._logger.debug("Initialising EasyOCR reader (CPU mode) for %s", langs)

        self._reader = easyocr.Reader(  # type: ignore[call-arg]
            langs,
            model_storage_directory=str(model_storage_dir) if model_storage_dir else None,
            gpu=False,  # <- **CPU only**
        )

    # ------------------------------ public API --------------------------- #
    def extract_text(
        self,
        image: Image.Image,
        *,
        confidence_threshold: int = 70,
    ) -> str:
        """OCR a :class:`PIL.Image.Image` and return a *single* text string.

        Parameters
        ----------
        image
            RGB or RGBA PIL image.
        confidence_threshold
            Any EasyOCR word candidate below this value (0‑100) is discarded.
            Default is **80**.
        """
        self._logger.debug("Extracting text (conf>=%d)", confidence_threshold)

        # EasyOCR expects ``numpy.ndarray``
        img_arr = np.asarray(image)

        results = self._reader.readtext(img_arr, detail=1)
        conf_cutoff = confidence_threshold / 100.0

        keep: List[str] = [txt for _, txt, conf in results if conf >= conf_cutoff and txt.strip()]
        return " ".join(keep)

    def extract_text_from_file(
        self,
        image_path: Path | str,
    ) -> str:
        """Convenience wrapper around :py:meth:`extract_text`."""
        path = Path(image_path)
        self._logger.debug("Opening image file %s", path)
        with Image.open(path) as img:
            return self.extract_text(img)


# --------------------------------------------------------------------- #
# Quick self‑test — run `python -m easyocr_text_extractor` to verify
# --------------------------------------------------------------------- #
if __name__ == "__main__":  # pragma: no cover
    from logger import logger

    cfg = Configuration()
    extractor = TextExtractor(cfg, logger)

    sample_file = Path("ocr_tests/fire_claw.png")
    text = extractor.extract_text_from_file(sample_file)
    print(text)
