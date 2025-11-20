from typing import Final, Optional
from urllib.parse import quote

from dictionaries.languages import EN_LANG_CODE, FR_LANG_CODE, RU_LANG_CODE
from dictionaries.multitran import multitran_dict, multitran_url
from dictionaries.reverso import get_reverso_dictionaries, reverso_url
from dictionaries.types import DictionaryId, Dictionary
from dictionaries.wiktionary import get_wiktionary_dictionaries, wiktionary_game_language_url, \
    wiktionary_user_language_url
from dictionaries.wordreference import get_wordreference_dictionaries, wordreference_url, wordreference_definition_url

_GOOGLE_TRANSLATE: Final = Dictionary(
    id=DictionaryId.google_translate,
    title="Google Translate",
)
_MICROSOFT_TRANSLATOR: Final = Dictionary(
    id=DictionaryId.microsoft_translator,
    title="Microsoft Translator",
)
_DEEPL: Final = Dictionary(
    id=DictionaryId.deepl,
    title="DeepL",
)

def get_dictionaries(game_language: str, user_language: str) -> list[Dictionary]:
    result: list[Dictionary] = [
        _GOOGLE_TRANSLATE,
        _MICROSOFT_TRANSLATOR,
        _DEEPL,
    ]

    result.extend(get_wiktionary_dictionaries(game_language, user_language))

    if game_language == EN_LANG_CODE:
        result.append(Dictionary(
            id=DictionaryId.cambridge_dictionary,
            title="Cambridge Dictionary"
        ))
        result.append(Dictionary(
            id=DictionaryId.merriam_webster,
            title="Merriam-Webster",
        ))

    if game_language == FR_LANG_CODE:
        result.append(Dictionary(
            id=DictionaryId.linternaute,
            title="Linternaute.com",
        ))

    result.append(Dictionary(
        id=DictionaryId.lingvo_live,
        title="Lingvo Live",
    ))

    result.extend(get_wordreference_dictionaries(game_language, user_language))
    result.extend(get_reverso_dictionaries(game_language, user_language))

    result.append(multitran_dict())

    return result


def _google_translate_url(text: str, game_language: str, user_language: str) -> str:
    text_encoded = quote(text)
    return f"https://translate.google.com/?sl={game_language}&tl={user_language}&text={text_encoded}&op=translate"


def _deepl_url(text: str, game_language: str, user_language: str) -> str:
    text_encoded = quote(text)
    return f"https://www.deepl.com/{user_language}/translator#{game_language}/{user_language}/{text_encoded}"


def _microsoft_translator_url(text: str, game_language: str, user_language: str) -> str:
    text_encoded = quote(text)
    return f"https://www.bing.com/translator?from={game_language}&to={user_language}&text={text_encoded}"


def _linternaute_url(text: str) -> str:
    text_encoded = quote(text)
    return f"https://www.linternaute.fr/dictionnaire/fr/definition/{text_encoded}"


def _cambridge_url(text: str) -> str:
    text_encoded = quote(text)
    return f"https://dictionary.cambridge.org/dictionary/english/{text_encoded}"


def _merriam_webster_url(text: str) -> str:
    text_encoded = quote(text)
    return f"https://www.merriam-webster.com/dictionary/{text_encoded}"


def _lingvo_live_url(text: str, game_language: str, user_language: str) -> str:
    text_encoded = quote(text)
    interface_lang = "ru-ru" if user_language == RU_LANG_CODE else "en-us"
    return f"https://www.lingvolive.com/{interface_lang}/translate/{game_language}-{user_language}/{text_encoded}"


def get_dictionary_url(*, text: str, game_language: str, user_language: str, dictionary_id: DictionaryId) -> Optional[str]:
    match dictionary_id:
        case DictionaryId.google_translate:
            return _google_translate_url(text, game_language, user_language)
        case DictionaryId.deepl:
            return _deepl_url(text, game_language, user_language)
        case DictionaryId.microsoft_translator:
            return _microsoft_translator_url(text, game_language, user_language)
        case DictionaryId.wiktionary_game_language:
            return wiktionary_game_language_url(text, game_language)
        case DictionaryId.wiktionary_user_language:
            return wiktionary_user_language_url(text, game_language, user_language)
        case DictionaryId.linternaute:
            return _linternaute_url(text)
        case DictionaryId.wordreference:
            return wordreference_url(text, game_language, user_language)
        case DictionaryId.wordreference_definition:
            return wordreference_definition_url(text, game_language)
        case DictionaryId.reverso:
            return reverso_url(text, game_language, user_language)
        case DictionaryId.multitran:
            return multitran_url(text, game_language, user_language)
        case DictionaryId.cambridge_dictionary:
            return _cambridge_url(text)
        case DictionaryId.merriam_webster:
            return _merriam_webster_url(text)
        case DictionaryId.lingvo_live:
            return _lingvo_live_url(text, game_language, user_language)
