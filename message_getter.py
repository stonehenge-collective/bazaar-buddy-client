import json
from rapidfuzz import process, fuzz
from system_handler import SYSTEM_PATH

entities_path = SYSTEM_PATH / "entities.json"
with entities_path.open("r", encoding="utf-8") as fp:
    entities = json.load(fp)

def match_keyword(text: str, threshold: int = 80):
    word_set = set([entity.get("name") for entity in entities])
    alt_text_list = [entity.get("alt_text") for entity in entities if entity.get("alt_text", None)]
    word_set.update(alt_text_list)
    result = process.extractOne(
        text,
        list(word_set),
        processor=str.lower,
        scorer=fuzz.token_set_ratio,
        score_cutoff=threshold,   # ignore anything below the bar
    )

    if result is None:
        return None

    word, score, _ = result
    print(word, score)
    return word

def get_message(screenshot_text: str):
    matched_word = match_keyword(screenshot_text)

    if not matched_word:
        print("did not match word")
        return None

    for entity in entities:
        name = entity.get("name")
        alt_text = entity.get("alt_text", None)
        if name == matched_word or alt_text == matched_word:
            print(f"found entity! {name}")
            return entity.get("display_message", None)

    return None
