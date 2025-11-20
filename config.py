from pathlib import Path
from typing import Final

from PyQt6.QtCore import QLocale, QSettings, QStandardPaths


class Config:
    _GOOGLE_API_KEY: Final = "google_api_key"
    _USER_LANGUAGE: Final = "user_language"
    _GLOBAL_HOTKEY: Final = "global_hotkey"
    _PROMPT_LANGUAGE: Final = "prompt_language"

    def __init__(self) -> None:
        config_dir = Path(
            QStandardPaths.writableLocation(
                QStandardPaths.StandardLocation.AppConfigLocation
            )
        )
        self._settings = QSettings(
            str(config_dir / "config.ini"), QSettings.Format.IniFormat
        )

    @property
    def google_api_key(self) -> str:
        return self._settings.value(self._GOOGLE_API_KEY)

    @google_api_key.setter
    def google_api_key(self, value: str) -> None:
        self._settings.setValue(self._GOOGLE_API_KEY, value)
        self._settings.sync()

    @property
    def has_valid_api_key(self) -> bool:
        key = self.google_api_key
        return key is not None and key.strip() != ""

    @property
    def user_language(self) -> str:
        locale = QLocale.system()
        default_language = QLocale.system().languageToCode(locale.language())
        return self._settings.value(self._USER_LANGUAGE, defaultValue=default_language)

    @user_language.setter
    def user_language(self, value: str) -> None:
        self._settings.setValue(self._USER_LANGUAGE, value)
        self._settings.sync()

    @property
    def global_hotkey(self) -> str:
        return self._settings.value(self._GLOBAL_HOTKEY, defaultValue="<alt>+x")

    @global_hotkey.setter
    def global_hotkey(self, value: str) -> None:
        self._settings.setValue(self._GLOBAL_HOTKEY, value)
        self._settings.sync()

    @property
    def prompt_language(self) -> str:
        return self._settings.value(self._PROMPT_LANGUAGE, defaultValue="en")

    @prompt_language.setter
    def prompt_language(self, value: str) -> None:
        self._settings.setValue(self._PROMPT_LANGUAGE, value)
        self._settings.sync()
