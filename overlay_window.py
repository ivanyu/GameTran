from dataclasses import dataclass
from typing import Final, override

from PyQt6.QtCore import QPointF, QRectF, Qt, pyqtSignal
from PyQt6.QtGui import (
    QBrush,
    QCloseEvent,
    QColor,
    QCursor,
    QHideEvent,
    QKeyEvent,
    QMouseEvent,
    QPainter,
    QPainterPath,
    QPalette,
    QPen,
    QPixmap,
    QPolygonF,
    QWheelEvent,
)
from PyQt6.QtWidgets import (
    QApplication,
    QFrame,
    QGraphicsPolygonItem,
    QGraphicsScene,
    QGraphicsView,
    QHBoxLayout,
    QLabel,
    QMainWindow,
    QMenu,
    QMessageBox,
    QPushButton,
    QWidget,
)

from analysis import AnalysisWorker, SyntaxAnalysis
from analysis_window import AnalysisWindow
from assets import load_icon, load_pixmap
from config import Config
from help_window import HelpWindow
from ocr import OCRResult, OcrWorker
from ocr import Word as OcrWord
from screenshot import Screenshot
from spinner import Spinner


@dataclass(slots=True, kw_only=True)
class _Word:
    widget: QGraphicsPolygonItem
    word: OcrWord
    selected: bool


class _Overlay(QGraphicsView):
    _DEFAULT_CURSOR_RADIUS: Final = 15

    def __init__(self) -> None:
        self._scene = _Scene()
        super().__init__(self._scene)
        self._cursor = _SelectionCursor(initial_radius=self._DEFAULT_CURSOR_RADIUS)
        self._loading = False

        # Remove frame and margins.
        self.setFrameShape(QGraphicsView.Shape.NoFrame)
        self.setContentsMargins(0, 0, 0, 0)

        self.setCursor(self._cursor.get_cursor(False))

        self._words: list[_Word] = []

    def set_screenshot(self, screenshot: Screenshot) -> None:
        self._scene.set_screenshot(screenshot)

    def set_ocr(self, ocr: OCRResult) -> None:
        for word in ocr.words:
            polygon = QPolygonF(
                [QPointF(vertex.x, vertex.y) for vertex in word.boundingBox]
            )
            polygon_widget = self._scene.add_box(polygon)
            self._words.append(_Word(widget=polygon_widget, word=word, selected=False))

    @override
    def mousePressEvent(self, event: QMouseEvent | None) -> None:
        if event.button() == Qt.MouseButton.LeftButton:
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
    def mouseReleaseEvent(self, event: QMouseEvent | None) -> None:
        if event.button() == Qt.MouseButton.LeftButton:
            self.setCursor(self._cursor.get_cursor(False))

        super().mouseReleaseEvent(event)

    @override
    def mouseMoveEvent(self, event: QMouseEvent | None) -> None:
        if event.buttons() & Qt.MouseButton.LeftButton:
            for word in self._find_collisions_at_point(event.position()):
                word.selected = True
                self._scene.select_box(word.widget)
        elif event.buttons() & Qt.MouseButton.RightButton:
            for word in self._find_collisions_at_point(event.position()):
                word.selected = False
                self._scene.deselect_box(word.widget)

        super().mouseMoveEvent(event)

    @override
    def wheelEvent(self, event: QWheelEvent | None) -> None:
        if event.modifiers() & Qt.KeyboardModifier.ControlModifier:
            delta = event.angleDelta().y()
            if delta > 0:
                new_radius = min(self._cursor.radius + 1, 50)
            else:
                new_radius = max(self._cursor.radius - 1, 3)

            if new_radius != self._cursor.radius:
                self._cursor.set_radius(new_radius)
                is_active = bool(event.buttons() & Qt.MouseButton.LeftButton)
                self.setCursor(self._cursor.get_cursor(is_active))
            event.accept()
        super().wheelEvent(event)

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
            actual_radius * 2,
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

    def start_loading(self) -> None:
        self._loading = True
        self.setCursor(Qt.CursorShape.WaitCursor)

    def finish_loading(self) -> None:
        self._loading = False
        self.setCursor(self._cursor.get_cursor(False))

    def get_selection(self) -> list[str]:
        return [word.word.text for word in self._words if word.selected]


