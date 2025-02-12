import yaml
from pathlib import Path

class Settings:
    def __init__(self):
        self.background_color = (0, 0, 0)  # 기본 배경색: 검정
        self.text_color = (200, 200, 200)  # 기본 텍스트색: 밝은 회색
        self.threshold = 240  # 흰색 감지 임계값
        
        self.load_settings()
        
    def load_settings(self):
        config_path = Path.home() / '.dark_reader' / 'config.yaml'
        if config_path.exists():
            with open(config_path, 'r') as f:
                config = yaml.safe_load(f)
                self.background_color = tuple(config.get('background_color', self.background_color))
                self.text_color = tuple(config.get('text_color', self.text_color))
                self.threshold = config.get('threshold', self.threshold)
                
    def save_settings(self):
        config_path = Path.home() / '.dark_reader' / 'config.yaml'
        config_path.parent.mkdir(parents=True, exist_ok=True)
        
        config = {
            'background_color': self.background_color,
            'text_color': self.text_color,
            'threshold': self.threshold
        }
        
        with open(config_path, 'w') as f:
            yaml.dump(config, f) 