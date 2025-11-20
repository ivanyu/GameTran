from dataclasses import dataclass
from enum import StrEnum


class DictionaryId(StrEnum):
    deepl = "Deepl"
    google_translate = "GoogleTranslate"
    microsoft_translator = "MicrosoftTranslator"
    cambridge_dictionary = "CambridgeDictionary"
    merriam_webster = "MerriamWebster"
    linternaute = "Linternaute"
    lingvo_live = "LingvoLive"
    multitran = "Multitran"
    reverso = "Reverso"
    wiktionary_game_language = "WiktionaryGameLanguage"
    wiktionary_user_language = "WiktionaryUserLanguage"
    wordreference = "Wordreference"
    wordreference_definition = "WordreferenceDefinition"


@dataclass(frozen=True, slots=True, kw_only=True)
class Dictionary:
    id: DictionaryId
    title: str
