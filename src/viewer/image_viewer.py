from PyQt6.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, 
                           QLabel, QFileDialog)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QImage, QPixmap
from pathlib import Path
from .image_processor import ImageProcessor
from ..config.settings import Settings

class ImageViewer(QMainWindow):
    def __init__(self):
        super().__init__()
        self.settings = Settings()
        self.image_processor = ImageProcessor(self.settings)
        self.current_folder = None
        self.current_images = []
        self.current_index = -1
        
        self.init_ui()
        
    def init_ui(self):
        self.setWindowTitle('다크 리더')
        self.setGeometry(100, 100, 800, 600)
        
        # 중앙 위젯 설정
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)
        
        # 이미지 표시 레이블
        self.image_label = QLabel()
        self.image_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.image_label)
        
        # 키보드 이벤트 활성화
        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        
    def keyPressEvent(self, event):
        if event.key() == Qt.Key.Key_Left:
            self.show_previous_image()
        elif event.key() == Qt.Key.Key_Right:
            self.show_next_image()
        elif event.key() == Qt.Key.Key_O:
            self.open_folder()
            
    def open_folder(self):
        folder = QFileDialog.getExistingDirectory(self, "폴더 선택")
        if folder:
            self.load_folder(folder)
            
    def load_folder(self, folder_path):
        self.current_folder = Path(folder_path)
        self.current_images = sorted([
            f for f in self.current_folder.glob("*")
            if f.suffix.lower() in ('.png', '.jpg', '.jpeg')
        ])
        if self.current_images:
            self.current_index = 0
            self.show_current_image()
            
    def show_current_image(self):
        if 0 <= self.current_index < len(self.current_images):
            image_path = self.current_images[self.current_index]
            processed_image = self.image_processor.process_image(str(image_path))
            self.display_image(processed_image)
            
    def show_next_image(self):
        if self.current_images and self.current_index < len(self.current_images) - 1:
            self.current_index += 1
            self.show_current_image()
            
    def show_previous_image(self):
        if self.current_images and self.current_index > 0:
            self.current_index -= 1
            self.show_current_image()
            
    def display_image(self, image):
        height = self.image_label.height()
        width = self.image_label.width()
        
        pixmap = QPixmap.fromImage(image)
        scaled_pixmap = pixmap.scaled(width, height, 
                                    Qt.AspectRatioMode.KeepAspectRatio,
                                    Qt.TransformationMode.SmoothTransformation)
        self.image_label.setPixmap(scaled_pixmap) 