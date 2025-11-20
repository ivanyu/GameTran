from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QLabel


class Spinner(QWidget):
    def __init__(self) -> None:
        super().__init__()
        self.setStyleSheet("background-color: black;")
        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)

        self._label = QLabel("Doing magic ✨")
        self._label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._label.setStyleSheet("font-size: 24px; color: white;")
        layout.addWidget(self._label)
        self.setLayout(layout)

    def set_error(self, error: str) -> None:
        self._label.setText(f"Error: {error}")
