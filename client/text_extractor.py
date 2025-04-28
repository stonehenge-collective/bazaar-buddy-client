from pathlib import Path
import os, sys
from PIL import Image, ImageFile
import pytesseract

if getattr(sys, "frozen", False):
    tess_dir = Path(sys._MEIPASS) / "tesseract"
    pytesseract.pytesseract.tesseract_cmd = str(tess_dir / "tesseract.exe")
    os.environ["TESSDATA_PREFIX"] = str(tess_dir / "tessdata")      # <- very important

def extract_text(image: Image) -> str:
    return pytesseract.image_to_string(image, lang="eng",
                                   config="bazaar_terms")

def extract_text_from_file(image_path: str) -> str:
    with Image.open(image_path) as image:
        return pytesseract.image_to_string(image, lang="eng", config="bazaar_terms")

if __name__ == "__main__":
    print(extract_text_from_file("dist/Screenshot (13).png"))
