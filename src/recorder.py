import sys
import shutil
import subprocess
from pathlib import Path
from PySide6.QtCore import QThread, Signal

class RecorderThread(QThread):
    finished = Signal(Path)
    error = Signal(str)

    def __init__(self, output: Path, fps: int = 30, region=None, parent=None):
        super().__init__(parent)
        self.output = output
        self.fps = fps
        self.region = region
        self._process = None

    def run(self):
        self.output.parent.mkdir(parents=True, exist_ok=True)
        ffmpeg_bin = shutil.which('ffmpeg')
        if not ffmpeg_bin:
            try:
                from imageio_ffmpeg import get_ffmpeg_exe

                ffmpeg_bin = get_ffmpeg_exe()
            except Exception:
                self.error.emit(
                    'ffmpeg not found and could not be downloaded.'
                )
                return
        # Basic cross-platform ffmpeg screen capture commands
        if sys.platform.startswith('win'):
            cmd = [
                ffmpeg_bin,
                '-y',
                '-f',
                'gdigrab',
                '-framerate',
                str(self.fps),
            ]
            if self.region is not None:
                cmd += [
                    '-offset_x',
                    str(self.region.x()),
                    '-offset_y',
                    str(self.region.y()),
                    '-video_size',
                    f'{self.region.width()}x{self.region.height()}',
                ]
            cmd += ['-i', 'desktop', str(self.output)]
        elif sys.platform == 'darwin':
            cmd = [
                ffmpeg_bin,
                '-y',
                '-f',
                'avfoundation',
                '-framerate',
                str(self.fps),
                '-i',
                '1',
            ]
            if self.region is not None:
                cmd += [
                    '-vf',
                    f'crop={self.region.width()}:{self.region.height()}:{self.region.x()}:{self.region.y()}',
                ]
            cmd.append(str(self.output))
        else:
            cmd = [
                ffmpeg_bin,
                '-y',
                '-f',
                'x11grab',
                '-framerate',
                str(self.fps),
            ]
            if self.region is not None:
                cmd += [
                    '-video_size',
                    f'{self.region.width()}x{self.region.height()}',
                    '-i',
                    f':0.0+{self.region.x()},{self.region.y()}',
                ]
            else:
                cmd += ['-i', ':0.0']
            cmd.append(str(self.output))
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
