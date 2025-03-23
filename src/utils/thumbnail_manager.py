from pathlib import Path
import hashlib
from PIL import Image
from typing import Optional
import os

class ThumbnailManager:
    def __init__(self):
        self.cache_dir = Path.home() / '.dark_reader' / 'thumbnails'
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.thumbnail_size = (200, 300)  # 섬네일 크기
        
    def get_thumbnail(self, image_path: str | Path) -> Optional[str]:
        """이미지의 섬네일을 반환합니다. 없으면 생성합니다."""
        image_path = Path(image_path)
        if not image_path.exists():
            print(f"Image file not found: {image_path}")
            return None
            
        # 캐시 파일명 생성
        hash_name = hashlib.md5(str(image_path.absolute()).encode()).hexdigest()
        thumb_path = self.cache_dir / f"{hash_name}.jpg"
        
        # 캐시된 섬네일이 있으면 반환
        if thumb_path.exists():
            #print(f"Using cached thumbnail: {thumb_path}")
            return str(thumb_path)
            
        # 섬네일 생성
        try:
            print(f"Creating thumbnail for: {image_path}")
            with Image.open(image_path) as img:
                # RGBA나 P 모드인 경우 RGB로 변환
                if img.mode in ('RGBA', 'P'):
                    img = img.convert('RGB')
                
                # 원본 크기 유지하면서 섬네일 크기에 맞게 조정
                img.thumbnail(self.thumbnail_size, Image.Resampling.LANCZOS)
                
                # 저장
                img.save(thumb_path, "JPEG", quality=90)
                print(f"Thumbnail created successfully: {thumb_path}")
                return str(thumb_path)
        except Exception as e:
            print(f"Error creating thumbnail: {e}")
            if thumb_path.exists():
                try:
                    os.remove(thumb_path)
                except:
                    pass
            return None 