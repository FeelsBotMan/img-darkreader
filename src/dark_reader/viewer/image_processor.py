"""이미지 다크/라이트 처리 및 업스케일 연동."""
from __future__ import annotations

import logging
from io import BytesIO

import cv2
import numpy as np
from PIL import Image, ImageEnhance
from PyQt6.QtCore import QObject, pyqtSignal
from PyQt6.QtGui import QImage

from ..config.settings import Settings
from ..utils.upscaler import ImageUpscaler

logger = logging.getLogger(__name__)


class ImageProcessor(QObject):
    """원본 → (캐시된) 2× 업스케일 → 다크/라이트 보정을 적용합니다."""

    upscale_completed = pyqtSignal(str)

    def __init__(self, settings: Settings, parent: QObject | None = None):
        super().__init__(parent)
        self.settings = settings
        self.upscaler = ImageUpscaler(memory_cache_size=5)
        self.current_cache_key: str | None = None
        self.reload_callback = None
        self._processing = False
        self.upscale_completed.connect(self._on_upscale_completed_main)

    def set_reload_callback(self, callback) -> None:
        self.reload_callback = callback

    def process_bytes(self, data: bytes, cache_key: str) -> QImage | None:
        """바이트 이미지를 처리해 QImage로 반환합니다.

        업스케일 캐시가 있으면 2× 이미지를 쓰고, 없으면 원본으로 표시한 뒤
        백그라운드 업스케일을 요청합니다.
        """
        self.current_cache_key = cache_key
        self._processing = True
        try:
            upscaled = self.upscaler.get_cached(cache_key)
            if upscaled is not None:
                img = self._bgr_to_pil(upscaled)
            else:
                img = Image.open(BytesIO(data))
                img.load()
                self.upscaler.upscale(
                    cache_key, data, self._emit_upscale_completed
                )

            if self.settings.is_dark_mode:
                img = self._process_dark_mode(img)
            else:
                img = self._process_light_mode(img)

            result = self._pil_to_qimage(img)
            if result is None:
                logger.error("이미지 변환 실패: %s", cache_key)
            return result
        except Exception:
            logger.exception("이미지 처리 중 오류: %s", cache_key)
            return None
        finally:
            self._processing = False

    def _emit_upscale_completed(self, cache_key: str) -> None:
        """워커 스레드에서 호출 → 시그널로 메인 스레드에 전달."""
        self.upscale_completed.emit(cache_key)

    def _on_upscale_completed_main(self, cache_key: str) -> None:
        if self._processing:
            return
        if self.current_cache_key == cache_key and self.reload_callback:
            self.reload_callback()

    def _process_dark_mode(self, img: Image.Image) -> Image.Image:
        if img.mode != "RGB":
            img = img.convert("RGB")

        theme = self.settings.current_theme
        data = np.array(img)
        inverted = 255 - data
        # 기본 dark brightness=0.9 → 기존과 동일한 ~1.3 배율
        brightness_factor = theme.brightness * (1.3 / 0.9)
        result = np.clip(inverted * brightness_factor, 0, 255).astype(np.uint8)
        out = Image.fromarray(result)
        out = ImageEnhance.Contrast(out).enhance(theme.contrast)
        out = ImageEnhance.Sharpness(out).enhance(theme.sharpness)
        return out

    def _process_light_mode(self, img: Image.Image) -> Image.Image:
        theme = self.settings.current_theme
        if img.mode != "RGB":
            img = img.convert("RGB")
        img = ImageEnhance.Contrast(img).enhance(theme.contrast)
        img = ImageEnhance.Brightness(img).enhance(theme.brightness)
        img = ImageEnhance.Sharpness(img).enhance(theme.sharpness)
        return img

    @staticmethod
    def _bgr_to_pil(bgr: np.ndarray) -> Image.Image:
        rgb = cv2.cvtColor(bgr, cv2.COLOR_BGR2RGB)
        return Image.fromarray(rgb)

    def _pil_to_qimage(self, img: Image.Image) -> QImage | None:
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
        except Exception:
            logger.exception("PIL→QImage 변환 오류")
            return None
