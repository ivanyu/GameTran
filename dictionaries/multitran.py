from typing import Final
from urllib.parse import quote

from dictionaries import EN_LANG_CODE, FR_LANG_CODE, RU_LANG_CODE
from dictionaries.languages import (
    AR_LANG_CODE,
    BG_LANG_CODE,
    CS_LANG_CODE,
    DE_LANG_CODE,
    EL_LANG_CODE,
    ES_LANG_CODE,
    FI_LANG_CODE,
    GA_LANG_CODE,
    IT_LANG_CODE,
    JA_LANG_CODE,
    KO_LANG_CODE,
    NL_LANG_CODE,
    PL_LANG_CODE,
    PT_LANG_CODE,
    RO_LANG_CODE,
    SV_LANG_CODE,
    TR_LANG_CODE,
)
from dictionaries.types import Dictionary, DictionaryId

MULTITRAN_SUPPORTED_DICTIONARIES: Final = {
    EN_LANG_CODE: 1,
    RU_LANG_CODE: 2,
    DE_LANG_CODE: 3,
    FR_LANG_CODE: 4,
    ES_LANG_CODE: 5,
    AR_LANG_CODE: 10,
    PT_LANG_CODE: 11,
    RO_LANG_CODE: 13,
    PL_LANG_CODE: 14,
    BG_LANG_CODE: 15,
    CS_LANG_CODE: 16,  # Czech
    IT_LANG_CODE: 23,
    NL_LANG_CODE: 24,
    JA_LANG_CODE: 28,
    SV_LANG_CODE: 29,
    TR_LANG_CODE: 32,
    FI_LANG_CODE: 36,
    EL_LANG_CODE: 38,  # Greek
    KO_LANG_CODE: 39,
    GA_LANG_CODE: 49,  # Irish
}


def multitran_dict() -> Dictionary:
    return Dictionary(id=DictionaryId.multitran, title="Multitran")


def multitran_url(text: str, game_language: str, user_language: str) -> str:
    text_encoded = quote(text)
    maybe_game_language = MULTITRAN_SUPPORTED_DICTIONARIES.get(game_language)
    maybe_user_language = MULTITRAN_SUPPORTED_DICTIONARIES.get(user_language)
    if maybe_game_language is not None and maybe_user_language is not None:
        return f"https://www.multitran.com/m.exe?s={text_encoded}&l1={maybe_game_language}&l2={maybe_user_language}"
    else:
        return ""
