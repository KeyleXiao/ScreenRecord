import sys
from pathlib import Path
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QVBoxLayout, QWidget,
    QPushButton, QFileDialog, QMessageBox, QDialog, QFormLayout,
    QSpinBox, QComboBox, QLineEdit, QLabel, QSystemTrayIcon, QMenu,
    QCheckBox
)
from PySide6.QtGui import QIcon, QAction, QShortcut, QKeySequence
from PySide6.QtCore import Qt

from settings import Settings
from recorder import RecorderThread
from utils import take_screenshot, timestamp_filename, video_to_gif
from editor import ScreenshotEditor

class SettingsDialog(QDialog):
    def __init__(self, settings: Settings, parent=None):
        super().__init__(parent)
        self.setWindowTitle('设置')
        self.settings = settings
        layout = QFormLayout(self)
        self.path_edit = QLineEdit(self.settings.save_path)
        browse_btn = QPushButton('浏览')
        browse_btn.clicked.connect(self.browse)
        path_layout = QVBoxLayout()
        path_layout.addWidget(self.path_edit)
        path_layout.addWidget(browse_btn)
        container = QWidget()
        container.setLayout(path_layout)
        layout.addRow('保存路径:', container)

        self.format_combo = QComboBox()
        self.format_combo.addItems(['mp4', 'gif'])
        self.format_combo.setCurrentText(self.settings.output_format)
        layout.addRow('默认格式:', self.format_combo)

        self.fps_spin = QSpinBox()
        self.fps_spin.setRange(1, 60)
        self.fps_spin.setValue(self.settings.gif_fps)
        layout.addRow('GIF 帧率:', self.fps_spin)

        self.start_check = QCheckBox('启动时最小化到托盘')
        self.start_check.setChecked(self.settings.start_minimized)
        layout.addRow(self.start_check)

        btn = QPushButton('保存')
        btn.clicked.connect(self.accept)
        layout.addWidget(btn)

    def browse(self):
        path = QFileDialog.getExistingDirectory(self, '选择保存目录', self.settings.save_path)
        if path:
            self.path_edit.setText(path)

    def accept(self):
        self.settings.save_path = self.path_edit.text()
        self.settings.output_format = self.format_combo.currentText()
        self.settings.gif_fps = self.fps_spin.value()
        self.settings.start_minimized = self.start_check.isChecked()
        self.settings.save()
        super().accept()


class GifExportDialog(QDialog):
    def __init__(self, parent=None, default_fps: int = 10):
        super().__init__(parent)
        self.setWindowTitle('导出 GIF')
        layout = QFormLayout(self)
        self.fps_spin = QSpinBox()
        self.fps_spin.setRange(1, 60)
        self.fps_spin.setValue(default_fps)
        layout.addRow('帧率:', self.fps_spin)
        ok_btn = QPushButton('导出')
        ok_btn.clicked.connect(self.accept)
        layout.addWidget(ok_btn)

    def fps(self) -> int:
        return self.fps_spin.value()

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle('Screen Recorder')
        self.resize(500, 80)
        self.settings = Settings.load()

        central = QWidget()
        self.setCentralWidget(central)
        layout = QHBoxLayout(central)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(6)

        self.record_btn = QPushButton('🎥 开始录制')
        self.record_btn.clicked.connect(self.start_record)
        layout.addWidget(self.record_btn)

        self.stop_btn = QPushButton('停止')
        self.stop_btn.clicked.connect(self.stop_record)
        self.stop_btn.setEnabled(False)
        layout.addWidget(self.stop_btn)

        shot_btn = QPushButton('📸 截图')
        shot_btn.clicked.connect(self.take_shot)
        layout.addWidget(shot_btn)

        set_btn = QPushButton('设置')
        set_btn.clicked.connect(self.open_settings)
        layout.addWidget(set_btn)

        exit_btn = QPushButton('退出')
        exit_btn.clicked.connect(self.exit_app)
        layout.addWidget(exit_btn)

        self.shortcut_shot = QShortcut(QKeySequence('Ctrl+Shift+S'), self)
        self.shortcut_shot.activated.connect(self.take_shot)

        self.tray = QSystemTrayIcon(QIcon(), self)
        tray_menu = QMenu()
        act_restore = QAction('显示窗口', self)
        # Restore the main window when the tray icon action is triggered
        act_restore.triggered.connect(self.showNormal)
        tray_menu.addAction(act_restore)
        act_shot = QAction('快速截图', self)
        act_shot.triggered.connect(self.take_shot)
        tray_menu.addAction(act_shot)
        act_quit = QAction('退出', self)
        act_quit.triggered.connect(self.exit_app)
        tray_menu.addAction(act_quit)
        self.tray.setContextMenu(tray_menu)
        self.tray.setToolTip('Screen Recorder')
        self.tray.activated.connect(self.on_tray_activated)
        self.tray.show()

        self.thread = None
        self.apply_style()

    def apply_style(self):
        self.setStyleSheet(
            """
            QPushButton { padding:4px 12px; border-radius:6px; background:#3498db; color:white; }
            QPushButton:hover { background:#2980b9; }
            """
        )

    def start_record(self):
        save_dir = Path(self.settings.save_path)
        save_dir.mkdir(parents=True, exist_ok=True)
        filename = timestamp_filename('.mp4')
        output = save_dir / filename
        self.thread = RecorderThread(output)
        self.thread.finished.connect(self.record_finished)
        self.thread.error.connect(self.record_error)
        self.record_btn.setEnabled(False)
        self.stop_btn.setEnabled(True)
        self.thread.start()

    def record_finished(self, path: Path):
        self.record_btn.setEnabled(True)
        self.stop_btn.setEnabled(False)
        QMessageBox.information(self, '完成', f'录制完成: {path}')

        if QMessageBox.question(self, '导出 GIF', '是否导出为 GIF?') == QMessageBox.Yes:
            dlg = GifExportDialog(self, self.settings.gif_fps)
            if dlg.exec():
                gif_path = path.with_suffix('.gif')
                video_to_gif(path, gif_path, dlg.fps())
                QMessageBox.information(self, 'GIF 导出', f'已保存 GIF: {gif_path}')

    def record_error(self, err: str):
        self.record_btn.setEnabled(True)
        self.stop_btn.setEnabled(False)
        QMessageBox.warning(self, '错误', err)

    def stop_record(self):
        if self.thread:
            self.thread.stop()

    def on_tray_activated(self, reason):
        if reason == QSystemTrayIcon.Trigger:
            self.showNormal()

    def exit_app(self):
        if self.thread:
            self.thread.stop()
        QApplication.instance().quit()

    def take_shot(self):
        save_dir = Path(self.settings.save_path)
        save_dir.mkdir(parents=True, exist_ok=True)
        path = save_dir / timestamp_filename('.png')
        take_screenshot(path)
        editor = ScreenshotEditor(path, self)
        editor.exec()
        QMessageBox.information(self, '截图', f'已保存截图: {path}')

    def open_settings(self):
        dlg = SettingsDialog(self.settings, self)
        if dlg.exec():
            if self.settings.start_minimized:
                self.hide()
            else:
                self.show()


def main():
    app = QApplication(sys.argv)
    w = MainWindow()
    if w.settings.start_minimized:
        w.hide()
    else:
        w.show()
    sys.exit(app.exec())

if __name__ == '__main__':
    main()
