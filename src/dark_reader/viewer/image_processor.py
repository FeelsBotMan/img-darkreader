from io import BytesIO

from PIL import Image, ImageEnhance
import numpy as np
from PyQt6.QtGui import QImage
from ..config.settings import Settings
from ..utils.upscaler import ImageUpscaler


class ImageProcessor:
    def __init__(self, settings: Settings):
        self.settings = settings
        self.upscaler = ImageUpscaler(memory_cache_size=5)
        self.current_cache_key = None
        self.reload_callback = None  # 이미지 리로드 콜백
        self._processing = False

    def set_reload_callback(self, callback):
        """이미지 리로드 콜백 설정"""
        self.reload_callback = callback

    def process_bytes(self, data: bytes, cache_key: str) -> QImage:
        """바이트 이미지 데이터를 처리합니다."""
        self.current_cache_key = cache_key
        self._processing = True
        try:
            img = Image.open(BytesIO(data))
            # 지연 디코딩으로 일부 손상 파일을 놓칠 수 있어 즉시 로드
            img.load()

            if self.settings.is_dark_mode:
                img = self._process_dark_mode(img)
            else:
                img = self._process_light_mode(img)

            result = self._pil_to_qimage(img)
            if result is None:
                print(f"이미지 변환 실패: {cache_key}")
                return None

            self.upscaler.upscale(cache_key, data, self._on_upscale_complete)
            return result

        except Exception as e:
            print(f"이미지 처리 중 오류 발생: {e}")
            return None
        finally:
            self._processing = False

    def _process_dark_mode(self, img: Image.Image) -> Image.Image:
        if img.mode != "RGB":
            img = img.convert("RGB")

        data = np.array(img)
        inverted_data = 255 - data
        brightness_factor = 1.3
        brightened_inverted_data = np.clip(
            inverted_data * brightness_factor, 0, 255
        ).astype(np.uint8)
        return Image.fromarray(brightened_inverted_data)

    def _process_light_mode(self, img: Image.Image) -> Image.Image:
        enhancer = ImageEnhance.Contrast(img)
        img = enhancer.enhance(1.1)
        enhancer = ImageEnhance.Sharpness(img)
        img = enhancer.enhance(1.1)
        return img

    def _pil_to_qimage(self, img: Image.Image) -> QImage:
        try:
            if img.mode != "RGBA":
                img = img.convert("RGBA")
            data = img.tobytes("raw", "RGBA")
            width, height = img.size
            bytes_per_line = 4 * width
            qt_image = QImage(
                data, width, height, bytes_per_line, QImage.Format.Format_RGBA8888
            )
            return qt_image.copy()
        except Exception as e:
            print(f"이미지 변환 중 오류 발생: {e}")
            return None

    def _on_upscale_complete(self, cache_key: str):
        """업스케일링 완료 시 호출되는 콜백 (백그라운드 스레드에서 호출됨)."""
        if self._processing:
            return
        if self.current_cache_key == cache_key and self.reload_callback:
            self.reload_callback()
