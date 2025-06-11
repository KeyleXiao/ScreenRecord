# ScreenRecord

A simple cross-platform screen recorder and screenshot tool using PySide6.
The tray icon now uses a built-in system icon to avoid startup errors on
platforms that require one.

## Features
- Record screen to MP4 via ffmpeg
- Optional GIF export with custom FPS
- Take screenshots using `mss`
- Edit screenshots before saving with adjustable brush size/color and text font/size
- System tray support and screenshot hotkey (Ctrl+Shift+S)
- Basic settings saved to `config.json`

## Usage
```bash
pip install -r requirements.txt
python src/main.py
```
