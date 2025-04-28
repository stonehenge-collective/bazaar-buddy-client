import json
from pathlib import Path

# -------------------------------------------------
# Directories
# -------------------------------------------------
CURRENT_DIR = Path(__file__).resolve().parent         # client/data
CLIENT_ROOT = CURRENT_DIR.parent                      # client

# -------------------------------------------------
# Input file paths (relative to CURRENT_DIR)
# -------------------------------------------------
events_file_path   = CURRENT_DIR / "events.json"
items_file_path    = CURRENT_DIR / "items.json"
monsters_file_path = CURRENT_DIR / "monsters.json"
word_list_file_path = CURRENT_DIR / "word_list.json"

# -------------------------------------------------
# Output file paths for Tesseract training
# -------------------------------------------------
tessdata_dir       = CLIENT_ROOT / "tools" / "tesseract" / "tessdata"
tessdata_terms_path = tessdata_dir / "eng.bazaar_terms"

configs_dir        = tessdata_dir / "configs"
char_set_file_path = configs_dir / "bazaar_terms"

# Ensure output directories exist
configs_dir.mkdir(parents=True, exist_ok=True)

# -------------------------------------------------
# Load JSON data
# -------------------------------------------------
with events_file_path.open(encoding="utf-8") as fp:
    events = json.load(fp)

with items_file_path.open(encoding="utf-8") as fp:
    items = json.load(fp).get("items", [])

with monsters_file_path.open(encoding="utf-8") as fp:
    monsters = json.load(fp)

# -------------------------------------------------
# Build the word set
# -------------------------------------------------
word_set = set()

for entry in events:
    name = entry.get("name")
    if name:
        word_set.add(name)

for entry in items:
    name = entry.get("name")
    if name:
        word_set.add(name)

for entry in monsters:
    name = entry.get("name")
    if name:
        word_set.add(name)
    alt_text = entry.get("alt_text")
    if alt_text:
        word_set.add(alt_text)

# -------------------------------------------------
# Write newline-separated word list expected by Tesseract
# -------------------------------------------------
with tessdata_terms_path.open("w", encoding="utf-8") as fp:
    fp.write("\n".join(sorted(word_set)) + "\n")

with word_list_file_path.open("w", encoding="utf-8") as fp:
    json.dump(list(word_set), fp, indent=2, ensure_ascii=False)

# -------------------------------------------------
# Build character whitelist from the word set
# -------------------------------------------------
char_set = set()
for word in word_set:
    char_set.update(word)

char_whitelist = "".join(sorted(char_set))

# -------------------------------------------------
# Write config file containing the whitelist
# -------------------------------------------------
config_content = (
    "load_system_dawg     F\n"
    "load_freq_dawg       F\n"
    "user_words_suffix    bazaar_terms\n"
    f"tessedit_char_whitelist {char_whitelist} \n"
)

with char_set_file_path.open("w", encoding="utf-8") as fp:
    fp.write(config_content)
