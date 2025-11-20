import hashlib
import json
import os
from http import HTTPStatus
from pathlib import Path
from typing import override

import requests
from pydantic import BaseModel
from PyQt6.QtCore import QThread, pyqtSignal

from config import Config


class TextSpan(BaseModel):
    content: str
    # beginOffset: int


class PartOfSpeech(BaseModel):
    tag: str
    # aspect: str
    # case: str
    # form: str
    # gender: str
    # mood: str
    # number: str
    # person: str
    # proper: str
    # reciprocity: str
    # tense: str
    # voice: str


# class Sentence(BaseModel):
#     text: TextSpan


# class DependencyEdge(BaseModel):
#     headTokenIndex: int
#     label: str


class Token(BaseModel):
    text: TextSpan
    partOfSpeech: PartOfSpeech
    # dependencyEdge: DependencyEdge
    lemma: str


class SyntaxAnalysis(BaseModel):
    # sentences: list[Sentence]
    tokens: list[Token]
    language: str


class AnalysisWorker(QThread):
    finished = pyqtSignal(SyntaxAnalysis)
    error = pyqtSignal(str)

    def __init__(self, content: str, game_language: str, config: Config) -> None:
        super().__init__()
        self._content = content
        self._game_language = game_language
        self._config = config
        self._interrupted = False

    @override
    def run(self) -> None:
        try:
            result = _get_analysis(
                self._content, self._game_language, self._config.google_api_key
            )
            if (
                os.environ.get("GT_DEV") == "true"
                and (delay := int(os.environ.get("GT_ANALYSIS_DELAY", 0))) > 0
            ):
                import time

                time.sleep(delay)
            if not self._interrupted:
                self.finished.emit(result)
        except Exception as e:
            if not self._interrupted:
                self.error.emit(str(e))

    def interrupt(self) -> None:
        self._interrupted = True


def _get_analysis(
    content: str, game_language: str, google_api_key: str
) -> SyntaxAnalysis:
    document = {
        "document": {
            "content": content,
            "language": game_language,
            "type": "PLAIN_TEXT",
        },
        "encodingType": "UTF8",
    }
    document_str = json.dumps(document)

    hash_bytes = hashlib.sha256(document_str.encode()).digest()
    hash_hex = hash_bytes.hex()
    cache_path = Path(f"dev/analysis_cache/{hash_hex}.json")
    if not cache_path.exists():
        response = requests.post(
            "https://language.googleapis.com/v1/documents:analyzeSyntax",
            data=document_str,
            headers={
                "Content-Type": "application/json",
                "X-goog-api-key": google_api_key,
            },
        )
        result_dict = response.json()

        if response.status_code != HTTPStatus.OK.value:
            raise Exception(str(result_dict))

        result = SyntaxAnalysis.model_validate(result_dict)

        cache_path.parent.mkdir(parents=True, exist_ok=True)
        with open(cache_path, "w", encoding="utf-8") as f:
            json.dump(result_dict, f, ensure_ascii=False, indent=2)

        return result
    else:
        with open(cache_path, "r", encoding="utf-8") as f:
            return SyntaxAnalysis.model_validate_json(f.read())
