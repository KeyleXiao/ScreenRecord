import tkinter as tk
from tkinter import filedialog, messagebox
from pathlib import Path
import time
import sys

if sys.platform.startswith("win"):
    try:
        from ctypes import windll
        try:
            windll.shcore.SetProcessDpiAwareness(2)
        except Exception:
            windll.user32.SetProcessDPIAware()
    except Exception:
        pass

from settings import Settings
from recorder import RecorderThread
from typing import Optional
from utils import (
    take_screenshot,
    timestamp_filename,
    video_to_gif,
    select_region,
    RecordingOverlay,
)
from editor import ScreenshotEditor


class SettingsDialog(tk.Toplevel):
    def __init__(self, settings: Settings, master=None):
        super().__init__(master)
        self.settings = settings
        self.title("设置")
        self.resizable(False, False)
        tk.Label(self, text="保存路径:").grid(row=0, column=0, sticky="e")
        self.path_var = tk.StringVar(value=self.settings.save_path)
        tk.Entry(self, textvariable=self.path_var, width=40).grid(row=0, column=1)
        tk.Button(self, text="浏览", command=self.browse).grid(row=0, column=2)
        tk.Label(self, text="默认格式:").grid(row=1, column=0, sticky="e")
        self.format_var = tk.StringVar(value=self.settings.output_format)
        tk.OptionMenu(self, self.format_var, "mp4", "gif").grid(row=1, column=1, columnspan=2, sticky="w")
        tk.Label(self, text="GIF 帧率:").grid(row=2, column=0, sticky="e")
        self.fps_var = tk.IntVar(value=self.settings.gif_fps)
        tk.Spinbox(self, from_=1, to=60, textvariable=self.fps_var, width=5).grid(row=2, column=1, sticky="w")
        self.start_var = tk.BooleanVar(value=self.settings.start_minimized)
        tk.Checkbutton(self, text="启动时最小化", variable=self.start_var).grid(row=3, column=0, columnspan=3, sticky="w")
        tk.Button(self, text="保存", command=self.on_ok).grid(row=4, column=0, columnspan=3, pady=5)

    def browse(self):
        path = filedialog.askdirectory(initialdir=self.settings.save_path)
        if path:
            self.path_var.set(path)

    def on_ok(self):
        self.settings.save_path = self.path_var.get()
        self.settings.output_format = self.format_var.get()
        self.settings.gif_fps = int(self.fps_var.get())
        self.settings.start_minimized = self.start_var.get()
        self.settings.save()
        self.destroy()


class GifExportDialog(tk.Toplevel):
    def __init__(self, master=None, default_fps: int = 10):
        super().__init__(master)
        self.title("导出 GIF")
        tk.Label(self, text="帧率:").pack(side="left")
        self.fps_var = tk.IntVar(value=default_fps)
        tk.Spinbox(self, from_=1, to=60, textvariable=self.fps_var, width=5).pack(side="left")
        tk.Button(self, text="导出", command=self.destroy).pack(side="left")

    def fps(self) -> int:
        return int(self.fps_var.get())


