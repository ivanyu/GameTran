from typing import Final
from urllib.parse import quote

from dictionaries import Dictionary, DictionaryId
from dictionaries.languages import LANGUAGE_LOCAL_NAMES, EN_LANG_CODE, FR_LANG_CODE, IT_LANG_CODE, ES_LANG_CODE, \
    PT_LANG_CODE, DE_LANG_CODE, RU_LANG_CODE, ZH_LANG_CODE, JA_LANG_CODE, KO_LANG_CODE, PL_LANG_CODE, TR_LANG_CODE

_LANGUAGE_NAMES: Final = {
    EN_LANG_CODE: {
        EN_LANG_CODE: "English",
        FR_LANG_CODE: "French",
        IT_LANG_CODE: "Italian",
        ES_LANG_CODE: "Spanish",
        PT_LANG_CODE: "Portuguese",
        DE_LANG_CODE: "German",
        RU_LANG_CODE: "Russian",
        ZH_LANG_CODE: "Chinese",
        JA_LANG_CODE: "Japanese",
        KO_LANG_CODE: "Korean",
        PL_LANG_CODE: "Polish",
        TR_LANG_CODE: "Turkish",
    },
    FR_LANG_CODE: {
        EN_LANG_CODE: "Anglais",
        FR_LANG_CODE: "Français",
        IT_LANG_CODE: "Italien",
        ES_LANG_CODE: "Espagnol",
        PT_LANG_CODE: "Portugais",
        DE_LANG_CODE: "Allemand",
        RU_LANG_CODE: "Russe",
        ZH_LANG_CODE: "Chinois",
        JA_LANG_CODE: "Japonais",
        KO_LANG_CODE: "Coréen",
        PL_LANG_CODE: "Polonais",
        TR_LANG_CODE: "Turc",
    },
    IT_LANG_CODE: {
        EN_LANG_CODE: "Inglese",
        FR_LANG_CODE: "Francese",
        IT_LANG_CODE: "Italiano",
        ES_LANG_CODE: "Spagnolo",
        PT_LANG_CODE: "Portoghese",
        DE_LANG_CODE: "Tedesco",
        RU_LANG_CODE: "Russo",
        ZH_LANG_CODE: "Cinese",
        JA_LANG_CODE: "Giapponese",
        KO_LANG_CODE: "Coreano",
        PL_LANG_CODE: "Polacco",
        TR_LANG_CODE: "Turco",
    },
    ES_LANG_CODE: {
        EN_LANG_CODE: "Inglés",
        FR_LANG_CODE: "Francés",
        IT_LANG_CODE: "Italiano",
        ES_LANG_CODE: "Español",
        PT_LANG_CODE: "Portugués",
        DE_LANG_CODE: "Alemán",
        RU_LANG_CODE: "Ruso",
        ZH_LANG_CODE: "Mandarín",
        JA_LANG_CODE: "Japonés",
        KO_LANG_CODE: "Coreano",
        PL_LANG_CODE: "Sueco",
        TR_LANG_CODE: "Turco",
    },
    PT_LANG_CODE: {
        EN_LANG_CODE: "Inglês",
        FR_LANG_CODE: "Francês",
        IT_LANG_CODE: "Italiano",
        ES_LANG_CODE: "Espanhol",
        PT_LANG_CODE: "Português",
        DE_LANG_CODE: "Alemão",
        RU_LANG_CODE: "Russo",
        ZH_LANG_CODE: "Chinês",
        JA_LANG_CODE: "Japonês",
        KO_LANG_CODE: "Coreano",
        PL_LANG_CODE: "Polonês",
        TR_LANG_CODE: "Turco",
    },
    DE_LANG_CODE: {
        EN_LANG_CODE: "Englisch",
        FR_LANG_CODE: "Französisch",
        IT_LANG_CODE: "Italienisch",
        ES_LANG_CODE: "Spanisch",
        PT_LANG_CODE: "Portugiesisch",
        DE_LANG_CODE: "Deutsch",
        RU_LANG_CODE: "Russisch",
        ZH_LANG_CODE: "Chinesisch",
        JA_LANG_CODE: "Japanisch",
        KO_LANG_CODE: "Koreanisch",
        PL_LANG_CODE: "Polnisch",
        TR_LANG_CODE: "Türkisch",
    },
    RU_LANG_CODE: {
        EN_LANG_CODE: "Английский",
        FR_LANG_CODE: "Французский",
        IT_LANG_CODE: "Итальянский",
        ES_LANG_CODE: "Испанский",
        PT_LANG_CODE: "Португальский",
        DE_LANG_CODE: "Немецкий",
        RU_LANG_CODE: "Русский",
        ZH_LANG_CODE: "Китайский",
        JA_LANG_CODE: "Японский",
        KO_LANG_CODE: "Корейский",
        PL_LANG_CODE: "Польский",
        TR_LANG_CODE: "Турецкий",
    },
    ZH_LANG_CODE: {
        EN_LANG_CODE: "英語",
        FR_LANG_CODE: "法語",
        IT_LANG_CODE: "意大利语",
        ES_LANG_CODE: "西班牙语",
        PT_LANG_CODE: "葡萄牙语",
        DE_LANG_CODE: "德語",
        RU_LANG_CODE: "俄語",
        ZH_LANG_CODE: "漢語",
        JA_LANG_CODE: "日語",
        KO_LANG_CODE: "朝鮮語",
        PL_LANG_CODE: "波蘭語",
        TR_LANG_CODE: "土耳其語",
    },
    JA_LANG_CODE: {
        EN_LANG_CODE: "英語",
        FR_LANG_CODE: "フランス語",
        IT_LANG_CODE: "イタリア語",
        ES_LANG_CODE: "スペイン語",
        PT_LANG_CODE: "ポルトガル語",
        DE_LANG_CODE: "ドイツ語",
        RU_LANG_CODE: "ロシア語",
        ZH_LANG_CODE: "中国語",
        JA_LANG_CODE: "日本語",
        KO_LANG_CODE: "朝鮮語",
        PL_LANG_CODE: "ポーランド語",
        TR_LANG_CODE: "トルコ語",
    },
    KO_LANG_CODE: {
        EN_LANG_CODE: "영어",
        FR_LANG_CODE: "프랑스어",
        IT_LANG_CODE: "이탈리아어",
        ES_LANG_CODE: "스페인어",
        PT_LANG_CODE: "포르투갈어",
        DE_LANG_CODE: "독일어",
        RU_LANG_CODE: "러시아어",
        ZH_LANG_CODE: "중국어",
        JA_LANG_CODE: "일본어",
        KO_LANG_CODE: "한국어",
        PL_LANG_CODE: "폴란드어",
        TR_LANG_CODE: "터키어",
    },
    PL_LANG_CODE: {
        EN_LANG_CODE: "język_angielski",
        FR_LANG_CODE: "język_francuski",
        IT_LANG_CODE: "język_włoski",
        ES_LANG_CODE: "język_hiszpański",
        PT_LANG_CODE: "język_portugalski",
        DE_LANG_CODE: "język_niemiecki",
        RU_LANG_CODE: "język_rosyjski",
        ZH_LANG_CODE: "język_koreański",
        JA_LANG_CODE: "język_japoński",
        KO_LANG_CODE: "język_koreański",
        PL_LANG_CODE: "język_polski",
        TR_LANG_CODE: "język_turecki",
    },
    TR_LANG_CODE: {
        EN_LANG_CODE: "İngilizce",
        FR_LANG_CODE: "Fransızca",
        IT_LANG_CODE: "İtalyanca",
        ES_LANG_CODE: "İspanyolca",
        PT_LANG_CODE: "Portekizce",
        DE_LANG_CODE: "Almanca",
        RU_LANG_CODE: "Rusça",
        ZH_LANG_CODE: "Çince",
        JA_LANG_CODE: "Japonca",
        KO_LANG_CODE: "Korece",
        PL_LANG_CODE: "Lehçe",
        TR_LANG_CODE: "Türkçe",
    },
}