class _DragHandle(QLabel):
    def __init__(self, *, parent: QWidget) -> None:
        super().__init__(parent)
        self.setPixmap(load_pixmap("ic_fluent_re_order_vertical_16_regular.svg"))
        self.setCursor(Qt.CursorShape.OpenHandCursor)
        # self.setFrameShape(QFrame.Shape.StyledPanel)
        # self.setLineWidth(1)

    @override
    def mousePressEvent(self, event: QMouseEvent) -> None:
        if event.button() == Qt.MouseButton.LeftButton:
            self.setCursor(Qt.CursorShape.ClosedHandCursor)
        super().mousePressEvent(event)

    @override
    def mouseReleaseEvent(self, event: QMouseEvent) -> None:
        if event.button() == Qt.MouseButton.LeftButton:
            self.setCursor(Qt.CursorShape.OpenHandCursor)
        super().mouseReleaseEvent(event)


class _FloatingToolbar(QFrame):
    analysis_requested = pyqtSignal()
    close_and_resume_requested = pyqtSignal()
    clear_selection_requested = pyqtSignal()
    save_screenshot_requested = pyqtSignal()

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setFrameShape(QFrame.Shape.Box)
        self.setFrameShadow(QFrame.Shadow.Plain)

        self.setObjectName("floating_toolbar")
        bg_color_semitransparent = QColor(
            self.palette().color(QPalette.ColorRole.Window)
        )
        bg_color_semitransparent.setAlphaF(0.3)
        self.setStyleSheet(f"""
            QWidget#floating_toolbar {{
                background-color: {bg_color_semitransparent.name(QColor.NameFormat.HexArgb)};
            }}
        """)

        self._drag_position = QPointF()
        self._dragging = False

        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        self._drag_handle = _DragHandle(parent=self)
        layout.addWidget(self._drag_handle)

        button_container = QWidget()
        button_layout = QHBoxLayout(button_container)
        button_layout.setContentsMargins(
            0, 4, 4, 4
        )  # 0 at left to bring drag handle close
        button_layout.setSpacing(2)

        self._translate_btn = QPushButton()
        self._translate_btn.setIcon(load_icon("ic_fluent_translate_32_light.svg"))
        self._translate_btn.setToolTip("Translate/analyze (T)")
        self._translate_btn.clicked.connect(self.analysis_requested.emit)
        button_layout.addWidget(self._translate_btn)

        self._close_and_resume = QPushButton()
        self._close_and_resume.setIcon(load_icon("ic_fluent_play_24_regular.svg"))
        self._close_and_resume.setToolTip("Close and resume game (Esc)")
        self._close_and_resume.clicked.connect(self.close_and_resume_requested.emit)
        button_layout.addWidget(self._close_and_resume)

        menu = QMenu(self)
        menu.addAction("Left click: Select").setEnabled(False)
        menu.addAction("Right click: Deselect").setEnabled(False)
        menu.addAction("Scroll+↑: Grow cursor").setEnabled(False)
        menu.addAction("Scroll+↓: Shrink cursor").setEnabled(False)
        menu.addSeparator()

        clear_action = menu.addAction("Clear selection (C)")
        clear_action.triggered.connect(self.clear_selection_requested.emit)

        save_screenshot_action = menu.addAction("Save screenshot")
        save_screenshot_action.triggered.connect(self.save_screenshot_requested.emit)

        def show_drop_down_menu() -> None:
            button_pos = self._drop_down_btn.mapToGlobal(
                self._drop_down_btn.rect().bottomLeft()
            )
            menu.exec(button_pos)

        self._drop_down_btn = QPushButton()
        self._drop_down_btn.setIcon(
            load_icon("ic_fluent_chevron_double_down_20_regular.svg")
        )
        self._drop_down_btn.setToolTip("More...")
        self._drop_down_btn.clicked.connect(show_drop_down_menu)
        button_layout.addWidget(self._drop_down_btn)

        layout.addWidget(button_container)

        self.adjustSize()

    @override
    def mousePressEvent(self, event: QMouseEvent | None) -> None:
        if event.button() == Qt.MouseButton.LeftButton:
            if self._drag_handle.geometry().contains(event.pos()):
                self._dragging = True
                self._drag_position = event.globalPosition() - QPointF(
                    self.pos().x(), self.pos().y()
                )
                event.accept()
                return
        super().mousePressEvent(event)

    @override
    def mouseMoveEvent(self, event: QMouseEvent | None) -> None:
        if self._dragging and event.buttons() & Qt.MouseButton.LeftButton:
            new_pos = event.globalPosition() - self._drag_position

            if self.parent():
                parent_rect = self.parent().rect()
                toolbar_rect = self.rect()
                # Constrain coordinates.
                new_x = max(
                    0, min(new_pos.x(), parent_rect.width() - toolbar_rect.width())
                )
                new_y = max(
                    0, min(new_pos.y(), parent_rect.height() - toolbar_rect.height())
                )
                self.move(int(new_x), int(new_y))
                event.accept()
                return
        super().mouseMoveEvent(event)

    @override
    def mouseReleaseEvent(self, event: QMouseEvent | None) -> None:
        if event.button() == Qt.MouseButton.LeftButton:
            self._dragging = False
            event.accept()
            return
        super().mouseReleaseEvent(event)


