from typing import override

from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QCloseEvent, QKeyEvent
from PyQt6.QtWidgets import QLabel, QSizePolicy, QVBoxLayout, QWidget


class Spinner(QWidget):
    interrupted = pyqtSignal()

    def __init__(self, parent: QWidget | None = None, embedded: bool = False) -> None:
        super().__init__(parent)
        self._closed_normally = False
        self._embedded = embedded

        if not embedded:
            self.setWindowFlags(
                Qt.WindowType.FramelessWindowHint | Qt.WindowType.Dialog
            )
            if parent:
                self.setWindowModality(Qt.WindowModality.WindowModal)
            else:
                self.setWindowModality(Qt.WindowModality.ApplicationModal)
            self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        else:
            self.setSizePolicy(
                QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding
            )
        self.setCursor(Qt.CursorShape.WaitCursor)

        wrapper_layout = QVBoxLayout()
        wrapper_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        wrapper_layout.setContentsMargins(0, 0, 0, 0)

        card = QWidget()
        card.setObjectName("spinnerCard")
        card.setMinimumWidth(280)
        card.setMinimumHeight(100)
        card.setStyleSheet("""
            #spinnerCard {
                background-color: rgba(0, 0, 0, 0.9);
                border-radius: 16px;
                padding: 24px 48px;
            }
        """)

        card_layout = QVBoxLayout()
        card_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        card_layout.setContentsMargins(0, 0, 0, 0)
        card_layout.setSpacing(12)

        self._label = QLabel("✨ Doing magic ✨")
        self._label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._label.setStyleSheet("""
            font-size: 24px;
            color: white;
        """)
        card_layout.addWidget(self._label)

        self._cancel_label = QLabel("Press Esc to cancel")
        self._cancel_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._cancel_label.setStyleSheet("""
            font-size: 14px;
            color: #E8E8E8;
        """)
        card_layout.addWidget(self._cancel_label)

        card.setLayout(card_layout)
        wrapper_layout.addWidget(card)
        self.setLayout(wrapper_layout)

    # @override
    # def showEvent(self, event: QShowEvent | None) -> None:
    #     super().showEvent(event)
    #     if not self._embedded:
    #         screen = QApplication.primaryScreen().availableGeometry()
    #         spinner_size = self.sizeHint()
    #         x = screen.center().x() - spinner_size.width() // 2
    #         y = screen.center().y() - spinner_size.height() // 2
    #         self.move(x, y)

    @override
    def keyPressEvent(self, event: QKeyEvent) -> None:
        if event.key() == Qt.Key.Key_Escape:
            self.close()
        super().keyPressEvent(event)

    def closeEvent(self, event: QCloseEvent) -> None:
        if not self._closed_normally:
            self.interrupted.emit()
        super().closeEvent(event)

    def close_normally(self) -> None:
        self._closed_normally = True
        self.close()
