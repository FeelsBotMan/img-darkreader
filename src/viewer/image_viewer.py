from PyQt6.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, 
                           QLabel, QFileDialog, QStackedWidget, QSizePolicy,
                           QScrollArea)
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
        self.image_processor.set_reload_callback(self.reload_current_image)
        self.library = Library()
        self.current_book: Optional[Book] = None
        self.current_folder = None
        self.current_images = []
        self.current_index = -1
        
        self.init_ui()
        self.apply_theme()  # 초기 테마 적용
        
        # 상태 표시 레이블 추가
        self.status_label = QLabel()
        self.statusBar().addWidget(self.status_label)
        
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
        reader_layout.setContentsMargins(0, 0, 0, 0)  # 여백 제거
        reader_layout.setSpacing(0)  # 간격 제거
        
        # 이미지 레이블 설정
        self.image_label = QLabel()
        self.image_label.setObjectName("image_label")  # 스타일시트에서 참조할 ID 설정
        self.image_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.image_label.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        
        # 컨테이너 위젯 생성
        container = QWidget()
        container.setStyleSheet("background-color: transparent;")  # 배경을 투명하게 설정
        container_layout = QVBoxLayout(container)
        container_layout.setContentsMargins(0, 0, 0, 0)
        container_layout.addWidget(self.image_label)
        
        # 스크롤 영역 설정
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidget(container)
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self.scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self.scroll_area.setStyleSheet("QScrollArea { border: none; }")
        
        # 메인 레이아웃에 스크롤 영역 추가
        reader_layout.addWidget(self.scroll_area)
        
        self.stack.addWidget(self.reader_widget)
        
        # 초기 라이브러리 로드
        self.library_widget.update_books(self.library.books)
        
        # 키보드 이벤트 활성화
        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        self.reader_widget.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        self.scroll_area.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        
    def keyPressEvent(self, event):
        #print(f"키 이벤트 발생: {event.key()}")  # 디버깅을 위한 로그 추가
        if self.stack.currentWidget() == self.reader_widget:
            if event.key() == Qt.Key.Key_Left:
                #print("이전 이미지로 이동")
                self.show_previous_image()
                event.accept()  # 이벤트 처리 완료 표시
                return
            elif event.key() == Qt.Key.Key_Right:
                #print("다음 이미지로 이동")
                self.show_next_image()
                event.accept()  # 이벤트 처리 완료 표시
                return
            elif event.key() == Qt.Key.Key_Escape:
                self.show_library()
                event.accept()
                return
            # 가독성 조정 단축키
            elif event.key() == Qt.Key.Key_BracketLeft:  # [
                self.adjust_contrast(-0.1)
                event.accept()
                return
            elif event.key() == Qt.Key.Key_BracketRight:  # ]
                self.adjust_contrast(0.1)
                event.accept()
                return
            elif event.key() == Qt.Key.Key_Minus:  # -
                self.adjust_brightness(-0.1)
                event.accept()
                return
            elif event.key() == Qt.Key.Key_Equal:  # =
                self.adjust_brightness(0.1)
                event.accept()
                return
            elif event.key() == Qt.Key.Key_Comma:  # ,
                self.adjust_sharpness(-0.1)
                event.accept()
                return
            elif event.key() == Qt.Key.Key_Period:  # .
                self.adjust_sharpness(0.1)
                event.accept()
                return
        
        if event.key() == Qt.Key.Key_O:
            self.open_folder()
            event.accept()
            return
        elif event.key() == Qt.Key.Key_T:  # T키로 테마 전환
            self.toggle_theme()
            event.accept()
            return
            
        event.ignore()  # 처리되지 않은 이벤트는 무시
        
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
            #print(f"이미지 처리 시작: {image_path}")
            processed_image = self.image_processor.process_image(str(image_path))
            #print(f"이미지 처리 완료: {image_path}")
            self.display_image(processed_image)
            
            # 다음 페이지들 미리 업스케일링
            next_images = []
            for i in range(1, 3):  # 다음 2페이지를 미리 처리
                next_index = self.current_index + i
                if next_index < len(self.current_images):
                    next_images.append(self.current_images[next_index])
            if next_images:
                #print(f"다음 페이지 미리 처리: {next_images}")
                self.image_processor.upscaler.prefetch_images(next_images)
            
            # 현재 페이지 업데이트 및 저장
            if self.current_book:
                self.current_book.update_current_page(self.current_index)
                self.library.update_book(self.current_book)
                
                # 제목 표시줄에 현재 페이지 정보 표시
                self.setWindowTitle(f'다크 리더 - {self.current_book.title} ({self.current_index + 1}/{self.current_book.total_pages})')
            
            # 업스케일링 상태 확인
            cache_path = self.image_processor.upscaler._get_cache_path(Path(image_path))
            if cache_path.exists():
                self.status_label.setText("업스케일링 완료")
            else:
                self.status_label.setText("업스케일링 처리 중...")
            
            # 포커스 설정
            self.setFocus()
            
    def show_next_image(self):
        if self.current_images and self.current_index < len(self.current_images) - 1:
            self.current_index += 1
            self.show_current_image()
            
    def show_previous_image(self):
        if self.current_images and self.current_index > 0:
            self.current_index -= 1
            self.show_current_image()
            
    def display_image(self, image):
        if image is None or image.isNull():
            print("이미지가 유효하지 않습니다.")
            return
            
        # 스크롤 영역의 실제 크기 가져오기
        scroll_size = self.scroll_area.viewport().size()
        if scroll_size.width() <= 0 or scroll_size.height() <= 0:
            print(f"스크롤 영역 크기가 유효하지 않습니다: {scroll_size}")
            return
            
        # 이미지 크기 계산
        image_size = image.size()
        image_ratio = image_size.width() / image_size.height()
        
        # 이미지를 창 너비에 맞추기
        scaled_width = scroll_size.width()
        scaled_height = int(scaled_width / image_ratio)
        
        #print(f"이미지 정보: 크기={image_size}, 포맷={image.format()}, 깊이={image.depth()}")
        #print(f"스크롤 영역 크기: {scroll_size}")
        
        # QPixmap 생성 및 설정
        pixmap = QPixmap.fromImage(image)
        if pixmap.isNull():
            print("QPixmap 변환 실패")
            return
            
        # 이미지 스케일링
        scaled_pixmap = pixmap.scaled(
            scaled_width,
            scaled_height,
            Qt.AspectRatioMode.KeepAspectRatio,
            Qt.TransformationMode.SmoothTransformation
        )
        
        if scaled_pixmap.isNull():
            print("이미지 스케일링 실패")
            return
            
        # 이미지 표시
        self.image_label.setPixmap(scaled_pixmap)
        #print(f"이미지 표시 완료: 원본 크기={image_size}, 스케일된 크기={scaled_width}x{scaled_height}")
        
        # 레이블 크기 조정
        self.image_label.setFixedSize(scaled_width, scaled_height)
        
        # 레이블 업데이트 강제
        self.image_label.update()
        
        # 스크롤 영역이 보이도록 스크롤
        self.scroll_area.ensureVisible(0, 0)
        
        # 포커스 설정
        self.setFocus()
        
    def toggle_theme(self):
        self.settings.toggle_theme()
        self.apply_theme()
        # 현재 이미지 다시 로드 (새로운 테마로 처리)
        if self.current_book:
            self.show_current_image()

    def apply_theme(self):
        """현재 테마를 적용합니다."""
        theme = self.settings.current_theme
        
        # 스타일시트 설정
        self.setStyleSheet(f"""
            QMainWindow {{
                background-color: {theme.window_background};
                color: {theme.window_text};
            }}
            QLabel#image_label {{
                background-color: {theme.window_background};
                border: 1px solid {theme.window_text};  /* 디버깅을 위한 테두리 추가 */
            }}
            QScrollArea {{
                background-color: {theme.window_background};
                border: none;  /* 스크롤 영역 테두리 제거 */
            }}
            QScrollBar {{
                background-color: {theme.window_background};
                width: 12px;
                height: 12px;
            }}
            QScrollBar::handle {{
                background-color: {theme.window_text};
                border-radius: 6px;
            }}
            QWidget {{
                background-color: {theme.window_background};
                color: {theme.window_text};
            }}
        """)
        
        # 라이브러리 뷰 업데이트
        self.library_widget.update_theme(theme)

    def adjust_contrast(self, delta: float):
        theme = self.settings.current_theme
        theme.contrast = max(0.5, min(2.0, theme.contrast + delta))
        self.show_current_image()  # 이미지 다시 처리

    def adjust_brightness(self, delta: float):
        theme = self.settings.current_theme
        theme.brightness = max(0.5, min(1.5, theme.brightness + delta))
        self.show_current_image()

    def adjust_sharpness(self, delta: float):
        theme = self.settings.current_theme
        theme.sharpness = max(0.5, min(2.0, theme.sharpness + delta))
        self.show_current_image() 

    def reload_current_image(self):
        """현재 이미지 다시 로드"""
        if hasattr(self, 'current_images') and 0 <= self.current_index < len(self.current_images):
            self.show_current_image()
            # 포커스 재설정
            self.setFocus()

    def resizeEvent(self, event):
        """창 크기가 변경될 때 호출되는 이벤트"""
        super().resizeEvent(event)
        if hasattr(self, 'current_images') and 0 <= self.current_index < len(self.current_images):
            self.show_current_image()  # 현재 이미지 다시 표시 