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

        try:
            # 이미지 로드
            img = Image.open(image_path)
            if img is None:
                print(f"이미지 로드 실패: {image_path}")
                return None

            # 이미지 처리
            if self.settings.is_dark_mode:
                img = self._process_dark_mode(img)
            else:
                img = self._process_light_mode(img)

            # PIL -> QImage 변환
            result = self._pil_to_qimage(img)
            if result is None:
                print(f"이미지 변환 실패: {image_path}")
                return None

            # 백그라운드에서 업스케일링 처리
            self.upscaler.upscale(image_path, self._on_upscale_complete)

            return result

        except Exception as e:
            print(f"이미지 처리 중 오류 발생: {e}")
            return None

    def _process_dark_mode(self, img: Image.Image) -> Image.Image:
        # 이미지를 RGB로 변환
        if img.mode != 'RGB':
            img = img.convert('RGB')

        # numpy 배열로 변환
        data = np.array(img)

        # 색상 반전
        inverted_data = 255 - data

        # 밝기 조절 (반전된 이미지에서 텍스트를 더 밝게)
        brightness_factor = 1.3  # 밝기 증가 비율 조정 가능
        brightened_inverted_data = np.clip(inverted_data * brightness_factor, 0, 255).astype(np.uint8)

        # PIL 이미지로 변환
        img = Image.fromarray(brightened_inverted_data)

        return img

    def _process_light_mode(self, img: Image.Image) -> Image.Image:
        # 기본적인 라이트 모드 처리는 그대로 유지하거나 필요에 따라 조정
        enhancer = ImageEnhance.Contrast(img)
        img = enhancer.enhance(1.1)
        enhancer = ImageEnhance.Sharpness(img)
        img = enhancer.enhance(1.1)
        return img

    def _pil_to_qimage(self, img: Image.Image) -> QImage:
        try:
            if img.mode != 'RGBA':
                img = img.convert('RGBA')
            data = img.tobytes('raw', 'RGBA')
            width, height = img.size
            bytes_per_line = 4 * width
            qt_image = QImage(data, width, height, bytes_per_line, QImage.Format.Format_RGBA8888)
            return qt_image.copy()
        except Exception as e:
            print(f"이미지 변환 중 오류 발생: {e}")
            return None

    def _on_upscale_complete(self, upscaled_path: str):
        """업스케일링 완료 시 호출되는 콜백"""
        if self.current_image_path == str(Path(upscaled_path).stem.replace('_upscaled', '')):
            if self.reload_callback:
                self.reload_callback()