class OverlayWindow(QMainWindow):
    got_focus = pyqtSignal()
    before_overlay_hidden = pyqtSignal()
    session_ended = pyqtSignal()
    save_screenshot_requested = pyqtSignal()

    def __init__(self, config: Config) -> None:
        super().__init__()
        self.setContentsMargins(0, 0, 0, 0)
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint)

        self._config = config

        self._toolbar = _FloatingToolbar(self)
        self._toolbar.analysis_requested.connect(self._on_analysis_requested)
        self._toolbar.close_and_resume_requested.connect(self._on_close_and_resume)
        self._toolbar.clear_selection_requested.connect(self._on_clear_selection)
        self._toolbar.save_screenshot_requested.connect(
            self.save_screenshot_requested.emit
        )
        self._toolbar.show()
        # Will be adjusted in showEvent
        self._toolbar.move(0, 0)

        self._ocr_spinner: Spinner | None = None
        self._analysis_spinner: Spinner | None = None

        self._ocr: OCRResult | None = None
        self._overlay: _Overlay | None = None
        self._ocr_worker: OcrWorker | None = None

        self._analysis_window: AnalysisWindow | None = None

    def start_session(self, screenshot: Screenshot) -> None:
        self._overlay = _Overlay()
        self.setCentralWidget(self._overlay)
        self._toolbar.raise_()

        self._ocr_spinner = Spinner(self)
        self._ocr_spinner.showFullScreen()
        self._ocr_spinner.interrupted.connect(self.close)

        self._overlay.set_screenshot(screenshot)
        self._overlay.start_loading()

        self._ocr_worker = OcrWorker(
            screenshot.pixmap, target_height=1080, config=self._config
        )
        self._ocr_worker.finished.connect(self._on_ocr_finished)
        self._ocr_worker.error.connect(self._on_ocr_error)
        self._ocr_worker.start()

    def end_session(self) -> None:
        if self._overlay:
            self._overlay.deleteLater()
            self._overlay = None
            self.setCentralWidget(None)
        if self._ocr_worker:
            self._ocr_worker.stop()
            self._ocr_worker = None
        if self._ocr_spinner and self._ocr_spinner.isVisible():
            self._ocr_spinner.close_normally()
        if self._analysis_window:
            self._analysis_window.close()
            self._analysis_window.deleteLater()
            self._analysis_window = None
        self.session_ended.emit()

    @override
    def showEvent(self, event) -> None:
        super().showEvent(event)
        # Center toolbar at top after window is shown
        self._position_toolbar_top_center()

    @override
    def resizeEvent(self, event) -> None:
        super().resizeEvent(event)
        # Reposition toolbar to maintain top-center position on resize
        self._position_toolbar_top_center()

    def _position_toolbar_top_center(self) -> None:
        """Position the toolbar at the top-center of the window."""
        if self._toolbar:
            toolbar_width = self._toolbar.width()
            window_width = self.width()
            x = (window_width - toolbar_width) // 2
            self._toolbar.move(x, 0)

    @override
    def focusInEvent(self, event) -> None:
        super().focusInEvent(event)
        self.got_focus.emit()

    def _on_ocr_finished(self, ocr: OCRResult) -> None:
        self._ocr = ocr

        self._overlay.set_ocr(ocr)
        self._overlay.finish_loading()
        if self._ocr_spinner:
            self._ocr_spinner.close_normally()
            self._ocr_spinner.deleteLater()
            self._ocr_spinner = None

    def _on_ocr_error(self, error: str) -> None:
        message_box = QMessageBox(self)
        message_box.setIcon(QMessageBox.Icon.Critical)
        message_box.setText(error)
        message_box.setWindowTitle("Error")
        message_box.setWindowModality(Qt.WindowModality.ApplicationModal)

        message_box.adjustSize()
        screen_center = QApplication.primaryScreen().availableGeometry().center()
        box_rect = message_box.frameGeometry()
        box_rect.moveCenter(screen_center)
        message_box.move(box_rect.topLeft())

        message_box.exec()
        self.close()

    @override
    def keyPressEvent(self, event: QKeyEvent) -> None:
        if event.key() == Qt.Key.Key_T:
            self._on_analysis_requested()
        elif event.key() == Qt.Key.Key_Escape:
            self._on_close_and_resume()
        elif event.key() == Qt.Key.Key_C:
            self._on_clear_selection()
        elif event.key() == Qt.Key.Key_F1:
            help_window = HelpWindow(self)
            help_window.exec()
        super().keyPressEvent(event)

    def _on_analysis_requested(self) -> None:
        if self._ocr is None:
            return

        words = self._overlay.get_selection()
        if not words:
            return

        self._analysis_worker = AnalysisWorker(
            content=" ".join(words),
            game_language=self._ocr.detectedLanguage,
            config=self._config,
        )
        self._analysis_worker.finished.connect(
            lambda analysis: self._on_analysis_finished(analysis, words)
        )
        self._analysis_worker.error.connect(self._on_analysis_error)
        self._analysis_worker.start()

        self._analysis_spinner = Spinner(self)
        self._analysis_spinner.showFullScreen()
        self._analysis_spinner.interrupted.connect(self._analysis_worker.interrupt)

    def _on_analysis_finished(self, analysis: SyntaxAnalysis, words: list[str]) -> None:
        self._hide_analysis_spinner()
        self._analysis_window = AnalysisWindow(
            analysis=analysis,
            config=self._config,
            words=words,
            game_language=self._ocr.detectedLanguage,
            parent=self,
        )
        self._analysis_window.exec()

    def _on_analysis_error(self, error: str) -> None:
        message_box = QMessageBox(self)
        message_box.setIcon(QMessageBox.Icon.Critical)
        message_box.setText(error)
        message_box.setWindowTitle("Error")
        message_box.setWindowModality(Qt.WindowModality.ApplicationModal)

        message_box.adjustSize()
        screen_center = QApplication.primaryScreen().availableGeometry().center()
        box_rect = message_box.frameGeometry()
        box_rect.moveCenter(screen_center)
        message_box.move(box_rect.topLeft())

        message_box.exec()
        self._hide_analysis_spinner()

    def _hide_analysis_spinner(self) -> None:
        if self._analysis_spinner:
            self._analysis_spinner.close_normally()
            self._analysis_spinner.deleteLater()
            self._analysis_spinner = None

    def _on_close_and_resume(self) -> None:
        self.hide()

    @override
    def hideEvent(self, event: QHideEvent) -> None:
        self.before_overlay_hidden.emit()
        self.end_session()
        print("Hiding overlay window")
        super().hideEvent(event)

    @override
    def closeEvent(self, event: QCloseEvent) -> None:
        self.hide()
        # Don't propagate.

    def _on_clear_selection(self) -> None:
        self._overlay.clear_selection()


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

        brush = (
            QBrush(QColor(255, 0, 0, 100))
            if active
            else QBrush(QColor(128, 128, 128, 100))
        )
        painter.setBrush(brush)

        pen = (
            QPen(QColor(255, 0, 0, 255)) if active else QPen(QColor(128, 128, 128, 255))
        )
        line_width = 1
        pen.setWidth(line_width)
        painter.setPen(pen)

        painter.drawEllipse(
            QPointF(radius, radius), radius - line_width, radius - line_width
        )
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

    def set_radius(self, radius: int) -> None:
        self._radius = radius
        self._inactive = self._create(self._radius, False)
        self._active = self._create(self._radius, True)


class _Scene(QGraphicsScene):
    def __init__(self) -> None:
        super().__init__()
        self.setBackgroundBrush(QBrush(QColor(0, 0, 0)))
        self.cursor_active = False

        self._unselected_pen = QPen(QColor(172, 172, 172, 255))
        self._unselected_pen.setWidth(1)
        self._selected_pen = QPen(QColor(255, 0, 0, 255))
        self._selected_pen.setWidth(1)

    def set_screenshot(self, screenshot: Screenshot) -> None:
        self.addPixmap(screenshot.pixmap)

        # Use logical dimensions (device-independent pixels).
        logical_width = screenshot.pixmap.width() / screenshot.device_pixel_ratio
        logical_height = screenshot.pixmap.height() / screenshot.device_pixel_ratio
        self.setSceneRect(0, 0, logical_width, logical_height)

    def add_box(self, polygon: QPolygonF) -> QGraphicsPolygonItem:
        return self.addPolygon(polygon, self._unselected_pen)

    def select_box(self, box: QGraphicsPolygonItem) -> None:
        box.setPen(self._selected_pen)

    def deselect_box(self, box: QGraphicsPolygonItem) -> None:
        box.setPen(self._unselected_pen)
