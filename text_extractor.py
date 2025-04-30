from pathlib import Path
import os, sys
from PIL import Image
import pytesseract
from system_handler import SYSTEM_PATH

tess_dir = SYSTEM_PATH / "tools" / "tesseract"
pytesseract.pytesseract.tesseract_cmd = str(tess_dir / "tesseract.exe")
os.environ["TESSDATA_PREFIX"] = str(tess_dir / "tessdata")      # <- very important

def extract_text(image: Image) -> str:
    return pytesseract.image_to_string(image, lang="eng",
                                   config="bazaar_terms")

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
