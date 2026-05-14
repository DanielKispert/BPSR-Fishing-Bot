import sys
import os
import multiprocessing
from PyQt6.QtWidgets import QApplication, QWidget
from PyQt6.QtGui import QPainter, QColor, QPen, QFont
from PyQt6.QtCore import Qt, QRect

# Imports detection settings from your project
from src.fishbot.config.detection_config import DetectionConfig
from src.fishbot.config.screen_config import ScreenConfig

# Disable Qt's automatic DPI scaling so pixel coordinates match pywinctl/mss
os.environ["QT_ENABLE_HIGHDPI_SCALING"] = "0"

class RoiVisualizer(QWidget):
    def __init__(self):
        super().__init__()
        self.detection_config = DetectionConfig()
        self.screen_config = ScreenConfig()

        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint |
            Qt.WindowType.WindowStaysOnTopHint |
            Qt.WindowType.WindowTransparentForInput
        )

        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)

        self.showFullScreen()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        colors = [QColor(255, 0, 0, 150), QColor(0, 255, 0, 150), QColor(0, 0, 255, 150),
                  QColor(255, 255, 0, 150), QColor(255, 0, 255, 150), QColor(0, 255, 255, 150)]
        color_index = 0

        for name, roi in self.detection_config.rois.items():
            if not roi:
                continue

            ref_x, ref_y, ref_w, ref_h = roi
            scale_x = self.screen_config.monitor_width / self.screen_config.REFERENCE_WIDTH
            scale_y = self.screen_config.monitor_height / self.screen_config.REFERENCE_HEIGHT
            x = int(ref_x * scale_x) + self.screen_config.monitor_x
            y = int(ref_y * scale_y) + self.screen_config.monitor_y
            w = int(ref_w * scale_x)
            h = int(ref_h * scale_y)
            color = colors[color_index % len(colors)]
            color_index += 1

            pen = QPen(color, 2, Qt.PenStyle.SolidLine)
            painter.setPen(pen)
            painter.drawRect(x, y, w, h)

            font = QFont("Arial", 10, QFont.Weight.Bold)
            painter.setFont(font)
            painter.drawText(x + 5, y + 15, name)

    def keyPressEvent(self, event):
        if event.key() == Qt.Key.Key_Escape:
            self.close()

def main():
    print("Starting ROI visualizer (PyQt)...")
    print("Press the 'Esc' key to close the window.")
    
    app = QApplication(sys.argv)
    visualizer = RoiVisualizer()
    visualizer.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    multiprocessing.freeze_support()
    main()