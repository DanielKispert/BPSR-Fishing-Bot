"""Combined ROI visualizer and region selector overlay.

F11 opens this overlay which shows:
- The capture region (green border, draggable/resizable)
- All detection ROIs drawn inside the capture region

Enter = confirm new region, Esc = cancel (keep current region).
"""

import sys

from PyQt6.QtWidgets import QApplication, QWidget, QLabel
from PyQt6.QtGui import QPainter, QColor, QPen, QFont, QScreen
from PyQt6.QtCore import Qt, QRect, QPoint

from src.fishbot.config.detection_config import DetectionConfig
from src.fishbot.config.screen_config import ScreenConfig


ROI_COLORS = [
    QColor(255, 0, 0, 150), QColor(0, 255, 0, 150), QColor(0, 0, 255, 150),
    QColor(255, 255, 0, 150), QColor(255, 0, 255, 150), QColor(0, 255, 255, 150),
]


class RegionOverlay(QWidget):
    """Fullscreen overlay: draggable capture region + ROI visualization."""

    EDGE_MARGIN = 14

    def __init__(self, screen_config, detection_config):
        super().__init__()
        self.screen_config = screen_config
        self.detection_config = detection_config

        sc = self.screen_config
        self.region = QRect(sc.monitor_x, sc.monitor_y, sc.monitor_width, sc.monitor_height)
        self._drag_mode = None
        self._drag_offset = QPoint()
        self._confirmed = False

        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint |
            Qt.WindowType.WindowStaysOnTopHint
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setMouseTracking(True)

        # Cover the monitor that contains the capture region
        region_center = self.region.center()
        target_screen = None
        for screen in QApplication.screens():
            if screen.geometry().contains(region_center):
                target_screen = screen
                break
        if target_screen:
            self.setScreen(target_screen)
            self.setGeometry(target_screen.geometry())
        self.showFullScreen()

        self._label = QLabel(self)
        self._label.setStyleSheet(
            "color: white; background: rgba(0,0,0,180); padding: 6px 12px; "
            "border-radius: 4px; font-size: 13px;"
        )
        self._update_label()
        self._label.show()

    def _update_label(self):
        r = self.region
        self._label.setText(
            f"Capture Region: {r.width()}x{r.height()} @ ({r.x()}, {r.y()})\n"
            "Drag to move · Drag edges/corners to resize · Enter = confirm · Esc = cancel"
        )
        self._label.adjustSize()
        self._label.move(r.x(), max(0, r.y() - self._label.height() - 4))

    def _hit_test(self, pos):
        r = self.region
        m = self.EDGE_MARGIN
        in_left = abs(pos.x() - r.left()) < m
        in_right = abs(pos.x() - r.right()) < m
        in_top = abs(pos.y() - r.top()) < m
        in_bottom = abs(pos.y() - r.bottom()) < m
        in_x = r.left() - m <= pos.x() <= r.right() + m
        in_y = r.top() - m <= pos.y() <= r.bottom() + m

        if in_top and in_left:
            return "resize_tl"
        if in_top and in_right:
            return "resize_tr"
        if in_bottom and in_left:
            return "resize_bl"
        if in_bottom and in_right:
            return "resize_br"
        if in_top and in_x:
            return "resize_t"
        if in_bottom and in_x:
            return "resize_b"
        if in_left and in_y:
            return "resize_l"
        if in_right and in_y:
            return "resize_r"
        if r.contains(pos):
            return "move"
        return None

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self._drag_mode = self._hit_test(event.pos())
            self._drag_offset = event.pos() - self.region.topLeft()

    def mouseMoveEvent(self, event):
        if self._drag_mode is None:
            hit = self._hit_test(event.pos())
            cursors = {
                "resize_tl": Qt.CursorShape.SizeFDiagCursor,
                "resize_br": Qt.CursorShape.SizeFDiagCursor,
                "resize_tr": Qt.CursorShape.SizeBDiagCursor,
                "resize_bl": Qt.CursorShape.SizeBDiagCursor,
                "resize_t": Qt.CursorShape.SizeVerCursor,
                "resize_b": Qt.CursorShape.SizeVerCursor,
                "resize_l": Qt.CursorShape.SizeHorCursor,
                "resize_r": Qt.CursorShape.SizeHorCursor,
                "move": Qt.CursorShape.SizeAllCursor,
            }
            self.setCursor(cursors.get(hit, Qt.CursorShape.ArrowCursor))
            return

        pos = event.pos()
        r = self.region
        min_size = 200

        if self._drag_mode == "move":
            self.region.moveTopLeft(pos - self._drag_offset)
        elif self._drag_mode == "resize_br":
            r.setBottomRight(QPoint(max(r.left() + min_size, pos.x()), max(r.top() + min_size, pos.y())))
        elif self._drag_mode == "resize_bl":
            r.setBottomLeft(QPoint(min(r.right() - min_size, pos.x()), max(r.top() + min_size, pos.y())))
        elif self._drag_mode == "resize_tr":
            r.setTopRight(QPoint(max(r.left() + min_size, pos.x()), min(r.bottom() - min_size, pos.y())))
        elif self._drag_mode == "resize_tl":
            r.setTopLeft(QPoint(min(r.right() - min_size, pos.x()), min(r.bottom() - min_size, pos.y())))
        elif self._drag_mode == "resize_t":
            r.setTop(min(r.bottom() - min_size, pos.y()))
        elif self._drag_mode == "resize_b":
            r.setBottom(max(r.top() + min_size, pos.y()))
        elif self._drag_mode == "resize_l":
            r.setLeft(min(r.right() - min_size, pos.x()))
        elif self._drag_mode == "resize_r":
            r.setRight(max(r.left() + min_size, pos.x()))

        self._update_label()
        self.update()

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self._drag_mode = None

    def keyPressEvent(self, event):
        if event.key() in (Qt.Key.Key_Return, Qt.Key.Key_Enter):
            self._confirmed = True
            self.close()
        elif event.key() == Qt.Key.Key_Escape:
            self._confirmed = False
            self.close()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        # Dim everything outside the capture region, keep region nearly transparent
        # (alpha=1 so it still captures mouse events — alpha=0 makes clicks fall through)
        outer = self.rect()
        r = self.region
        painter.fillRect(outer.x(), outer.y(), outer.width(), r.top() - outer.y(), QColor(0, 0, 0, 100))
        painter.fillRect(outer.x(), r.top(), r.left() - outer.x(), r.height(), QColor(0, 0, 0, 100))
        painter.fillRect(r.right() + 1, r.top(), outer.right() - r.right(), r.height(), QColor(0, 0, 0, 100))
        painter.fillRect(outer.x(), r.bottom() + 1, outer.width(), outer.bottom() - r.bottom(), QColor(0, 0, 0, 100))
        painter.fillRect(r, QColor(0, 0, 0, 1))

        # Green border for capture region
        painter.setPen(QPen(QColor(0, 255, 0, 200), 3))
        painter.drawRect(self.region)

        # Corner handles
        handle_size = 8
        for corner in [self.region.topLeft(), self.region.topRight(),
                       self.region.bottomLeft(), self.region.bottomRight()]:
            painter.fillRect(
                corner.x() - handle_size // 2, corner.y() - handle_size // 2,
                handle_size, handle_size, QColor(0, 255, 0, 255)
            )

        # Draw ROIs inside the capture region
        r = self.region
        scale_x = r.width() / self.screen_config.REFERENCE_WIDTH
        scale_y = r.height() / self.screen_config.REFERENCE_HEIGHT
        color_idx = 0

        for name, roi in self.detection_config.rois.items():
            if not roi:
                continue
            ref_x, ref_y, ref_w, ref_h = roi
            rx = int(ref_x * scale_x) + r.x()
            ry = int(ref_y * scale_y) + r.y()
            rw = int(ref_w * scale_x)
            rh = int(ref_h * scale_y)

            color = ROI_COLORS[color_idx % len(ROI_COLORS)]
            color_idx += 1

            painter.setPen(QPen(color, 2, Qt.PenStyle.SolidLine))
            painter.drawRect(rx, ry, rw, rh)

            painter.setFont(QFont("Arial", 10, QFont.Weight.Bold))
            painter.drawText(rx + 5, ry + 15, name)

    @property
    def confirmed(self):
        return self._confirmed

    @property
    def result(self):
        r = self.region
        return r.x(), r.y(), r.width(), r.height()


