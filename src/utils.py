from __future__ import annotations

from pathlib import Path
import time
import imageio.v2 as imageio
from PIL import Image
import mss
from PySide6.QtWidgets import QDialog, QRubberBand
from PySide6.QtCore import Qt, QRect, QPoint, QSize


class RegionSelector(QDialog):
    """Full screen dialog allowing the user to drag-select a rectangle."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowFlags(
            Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint | Qt.Dialog
        )
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setWindowState(Qt.WindowFullScreen)
        self.setCursor(Qt.CrossCursor)
        self.origin = QPoint()
        self.rubber = QRubberBand(QRubberBand.Rectangle, self)
        self.selected: QRect | None = None

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.origin = event.pos()
            self.rubber.setGeometry(QRect(self.origin, QSize()))
            self.rubber.show()

    def mouseMoveEvent(self, event):
        if not self.origin.isNull():
            rect = QRect(self.origin, event.pos()).normalized()
            self.rubber.setGeometry(rect)

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.selected = self.rubber.geometry()
            self.accept()


def select_region(parent=None) -> QRect | None:
    dialog = RegionSelector(parent)
    return dialog.selected if dialog.exec() else None


def take_screenshot(path: Path, region: QRect | None = None) -> Path:
    """Capture a screenshot optionally limited to *region*."""
    path.parent.mkdir(parents=True, exist_ok=True)
    with mss.mss() as sct:
        if region is None:
            screenshot = sct.grab(sct.monitors[0])
        else:
            monitor = {
                "left": region.x(),
                "top": region.y(),
                "width": region.width(),
                "height": region.height(),
            }
            screenshot = sct.grab(monitor)
        img = Image.frombytes("RGB", screenshot.size, screenshot.rgb)
        img.save(path)
    return path

def video_to_gif(video_path: Path, gif_path: Path, fps: int = 10) -> Path:
    reader = imageio.get_reader(str(video_path))
    frames = []
    for frame in reader:
        frames.append(frame)
    imageio.mimsave(gif_path, frames, fps=fps)
    return gif_path

def timestamp_filename(ext: str) -> str:
    return time.strftime('%Y%m%d_%H%M%S') + ext
