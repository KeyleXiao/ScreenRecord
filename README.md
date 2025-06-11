# ScreenRecord

A simple cross-platform screen recorder and screenshot tool using Python's
built-in Tkinter GUI toolkit. The previous PySide6 interface has been replaced
for better compatibility.

## Features
- Record screen to MP4 via ffmpeg
- Optional GIF export with custom FPS
- Take screenshots using `mss`
- Edit screenshots with a simple drawing tool
- Basic settings saved to `config.json`
- Recording area highlighted with a 5-pixel red frame
- Recording duration shown on the main window

## Usage
```bash
pip install -r requirements.txt
python src/main.py
```

When you click the "Start Recording" or "Screenshot" buttons, a full-screen
overlay with a crosshair cursor will appear. Drag to select the region you want
to capture. You can press **Esc** or right-click to cancel. The application
waits for this selection before continuing, so be sure to draw a rectangle
instead of thinking the program has frozen.
