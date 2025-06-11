from pathlib import Path
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QLabel, QPushButton, QHBoxLayout,
    QSlider, QComboBox, QFontComboBox, QSpinBox, QTextEdit
)
from PySide6.QtGui import QPixmap, QPainter, QPen, QColor, QFont
from PySide6.QtCore import Qt, QPoint, QRect


class DraggableTextEdit(QTextEdit):
    """Transparent text edit that can be moved and resized by dragging."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setStyleSheet("background: transparent; border: 2px solid red; color: red;")
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setFrameStyle(QTextEdit.NoFrame)
        self.setMinimumSize(40, 20)
        self._drag = False
        self._resize = False
        self._drag_pos = QPoint()

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            margin = 6
            if (self.width() - event.pos().x() < margin and
                    self.height() - event.pos().y() < margin):
                self._resize = True
            else:
                self._drag = True
                self._drag_pos = event.globalPosition().toPoint() - self.pos()
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        if self._drag:
            new_pos = event.globalPosition().toPoint() - self._drag_pos
            self.move(new_pos)
        elif self._resize:
            new_size = event.pos()
            self.resize(max(new_size.x(), 40), max(new_size.y(), 20))
        else:
            super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event):
        self._drag = False
        self._resize = False
        super().mouseReleaseEvent(event)

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
        self.setMouseTracking(True)
        self.last_point: QPoint | None = None
        self.drawing = False
        self.mode = 'draw'
        self.text_edits: list[DraggableTextEdit] = []
        self.pen_width = 2
        self.pen_color = QColor('red')
        self.text_color = QColor('red')
        self.text_size = 14
        self.font_family = QFont().family()

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        self.label = QLabel()
        self.label.setPixmap(self._compose())
        self.label.setAttribute(Qt.WA_TransparentForMouseEvents)
        self.label.setMouseTracking(True)
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
        self.mode = 'text'

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            if self.mode == 'draw':
                self.drawing = True
                self.last_point = event.position().toPoint()
            elif self.mode == 'text':
                te = DraggableTextEdit(self.label)
                te.setFont(QFont(self.font_family, self.text_size))
                te.setGeometry(QRect(event.position().toPoint(), te.size()))
                te.setStyleSheet(
                    f"background: transparent; border: 2px solid {self.text_color.name()}; color: {self.text_color.name()};"
                )
                te.show()
                te.setFocus()
                self.text_edits.append(te)
                self.mode = 'draw'
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
        painter = QPainter(self.overlay)
        pen = QPen(self.text_color)
        painter.setPen(pen)
        for te in self.text_edits:
            painter.setFont(te.font())
            pos = te.pos()
            rect = QRect(pos, te.size())
            painter.drawText(rect, Qt.AlignLeft | Qt.AlignTop, te.toPlainText())
            te.hide()
        painter.end()
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