def _run_overlay_process(screen_dict, detection_dict, result_queue):
    """Entry point for the overlay subprocess. Must be a top-level function for pickling."""
    import os
    os.environ["QT_LOGGING_RULES"] = "qt.qpa.window=false"
    os.environ["QT_ENABLE_HIGHDPI_SCALING"] = "0"

    sc = ScreenConfig.__new__(ScreenConfig)
    sc.REFERENCE_WIDTH = screen_dict["ref_w"]
    sc.REFERENCE_HEIGHT = screen_dict["ref_h"]
    sc.monitor_x = screen_dict["monitor_x"]
    sc.monitor_y = screen_dict["monitor_y"]
    sc.monitor_width = screen_dict["monitor_width"]
    sc.monitor_height = screen_dict["monitor_height"]

    dc = DetectionConfig()
    dc.rois = detection_dict["rois"]

    app = QApplication(sys.argv)
    overlay = RegionOverlay(sc, dc)
    app.exec()
    result_queue.put((overlay.confirmed, *overlay.result))


def show_overlay(screen_config=None, detection_config=None):
    """Show the combined region selector + ROI overlay in a subprocess.

    Returns (confirmed, x, y, w, h). Runs in a separate process so Qt
    gets its own main thread and doesn't conflict with existing DPI settings.
    """
    import multiprocessing

    if screen_config is None:
        screen_config = ScreenConfig()
    if detection_config is None:
        detection_config = DetectionConfig()

    screen_dict = {
        "monitor_x": screen_config.monitor_x,
        "monitor_y": screen_config.monitor_y,
        "monitor_width": screen_config.monitor_width,
        "monitor_height": screen_config.monitor_height,
        "ref_w": screen_config.REFERENCE_WIDTH,
        "ref_h": screen_config.REFERENCE_HEIGHT,
    }
    detection_dict = {"rois": detection_config.rois}

    result_queue = multiprocessing.Queue()
    proc = multiprocessing.Process(target=_run_overlay_process, args=(screen_dict, detection_dict, result_queue))
    proc.start()
    proc.join()

    if not result_queue.empty():
        return result_queue.get()
    return False, 0, 0, 0, 0


if __name__ == "__main__":
    import multiprocessing
    multiprocessing.freeze_support()
    confirmed, x, y, w, h = show_overlay()
    if confirmed:
        print(f"Confirmed: {w}x{h} @ ({x}, {y})")
    else:
        print("Cancelled.")


