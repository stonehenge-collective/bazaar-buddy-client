import platform
import logging

# Set up logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

operating_system = platform.system()
logger.debug(f"Operating system: {operating_system}")

from pathlib import Path
import os, sys
from PIL import Image
import pytesseract
from system_handler import SYSTEM_PATH

if operating_system == "Windows":
    tess_dir = SYSTEM_PATH / "tools" / "windows_tesseract"
    pytesseract.pytesseract.tesseract_cmd = str(tess_dir / "tesseract.exe")
    os.environ["TESSDATA_PREFIX"] = str(tess_dir / "tessdata")  # <- very important
else:
    tess_dir = SYSTEM_PATH / "tools" / "mac_tesseract"
    pytesseract.pytesseract.tesseract_cmd = str(tess_dir / "bin" / "tesseract")
    os.environ["TESSDATA_PREFIX"] = str(tess_dir / "share" / "tessdata")  # <- very important


def extract_text(image: Image) -> str:
    try:
        logger.debug("Attempting to extract text from image")
        result = pytesseract.image_to_string(image, lang="eng", config="bazaar_terms")
        logger.debug(f"Extracted text: {result}")
        return result
    except Exception as e:
        logger.error(f"Error extracting text: {str(e)}")
        raise


def extract_text_from_file(image_path: str) -> str:
    with Image.open(image_path) as image:
        return extract_text(image)


if __name__ == "__main__":
    from message_getter import match_keyword

    image_name = "the_cult"
    entity_name = "The Cult"
    # image_name = "force_field"
    # entity_name = "Force Field"
    image_name = "frost_street_champion"
    entity_name = "Frost Street Champion"
    success_counter = 0
    for x in range(30):
        result = extract_text_from_file(f"screenshot_examples/{image_name}.png")
        print(result)
        matched_word = match_keyword(result)
        print(matched_word)
        if matched_word == entity_name:
            success_counter += 1
    print(success_counter)
