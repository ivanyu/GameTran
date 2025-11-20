from dataclasses import dataclass
from typing import Final, Optional, override

from PyQt6.QtCore import Qt, QPointF, QRectF, pyqtSignal
from PyQt6.QtGui import QCursor, QPixmap, QPainter, QBrush, QColor, QPen, QPolygonF, QPainterPath, QMouseEvent, QImage, \
    QKeyEvent
from PyQt6.QtWidgets import QGraphicsView, QGraphicsScene, QApplication, QGraphicsPolygonItem, QMessageBox

from ocr import OCRResult, Word as OcrWord


@dataclass(slots=True, kw_only=True)
class _Word:
    widget: QGraphicsPolygonItem
    word: OcrWord
    selected: bool


class Overlay(QGraphicsView):
    CURSOR_RADIUS: Final = 30
    analysis_requested = pyqtSignal(list)

    def __init__(self) -> None:
        self._scene = _Scene(cursor_radius=self.CURSOR_RADIUS)
        super().__init__(self._scene)
        self._cursor = _SelectionCursor(initial_radius=self.CURSOR_RADIUS)

        # Remove frame and margins.
        self.setFrameShape(QGraphicsView.Shape.NoFrame)
        self.setContentsMargins(0, 0, 0, 0)

        # self._cursor.set_state(CursorState.neutral)
        self.setCursor(self._cursor.get_cursor(False))

        self._words: list[_Word] = []

    def set_screenshot(self, screenshot: QPixmap) -> None:
        self._scene.set_screenshot(screenshot)

    def set_ocr(self, ocr: OCRResult) -> None:
        for word in ocr.words:
            polygon = QPolygonF([
                QPointF(vertex.x, vertex.y) for vertex in word.boundingBox
            ])
            polygon_widget = self._scene.add_box(polygon)
            self._words.append(_Word(widget=polygon_widget, word=word, selected=False))

    @override
    def mousePressEvent(self, event: Optional[QMouseEvent]) -> None:
        if event.button() == Qt.MouseButton.LeftButton:
            # self._cursor.set_state(CursorState.selecting)
            self.setCursor(self._cursor.get_cursor(True))

            for word in self._find_collisions_at_point(event.position()):
                word.selected = True
                self._scene.select_box(word.widget)

        elif event.button() == Qt.MouseButton.RightButton:
            for word in self._find_collisions_at_point(event.position()):
                word.selected = False
                self._scene.deselect_box(word.widget)

        super().mousePressEvent(event)

    @override
    def mouseReleaseEvent(self, event: Optional[QMouseEvent]) -> None:
        if event.button() == Qt.MouseButton.LeftButton:
            self.setCursor(self._cursor.get_cursor(False))

        super().mouseReleaseEvent(event)

    @override
    def mouseMoveEvent(self, event: Optional[QMouseEvent]) -> None:
        if event.buttons() & Qt.MouseButton.LeftButton:
            for word in self._find_collisions_at_point(event.position()):
                word.selected = True
                self._scene.select_box(word.widget)
        elif event.buttons() & Qt.MouseButton.RightButton:
            for word in self._find_collisions_at_point(event.position()):
                word.selected = False
                self._scene.deselect_box(word.widget)

        super().mouseMoveEvent(event)

    def _find_collisions_at_point(self, point: QPointF) -> list[_Word]:
        result = []

        # Adjust cursor radius for display scaling.
        device_pixel_ratio = QApplication.primaryScreen().devicePixelRatio()
        actual_radius = self._cursor.radius / device_pixel_ratio

        cursor_path = QPainterPath()
        cursor_rect = QRectF(
            point.x() - actual_radius,
            point.y() - actual_radius,
            actual_radius * 2,
            actual_radius * 2
        )
        cursor_path.addEllipse(cursor_rect)

        for w in self._words:
            if cursor_path.intersects(w.widget.shape()):
                result.append(w)

        return result

    def clear_selection(self) -> None:
        for word in self._words:
            if word.selected:
                word.selected = False
                self._scene.deselect_box(word.widget)

    @override
    def keyPressEvent(self, event: QKeyEvent) -> None:
        if event.key() == Qt.Key.Key_C:
            self.clear_selection()
        elif event.key() == Qt.Key.Key_T:
            selected_words = [word.word.text for word in self._words if word.selected]
            self.analysis_requested.emit(selected_words)
        super().keyPressEvent(event)


class _SelectionCursor:
    def __init__(self, *, initial_radius: int) -> None:
        self._radius = initial_radius
        self._inactive = self._create(self._radius, False)
        self._active = self._create(self._radius, True)

    @staticmethod
    def _create(radius: int, active: bool) -> QCursor:
        cursor_size = radius * 2
        cursor_pixmap = QPixmap(cursor_size, cursor_size)
        cursor_pixmap.fill(Qt.GlobalColor.transparent)

        painter = QPainter(cursor_pixmap)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        brush = QBrush(QColor(255, 0, 0, 100)) if active else QBrush(QColor(128, 128, 128, 100))
        painter.setBrush(brush)

        pen = QPen(QColor(255, 0, 0, 255)) if active else QPen(QColor(128, 128, 128, 255))
        line_width = 1
        pen.setWidth(line_width)
        painter.setPen(pen)

        painter.drawEllipse(QPointF(radius, radius), radius - line_width, radius - line_width)
        painter.end()

        return QCursor(cursor_pixmap, -1, -1)

    def get_cursor(self, active: bool) -> QCursor:
        if active:
            return self._active
        else:
            return self._inactive

    @property
    def radius(self) -> int:
        return self._radius


class _Scene(QGraphicsScene):
    def __init__(self, *, cursor_radius: int) -> None:
        super().__init__()
        self.setBackgroundBrush(QBrush(QColor(0, 0, 0)))
        self.cursor_active = False
        self._cursor_radius = cursor_radius

        self._unselected_pen = QPen(QColor(172, 172, 172, 255))
        self._unselected_pen.setWidth(1)
        self._selected_pen = QPen(QColor(255, 0, 0, 255))
        self._selected_pen.setWidth(1)

    def set_screenshot(self, screenshot: QPixmap) -> None:
        self.addPixmap(screenshot)
        self.setSceneRect(0, 0, screenshot.width(), screenshot.height())

    def add_box(self, polygon: QPolygonF) -> QGraphicsPolygonItem:
        return self.addPolygon(polygon, self._unselected_pen)

    def select_box(self, box: QGraphicsPolygonItem) -> None:
        box.setPen(self._selected_pen)

    def deselect_box(self, box: QGraphicsPolygonItem) -> None:
        box.setPen(self._unselected_pen)
