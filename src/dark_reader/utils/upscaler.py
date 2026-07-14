"""이미지 업스케일(2x Lanczos) 및 메모리/디스크 캐시."""
from __future__ import annotations

import itertools
import logging
import threading
from collections import OrderedDict
from io import BytesIO
from pathlib import Path
from queue import Empty, PriorityQueue
from typing import Callable, Optional

import cv2
import numpy as np
from PIL import Image

from ..config.paths import AppPaths

logger = logging.getLogger(__name__)

# 우선순위: 숫자가 작을수록 먼저 처리
_PRIORITY_HIGH = 0
_PRIORITY_LOW = 1

# 디스크 캐시 기본 한도 (바이트)
_DEFAULT_DISK_CACHE_MAX_BYTES = 500 * 1024 * 1024


class ImageUpscaler:
    def __init__(
        self,
        memory_cache_size: int = 5,
        disk_cache_max_bytes: int = _DEFAULT_DISK_CACHE_MAX_BYTES,
        cache_dir: Path | None = None,
    ):
        self.memory_cache_size = memory_cache_size
        self.disk_cache_max_bytes = disk_cache_max_bytes
        self.memory_cache: OrderedDict[str, np.ndarray] = OrderedDict()
        self.cache_lock = threading.Lock()

        self._queue: PriorityQueue = PriorityQueue()
        self._queue_lock = threading.Lock()
        self._queued_or_processing: set[str] = set()
        self._counter = itertools.count()

        self.cache_dir = cache_dir or AppPaths.upscale_cache_dir()
        self.cache_dir.mkdir(parents=True, exist_ok=True)

        self._start_background_thread()

    def _add_to_memory_cache(self, cache_key: str, image: np.ndarray) -> None:
        with self.cache_lock:
            if len(self.memory_cache) >= self.memory_cache_size:
                self.memory_cache.popitem(last=False)
            self.memory_cache[cache_key] = image

    def _get_from_memory_cache(self, cache_key: str) -> Optional[np.ndarray]:
        with self.cache_lock:
            if cache_key in self.memory_cache:
                image = self.memory_cache.pop(cache_key)
                self.memory_cache[cache_key] = image
                return image
            return None

    def get_cached(self, cache_key: str) -> Optional[np.ndarray]:
        """메모리 또는 디스크 캐시에서 업스케일 이미지를 반환합니다."""
        cached = self._get_from_memory_cache(cache_key)
        if cached is not None:
            return cached
        cached = self._get_from_disk_cache(cache_key)
        if cached is not None:
            self._add_to_memory_cache(cache_key, cached)
            return cached
        return None

    def _get_cache_path(self, cache_key: str) -> Path:
        return self.cache_dir / f"{cache_key}_upscaled.jpg"

    def _get_from_disk_cache(self, cache_key: str) -> Optional[np.ndarray]:
        cache_path = self._get_cache_path(cache_key)
        if cache_path.exists():
            try:
                return self._decode_image_bytes(cache_path.read_bytes())
            except OSError as e:
                logger.warning("디스크 캐시 읽기 오류: %s", e)
        return None

    def _save_to_disk_cache(self, cache_key: str, image: np.ndarray) -> None:
        cache_path = self._get_cache_path(cache_key)
        try:
            if not cv2.imwrite(str(cache_path), image):
                logger.warning("디스크 캐시 저장 실패: %s", cache_path)
                return
            self._enforce_disk_cache_limit()
        except OSError as e:
            logger.warning("디스크 캐시 저장 오류: %s", e)

    def _enforce_disk_cache_limit(self) -> None:
        """캐시 총량이 한도를 넘으면 오래된 파일부터 삭제합니다."""
        try:
            files = [
                p
                for p in self.cache_dir.glob("*_upscaled.jpg")
                if p.is_file()
            ]
            files.sort(key=lambda p: p.stat().st_mtime)
            total = sum(p.stat().st_size for p in files)
            while total > self.disk_cache_max_bytes and files:
                oldest = files.pop(0)
                size = oldest.stat().st_size
                try:
                    oldest.unlink()
                    total -= size
                    logger.debug("캐시 한도 초과로 삭제: %s", oldest)
                except OSError as e:
                    logger.warning("캐시 파일 삭제 실패: %s", e)
                    break
        except OSError as e:
            logger.warning("캐시 한도 검사 오류: %s", e)

    @staticmethod
    def _decode_image_bytes(data: bytes) -> Optional[np.ndarray]:
        try:
            arr = np.frombuffer(data, dtype=np.uint8)
            return cv2.imdecode(arr, cv2.IMREAD_COLOR)
        except Exception as e:
            logger.warning("이미지 디코딩 오류: %s", e)
            return None

    def has_disk_cache(self, cache_key: str) -> bool:
        return self._get_cache_path(cache_key).exists()

    def is_cached(self, cache_key: str) -> bool:
        with self.cache_lock:
            if cache_key in self.memory_cache:
                return True
        return self.has_disk_cache(cache_key)

    def upscale(
        self,
        cache_key: str,
        data: bytes,
        callback: Optional[Callable[[str], None]] = None,
        priority: bool = True,
    ) -> Optional[str]:
        """이미지 업스케일링.

        캐시 히트 시 cache_key를 반환하고 콜백은 호출하지 않습니다.
        백그라운드에서 새로 처리가 끝난 뒤에만 callback을 호출합니다.
        """
        if self.get_cached(cache_key) is not None:
            return cache_key

        pri = _PRIORITY_HIGH if priority else _PRIORITY_LOW
        with self._queue_lock:
            if cache_key in self._queued_or_processing:
                return None
            self._queued_or_processing.add(cache_key)
            seq = next(self._counter)
            self._queue.put((pri, seq, cache_key, data, callback))
        return None

    def prefetch_images(self, items: list[tuple[str, bytes]]) -> None:
        for cache_key, data in items:
            self.upscale(cache_key, data, priority=False)

    def _process_image(self, img: np.ndarray) -> np.ndarray:
        h, w = img.shape[:2]
        return cv2.resize(img, (w * 2, h * 2), interpolation=cv2.INTER_LANCZOS4)

    def is_processing(self, cache_key: str) -> bool:
        with self._queue_lock:
            return cache_key in self._queued_or_processing

    def _start_background_thread(self) -> None:
        def process_queue() -> None:
            while True:
                try:
                    _pri, _seq, cache_key, data, callback = self._queue.get(
                        timeout=1.0
                    )
                except Empty:
                    continue

                try:
                    if self.get_cached(cache_key) is not None:
                        if callback:
                            callback(cache_key)
                        continue

                    img = self._decode_image_bytes(data)
                    if img is None:
                        pil_img = Image.open(BytesIO(data))
                        if pil_img.mode != "RGB":
                            pil_img = pil_img.convert("RGB")
                        img = cv2.cvtColor(np.array(pil_img), cv2.COLOR_RGB2BGR)

                    output = self._process_image(img)
                    self._add_to_memory_cache(cache_key, output)
                    self._save_to_disk_cache(cache_key, output)

                    if callback:
                        callback(cache_key)
                except Exception:
                    logger.exception("업스케일 처리 실패: %s", cache_key)
                finally:
                    with self._queue_lock:
                        self._queued_or_processing.discard(cache_key)
                    self._queue.task_done()

        thread = threading.Thread(target=process_queue, daemon=True, name="upscaler")
        thread.start()
