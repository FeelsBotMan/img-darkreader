from pathlib import Path
import cv2
import numpy as np
from PIL import Image
import threading
from queue import Queue
from typing import Optional, Callable, Dict
from collections import OrderedDict

class ImageUpscaler:
    def __init__(self, memory_cache_size: int = 5):
        self.processing_queue = Queue()
        self.processing_images = set()
        
        # 메모리 캐시 설정
        self.memory_cache_size = memory_cache_size
        self.memory_cache: OrderedDict[str, np.ndarray] = OrderedDict()
        self.cache_lock = threading.Lock()
        
        self._start_background_thread()
    
    def _add_to_memory_cache(self, image_path: str, image: np.ndarray):
        """메모리 캐시에 이미지 추가"""
        with self.cache_lock:
            if len(self.memory_cache) >= self.memory_cache_size:
                self.memory_cache.popitem(last=False)  # 가장 오래된 항목 제거
            self.memory_cache[str(image_path)] = image
    
    def _get_from_memory_cache(self, image_path: str) -> Optional[np.ndarray]:
        """메모리 캐시에서 이미지 조회"""
        with self.cache_lock:
            if str(image_path) in self.memory_cache:
                # 캐시 히트 시 해당 항목을 가장 최근 사용으로 이동
                image = self.memory_cache.pop(str(image_path))
                self.memory_cache[str(image_path)] = image
                return image
            return None

    def _get_cache_path(self, image_path: Path) -> Path:
        """캐시된 이미지 경로 반환"""
        return self.cache_dir / f"{image_path.stem}_upscaled{image_path.suffix}"
    
    def _read_image(self, path: str) -> Optional[np.ndarray]:
        """한글 경로 지원하는 이미지 읽기"""
        try:
            return cv2.imdecode(
                np.fromfile(path, dtype=np.uint8), 
                cv2.IMREAD_COLOR
            )
        except Exception as e:
            print(f"이미지 읽기 오류: {e}")
            return None
        
    def upscale(self, image_path: str | Path, callback: Optional[Callable] = None, 
                priority: bool = True) -> Optional[str]:
        """이미지 업스케일링 (메모리 캐시 확인 후 필요시 처리)"""
        image_path = Path(image_path)
        
        # 메모리 캐시 확인
        cached_image = self._get_from_memory_cache(str(image_path))
        if cached_image is not None:
            if callback:
                callback(str(image_path))
            return str(image_path)
        
        # 우선순위가 높은 작업은 큐의 앞쪽에 추가
        if priority:
            # 기존 큐의 내용을 임시 저장
            temp_queue = Queue()
            while not self.processing_queue.empty():
                temp_queue.put(self.processing_queue.get())
            # 새 작업을 먼저 추가
            self.processing_queue.put((image_path, callback))
            # 기존 작업들을 다시 추가
            while not temp_queue.empty():
                self.processing_queue.put(temp_queue.get())
        else:
            self.processing_queue.put((image_path, callback))
        
        return None

    def prefetch_images(self, image_paths: list[Path | str]):
        """다음 이미지들을 미리 업스케일링 큐에 추가"""
        for path in image_paths:
            self.upscale(path, priority=False)

    def _process_image(self, img: np.ndarray) -> np.ndarray:
        """이미지 업스케일링 처리"""
        h, w = img.shape[:2]
        return cv2.resize(img, (w*2, h*2), interpolation=cv2.INTER_LANCZOS4)

    def is_processing(self, image_path: str | Path) -> bool:
        """이미지가 현재 처리 중인지 확인"""
        return str(image_path) in self.processing_images
    
    def _start_background_thread(self):
        """백그라운드 처리 스레드 시작"""
        def process_queue():
            while True:
                image_path, callback = self.processing_queue.get()
                try:
                    self.processing_images.add(str(image_path))
                    
                    # 이미지 로드
                    img = self._read_image(str(image_path))
                    if img is None:
                        pil_img = Image.open(image_path)
                        if pil_img.mode != 'RGB':
                            pil_img = pil_img.convert('RGB')
                        img = cv2.cvtColor(np.array(pil_img), cv2.COLOR_RGB2BGR)
                    
                    # 이미지 처리
                    output = self._process_image(img)
                    
                    # 메모리 캐시에 추가
                    self._add_to_memory_cache(str(image_path), output)
                    
                    if callback:
                        callback(str(image_path))
                finally:
                    self.processing_images.remove(str(image_path))
                    self.processing_queue.task_done()
        
        thread = threading.Thread(target=process_queue, daemon=True)
        thread.start() 