import json
from pathlib import Path
from dataclasses import dataclass, asdict

CONFIG_FILE = Path('config.json')

default_config = {
    'save_path': str(Path('recordings')),
    'output_format': 'mp4',
    'gif_fps': 10,
    'start_minimized': False,
}

@dataclass
class Settings:
    save_path: str = default_config['save_path']
    output_format: str = default_config['output_format']
    gif_fps: int = default_config['gif_fps']
    start_minimized: bool = default_config['start_minimized']

    @classmethod
    def load(cls) -> 'Settings':
        if CONFIG_FILE.exists():
            with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
                data = json.load(f)
            return cls(**{**default_config, **data})
        return cls()

    def save(self) -> None:
        CONFIG_FILE.parent.mkdir(parents=True, exist_ok=True)
        with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
            json.dump(asdict(self), f, indent=2)
