from pathlib import Path
import hashlib
from PIL import Image
from typing import Optional
import os
from io import BytesIO


class ThumbnailManager:
    def __init__(self):
        self.cache_dir = Path.home() / ".dark_reader" / "thumbnails"
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.thumbnail_size = (200, 300)  # 섬네일 크기

    def get_thumbnail_bytes(self, data: bytes, cache_id: str) -> Optional[str]:
        """바이트 이미지의 섬네일을 반환합니다. 없으면 생성합니다."""
        hash_name = hashlib.md5(cache_id.encode("utf-8")).hexdigest()
        thumb_path = self.cache_dir / f"{hash_name}.jpg"

        if thumb_path.exists():
            return str(thumb_path)

        try:
            print(f"Creating thumbnail for: {cache_id}")
            with Image.open(BytesIO(data)) as img:
                if img.mode in ("RGBA", "P"):
                    img = img.convert("RGB")
                img.thumbnail(self.thumbnail_size, Image.Resampling.LANCZOS)
                img.save(thumb_path, "JPEG", quality=90)
                print(f"Thumbnail created successfully: {thumb_path}")
                return str(thumb_path)
        except Exception as e:
            print(f"Error creating thumbnail: {e}")
            if thumb_path.exists():
                try:
                    os.remove(thumb_path)
                except OSError:
                    pass
            return None
