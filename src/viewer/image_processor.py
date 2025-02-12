from PIL import Image
from PyQt6.QtGui import QImage
import numpy as np

class ImageProcessor:
    def __init__(self, settings):
        self.settings = settings
        
    def process_image(self, image_path):
        # PIL로 이미지 로드
        image = Image.open(image_path)
        
        # RGBA로 변환
        if image.mode != 'RGBA':
            image = image.convert('RGBA')
            
        # numpy 배열로 변환
        data = np.array(image)
        
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