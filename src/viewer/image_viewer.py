from PyQt6.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, 
                           QLabel, QFileDialog, QStackedWidget)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QImage, QPixmap
from pathlib import Path
from viewer.image_processor import ImageProcessor
from config.settings import Settings
from models.library import Library
from models.book import Book
from typing import Optional
from .library_widget import LibraryWidget

class ImageViewer(QMainWindow):
    def __init__(self):
        super().__init__()
        self.settings = Settings()
        self.image_processor = ImageProcessor(self.settings)
        self.library = Library()
        self.current_book: Optional[Book] = None
        self.current_folder = None
        self.current_images = []
        self.current_index = -1
        
        self.init_ui()
        
    def init_ui(self):
        self.setWindowTitle('다크 리더')
        self.setGeometry(100, 100, 1200, 800)
        
        # 스택 위젯 설정
        self.stack = QStackedWidget()
        self.setCentralWidget(self.stack)
        
        # 라이브러리 뷰
        self.library_widget = LibraryWidget()
        self.library_widget.bookSelected.connect(self.open_book)
        self.stack.addWidget(self.library_widget)
        
        # 리더 뷰
        self.reader_widget = QWidget()
        reader_layout = QVBoxLayout(self.reader_widget)
        self.image_label = QLabel()
        self.image_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        reader_layout.addWidget(self.image_label)
        self.stack.addWidget(self.reader_widget)
        
        # 초기 라이브러리 로드
        self.library_widget.update_books(self.library.books)
        
        # 키보드 이벤트 활성화
        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        
    def keyPressEvent(self, event):
        if self.stack.currentWidget() == self.reader_widget:
            if event.key() == Qt.Key.Key_Left:
                self.show_previous_image()
            elif event.key() == Qt.Key.Key_Right:
                self.show_next_image()
            elif event.key() == Qt.Key.Key_Escape:
                self.show_library()
        if event.key() == Qt.Key.Key_O:
            self.open_folder()
            
    def open_book(self, book: Book):
        self.current_book = book
        self.load_folder(str(book.path))
        self.stack.setCurrentWidget(self.reader_widget)
        
    def show_library(self):
        self.library_widget.update_books(self.library.books)
        self.stack.setCurrentWidget(self.library_widget)
        
    def open_folder(self):
        folder = QFileDialog.getExistingDirectory(self, "폴더 선택")
        if folder:
            self.load_folder(folder)
            self.stack.setCurrentWidget(self.reader_widget)
            
    def load_folder(self, folder_path):
        print(f"Loading folder: {folder_path}")
        self.current_book = self.library.add_book(folder_path)
        self.current_images = sorted([
            f for f in Path(folder_path).glob("*")
            if f.suffix.lower() in ('.png', '.jpg', '.jpeg')
        ])
        print(f"Found {len(self.current_images)} images")
        
        if self.current_images:
            # 저장된 현재 페이지로 이동
            self.current_index = self.current_book.get_current_page()
            print(f"Starting from page {self.current_index}")
            self.show_current_image()
            self.stack.setCurrentWidget(self.reader_widget)
        else:
            from PyQt6.QtWidgets import QMessageBox
            QMessageBox.warning(self, "오류", "선택한 폴더에 이미지 파일이 없습니다.")
            
    def show_current_image(self):
        if 0 <= self.current_index < len(self.current_images):
            image_path = self.current_images[self.current_index]
            processed_image = self.image_processor.process_image(str(image_path))
            self.display_image(processed_image)
            
            # 현재 페이지 업데이트 및 저장
            if self.current_book:
                self.current_book.update_current_page(self.current_index)
                self.library.update_book(self.current_book)
                
                # 제목 표시줄에 현재 페이지 정보 표시
                self.setWindowTitle(f'다크 리더 - {self.current_book.title} ({self.current_index + 1}/{self.current_book.total_pages})')
            
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