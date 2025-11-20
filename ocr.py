import base64
import hashlib
import json
import os
from http import HTTPStatus
from pathlib import Path
from typing import Any, override

import requests
from pydantic import BaseModel, ConfigDict
from PyQt6.QtCore import QBuffer, QIODevice, Qt, QThread, pyqtSignal
from PyQt6.QtGui import QImage, QPixmap

from config import Config


class Vertex(BaseModel):
    model_config = ConfigDict(frozen=True)

    x: int
    y: int


class Word(BaseModel):
    model_config = ConfigDict(frozen=True)

    id: int
    text: str
    boundingBox: list[Vertex]


class OCRResult(BaseModel):
    model_config = ConfigDict(frozen=True)

    # type: Literal["success", "error"]
    detectedLanguage: str
    words: list[Word]


class OcrWorker(QThread):
    finished = pyqtSignal(OCRResult)
    error = pyqtSignal(str)

    def __init__(self, screenshot: QPixmap, target_height: int, config: Config) -> None:
        super().__init__()
        self._stopped = False
        self._screenshot = screenshot
        self._target_height = target_height
        self._config = config

    @override
    def run(self) -> None:
        try:
            ocr_image_base64 = _prepare_screenshot_for_ocr(
                self._screenshot, target_height=self._target_height
            )
            result = _get_ocr(ocr_image_base64, self._config.google_api_key)
            if (
                os.environ.get("GT_DEV") == "true"
                and (delay := int(os.environ.get("GT_OCR_DELAY", 0))) > 0
            ):
                import time

                time.sleep(delay)
            if not self._stopped:
                self.finished.emit(result)
        except Exception as e:
            if not self._stopped:
                self.error.emit(str(e))

    def stop(self) -> None:
        self._stopped = True


def _prepare_screenshot_for_ocr(pixmap: QPixmap, *, target_height: int) -> str:
    image = pixmap.toImage()
    if image.format() != QImage.Format.Format_RGB888:
        image = image.convertToFormat(QImage.Format.Format_RGB888)

    # Calculate scale factor and new dimensions.
    scale_factor = image.height() / target_height
    scaled_width = int(image.width() / scale_factor)
    scaled_height = int(image.height() / scale_factor)

    scaled_image = image.scaled(
        scaled_width,
        scaled_height,
        Qt.AspectRatioMode.IgnoreAspectRatio,
        Qt.TransformationMode.SmoothTransformation,
    )

    buffer = QBuffer()
    buffer.open(QIODevice.OpenModeFlag.WriteOnly)
    if not scaled_image.save(buffer, "JPEG"):
        raise RuntimeError("Failed to save as JPEG")
    jpeg_bytes = buffer.data().data()
    buffer.close()

    return base64.b64encode(jpeg_bytes).decode("ascii")


def _get_ocr(ocr_image_base64: str, google_api_key: str) -> OCRResult:
    hash_bytes = hashlib.sha256(ocr_image_base64.encode()).digest()
    hash_hex = hash_bytes.hex()
    cache_path = Path(f"dev/ocr_cache/{hash_hex}.json")
    if not cache_path.exists():
        request = {
            "requests": [
                {
                    "image": {"content": ocr_image_base64},
                    "features": {"type": "TEXT_DETECTION"},
                }
            ]
        }
        response = requests.post(
            "https://vision.googleapis.com/v1/images:annotate",
            data=json.dumps(request),
            headers={
                "Content-Type": "application/json; charset=utf-8",
                "X-goog-api-key": google_api_key,
            },
        )

        if response.status_code != HTTPStatus.OK.value:
            raise Exception(str(response.json()["error"]))

        page = response.json()["responses"][0]["fullTextAnnotation"]["pages"][0]
        detected_languages: list[dict[str, Any]] = page["property"]["detectedLanguages"]
        detected_languages.sort(key=lambda dl: dl["confidence"])
        detected_language = detected_languages[-1]["languageCode"]

        words = []
        word_id = 0
        for block in page["blocks"]:
            if block["blockType"] != "TEXT" and block["blockType"] != "TABLE":
                continue
            for paragraph in block["paragraphs"]:
                for word_json in paragraph["words"]:
                    word = Word(
                        id=word_id,
                        text="".join([s["text"] for s in word_json["symbols"]]),
                        boundingBox=[
                            Vertex(x=v["x"], y=v["y"])
                            for v in word_json["boundingBox"]["vertices"]
                        ],
                    )
                    word_id += 1
                    words.append(word)
        result = OCRResult(detectedLanguage=detected_language, words=words)

        cache_path.parent.mkdir(parents=True, exist_ok=True)
        with open(cache_path, "w", encoding="utf-8") as f:
            f.write(result.model_dump_json())

        return result
    else:
        with open(cache_path, "r", encoding="utf-8") as f:
            return OCRResult.model_validate_json(f.read())
