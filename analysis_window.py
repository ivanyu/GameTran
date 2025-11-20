import webbrowser
from typing import override
from urllib.parse import quote

from PyQt6.QtCore import QMargins, QPoint, QRect, QSize, Qt
from PyQt6.QtGui import QAction, QCursor, QKeyEvent
from PyQt6.QtWidgets import (
    QApplication,
    QDialog,
    QHBoxLayout,
    QLayout,
    QLayoutItem,
    QMenu,
    QMessageBox,
    QPushButton,
    QScrollArea,
    QSizePolicy,
    QVBoxLayout,
    QWidget,
)

from analysis import SyntaxAnalysis, Token
from config import Config
from dictionaries import get_dictionaries, get_dictionary_url


class _TokenButton(QPushButton):
    def __init__(self, token: Token, game_language: str, config: Config) -> None:
        super().__init__(token.text.content)
        self._token = token
        self._game_language = game_language
        self._config = config
        interactive = token.partOfSpeech.tag != "PUNCT"
        if interactive:
            color_base: str
            color_hover: str
            color_press: str
            if token.partOfSpeech.tag == "NOUN":
                color_base = "#ffc1c1 "
                color_hover = "#ff7d7d"
                color_press = "#c64242"
            elif token.partOfSpeech.tag == "ADJ":
                color_base = "#c1ffc1"
                color_hover = "#7dff7d"
                color_press = "#42c642"
            elif token.partOfSpeech.tag == "VERB":
                color_base = "#c1c1ff"
                color_hover = "#7d7dff"
                color_press = "#4242c6"
            else:
                color_base = "#c1c1c1"
                color_hover = "#7d7d7d"
                color_press = "#424242"

            self.setStyleSheet(f"""
                QPushButton {{
                    padding: 8px 12px;
                    margin: 4px;
                    background-color: {color_base};
                    border: none;
                    border-radius: 4px;
                    font-size: 16px;
                }}
                QPushButton:hover {{
                    background-color: {color_hover};
                }}
                QPushButton:pressed {{
                    background-color: {color_press};
                }}
            """)
            self.setCursor(Qt.CursorShape.PointingHandCursor)
            self.clicked.connect(self._show_menu)
        else:
            self.setStyleSheet("""
                QPushButton {
                    padding: 8px 12px;
                    margin: 4px;
                    background-color: transparent;
                    border: none;
                    border-radius: 4px;
                    font-size: 16px;
                }
            """)

    def _show_menu(self) -> None:
        menu = QMenu(self)

        menu.addAction(f"Base form: {self._token.lemma}").setDisabled(True)
        menu.addAction(f"Part of speech: {self._token.partOfSpeech.tag}").setDisabled(
            True
        )
        menu.addSeparator()

        for dictionary in get_dictionaries(
            self._game_language, self._config.user_language
        ):
            action = menu.addAction(dictionary.title)
            action.setData(dictionary)

        menu.triggered.connect(self._on_dictionary_selected)

        menu.exec(QCursor.pos())

    def _on_dictionary_selected(self, action: QAction) -> None:
        dictionary = action.data()
        url = get_dictionary_url(
            text=self._token.text.content,
            game_language=self._game_language,
            user_language=self._config.user_language,
            dictionary_id=dictionary.id,
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
        size += QSize(
            2 * self.contentsMargins().top(), 2 * self.contentsMargins().top()
        )
        return size

    def _do_layout(self, rect: QRect, test_only: bool) -> int:
        x = rect.x()
        y = rect.y()
        line_height = 0
        spacing = self.spacing()

        for item in self._item_list:
            style = item.widget().style()
            layout_spacing_x = style.layoutSpacing(
                QSizePolicy.ControlType.PushButton,
                QSizePolicy.ControlType.PushButton,
                Qt.Orientation.Horizontal,
            )
            layout_spacing_y = style.layoutSpacing(
                QSizePolicy.ControlType.PushButton,
                QSizePolicy.ControlType.PushButton,
                Qt.Orientation.Vertical,
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
    def __init__(
        self,
        analysis: SyntaxAnalysis,
        config: Config,
        words: list[str],
        game_language: str,
        parent: QWidget = None,
    ) -> None:
        super().__init__(parent)
        self._analysis = analysis
        self._config = config
        self._words = words
        self._game_language = game_language

        self.setWindowTitle("Analysis")

        main_layout = QVBoxLayout()
        self.setLayout(main_layout)

        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)

        self._token_container = QWidget()
        self._token_layout = _FlowLayout(self._token_container)
        self._token_container.setLayout(self._token_layout)

        for token in analysis.tokens:
            token_button = _TokenButton(token, self._game_language, self._config)
            self._token_layout.addWidget(token_button)

        scroll_area.setWidget(self._token_container)

        self._button_layout = QHBoxLayout()

        self._translate_button = QPushButton("Translate")
        self._translate_button.clicked.connect(self._on_translate_clicked)
        self._button_layout.addWidget(self._translate_button)

        self._ai_button = QPushButton("Explain with ChatGPT")
        self._ai_button.clicked.connect(self._on_explain_with_chatgpt)
        self._button_layout.addWidget(self._ai_button)

        main_layout.addWidget(scroll_area)
        main_layout.addLayout(self._button_layout)

        self._adjust_window_size()

    def _adjust_window_size(self) -> None:
        self._token_container.adjustSize()

        self.resize(630, self.height())
        self._token_container.setFixedWidth(600)
        content_height = self._token_layout.heightForWidth(
            self._token_container.width()
        )

        margins = self.layout().contentsMargins()
        buttons_height = self._button_layout.sizeHint().height()

        total_height = (
            content_height + margins.top() + margins.bottom() + buttons_height + 20
        )

        if self.parent():
            max_height = int(self.parent().height() * 0.8)
        else:
            screen = QApplication.primaryScreen().geometry()
            max_height = int(screen.height() * 0.8)

        new_height = min(total_height, max_height)
        self.resize(self.width(), new_height)

        # Center window on screen.
        screen = QApplication.primaryScreen().geometry()
        x = (screen.width() - self.width()) // 2
        y = (screen.height() - self.height()) // 2
        self.move(x, y)

    def _on_translate_clicked(self) -> None:
        text_encoded = quote(" ".join(self._words))
        game_language = self._game_language
        user_language = self._config.user_language
        url = f"https://translate.google.com/?sl={game_language}&tl={user_language}&text={text_encoded}&op=translate"
        webbrowser.open(url)

    def _on_explain_with_chatgpt(self) -> None:
        text = " ".join(self._words)
        prompt_encoded: str
        # TODO support more languages
        prompt_encoded = quote(
            f"Translate and explain the following phrase from a video game:\n{text}"
        )
        url = f"https://chatgpt.com/?prompt={prompt_encoded}"
        webbrowser.open(url)

    @override
    def keyPressEvent(self, event: QKeyEvent) -> None:
        if event.key() == Qt.Key.Key_Escape:
            self.close()
        super().keyPressEvent(event)
