import os
from dataclasses import dataclass

import mss
from PyQt6.QtGui import QImage, QPixmap
from PyQt6.QtWidgets import QApplication


@dataclass(frozen=True, slots=True, kw_only=True)
class Screenshot:
    pixmap: QPixmap
    device_pixel_ratio: float


def take_screenshot() -> Screenshot:
    if os.environ.get("GT_DEV") == "true":
        screenshot_keys = [
            k for k in os.environ.keys() if k.startswith("GT_SCREENSHOT_")
        ]
        assert screenshot_keys
        try:
            getattr(take_screenshot, "screenshot_key_idx")
        except AttributeError:
            take_screenshot.screenshot_key_idx = 0
        file = os.environ.get(screenshot_keys[take_screenshot.screenshot_key_idx])
        take_screenshot.screenshot_key_idx += 1
        if take_screenshot.screenshot_key_idx >= len(screenshot_keys):
            take_screenshot.screenshot_key_idx = 0
        image = QImage(file)
        if image.isNull():
            raise FileNotFoundError(f"Failed to load screenshot from {file}")
        return Screenshot(pixmap=QPixmap.fromImage(image), device_pixel_ratio=1.0)
    else:
        with mss.mss() as sct:
            monitor = sct.monitors[1]
            screenshot = sct.grab(monitor)

            # Convert mss screenshot to QImage.
            # mss returns BGRA format, need to convert to RGB32 or RGBA8888.
            width, height = screenshot.size
            img = QImage(
                screenshot.bgra,
                width,
                height,
                width * 4,  # bytes per line (4 bytes per pixel for BGRA)
                QImage.Format.Format_ARGB32,  # mss uses BGRA, Qt expects ARGB32
            )
            # Convert to RGB32 to remove alpha channel if not needed.
            img = img.convertToFormat(QImage.Format.Format_RGB32)
            pixmap = QPixmap.fromImage(img)

            # Set the device pixel ratio so Qt scales it correctly.
            device_pixel_ratio = QApplication.primaryScreen().devicePixelRatio()
            pixmap.setDevicePixelRatio(device_pixel_ratio)
            return Screenshot(pixmap=pixmap, device_pixel_ratio=device_pixel_ratio)
