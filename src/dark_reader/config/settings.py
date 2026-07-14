from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Tuple

import yaml

from .paths import AppPaths

logger = logging.getLogger(__name__)


@dataclass
class Theme:
    background_color: Tuple[int, int, int]
    text_color: Tuple[int, int, int]
    window_background: str
    window_text: str
    contrast: float = 1.0
    brightness: float = 1.0
    sharpness: float = 1.0
    gamma: float = 1.0
    use_ai_upscaling: bool = False
    upscale_factor: int = 2


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
            gamma=1.1,
        )
        self.light_theme = Theme(
            background_color=(255, 255, 255),
            text_color=(0, 0, 0),
            window_background="#FFFFFF",
            window_text="#000000",
            contrast=1.1,
            brightness=1.0,
            sharpness=1.1,
            gamma=1.0,
        )

        self.is_dark_mode = True
        self.threshold = 240

        AppPaths.ensure_dirs()
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

    def toggle_theme(self) -> None:
        self.is_dark_mode = not self.is_dark_mode
        self.save_settings()

    def load_settings(self) -> None:
        config_path = AppPaths.config_file()
        if not config_path.exists():
            return
        try:
            with open(config_path, "r", encoding="utf-8") as f:
                config = yaml.safe_load(f) or {}
            self.is_dark_mode = config.get("is_dark_mode", True)
            self.threshold = config.get("threshold", self.threshold)
        except (OSError, yaml.YAMLError) as e:
            logger.error("설정 로드 실패: %s", e)

    def save_settings(self) -> None:
        config_path = AppPaths.config_file()
        try:
            config_path.parent.mkdir(parents=True, exist_ok=True)
            config = {
                "is_dark_mode": self.is_dark_mode,
                "threshold": self.threshold,
            }
            with open(config_path, "w", encoding="utf-8") as f:
                yaml.dump(config, f)
        except OSError as e:
            logger.error("설정 저장 실패: %s", e)