class MainWindow(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Screen Recorder")
        self.settings = Settings.load()
        # Reduce height slightly for a sleeker look
        self.geometry("520x50")
        # Allow width resizing but lock the height
        self.resizable(True, False)

        top = tk.Frame(self)
        top.pack(fill="both", expand=True)

        btn_frame = tk.Frame(top)
        btn_frame.pack(side="left", fill="both", expand=True)

        self.record_btn = tk.Button(
            btn_frame,
            text="⏺ 开始录制",
            command=self.start_record,
            borderwidth=0,
        )
        self.record_btn.pack(side="left", fill="both", expand=True, padx=(0, 1), pady=1)

        self.stop_btn = tk.Button(
            btn_frame,
            text="⏹ 停止",
            command=self.stop_record,
            state="disabled",
            borderwidth=0,
        )
        self.stop_btn.pack(side="left", fill="both", expand=True, padx=(0, 1), pady=1)

        tk.Button(
            btn_frame,
            text="📸 截图",
            command=self.take_shot,
            borderwidth=0,
        ).pack(
            side="left", fill="both", expand=True, padx=(0, 1), pady=1
        )
        tk.Button(
            btn_frame,
            text="⚙ 设置",
            command=self.open_settings,
            borderwidth=0,
        ).pack(
            side="left", fill="both", expand=True, padx=(0, 1), pady=1
        )
        tk.Button(
            btn_frame,
            text="❌ 退出",
            command=self.exit_app,
            borderwidth=0,
        ).pack(
            side="left", fill="both", expand=True, pady=1
        )

        self.timer_var = tk.StringVar(value="00:00")
        self.timer_label = tk.Label(top, textvariable=self.timer_var, width=6)
        self.timer_label.pack(side="right", fill="y", padx=5)
        self.thread: Optional[RecorderThread] = None
        self.overlay: Optional[RecordingOverlay] = None
        self.timer_job = None
        self.start_time = None
        if self.settings.start_minimized:
            self.withdraw()

    # Recording
    def start_record(self):
        region = select_region(self)
        if region is None:
            return
        default = Path(self.settings.save_path) / timestamp_filename(".mp4")
        file_path = filedialog.asksaveasfilename(initialfile=str(default), defaultextension=".mp4", filetypes=[("MP4", "*.mp4")])
        if not file_path:
            return
        self.overlay = RecordingOverlay(region, master=self)
        self.start_time = time.time()
        self.update_timer()
        def on_finished(path: Path):
            self.record_btn.config(state="normal")
            self.stop_btn.config(state="disabled")
            if self.overlay:
                self.overlay.destroy()
                self.overlay = None
            if self.timer_job:
                self.after_cancel(self.timer_job)
                self.timer_job = None
            self.timer_var.set("00:00")
            messagebox.showinfo("完成", f"录制完成: {path}")
            if messagebox.askyesno("导出 GIF", "是否导出为 GIF?"):
                dlg = GifExportDialog(self, self.settings.gif_fps)
                self.wait_window(dlg)
                gif_path = Path(path).with_suffix(".gif")
                video_to_gif(Path(path), gif_path, dlg.fps())
                messagebox.showinfo("GIF", f"已保存 GIF: {gif_path}")
        def on_error(err: str):
            self.record_btn.config(state="normal")
            self.stop_btn.config(state="disabled")
            if self.overlay:
                self.overlay.destroy()
                self.overlay = None
            if self.timer_job:
                self.after_cancel(self.timer_job)
                self.timer_job = None
            self.timer_var.set("00:00")
            messagebox.showerror("错误", err)
        self.thread = RecorderThread(Path(file_path), region=region, on_finished=on_finished, on_error=on_error)
        self.thread.start()
        self.record_btn.config(state="disabled")
        self.stop_btn.config(state="normal")

    def update_timer(self):
        if self.start_time is None:
            return
        elapsed = int(time.time() - self.start_time)
        mins, secs = divmod(elapsed, 60)
        self.timer_var.set(f"{mins:02d}:{secs:02d}")
        self.timer_job = self.after(1000, self.update_timer)

    def stop_record(self):
        if self.thread:
            self.thread.stop()
            self.thread = None
            self.record_btn.config(state="normal")
            self.stop_btn.config(state="disabled")
        if self.overlay:
            self.overlay.destroy()
            self.overlay = None
        if self.timer_job:
            self.after_cancel(self.timer_job)
            self.timer_job = None
        self.timer_var.set("00:00")

    # Screenshot
    def take_shot(self):
        region = select_region(self)
        if region is None:
            return
        default = Path(self.settings.save_path) / timestamp_filename(".png")
        file_path = filedialog.asksaveasfilename(initialfile=str(default), defaultextension=".png", filetypes=[("PNG", "*.png")])
        if not file_path:
            return
        path = Path(file_path)
        take_screenshot(path, region)
        editor = ScreenshotEditor(path, self)
        self.wait_window(editor)
        messagebox.showinfo("截图", f"已保存截图: {path}")

    def open_settings(self):
        dlg = SettingsDialog(self.settings, self)
        self.wait_window(dlg)
        if self.settings.start_minimized:
            self.withdraw()
        else:
            self.deiconify()

    def exit_app(self):
        if self.thread:
            self.thread.stop()
        self.destroy()


def main():
    app = MainWindow()
    app.mainloop()


if __name__ == "__main__":
    main()
