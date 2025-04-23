from pathlib import Path
import os, sys
from PIL import Image, ImageFile
import pytesseract

def resource(rel: str) -> Path:
    """Return an absolute path that works both frozen & unfrozen."""
    base = Path(sys._MEIPASS)
    return base / rel

if getattr(sys, "frozen", False):
    tess_dir = resource("tesseract")
    pytesseract.pytesseract.tesseract_cmd = str(tess_dir / "tesseract.exe")
    os.environ["TESSDATA_PREFIX"] = str(tess_dir)      # <- very important

def extract_text(image: Image) -> str:
    return pytesseract.image_to_string(image)

def extract_text_from_file(image_path: str) -> str:
    with Image.open(image_path) as image:
        return pytesseract.image_to_string(image)

if __name__ == "__main__":
    print(extract_text_from_file("dist/screenshot.png"))
