import sys
import json
from PyQt6.QtWidgets import QApplication, QMainWindow, QGraphicsView, QGraphicsScene
from PyQt6.QtGui import QPixmap, QKeyEvent, QPen, QPolygonF, QColor
from PyQt6.QtCore import Qt, QPointF


class ImageViewer(QMainWindow):
    def __init__(self) -> None:
        super().__init__()
        self.init_ui()

    def init_ui(self) -> None:
        # Create graphics view and scene
        self.scene = QGraphicsScene(self)
        self.view = QGraphicsView(self.scene, self)
        self.setCentralWidget(self.view)

        # Load and display image
        pixmap = QPixmap("dev/screenshots/screen_atom_0.png")
        self.scene.addPixmap(pixmap)

        # Load OCR data and draw bounding boxes
        self.load_and_draw_bounding_boxes()

        # Set window to fullscreen
        self.showFullScreen()

    def load_and_draw_bounding_boxes(self) -> None:
        # Load OCR cache JSON
        ocr_file = "dev/ocr_cache/18ba1504a6092b1c2ba0ab6f276ad1eedd637c15bf529a2b16d90eca0a2dfb99.json"
        with open(ocr_file, 'r', encoding='utf-8') as f:
            ocr_data = json.load(f)

        # Create pen for drawing rectangles
        pen = QPen(QColor(255, 0, 0, 180))  # Red with transparency
        pen.setWidth(2)

        # Draw bounding box for each word
        for word in ocr_data.get('words', []):
            bbox = word['boundingBox']
            # Convert bounding box points to QPolygonF
            polygon = QPolygonF([
                QPointF(point['x'], point['y']) for point in bbox
            ])
            # Add polygon to scene
            polygon_item = self.scene.addPolygon(polygon, pen)
            # Make it possible to interact with in the future
            polygon_item.setFlag(polygon_item.GraphicsItemFlag.ItemIsSelectable)

    def keyPressEvent(self, event: QKeyEvent) -> None:
        # Exit on Esc key
        if event.key() == Qt.Key.Key_Escape:
            self.close()


def main() -> None:
    app = QApplication(sys.argv)
    viewer = ImageViewer()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
