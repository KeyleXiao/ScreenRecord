from pathlib import Path
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QLabel, QPushButton, QHBoxLayout,
    QInputDialog, QSlider, QComboBox, QFontComboBox, QSpinBox
)
from PySide6.QtGui import QPixmap, QPainter, QPen, QColor, QFont
from PySide6.QtCore import Qt, QPoint

class ScreenshotEditor(QDialog):
    """Simple dialog to draw and add text on a screenshot."""

    def __init__(self, image_path: Path, parent=None):
        super().__init__(parent)
        self.setWindowTitle('编辑截图')
        self.image_path = image_path
        self.base_pixmap = QPixmap(str(image_path))
        self.overlay = QPixmap(self.base_pixmap.size())
        self.overlay.fill(Qt.transparent)
        self.setFixedSize(self.base_pixmap.size())
        self.last_point: QPoint | None = None
        self.drawing = False
        self.mode = 'draw'
        self.pending_text = ''
        self.pen_width = 2
        self.pen_color = QColor('red')
        self.text_color = QColor('red')
        self.text_size = 14
        self.font_family = QFont().family()

        layout = QVBoxLayout(self)
        self.label = QLabel()
        self.label.setPixmap(self._compose())
        layout.addWidget(self.label)

        btn_layout = QHBoxLayout()
        draw_btn = QPushButton('画笔')
        draw_btn.clicked.connect(self._set_draw_mode)
        text_btn = QPushButton('文字')
        text_btn.clicked.connect(self._prepare_text)
        save_btn = QPushButton('保存')
        save_btn.clicked.connect(self._save)
        btn_layout.addWidget(draw_btn)
        btn_layout.addWidget(text_btn)
        btn_layout.addStretch()
        btn_layout.addWidget(save_btn)
        layout.addLayout(btn_layout)

        control_layout = QHBoxLayout()
        self.width_slider = QSlider(Qt.Horizontal)
        self.width_slider.setRange(1, 20)
        self.width_slider.setValue(self.pen_width)
        self.width_slider.valueChanged.connect(self._update_width)
        self.color_combo = QComboBox()
        for c in ['black', 'red', 'green', 'blue', 'yellow']:
            self.color_combo.addItem(c)
        self.color_combo.setCurrentText('red')
        self.color_combo.currentTextChanged.connect(self._update_pen_color)
        self.font_combo = QFontComboBox()
        self.font_combo.currentFontChanged.connect(self._update_font)
        self.text_size_spin = QSpinBox()
        self.text_size_spin.setRange(8, 72)
        self.text_size_spin.setValue(self.text_size)
        self.text_size_spin.valueChanged.connect(self._update_text_size)
        self.text_color_combo = QComboBox()
        for c in ['black', 'red', 'green', 'blue', 'yellow']:
            self.text_color_combo.addItem(c)
        self.text_color_combo.setCurrentText('red')
        self.text_color_combo.currentTextChanged.connect(self._update_text_color)
        control_layout.addWidget(QLabel('笔宽'))
        control_layout.addWidget(self.width_slider)
        control_layout.addWidget(QLabel('笔色'))
        control_layout.addWidget(self.color_combo)
        control_layout.addWidget(QLabel('字体'))
        control_layout.addWidget(self.font_combo)
        control_layout.addWidget(QLabel('字号'))
        control_layout.addWidget(self.text_size_spin)
        control_layout.addWidget(QLabel('文字颜色'))
        control_layout.addWidget(self.text_color_combo)
        layout.addLayout(control_layout)

    def _compose(self) -> QPixmap:
        result = QPixmap(self.base_pixmap)
        painter = QPainter(result)
        painter.drawPixmap(0, 0, self.overlay)
        painter.end()
        return result

    def _set_draw_mode(self):
        self.mode = 'draw'

    def _prepare_text(self):
        text, ok = QInputDialog.getText(self, '文字', '输入文字:')
        if ok and text:
            self.pending_text = text
            self.mode = 'text'

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            if self.mode == 'draw':
                self.drawing = True
                self.last_point = event.position().toPoint()
            elif self.mode == 'text':
                painter = QPainter(self.overlay)
                pen = QPen(self.text_color)
                painter.setPen(pen)
                font = QFont(self.font_family, self.text_size)
                painter.setFont(font)
                painter.drawText(event.position().toPoint(), self.pending_text)
                painter.end()
                self.mode = 'draw'
                self.pending_text = ''
                self.label.setPixmap(self._compose())
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        if self.drawing and self.last_point is not None:
            painter = QPainter(self.overlay)
            pen = QPen(self.pen_color, self.pen_width)
            painter.setPen(pen)
            painter.drawLine(self.last_point, event.position().toPoint())
            painter.end()
            self.last_point = event.position().toPoint()
            self.label.setPixmap(self._compose())
        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.LeftButton and self.drawing:
            self.drawing = False
            self.last_point = None
        super().mouseReleaseEvent(event)

    def _save(self):
        final = self._compose()
        final.save(str(self.image_path))
        self.accept()

    def _update_width(self, value: int):
        self.pen_width = value

    def _update_pen_color(self, name: str):
        self.pen_color = QColor(name)

    def _update_font(self, font: QFont):
        self.font_family = font.family()

    def _update_text_size(self, size: int):
        self.text_size = size

    def _update_text_color(self, name: str):
        self.text_color = QColor(name)