def get_wiktionary_dictionaries(game_language: str, user_language: str) -> list[Dictionary]:
    result: list[Dictionary] = []

    game_language_localized = LANGUAGE_LOCAL_NAMES.get(game_language)
    if game_language_localized:
        result.append(Dictionary(
            id=DictionaryId.wiktionary_game_language,
            title=f"Wiktionary {game_language_localized}"
        ))

    user_language_localized = LANGUAGE_LOCAL_NAMES.get(user_language)
    if user_language_localized:
        result.append(Dictionary(
            id=DictionaryId.wiktionary_user_language,
            title=f"Wiktionary {user_language_localized}"
        ))

    return result


def wiktionary_game_language_url(text: str, game_language: str) -> str:
    text_encoded = quote(text)
    language_name_in_language = _LANGUAGE_NAMES.get(game_language, {}).get(game_language)
    anchor = f"#{language_name_in_language}"
    return f"https://{game_language}.wiktionary.org/wiki/{text_encoded}{anchor}"


def wiktionary_user_language_url(text: str, game_language: str, user_language: str) -> str:
    text_encoded = quote(text)
    language_name_in_language = _LANGUAGE_NAMES.get(user_language, {}).get(game_language)
    anchor = f"#{language_name_in_language}"
    return f"https://{user_language}.wiktionary.org/wiki/{text_encoded}{anchor}"
