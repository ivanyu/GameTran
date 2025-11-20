from typing import Final, Tuple
from urllib.parse import quote

from dictionaries import EN_LANG_CODE, FR_LANG_CODE, Dictionary, DictionaryId
from dictionaries.languages import ES_LANG_CODE, IT_LANG_CODE, DE_LANG_CODE, NL_LANG_CODE, SV_LANG_CODE, IS_LANG_CODE, \
    RU_LANG_CODE, PT_LANG_CODE, PL_LANG_CODE, RO_LANG_CODE, TR_LANG_CODE, ZH_LANG_CODE, JA_LANG_CODE, KO_LANG_CODE, \
    AR_LANG_CODE, CS_LANG_CODE, EL_LANG_CODE

WORDREFERENCE_NAME: Final = "WordReference.com"

WORDREFERENCE_LANGUAGE_PAIRS: Final[list[Tuple[str, str]]] = [
    # English
    (EN_LANG_CODE, ES_LANG_CODE),
    (EN_LANG_CODE, FR_LANG_CODE),
    (EN_LANG_CODE, IT_LANG_CODE),
    (EN_LANG_CODE, DE_LANG_CODE),
    (EN_LANG_CODE, NL_LANG_CODE),
    (EN_LANG_CODE, SV_LANG_CODE),
    (EN_LANG_CODE, IS_LANG_CODE),
    (EN_LANG_CODE, RU_LANG_CODE),
    (EN_LANG_CODE, PT_LANG_CODE),
    (EN_LANG_CODE, PL_LANG_CODE),
    (EN_LANG_CODE, RO_LANG_CODE),
    (EN_LANG_CODE, "cz"),
    (EN_LANG_CODE, "gr"),
    (EN_LANG_CODE, TR_LANG_CODE),
    (EN_LANG_CODE, ZH_LANG_CODE),
    (EN_LANG_CODE, JA_LANG_CODE),
    (EN_LANG_CODE, KO_LANG_CODE),
    (EN_LANG_CODE, AR_LANG_CODE),
    # Spanish
    (ES_LANG_CODE, EN_LANG_CODE),
    (ES_LANG_CODE, FR_LANG_CODE),
    (ES_LANG_CODE, PT_LANG_CODE),
    (ES_LANG_CODE, IT_LANG_CODE),
    (ES_LANG_CODE, DE_LANG_CODE),
    # French
    (FR_LANG_CODE, EN_LANG_CODE),
    (FR_LANG_CODE, ES_LANG_CODE),
    # Italian
    (IT_LANG_CODE, EN_LANG_CODE),
    (IT_LANG_CODE, ES_LANG_CODE),
    # German
    (DE_LANG_CODE, EN_LANG_CODE),
    (DE_LANG_CODE, ES_LANG_CODE),
    # Dutch
    (NL_LANG_CODE, EN_LANG_CODE),
    # Swedish
    (SV_LANG_CODE, EN_LANG_CODE),
    # Russian
    (RU_LANG_CODE, EN_LANG_CODE),
    # Portuguese
    (PT_LANG_CODE, EN_LANG_CODE),
    (PT_LANG_CODE, ES_LANG_CODE),
    # Polish
    (PL_LANG_CODE, EN_LANG_CODE),
    # Romanian
    (RO_LANG_CODE, EN_LANG_CODE),
    # Czech
    ("cz", EN_LANG_CODE),
    # Greek
    ("gr", EN_LANG_CODE),
    # Turkish
    (TR_LANG_CODE, EN_LANG_CODE),
    # Chinese
    (ZH_LANG_CODE, EN_LANG_CODE),
    # Japanese
    (JA_LANG_CODE, EN_LANG_CODE),
    # Korean
    (KO_LANG_CODE, EN_LANG_CODE),
    # Arabic
    (AR_LANG_CODE, EN_LANG_CODE),
]

def get_wordreference_dictionaries(game_language: str, user_language: str) -> list[Dictionary]:
    result: list[Dictionary] = []

    def language_to_lookup(lang: str) -> str:
        if lang == CS_LANG_CODE:
            return "cz"
        elif lang == EL_LANG_CODE:
            return "gr"
        else:
            return lang

    game_language_to_lookup = language_to_lookup(game_language)
    user_language_to_lookup = language_to_lookup(user_language)

    for gl, ul in WORDREFERENCE_LANGUAGE_PAIRS:
        if gl == game_language_to_lookup and ul == user_language_to_lookup:
            result.append(Dictionary(
                id=DictionaryId.wordreference,
                title=f"{WORDREFERENCE_NAME} {gl} → {ul}"
            ))
            break

    if game_language == EN_LANG_CODE:
        result.append(Dictionary(
            id=DictionaryId.wordreference_definition,
            title=f"{WORDREFERENCE_NAME} definition"
        ))
    elif game_language == ES_LANG_CODE:
        result.append(Dictionary(
            id=DictionaryId.wordreference_definition,
            title=f"{WORDREFERENCE_NAME} definición"
        ))
    elif game_language == IT_LANG_CODE:
        result.append(Dictionary(
            id=DictionaryId.wordreference_definition,
            title=f"{WORDREFERENCE_NAME} definizione"
        ))

    return result


def wordreference_url(text: str, game_language: str, user_language: str) -> str:
    text_encoded = quote(text)
    return f"https://www.wordreference.com/{game_language}{user_language}/{text_encoded}"


def wordreference_definition_url(text: str, game_language: str) -> str:
    text_encoded = quote(text)
    return f"https://www.wordreference.com/{game_language}{game_language}/{text_encoded}"
