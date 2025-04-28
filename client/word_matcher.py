import json
from pathlib import Path
import sys
from rapidfuzz import process, fuzz

if getattr(sys, 'frozen', False):        # running inside the .exe
    system_path = Path(sys._MEIPASS)           # type: ignore[attr-defined]
else:                                    # running from source
    system_path = Path(__file__).resolve().parent

word_list_path = system_path / "data/word_list.json"
with word_list_path.open("r", encoding="utf-8") as fp:
    word_list = json.load(fp)

def match_word(text: str, threshold: int = 80):
    result = process.extractOne(
        text,
        word_list,
        processor=str.lower,
        scorer=fuzz.token_set_ratio,
        score_cutoff=threshold,   # ignore anything below the bar
    )

    if result is None:
        return None

    word, score, _ = result
    print(word, score)
    return word