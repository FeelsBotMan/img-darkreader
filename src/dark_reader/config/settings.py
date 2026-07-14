from dataclasses import dataclass
from pathlib import Path
import yaml
from typing import Tuple

@dataclass
class Theme:
    background_color: Tuple[int, int, int]
    text_color: Tuple[int, int, int]
    window_background: str
    window_text: str
    contrast: float = 1.0  # 대비
    brightness: float = 1.0  # 밝기
    sharpness: float = 1.0  # 선명도
    gamma: float = 1.0  # 감마
    use_ai_upscaling: bool = True  # AI 업스케일링 사용 여부
    upscale_factor: int = 2  # 업스케일링 배율

class Settings:
    def __init__(self):
        self.dark_theme = Theme(
            background_color=(0, 0, 0),
            text_color=(200, 200, 200),
            window_background="#2B2B2B",
            window_text="#FFFFFF",
            contrast=1.2,
            brightness=0.9,
            sharpness=1.1,
            gamma=1.1
        )
        self.light_theme = Theme(
            background_color=(255, 255, 255),
            text_color=(0, 0, 0),
            window_background="#FFFFFF",
            window_text="#000000",
            contrast=1.1,
            brightness=1.0,
            sharpness=1.1,
            gamma=1.0
        )
        
        self.is_dark_mode = True
        self.threshold = 240
        
        self.load_settings()
    
    @property
    def current_theme(self) -> Theme:
        return self.dark_theme if self.is_dark_mode else self.light_theme
    
    @property
    def background_color(self) -> Tuple[int, int, int]:
        return self.current_theme.background_color
    
    @property
    def text_color(self) -> Tuple[int, int, int]:
        return self.current_theme.text_color
    
    def toggle_theme(self):
        self.is_dark_mode = not self.is_dark_mode
        self.save_settings()
    
    def load_settings(self):
        config_path = Path.home() / '.dark_reader' / 'config.yaml'
        if config_path.exists():
            with open(config_path, 'r', encoding='utf-8') as f:
                config = yaml.safe_load(f)
                self.is_dark_mode = config.get('is_dark_mode', True)
                self.threshold = config.get('threshold', self.threshold)
    
    def save_settings(self):
        config_path = Path.home() / '.dark_reader' / 'config.yaml'
        config_path.parent.mkdir(parents=True, exist_ok=True)
        
        config = {
            'is_dark_mode': self.is_dark_mode,
            'threshold': self.threshold
        }
        
        with open(config_path, 'w', encoding='utf-8') as f:
            yaml.dump(config, f) 