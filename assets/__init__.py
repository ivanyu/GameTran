import pkgutil

from PyQt6.QtGui import QIcon, QPixmap


def load_pixmap(name: str) -> QPixmap:
    pixmap = QPixmap()
    pixmap.loadFromData(pkgutil.get_data("assets", name))
    return pixmap


def load_icon(name: str) -> QIcon:
    return QIcon(load_pixmap(name))
