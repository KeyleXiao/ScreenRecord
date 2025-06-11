import sys
import subprocess
from pathlib import Path
from PySide6.QtCore import QThread, Signal

class RecorderThread(QThread):
    finished = Signal(Path)
    error = Signal(str)

    def __init__(self, output: Path, fps: int = 30, parent=None):
        super().__init__(parent)
        self.output = output
        self.fps = fps
        self._process = None

    def run(self):
        self.output.parent.mkdir(parents=True, exist_ok=True)
        # Basic cross-platform ffmpeg screen capture commands
        if sys.platform.startswith('win'):
            cmd = [
                'ffmpeg', '-y', '-f', 'gdigrab', '-framerate', str(self.fps),
                '-i', 'desktop', str(self.output)
            ]
        elif sys.platform == 'darwin':
            cmd = [
                'ffmpeg', '-y', '-f', 'avfoundation', '-framerate', str(self.fps),
                '-i', '1', str(self.output)
            ]
        else:
            cmd = [
                'ffmpeg', '-y', '-f', 'x11grab', '-framerate', str(self.fps),
                '-i', ':0.0', str(self.output)
            ]
        try:
            self._process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            self._process.wait()
            if self._process.returncode == 0:
                self.finished.emit(self.output)
            else:
                err = self._process.stderr.read().decode('utf-8')
                self.error.emit(err)
        except Exception as e:
            self.error.emit(str(e))

    def stop(self):
        if self._process and self._process.poll() is None:
            self._process.terminate()
            self._process.wait()
