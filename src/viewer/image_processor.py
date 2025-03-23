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
            #print(f"이미지 로드 시작: {image_path}")
            img = Image.open(image_path)
            if img is None:
                print(f"이미지 로드 실패: {image_path}")
                return None
            #print(f"이미지 로드 완료: 크기={img.size}, 모드={img.mode}")
            
            # 이미지 처리
            if self.settings.is_dark_mode:
                #print("다크모드 처리 시작")
                img = self._process_dark_mode(img)
            else:
                #print("라이트모드 처리 시작")
                img = self._process_light_mode(img)
            #print(f"이미지 처리 완료: 크기={img.size}, 모드={img.mode}")
            
            # PIL -> QImage 변환
            #print("QImage 변환 시작")
            result = self._pil_to_qimage(img)
            if result is None:
                print(f"이미지 변환 실패: {image_path}")
                return None
            #print(f"QImage 변환 완료: 크기={result.size()}, 포맷={result.format()}")
            
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
        
        # 밝기 계산 (그레이스케일)
        brightness = np.mean(data, axis=2)
        
        # 임계값 기반 마스크 생성 (밝은 부분 검출)
        # 임계값을 220으로 낮춰 더 많은 밝은 영역을 포함
        bright_mask = brightness > 220
        
        # 색상 반전
        data = 255 - data
        
        # 밝은 부분(텍스트 영역)을 검정색으로 변환
        data[bright_mask] = [0, 0, 0]
        
        # 대비 향상
        data = np.clip((data.astype(float) * 1.4), 0, 255).astype(np.uint8)
        
        # 어두운 부분 더 어둡게
        dark_mask = brightness <= 220
        data[dark_mask] = np.clip(data[dark_mask] * 0.8, 0, 255).astype(np.uint8)
        
        # PIL 이미지로 변환
        img = Image.fromarray(data)
        
        # 선명도 향상
        enhancer = ImageEnhance.Sharpness(img)
        img = enhancer.enhance(1.2)
        
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
        try:
            # RGBA로 변환
            if img.mode != 'RGBA':
                #print(f"이미지 모드 변환: {img.mode} -> RGBA")
                img = img.convert('RGBA')
                
            # numpy 배열로 변환
            data = np.array(img)
            #print(f"numpy 배열 생성: shape={data.shape}, dtype={data.dtype}")
            
            # 밝기 계산 (알파 채널 제외)
            brightness = np.mean(data[..., :3], axis=2)
            
            # 임계값 기반 마스크 생성
            bright_mask = brightness > 220
            
            if self.settings.is_dark_mode:
                # 다크모드: 밝은 부분을 검정색으로
                data[..., :3][bright_mask] = [0, 0, 0]
            else:
                # 라이트모드: 밝은 부분을 흰색으로
                data[..., :3][bright_mask] = [255, 255, 255]
            
            # 알파 채널 설정 (완전 불투명)
            data[..., 3] = 255
            
            # QImage로 변환
            height, width = data.shape[:2]
            bytes_per_line = 4 * width
            
            # 데이터가 연속적인지 확인하고 필요한 경우 복사
            if not data.flags['C_CONTIGUOUS']:
                print("데이터를 연속적인 메모리로 복사")
                data = np.ascontiguousarray(data)
            
            qt_image = QImage(data.tobytes(), width, height, 
                            bytes_per_line, QImage.Format.Format_RGBA8888)
            
            # 이미지가 유효한지 확인
            if qt_image.isNull():
                print("QImage 변환 실패")
                return None
                
            #print(f"QImage 생성 성공: 크기={qt_image.size()}, 포맷={qt_image.format()}")
            return qt_image.copy()  # 깊은 복사본 반환
            
        except Exception as e:
            print(f"이미지 변환 중 오류 발생: {e}")
            return None

    def _on_upscale_complete(self, upscaled_path: str):
        """업스케일링 완료 시 호출되는 콜백"""
        if self.current_image_path == str(Path(upscaled_path).stem.replace('_upscaled', '')):
            if self.reload_callback:
                self.reload_callback() 