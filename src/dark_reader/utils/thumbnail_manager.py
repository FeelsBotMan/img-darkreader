from __future__ import annotations

import logging
import os
from io import BytesIO
from pathlib import Path
from typing import Optional

from PIL import Image

from ..config.paths import AppPaths

logger = logging.getLogger(__name__)


class ThumbnailManager:
    def __init__(self, cache_dir: Path | None = None):
        self.cache_dir = cache_dir or AppPaths.thumbnails_dir()
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.thumbnail_size = (200, 300)

    def get_thumbnail_path(self, data: bytes, cache_id: str) -> Optional[str]:
        """바이트 이미지의 섬네일 경로를 반환합니다. 없으면 생성합니다."""
        # cache_id가 이미 해시인 경우 그대로 파일명으로 사용
        thumb_path = self.cache_dir / f"{cache_id}.jpg"

        if thumb_path.exists():
            return str(thumb_path)

        try:
            logger.debug("섬네일 생성: %s", cache_id)
            with Image.open(BytesIO(data)) as img:
                if img.mode in ("RGBA", "P"):
                    img = img.convert("RGB")
                img.thumbnail(self.thumbnail_size, Image.Resampling.LANCZOS)
                img.save(thumb_path, "JPEG", quality=85)
                return str(thumb_path)
        except Exception:
            logger.exception("섬네일 생성 실패: %s", cache_id)
            if thumb_path.exists():
                try:
                    os.remove(thumb_path)
                except OSError:
                    pass
            return None

    # 하위 호환 별칭
    def get_thumbnail_bytes(self, data: bytes, cache_id: str) -> Optional[str]:
        return self.get_thumbnail_path(data, cache_id)
