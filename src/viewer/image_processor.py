from PIL import Image, ImageEnhance
import numpy as np
from PyQt6.QtGui import QImage
from config.settings import Settings
from utils.upscaler import ImageUpscaler
from pathlib import Path

class ImageProcessor:
    def __init__(self, settings: Settings):
        self.settings = settings
        self.upscaler = ImageUpscaler(memory_cache_size=5)
        self.current_image_path = None
        self.reload_callback = None  # 이미지 리로드 콜백
        
    def set_reload_callback(self, callback):
        """이미지 리로드 콜백 설정"""
        self.reload_callback = callback
    
    def process_image(self, image_path: str) -> QImage:
        self.current_image_path = str(Path(image_path))  # 경로 정규화
        # 업스케일링된 이미지 경로 확인
        upscaled_path = self.upscaler.upscale(image_path, self._on_upscale_complete)
        
        # 업스케일링된 이미지가 있으면 사용
        if upscaled_path:
            img = Image.open(upscaled_path)
        else:
            # 없으면 원본 사용하고 백그라운드에서 업스케일링
            img = Image.open(image_path)
            self.upscaler.upscale(image_path, self._on_upscale_complete)
        
        # 이미지 처리
        if self.settings.is_dark_mode:
            # 다크모드 처리
            img = self._process_dark_mode(img)
        else:
            # 라이트모드 처리
            img = self._process_light_mode(img)
        
        # PIL -> QImage 변환
        return self._pil_to_qimage(img)
    
    def _process_dark_mode(self, img: Image.Image) -> Image.Image:
        # 대비 향상
        enhancer = ImageEnhance.Contrast(img)
        img = enhancer.enhance(1.2)
        
        # 선명도 향상
        enhancer = ImageEnhance.Sharpness(img)
        img = enhancer.enhance(1.1)
        
        # 밝기 조정
        enhancer = ImageEnhance.Brightness(img)
        img = enhancer.enhance(0.9)
        
        # 색상 반전
        if img.mode == 'L':  # 흑백 이미지
            img = Image.fromarray(255 - np.array(img))
        else:  # RGB 이미지
            img = Image.fromarray(255 - np.array(img))
        
        return img
    
    def _process_light_mode(self, img: Image.Image) -> Image.Image:
        # 대비 향상
        enhancer = ImageEnhance.Contrast(img)
        img = enhancer.enhance(1.1)
        
        # 선명도 향상
        enhancer = ImageEnhance.Sharpness(img)
        img = enhancer.enhance(1.1)
        
        return img

    def _pil_to_qimage(self, img: Image.Image) -> QImage:
        # RGBA로 변환
        if img.mode != 'RGBA':
            img = img.convert('RGBA')
            
        # numpy 배열로 변환
        data = np.array(img)
        
        # 배경색 변환 (흰색을 검정색으로)
        r, g, b, a = data.T
        white_areas = (r > 240) & (g > 240) & (b > 240)
        data[..., :3][white_areas.T] = self.settings.background_color
        
        # QImage로 변환
        height, width = data.shape[:2]
        bytes_per_line = 4 * width
        qt_image = QImage(data.tobytes(), width, height, 
                         bytes_per_line, QImage.Format.Format_RGBA8888)
        
        return qt_image 

    def _on_upscale_complete(self, upscaled_path: str):
        """업스케일링 완료 시 호출되는 콜백"""
        if self.current_image_path == str(Path(upscaled_path).stem.replace('_upscaled', '')):
            if self.reload_callback:
                self.reload_callback() 