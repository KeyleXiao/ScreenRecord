from __future__ import annotations

from pathlib import Path
import tkinter as tk
from PIL import Image, ImageTk, ImageDraw


class ScreenshotEditor(tk.Toplevel):
    """Very small editor to draw on a screenshot with the mouse."""

    def __init__(self, image_path: Path, master=None):
        super().__init__(master)
        self.title("编辑截图")
        self.image_path = image_path
        self.original = Image.open(image_path).convert("RGBA")
        self.overlay = Image.new("RGBA", self.original.size, (0, 0, 0, 0))
        self.tk_img = ImageTk.PhotoImage(self.original)
        self.canvas = tk.Canvas(self, width=self.original.width, height=self.original.height, cursor="cross")
        self.canvas.pack()
        self.canvas_image = self.canvas.create_image(0, 0, anchor="nw", image=self.tk_img)
        self.drawing = False
        self.last_pos = None
        self.draw = ImageDraw.Draw(self.overlay)
        self.bind_events()
        save_btn = tk.Button(self, text="保存", command=self.save)
        save_btn.pack(fill=tk.X)

    def bind_events(self):
        self.canvas.bind("<ButtonPress-1>", self.on_press)
        self.canvas.bind("<B1-Motion>", self.on_move)
        self.canvas.bind("<ButtonRelease-1>", self.on_release)

    def on_press(self, event):
        self.drawing = True
        self.last_pos = (event.x, event.y)

    def on_move(self, event):
        if self.drawing and self.last_pos:
            x1, y1 = self.last_pos
            x2, y2 = event.x, event.y
            self.draw.line([x1, y1, x2, y2], fill="red", width=2)
            self.last_pos = (x2, y2)
            self.update_canvas()

    def on_release(self, event):
        self.drawing = False
        self.last_pos = None

    def update_canvas(self):
        combined = Image.alpha_composite(self.original, self.overlay)
        self.tk_img = ImageTk.PhotoImage(combined)
        self.canvas.itemconfigure(self.canvas_image, image=self.tk_img)

    def save(self):
        combined = Image.alpha_composite(self.original, self.overlay)
        combined.convert("RGB").save(self.image_path)
        self.destroy()
