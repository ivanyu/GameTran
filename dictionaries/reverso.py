from typing import Final, Optional
from urllib.parse import quote

from dictionaries.types import Dictionary, DictionaryId
from dictionaries.languages import AR_LANG_CODE, ZH_LANG_CODE, CS_LANG_CODE, DA_LANG_CODE, NL_LANG_CODE, EN_LANG_CODE, \
    FR_LANG_CODE, DE_LANG_CODE, EL_LANG_CODE, HE_LANG_CODE, HI_LANG_CODE, HU_LANG_CODE, IT_LANG_CODE, JA_LANG_CODE, \
    KO_LANG_CODE, FA_LANG_CODE, PL_LANG_CODE, PT_LANG_CODE, RO_LANG_CODE, RU_LANG_CODE, SK_LANG_CODE, ES_LANG_CODE, \
    SV_LANG_CODE, TH_LANG_CODE, TK_LANG_CODE, UK_LANG_CODE

LANGUAGE_CODE_TO_THREE_LETTER_CODE: Final = {
    AR_LANG_CODE: "ara",
    ZH_LANG_CODE: "chi",
    CS_LANG_CODE: "cze",
    DA_LANG_CODE: "dan",
    NL_LANG_CODE: "dut",
    EN_LANG_CODE: "eng",
    FR_LANG_CODE: "fra",
    DE_LANG_CODE: "ger",
    EL_LANG_CODE: "gre",
    HE_LANG_CODE: "heb",
    HI_LANG_CODE: "hin",
    HU_LANG_CODE: "hun",
    IT_LANG_CODE: "ita",
    JA_LANG_CODE: "jpn",
    KO_LANG_CODE: "kor",
    FA_LANG_CODE: "per",
    PL_LANG_CODE: "pol",
    PT_LANG_CODE: "por",
    RO_LANG_CODE: "rum",
    RU_LANG_CODE: "rus",
    SK_LANG_CODE: "slo",
    ES_LANG_CODE: "spa",
    SV_LANG_CODE: "swe",
    TH_LANG_CODE: "tha",
    TK_LANG_CODE: "tur",
    UK_LANG_CODE: "ukr",
}

def get_reverso_dictionaries(game_language: str, user_language: str) -> list[Dictionary]:
    result: list[Dictionary] = []
    if game_language in LANGUAGE_CODE_TO_THREE_LETTER_CODE and user_language in LANGUAGE_CODE_TO_THREE_LETTER_CODE:
        result.append(Dictionary(
            id=DictionaryId.reverso,
            title="Reverso",
        ))
    return result


def reverso_url(text: str, game_language: str, user_language: str) -> Optional[str]:
    text_encoded = quote(text)
    maybe_game_language = LANGUAGE_CODE_TO_THREE_LETTER_CODE.get(game_language)
    maybe_user_language = LANGUAGE_CODE_TO_THREE_LETTER_CODE.get(user_language)
    if maybe_game_language and maybe_user_language:
        return f"https://www.reverso.net/text-translation#sl={game_language}&tl={user_language}&text={text_encoded}"
    else:
        return None
