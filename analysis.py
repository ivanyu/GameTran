import hashlib
import json
import webbrowser
from pathlib import Path
from typing import override

import requests
from pydantic import BaseModel
from PyQt6.QtCore import Qt, QRect, QSize, QPoint, QMargins
from PyQt6.QtGui import QKeyEvent, QCursor, QAction
from PyQt6.QtWidgets import QDialog, QVBoxLayout, QScrollArea, QWidget, QLayout, QLayoutItem, QSizePolicy, QMenu, \
    QPushButton, QMessageBox

from config import Config
from dictionaries import get_dictionaries, get_dictionary_url


class TextSpan(BaseModel):
    content: str
    # beginOffset: int


# class Sentence(BaseModel):
#     text: TextSpan


class PartOfSpeech(BaseModel):
    tag: str
    # aspect: str
    # case: str
    # form: str
    # gender: str
    # mood: str
    # number: str
    # person: str
    # proper: str
    # reciprocity: str
    # tense: str
    # voice: str


# class DependencyEdge(BaseModel):
#     headTokenIndex: int
#     label: str


class Token(BaseModel):
    text: TextSpan
    partOfSpeech: PartOfSpeech
    # dependencyEdge: DependencyEdge
    lemma: str


class SyntaxAnalysis(BaseModel):
    # sentences: list[Sentence]
    tokens: list[Token]
    language: str


class _TokenButton(QPushButton):
    def __init__(self, token: Token, game_language: str, config: Config) -> None:
        super().__init__(token.text.content)
        self._token = token
        self._game_language = game_language
        self._config = config
        self.setStyleSheet("""
            QPushButton {
                padding: 8px 12px;
                margin: 4px;
                background-color: #e0e0e0;
                border: none;
                border-radius: 4px;
                font-size: 16px;
            }
            QPushButton:hover {
                background-color: #c0c0c0;
            }
            QPushButton:pressed {
                background-color: #b0b0b0;
            }
        """)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.clicked.connect(self._show_menu)

    def _show_menu(self) -> None:
        menu = QMenu(self)

        menu.addAction(f"Lemma: {self._token.lemma}").setDisabled(True)
        menu.addAction(f"Part of speech: {self._token.partOfSpeech.tag}").setDisabled(True)
        menu.addSeparator()

        for dictionary in get_dictionaries(self._game_language, self._config.user_language()):
            action = menu.addAction(dictionary.title)
            action.setData(dictionary)

        menu.triggered.connect(self._on_dictionary_selected)

        menu.exec(QCursor.pos())

    def _on_dictionary_selected(self, action: QAction) -> None:
        dictionary = action.data()
        url = get_dictionary_url(
            text=self._token.text.content,
            game_language=self._game_language,
            user_language=self._config.user_language(),
            dictionary_id=dictionary.id
        )
        if url:
            webbrowser.open(url)
        else:
            QMessageBox.critical(self, "URL not found", "URL not found")


