import os

from PyQt6.QtGui import QImage, QPixmap
from dotenv import load_dotenv

load_dotenv()

def take_screenshot() -> QPixmap:
    file = os.environ.get("SCREENSHOT")
    image = QImage(file)
    if image.isNull():
        raise FileNotFoundError(f"Failed to load screenshot from {file}")
    return QPixmap.fromImage(image)
