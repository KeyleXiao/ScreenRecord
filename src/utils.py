from pathlib import Path
import time
import imageio.v2 as imageio
from PIL import Image
import mss

def take_screenshot(path: Path) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    with mss.mss() as sct:
        screenshot = sct.grab(sct.monitors[0])
        img = Image.frombytes('RGB', screenshot.size, screenshot.rgb)
        img.save(path)
    return path

def video_to_gif(video_path: Path, gif_path: Path, fps: int = 10) -> Path:
    reader = imageio.get_reader(str(video_path))
    frames = []
    for frame in reader:
        frames.append(frame)
    imageio.mimsave(gif_path, frames, fps=fps)
    return gif_path

def timestamp_filename(ext: str) -> str:
    return time.strftime('%Y%m%d_%H%M%S') + ext