class _FlowLayout(QLayout):
    # https://doc.qt.io/qtforpython-6/examples/example_widgets_layouts_flowlayout.html

    def __init__(self, parent=None) -> None:
        super().__init__(parent)

        if parent is not None:
            self.setContentsMargins(QMargins(0, 0, 0, 0))

        self._item_list: list[QLayoutItem] = []

    def __del__(self) -> None:
        item = self.takeAt(0)
        while item:
            item = self.takeAt(0)

    @override
    def addItem(self, item: QLayoutItem) -> None:
        self._item_list.append(item)

    @override
    def count(self) -> int:
        return len(self._item_list)

    @override
    def itemAt(self, index: int) -> QLayoutItem | None:
        if 0 <= index < len(self._item_list):
            return self._item_list[index]
        return None

    @override
    def takeAt(self, index: int) -> QLayoutItem | None:
        if 0 <= index < len(self._item_list):
            return self._item_list.pop(index)
        return None

    @override
    def expandingDirections(self) -> Qt.Orientation:
        return Qt.Orientation(0)

    @override
    def hasHeightForWidth(self) -> bool:
        return True

    @override
    def heightForWidth(self, width: int) -> int:
        height = self._do_layout(QRect(0, 0, width, 0), True)
        return height

    @override
    def setGeometry(self, rect: QRect) -> None:
        super().setGeometry(rect)
        self._do_layout(rect, False)

    @override
    def sizeHint(self) -> QSize:
        return self.minimumSize()

    @override
    def minimumSize(self) -> QSize:
        size = QSize()
        for item in self._item_list:
            size = size.expandedTo(item.minimumSize())
        size += QSize(2 * self.contentsMargins().top(), 2 * self.contentsMargins().top())
        return size

    def _do_layout(self, rect: QRect, test_only: bool) -> int:
        x = rect.x()
        y = rect.y()
        line_height = 0
        spacing = self.spacing()

        for item in self._item_list:
            style = item.widget().style()
            layout_spacing_x = style.layoutSpacing(
                QSizePolicy.ControlType.PushButton, QSizePolicy.ControlType.PushButton,
                Qt.Orientation.Horizontal
            )
            layout_spacing_y = style.layoutSpacing(
                QSizePolicy.ControlType.PushButton, QSizePolicy.ControlType.PushButton,
                Qt.Orientation.Vertical
            )
            space_x = spacing + layout_spacing_x
            space_y = spacing + layout_spacing_y
            next_x = x + item.sizeHint().width() + space_x
            if next_x - space_x > rect.right() and line_height > 0:
                x = rect.x()
                y = y + line_height + space_y
                next_x = x + item.sizeHint().width() + space_x
                line_height = 0

            if not test_only:
                item.setGeometry(QRect(QPoint(x, y), item.sizeHint()))

            x = next_x
            line_height = max(line_height, item.sizeHint().height())

        return y + line_height - rect.y()


class AnalysisWindow(QDialog):
    def __init__(self, config: Config) -> None:
        super().__init__()
        self._config = config
        self._words: list[str] = []

        self.setWindowTitle("Analysis")
        self.resize(800, 600)

        main_layout = QVBoxLayout()

        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)

        self._token_container = QWidget()
        self._token_layout = _FlowLayout(self._token_container)
        self._token_container.setLayout(self._token_layout)

        scroll_area.setWidget(self._token_container)
        main_layout.addWidget(scroll_area)

        self.setLayout(main_layout)

    @override
    def keyPressEvent(self, event: QKeyEvent) -> None:
        if event.key() == Qt.Key.Key_Escape:
            self.close()
        super().keyPressEvent(event)

    def init(self, words: list[str], game_language: str) -> None:
        self._words = words

        content = " ".join(words)
        document = {
            "document": {
                "content": content,
                "language": game_language,
                "type": "PLAIN_TEXT"
            },
            "encodingType": "UTF8"
        }
        document_str = json.dumps(document)

        # TODO make async
        hash_bytes = hashlib.sha256(document_str.encode()).digest()
        hash_hex = hash_bytes.hex()
        cache_path = Path(f"dev/analysis_cache/{hash_hex}.json")
        if cache_path.exists():
            with open(cache_path, "r", encoding="utf-8") as f:
                result_dict = json.load(f)
        else:
            response = requests.post(
                "https://language.googleapis.com/v1/documents:analyzeSyntax",
                data=document_str,
                headers={
                    "Content-Type": "application/json",
                    "X-goog-api-key": self._config.google_api_key()
                }
            )
            result_dict = response.json()

            cache_path.parent.mkdir(parents=True, exist_ok=True)
            with open(cache_path, "w", encoding="utf-8") as f:
                json.dump(result_dict, f, ensure_ascii=False, indent=2)

        analysis = SyntaxAnalysis.model_validate(result_dict)

        while self._token_layout.count():
            item = self._token_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        for token in analysis.tokens:
            token_button = _TokenButton(token, game_language, self._config)
            self._token_layout.addWidget(token_button)
