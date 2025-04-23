from pathlib import Path
import os, sys
from PIL import Image
import pytesseract

# def resource(rel: str) -> Path:
#     """Return an absolute path that works both frozen & unfrozen."""
#     base = Path(sys._MEIPASS) if getattr(sys, "frozen", False) else Path(__file__).parent
#     return base / rel

# # --- point pytesseract at the bundled engine ---
# tess_dir = resource("tesseract")
# pytesseract.pytesseract.tesseract_cmd = str(tess_dir / "tesseract.exe")
# os.environ["TESSDATA_PREFIX"] = str(tess_dir)      # <- very important

def extract_text(image_path: str) -> str:
    with Image.open(image_path) as img:
        return pytesseract.image_to_string(img)

if __name__ == "__main__":
    print(extract_text("dist/screenshot.png"))
