import base64
import hashlib
import time
from pathlib import Path
from typing import Literal

from PyQt6.QtCore import QBuffer, QIODevice, Qt, QThread, pyqtSignal
from PyQt6.QtGui import QImage, QPixmap
from pydantic import BaseModel, ConfigDict


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

    def __init__(self, screenshot: QPixmap, target_height: int) -> None:
        super().__init__()
        self._screenshot = screenshot
        self._target_height = target_height

    def run(self) -> None:
        try:
            ocr_image_base64 = _prepare_screenshot_for_ocr(self._screenshot, target_height=self._target_height)
            result = _get_ocr(ocr_image_base64)
            # time.sleep(2)
            self.finished.emit(result)
        except Exception as e:
            self.error.emit(str(e))


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
        Qt.TransformationMode.SmoothTransformation
    )

    buffer = QBuffer()
    buffer.open(QIODevice.OpenModeFlag.WriteOnly)
    if not scaled_image.save(buffer, "JPEG"):
        raise RuntimeError("Failed to save as JPEG")
    jpeg_bytes = buffer.data().data()
    buffer.close()

    return base64.b64encode(jpeg_bytes).decode("ascii")


def _get_ocr(ocr_image_base64: str) -> OCRResult:
    hash_bytes = hashlib.sha256(ocr_image_base64.encode()).digest()
    hash_hex = hash_bytes.hex()

    cache_path = Path(f"dev/ocr_cache/{hash_hex}.json")
    if not cache_path.exists():
        raise FileNotFoundError(f"OCR cache not found: {cache_path}")

    with open(cache_path, "r", encoding="utf-8") as f:
        return OCRResult.model_validate_json(f.read())
