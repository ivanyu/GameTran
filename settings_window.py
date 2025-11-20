import webbrowser
from typing import override

from PyQt6.QtCore import QObject, Qt
from PyQt6.QtWidgets import (
    QComboBox,
    QDialog,
    QFormLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QVBoxLayout,
)

from config import Config


class SettingsWindow(QDialog):
    def __init__(self, config: Config, parent: QObject | None = None) -> None:
        super().__init__(parent)
        self._config = config

        self.setWindowTitle("Settings")
        self.setMinimumWidth(500)

        layout = QVBoxLayout(self)

        form_layout = QFormLayout()

        self._user_language_input = QLineEdit()
        self._user_language_input.setPlaceholderText("e.g., en, ja, es")
        form_layout.addRow("User Language:", self._user_language_input)

        api_key_layout = QHBoxLayout()
        api_key_layout.setSpacing(8)

        self._google_api_key_input = QLineEdit()
        self._google_api_key_input.setEchoMode(QLineEdit.EchoMode.Password)
        self._google_api_key_input.setPlaceholderText("Enter your Google Cloud API key")
        self._google_api_key_input.textChanged.connect(
            self._update_api_key_field_styling
        )
        api_key_layout.addWidget(self._google_api_key_input)

        api_key_help_link = QLabel(
            '<a style="text-decoration: underline; color: #0066cc;" href="#">how to create</a>'
        )
        api_key_help_link.setCursor(Qt.CursorShape.PointingHandCursor)
        api_key_help_link.linkActivated.connect(
            lambda: webbrowser.open(
                "https://github.com/ivanyu/GameTran/blob/main/docs/api_key.md"
            )
        )
        api_key_layout.addWidget(api_key_help_link)

        form_layout.addRow("Google Cloud API Key:", api_key_layout)

        self._global_hotkey_input = QLineEdit()
        self._global_hotkey_input.setPlaceholderText("e.g., <alt>+p, <ctrl>+<shift>+s")
        form_layout.addRow("Global Hotkey:", self._global_hotkey_input)

        self._prompt_language_combo = QComboBox()
        self._prompt_language_combo.addItem("en")
        form_layout.addRow("Prompt Language:", self._prompt_language_combo)

        layout.addLayout(form_layout)

        button_layout = QHBoxLayout()
        button_layout.addStretch()

        self._save_button = QPushButton("Save")
        self._save_button.clicked.connect(self._on_save)
        button_layout.addWidget(self._save_button)

        self._cancel_button = QPushButton("Cancel")
        self._cancel_button.clicked.connect(self.reject)
        button_layout.addWidget(self._cancel_button)

        layout.addLayout(button_layout)

        self._user_language_input.setText(self._config.user_language)
        self._google_api_key_input.setText(self._config.google_api_key)
        self._global_hotkey_input.setText(self._config.global_hotkey)

        # Set current prompt language value
        index = self._prompt_language_combo.findText(self._config.prompt_language)
        if index >= 0:
            self._prompt_language_combo.setCurrentIndex(index)

        self._update_api_key_field_styling()

    def _update_api_key_field_styling(self, text: str = "") -> None:
        if not self._google_api_key_input.text().strip():
            self._google_api_key_input.setStyleSheet(
                "QLineEdit { border: 2px solid #e74c3c; background-color: #fde8e8; }"
            )
        else:
            self._google_api_key_input.setStyleSheet("")

    def _on_save(self) -> None:
        self._config.user_language = self._user_language_input.text()
        self._config.google_api_key = self._google_api_key_input.text()
        self._config.global_hotkey = self._global_hotkey_input.text()
        self._config.prompt_language = self._prompt_language_combo.currentText()
        self.accept()

    @override
    def keyPressEvent(self, event) -> None:
        if event.key() == Qt.Key.Key_Return or event.key() == Qt.Key.Key_Enter:
            self._on_save()
        elif event.key() == Qt.Key.Key_Escape:
            self.reject()
        else:
            super().keyPressEvent(event)
