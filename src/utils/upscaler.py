from pathlib import Path
import cv2
import numpy as np
from PIL import Image
import threading
from queue import Queue
from typing import Optional, Callable

class ImageUpscaler:
    def __init__(self, cache_dir: Path):
        self.cache_dir = cache_dir
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.processing_queue = Queue()
        self.processing_images = set()  # 현재 처리 중인 이미지 추적
        self._start_background_thread()
    
    def _get_cache_path(self, image_path: Path) -> Path:
        """캐시된 이미지 경로 반환"""
        return self.cache_dir / f"{image_path.stem}_upscaled{image_path.suffix}"
    
    def upscale(self, image_path: str | Path, callback: Optional[Callable] = None) -> Optional[str]:
        """이미지 업스케일링 (캐시 확인 후 필요시 처리)"""
        image_path = Path(image_path)
        cache_path = self._get_cache_path(image_path)
        
        if cache_path.exists():
            if callback:
                callback(str(cache_path))
            return str(cache_path)
        
        # 큐에 작업 추가
        self.processing_queue.put((image_path, cache_path, callback))
        return None
    
    def _process_image(self, img: np.ndarray) -> np.ndarray:
        """이미지 업스케일링 처리"""
        # Lanczos 보간법으로 2배 확대
        h, w = img.shape[:2]
        return cv2.resize(img, (w*2, h*2), interpolation=cv2.INTER_LANCZOS4)
    
    def is_processing(self, image_path: str | Path) -> bool:
        """이미지가 현재 처리 중인지 확인"""
        return str(image_path) in self.processing_images
    
    def _start_background_thread(self):
        """백그라운드 처리 스레드 시작"""
        def process_queue():
            while True:
                image_path, cache_path, callback = self.processing_queue.get()
                try:
                    self.processing_images.add(str(image_path))
                    
                    # 한글 경로 지원을 위해 np.fromfile 사용
                    img_array = np.fromfile(str(image_path), np.uint8)
                    img = cv2.imdecode(img_array, cv2.IMREAD_COLOR)
                    if img is None:
                        # OpenCV로 읽기 실패시 PIL로 시도
                        pil_img = Image.open(image_path)
                        if pil_img.mode != 'RGB':
                            pil_img = pil_img.convert('RGB')
                        img = cv2.cvtColor(np.array(pil_img), cv2.COLOR_RGB2BGR)
                    
                    # 이미지 처리
                    output = self._process_image(img)
                    
                    # 한글 경로 지원을 위해 imencode 사용
                    _, encoded_img = cv2.imencode(Path(cache_path).suffix, output, 
                                                [cv2.IMWRITE_JPEG_QUALITY, 95])
                    encoded_img.tofile(str(cache_path))
                    
                    if callback:
                        callback(str(cache_path))
                finally:
                    self.processing_images.remove(str(image_path))
                    self.processing_queue.task_done()
        
        thread = threading.Thread(target=process_queue, daemon=True)
        thread.start() 