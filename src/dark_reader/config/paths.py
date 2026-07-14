"""애플리케이션 데이터 경로 (설정·라이브러리·캐시)."""
from __future__ import annotations

from pathlib import Path


class AppPaths:
    """모든 영속 데이터의 루트를 ~/.dark_reader 로 통일합니다."""

    @staticmethod
    def root() -> Path:
        return Path.home() / ".dark_reader"

    @classmethod
    def config_file(cls) -> Path:
        return cls.root() / "config.yaml"

    @classmethod
    def library_file(cls) -> Path:
        return cls.root() / "library.json"

    @classmethod
    def thumbnails_dir(cls) -> Path:
        return cls.root() / "thumbnails"

    @classmethod
    def upscale_cache_dir(cls) -> Path:
        return cls.root() / "cache"

    @classmethod
    def ensure_dirs(cls) -> None:
        cls.root().mkdir(parents=True, exist_ok=True)
        cls.thumbnails_dir().mkdir(parents=True, exist_ok=True)
        cls.upscale_cache_dir().mkdir(parents=True, exist_ok=True)
