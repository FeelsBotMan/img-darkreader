from pathlib import Path
import cv2
import numpy as np
from PIL import Image
import threading
from queue import Queue
from typing import Optional, Callable
from collections import OrderedDict
from io import BytesIO


class ImageUpscaler:
    def __init__(self, memory_cache_size: int = 5):
        self.processing_queue = Queue()
        self.processing_images = set()

        # 메모리 캐시 설정 (키: cache_key 문자열)
        self.memory_cache_size = memory_cache_size
        self.memory_cache: OrderedDict[str, np.ndarray] = OrderedDict()
        self.cache_lock = threading.Lock()

        # 캐시 디렉토리 초기화
        self.cache_dir = Path.home() / ".img-darkreader" / "cache"
        self.cache_dir.mkdir(parents=True, exist_ok=True)

        self._start_background_thread()

    def _add_to_memory_cache(self, cache_key: str, image: np.ndarray):
        """메모리 캐시에 이미지 추가"""
        with self.cache_lock:
            if len(self.memory_cache) >= self.memory_cache_size:
                self.memory_cache.popitem(last=False)
            self.memory_cache[cache_key] = image

    def _get_from_memory_cache(self, cache_key: str) -> Optional[np.ndarray]:
        """메모리 캐시에서 이미지 조회"""
        with self.cache_lock:
            if cache_key in self.memory_cache:
                image = self.memory_cache.pop(cache_key)
                self.memory_cache[cache_key] = image
                return image
            return None

    def _get_cache_path(self, cache_key: str) -> Path:
        """캐시된 이미지 경로 반환"""
        return self.cache_dir / f"{cache_key}_upscaled.jpg"

    def _get_from_disk_cache(self, cache_key: str) -> Optional[np.ndarray]:
        """디스크 캐시에서 이미지 조회"""
        cache_path = self._get_cache_path(cache_key)
        if cache_path.exists():
            try:
                return self._decode_image_bytes(cache_path.read_bytes())
            except Exception as e:
                print(f"디스크 캐시 읽기 오류: {e}")
        return None

    def _save_to_disk_cache(self, cache_key: str, image: np.ndarray):
        """이미지를 디스크 캐시에 저장"""
        cache_path = self._get_cache_path(cache_key)
        try:
            cv2.imwrite(str(cache_path), image)
        except Exception as e:
            print(f"디스크 캐시 저장 오류: {e}")

    @staticmethod
    def _decode_image_bytes(data: bytes) -> Optional[np.ndarray]:
        """바이트에서 OpenCV 이미지 디코딩"""
        try:
            return cv2.imdecode(np.frombuffer(data, dtype=np.uint8), cv2.IMREAD_COLOR)
        except Exception as e:
            print(f"이미지 디코딩 오류: {e}")
            return None

    def has_disk_cache(self, cache_key: str) -> bool:
        return self._get_cache_path(cache_key).exists()

    def upscale(
        self,
        cache_key: str,
        data: bytes,
        callback: Optional[Callable] = None,
        priority: bool = True,
    ) -> Optional[str]:
        """이미지 업스케일링 (메모리 캐시 확인 후 필요시 처리).

        캐시 히트 시에는 콜백을 호출하지 않습니다.
        (콜백이 UI를 다시 그리면 process → upscale → 콜백 재귀가 발생합니다.)
        백그라운드에서 새로 업스케일을 끝냈을 때만 callback을 호출합니다.
        """
        cached_image = self._get_from_memory_cache(cache_key)
        if cached_image is not None:
            return cache_key

        cached_image = self._get_from_disk_cache(cache_key)
        if cached_image is not None:
            self._add_to_memory_cache(cache_key, cached_image)
            return cache_key

        item = (cache_key, data, callback)
        if priority:
            temp_queue = Queue()
            while not self.processing_queue.empty():
                temp_queue.put(self.processing_queue.get())
            self.processing_queue.put(item)
            while not temp_queue.empty():
                self.processing_queue.put(temp_queue.get())
        else:
            self.processing_queue.put(item)

        return None

    def prefetch_images(self, items: list[tuple[str, bytes]]):
        """다음 이미지들을 미리 업스케일링 큐에 추가. items: (cache_key, bytes)"""
        for cache_key, data in items:
            self.upscale(cache_key, data, priority=False)

    def _process_image(self, img: np.ndarray) -> np.ndarray:
        """이미지 업스케일링 처리"""
        h, w = img.shape[:2]
        return cv2.resize(img, (w * 2, h * 2), interpolation=cv2.INTER_LANCZOS4)

    def is_processing(self, cache_key: str) -> bool:
        """이미지가 현재 처리 중인지 확인"""
        return cache_key in self.processing_images

    def _start_background_thread(self):
        """백그라운드 처리 스레드 시작"""

        def process_queue():
            while True:
                cache_key, data, callback = self.processing_queue.get()
                try:
                    self.processing_images.add(cache_key)

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
                finally:
                    self.processing_images.discard(cache_key)
                    self.processing_queue.task_done()

        thread = threading.Thread(target=process_queue, daemon=True)
        thread.start()
