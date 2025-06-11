from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import time
import tkinter as tk
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
        self.withdraw()
        self.overrideredirect(True)
        self.attributes("-fullscreen", True)
        self.attributes("-alpha", 0.3)
        self.configure(background="black")
        self.canvas = tk.Canvas(self, cursor="cross", highlightthickness=0, bg="black")
        self.canvas.pack(fill=tk.BOTH, expand=True)
        self.start_pos: tuple[int, int] | None = None
        self.rect_id: int | None = None
        self.selected: Rect | None = None
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
        self.start_pos = (event.x, event.y)
        self.rect_id = self.canvas.create_rectangle(event.x, event.y, event.x, event.y, outline="red")

    def on_drag(self, event):
        if self.start_pos and self.rect_id:
            x1, y1 = self.start_pos
            self.canvas.coords(self.rect_id, x1, y1, event.x, event.y)

    def on_release(self, event):
        if self.start_pos and self.rect_id:
            x1, y1 = self.start_pos
            x2, y2 = event.x, event.y
            self.selected = Rect(min(x1, x2), min(y1, y2), abs(x2 - x1), abs(y2 - y1))
        self.destroy()

    def cancel(self):
        self.selected = None
        self.destroy()


def select_region(master=None) -> Rect | None:
    root = tk.Tk() if master is None else master
    if master is None:
        root.withdraw()
    selector = RegionSelector(root)
    selector.grab_set()
    root.wait_window(selector)
    if master is None:
        root.destroy()
    return selector.selected


def take_screenshot(path: Path, region: Rect | None = None) -> Path:
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
