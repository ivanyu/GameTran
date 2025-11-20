from typing import Optional, override

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QDialog,
    QLabel,
    QPushButton,
    QVBoxLayout,
    QWidget,
)


class HelpWindow(QDialog):
    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self.setWindowTitle("Help")
        self.setModal(True)
        self.setMinimumWidth(300)

        layout = QVBoxLayout(self)
        layout.addStretch()

        help_text = (
            "<b>Left click:</b> select words.<br>"
            "<b>Right click:</b> deselect words.<br>"
            "<b>Ctrl+Scroll:</b> change selector cursor size.<br>"
            "<b>T:</b> analyze the selected text.<br>"
            "<b>C:</b> clear the selection.<br>"
            "<b>Esc:</b> close and resume the game."
        )
        label = QLabel(help_text, self)
        label.setAlignment(Qt.AlignmentFlag.AlignLeft)
        label.setWordWrap(True)
        label.setTextFormat(Qt.TextFormat.RichText)
        layout.addWidget(label, alignment=Qt.AlignmentFlag.AlignCenter)

        layout.addStretch()

        ok_button = QPushButton("OK", self)
        ok_button.clicked.connect(self.accept)
        layout.addWidget(ok_button, alignment=Qt.AlignmentFlag.AlignCenter)

    @override
    def showEvent(self, event) -> None:
        super().showEvent(event)

        parent = self.parentWidget()
        if not parent:
            return

        self.adjustSize()
        parent_center = parent.frameGeometry().center()
        window_geometry = self.frameGeometry()
        window_geometry.moveCenter(parent_center)
        self.move(window_geometry.topLeft())
