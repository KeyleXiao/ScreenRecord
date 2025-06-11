from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import time
import tkinter as tk
from typing import Optional, Tuple
from PIL import Image
import imageio.v2 as imageio
import mss


@dataclass
class Rect:
    x: int
    y: int
    width: int
    height: int


class RegionSelector(tk.Toplevel):
    """Fullscreen window allowing the user to drag to select a region."""

    def __init__(self, master=None):
        super().__init__(master)
        self.scaling = float(self.tk.call("tk", "scaling"))
        self.withdraw()
        self.overrideredirect(True)
        self.attributes("-fullscreen", True)
        self.attributes("-alpha", 0.3)
        self.configure(background="black")
        self.canvas = tk.Canvas(self, cursor="cross", highlightthickness=0, bg="black")
        self.canvas.pack(fill=tk.BOTH, expand=True)
        self.start_pos: Optional[Tuple[int, int]] = None
        self.rect_id: Optional[int] = None
        self.selected: Optional[Rect] = None
        self.button_frame: Optional[tk.Frame] = None
        self.button_window: Optional[int] = None
        self.bind("<ButtonPress-1>", self.on_press)
        self.bind("<B1-Motion>", self.on_drag)
        self.bind("<ButtonRelease-1>", self.on_release)
        self.bind("<ButtonPress-3>", lambda e: self.cancel())
        self.bind("<Escape>", lambda e: self.cancel())
        # instruction label
        self.label = tk.Label(
            self,
            text="拖动选择区域，按 Esc 或右键取消",
            bg="#000000",
            fg="white",
        )
        self.label.pack(anchor="nw", padx=20, pady=20)
        self.deiconify()

    def on_press(self, event):
        if self.rect_id:
            self.canvas.delete(self.rect_id)
        if self.button_window is not None:
            self.canvas.delete(self.button_window)
            self.button_window = None
        if self.button_frame is not None:
            self.button_frame.destroy()
            self.button_frame = None
        self.start_pos = (event.x, event.y)
        self.rect_id = self.canvas.create_rectangle(event.x, event.y, event.x, event.y, outline="red")

    def on_drag(self, event):
        if self.start_pos and self.rect_id:
            x1, y1 = self.start_pos
            self.canvas.coords(self.rect_id, x1, y1, event.x, event.y)

    def on_release(self, event):
        if not (self.start_pos and self.rect_id):
            return
        x1, y1 = self.start_pos
        x2, y2 = event.x, event.y
        ux = min(x1, x2)
        uy = min(y1, y2)
        uw = abs(x2 - x1)
        uh = abs(y2 - y1)
        sx1, sy1 = int(round(ux * self.scaling)), int(round(uy * self.scaling))
        sx2, sy2 = int(round((ux + uw) * self.scaling)), int(round((uy + uh) * self.scaling))
        self.selected = Rect(min(sx1, sx2), min(sy1, sy2), abs(sx2 - sx1), abs(sy2 - sy1))
        self.show_buttons(ux + uw, uy + uh)

    def show_buttons(self, x: float, y: float) -> None:
        if self.button_window is not None:
            self.canvas.delete(self.button_window)
            self.button_window = None
        if self.button_frame is not None:
            self.button_frame.destroy()
        self.button_frame = tk.Frame(self.canvas, bg="white")
        tk.Button(self.button_frame, text="取消", command=self.cancel).pack(side="left")
        tk.Button(self.button_frame, text="确认", command=self.confirm).pack(side="left")
        self.button_window = self.canvas.create_window(x, y, anchor="se", window=self.button_frame)

    def confirm(self):
        self.destroy()

    def cancel(self):
        self.selected = None
        self.destroy()


def select_region(master=None) -> Optional[Rect]:
    root = tk.Tk() if master is None else master
    if master is None:
        root.withdraw()
    selector = RegionSelector(root)
    selector.grab_set()
    root.wait_window(selector)
    if master is None:
        root.destroy()
    return selector.selected


def take_screenshot(path: Path, region: Optional[Rect] = None) -> Path:
    """Capture a screenshot optionally limited to *region*."""
    path.parent.mkdir(parents=True, exist_ok=True)
    with mss.mss() as sct:
        if region is None:
            screenshot = sct.grab(sct.monitors[0])
        else:
            monitor = {
                "left": region.x,
                "top": region.y,
                "width": region.width,
                "height": region.height,
            }
            screenshot = sct.grab(monitor)
        img = Image.frombytes("RGB", screenshot.size, screenshot.rgb)
        img.save(path)
    return path


def video_to_gif(video_path: Path, gif_path: Path, fps: int = 10) -> Path:
    reader = imageio.get_reader(str(video_path))
    frames = [frame for frame in reader]
    imageio.mimsave(gif_path, frames, fps=fps)
    return gif_path


def timestamp_filename(ext: str) -> str:
    return time.strftime("%Y%m%d_%H%M%S") + ext


class RecordingOverlay:
    """Display a red rectangle around the recording area."""

    def __init__(self, region: Rect, master=None, color: str = "red", width: int = 5):
        self.windows = []
        self.color = color
        self.width = width
        self.create_windows(region, master)

    def create_windows(self, region: Rect, master=None) -> None:
        x, y, w, h = region.x, region.y, region.width, region.height
        # top
        self.windows.append(self._make_win(w, self.width, x, y, master))
        # bottom
        self.windows.append(self._make_win(w, self.width, x, y + h - self.width, master))
        # left
        self.windows.append(self._make_win(self.width, h, x, y, master))
        # right
        self.windows.append(self._make_win(self.width, h, x + w - self.width, y, master))

    def _make_win(self, w: int, h: int, x: int, y: int, master=None) -> tk.Toplevel:
        win = tk.Toplevel(master)
        win.overrideredirect(True)
        win.attributes("-topmost", True)
        win.geometry(f"{w}x{h}+{x}+{y}")
        win.configure(background=self.color)
        return win

    def destroy(self) -> None:
        for win in self.windows:
            win.destroy()
