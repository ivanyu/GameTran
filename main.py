import sys
from typing import override, Optional

from PyQt6.QtCore import Qt
from PyQt6.QtGui import QKeyEvent
from PyQt6.QtWidgets import QApplication, QMainWindow

from config import Config
from ocr import OcrWorker, OCRResult
from overlay import Overlay
from screenshot import take_screenshot
from spinner import Spinner
from analysis import AnalysisWindow


class MainWindow(QMainWindow):
    def __init__(self) -> None:
        super().__init__()
        self.setContentsMargins(0, 0, 0, 0)

        self.spinner = Spinner()
        self.setCentralWidget(self.spinner)
        # self.showFullScreen()

        self._screenshot = take_screenshot()
        self.ocr_worker = OcrWorker(self._screenshot, target_height=1080)
        self.ocr_worker.finished.connect(self._on_ocr_finished)
        self.ocr_worker.error.connect(self.spinner.set_error)
        self.ocr_worker.start()

        self._config = Config()
        self._analysis_window = AnalysisWindow(self._config)

        self._ocr: Optional[OCRResult] = None


        self._analysis_window.init(['Il', "s'agit", 'du', 'registre', 'que', 'vous', 'avez', 'trouvé', 'dans', 'la', 'benne', 'à', 'ordure', '.'], "fr")
        self._analysis_window.exec()

    def _on_ocr_finished(self, ocr: OCRResult) -> None:
        self._ocr = ocr

        overlay = Overlay()
        overlay.set_screenshot(self._screenshot)
        overlay.set_ocr(ocr)
        overlay.analysis_requested.connect(self._on_analysis_requested)
        self.setCentralWidget(overlay)
        overlay.setFocus()

    def _on_analysis_requested(self, words: list[str]) -> None:
        if self._ocr:
            self._analysis_window.init(words, self._ocr.detectedLanguage)
            self._analysis_window.exec()

    @override
    def keyPressEvent(self, event: QKeyEvent) -> None:
        if event.key() in {Qt.Key.Key_Escape, Qt.Key.Key_Q}:
            self.close()
        super().keyPressEvent(event)


def main() -> None:
    app = QApplication(sys.argv)
    viewer = MainWindow()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
