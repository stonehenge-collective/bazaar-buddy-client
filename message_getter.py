import json, re
from rapidfuzz import process, fuzz
from configuration.configuration import get_configuration

config = get_configuration()

entities_path = config.system_path / "entities.json"
with entities_path.open("r", encoding="utf-8") as fp:
    entities = json.load(fp)


decorate_path = config.system_path / "decorate.json"
with decorate_path.open("r", encoding="utf-8") as fp:
    decorate_words = json.load(fp)


def match_keyword(text: str, threshold: int = 80):
    word_set = set([entity.get("name") for entity in entities])
    alt_text_list = [entity.get("alt_text") for entity in entities if entity.get("alt_text", None)]
    word_set.update(alt_text_list)
    result = process.extractOne(
        text,
        list(word_set),
        processor=str.lower,
        scorer=fuzz.token_set_ratio,
        score_cutoff=threshold,  # ignore anything below the bar
    )

    if result is None:
        return None

    word, score, _ = result
    print(word, score)
    return word


def get_message(screenshot_text: str):
    print(f"matching screenshot text, {screenshot_text}")
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


# def decorate_message(message: str): No longer need this if entities.json has the decoration already
#     decorated_message = message

#     def _get_replacer(word):
#         def _replacer(match):
#             original = match.group(0)
#             return word.replace("{word}", original)

#         return _replacer

#     for decorate in decorate_words:
#         decorated_message = re.sub(
#             decorate.get("word"), _get_replacer(decorate.get("decorate")), decorated_message, flags=re.IGNORECASE
#         )

#     return decorated_message


if __name__ == "__main__":
    from message_getter import match_keyword

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
    print(success_counter)
