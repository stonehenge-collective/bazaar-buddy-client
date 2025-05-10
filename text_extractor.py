import os
from PIL import Image
import pytesseract
from configuration.configuration import get_configuration

config = get_configuration()

if config.operating_system == "Windows":
    tess_dir = config.system_path / "tools" / "windows_tesseract"
    pytesseract.pytesseract.tesseract_cmd = str(tess_dir / "tesseract.exe")
    os.environ["TESSDATA_PREFIX"] = str(tess_dir / "tessdata")  # <- very important
else:
    tess_dir = config.system_path / "tools" / "mac_tesseract"
    pytesseract.pytesseract.tesseract_cmd = str(tess_dir / "bin" / "tesseract")
    os.environ["DYLD_LIBRARY_PATH"] = str(tess_dir / "lib")
    os.environ["TESSDATA_PREFIX"] = str(tess_dir / "share" / "tessdata")  # <- very important


def extract_text(image: Image) -> str:
    try:
        print("Attempting to extract text from image")
        result = pytesseract.image_to_string(image, lang="eng", config="bazaar_terms")
        print(f"Extracted text: {result}")
        return result
    except Exception as e:
        print(f"Error extracting text: {str(e)}")
        raise


def extract_text_from_file(image_path: str) -> str:
    with Image.open(image_path) as image:
        return extract_text(image)


if __name__ == "__main__":
    from message_builder import match_keyword, get_message

    image_name = "the_cult"
    entity_name = "The Cult"
    # image_name = "force_field"
    # entity_name = "Force Field"
    # image_name = "frost_street_champion"
    # entity_name = "Frost Street Champion"
    image_name = "piano"
    entity_name = "Piano"
    success_counter = 0
    for x in range(30):
        result = extract_text_from_file(f"screenshot_examples/{image_name}.png")
        print(result)
        matched_word = match_keyword(result)
        print(matched_word)
        if matched_word == entity_name:
            success_counter += 1
        print(get_message(result))
    print(success_counter)
