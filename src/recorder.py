import sys
import shutil
import subprocess
import threading
from pathlib import Path

from utils import Rect


class RecorderThread(threading.Thread):
    """Simple ffmpeg based screen recorder running in a thread."""

    def __init__(self, output: Path, fps: int = 30, region: Rect | None = None,
                 on_finished=None, on_error=None):
        super().__init__(daemon=True)
        self.output = output
        self.fps = fps
        self.region = region
        self.on_finished = on_finished
        self.on_error = on_error
        self._process = None
        self._stop_event = threading.Event()

    def run(self):
        self.output.parent.mkdir(parents=True, exist_ok=True)
        ffmpeg_bin = shutil.which("ffmpeg")
        if not ffmpeg_bin:
            try:
                from imageio_ffmpeg import get_ffmpeg_exe

                ffmpeg_bin = get_ffmpeg_exe()
            except Exception:
                if self.on_error:
                    self.on_error("ffmpeg not found and could not be downloaded.")
                return
        if sys.platform.startswith("win"):
            cmd = [
                ffmpeg_bin,
                "-y",
                "-f",
                "gdigrab",
                "-framerate",
                str(self.fps),
            ]
            if self.region is not None:
                cmd += [
                    "-offset_x",
                    str(self.region.x),
                    "-offset_y",
                    str(self.region.y),
                    "-video_size",
                    f"{self.region.width}x{self.region.height}",
                ]
            cmd += ["-i", "desktop", str(self.output)]
        elif sys.platform == "darwin":
            cmd = [
                ffmpeg_bin,
                "-y",
                "-f",
                "avfoundation",
                "-framerate",
                str(self.fps),
                "-i",
                "1",
            ]
            if self.region is not None:
                cmd += [
                    "-vf",
                    (
                        f"crop={self.region.width}:{self.region.height}:"
                        f"{self.region.x}:{self.region.y}"
                    ),
                ]
            cmd.append(str(self.output))
        else:
            cmd = [
                ffmpeg_bin,
                "-y",
                "-f",
                "x11grab",
                "-framerate",
                str(self.fps),
            ]
            if self.region is not None:
                cmd += [
                    "-video_size",
                    f"{self.region.width}x{self.region.height}",
                    "-i",
                    f":0.0+{self.region.x},{self.region.y}",
                ]
            else:
                cmd += ["-i", ":0.0"]
            cmd.append(str(self.output))
        try:
            self._process = subprocess.Popen(
                cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE
            )
            self._process.wait()
            if self._stop_event.is_set():
                return
            if self._process.returncode == 0:
                if self.on_finished:
                    self.on_finished(self.output)
            else:
                err = self._process.stderr.read().decode("utf-8")
                if self.on_error:
                    self.on_error(err)
        except Exception as e:
            if self.on_error:
                self.on_error(str(e))

    def stop(self):
        self._stop_event.set()
        if self._process and self._process.poll() is None:
            self._process.terminate()
            self._process.wait()
