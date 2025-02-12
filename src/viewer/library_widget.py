from PyQt6.QtWidgets import (QWidget, QGridLayout, QLabel, 
                           QVBoxLayout, QHBoxLayout, QScrollArea)
from PyQt6.QtCore import Qt, pyqtSignal, QRect, QPointF
from PyQt6.QtGui import (QPixmap, QMouseEvent, QPainter, QColor, 
                        QPen, QPolygonF, QBrush)
from pathlib import Path
from models.book import Book
from utils.thumbnail_manager import ThumbnailManager
from typing import List
import math

class StarRating(QWidget):
    """별점 위젯"""
    ratingChanged = pyqtSignal(float)
    
    def __init__(self, rating: float = 0):
        super().__init__()
        self._rating = rating  # 현재 별점 (0-5)
        self._hover_rating = 0  # 마우스 호버 시 임시 별점
        self._star_count = 5  # 총 별 개수
        self._star_size = 20  # 별 하나의 크기
        self._spacing = 5  # 별 사이 간격
        
        # 위젯 크기 설정
        total_width = (self._star_size * self._star_count) + (self._spacing * (self._star_count - 1))
        self.setFixedSize(total_width, self._star_size)
        
        # 마우스 트래킹 활성화 (hover 효과를 위해)
        self.setMouseTracking(True)
    
    def _draw_star(self, painter: QPainter, x: int, filled: bool = False):
        """별 하나를 그리는 메서드"""
        points = []
        center = QPointF(x + self._star_size/2, self._star_size/2)
        outer_radius = self._star_size/2
        inner_radius = self._star_size/4
        
        # 별의 10개 꼭지점 계산 (5개의 외곽점과 5개의 내부점)
        for i in range(10):
            angle = math.pi/2 + (2 * math.pi * i)/10
            radius = outer_radius if i % 2 == 0 else inner_radius
            points.append(QPointF(
                center.x() + radius * math.cos(angle),
                center.y() - radius * math.sin(angle)
            ))
        
        # 별 그리기
        star = QPolygonF(points)
        if filled:
            painter.setBrush(QColor(255, 215, 0))  # 금색
        else:
            painter.setBrush(Qt.BrushStyle.NoBrush)
        painter.drawPolygon(star)
    
    def paintEvent(self, event):
        """위젯 그리기"""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        # 테두리 색상 설정
        painter.setPen(QPen(QColor(255, 215, 0), 1))  # 금색 테두리
        
        # 각 별 그리기
        for i in range(self._star_count):
            x = i * (self._star_size + self._spacing)
            # hover 중이면 hover_rating 사용, 아니면 실제 rating 사용
            rating_to_use = self._hover_rating if self._hover_rating > 0 else self._rating
            self._draw_star(painter, x, filled=(i < rating_to_use))
    
    def mouseMoveEvent(self, event: QMouseEvent):
        """마우스 이동 시 호버 효과"""
        x = event.position().x()
        star_index = x // (self._star_size + self._spacing)
        # 마우스가 위젯 영역을 벗어나면 hover 효과 제거
        if 0 <= star_index < self._star_count:
            self._hover_rating = star_index + 1
        else:
            self._hover_rating = 0
        self.update()
    
    def leaveEvent(self, event):
        """마우스가 위젯을 벗어날 때"""
        self._hover_rating = 0
        self.update()
    
    def mousePressEvent(self, event: QMouseEvent):
        """클릭으로 별점 선택"""
        if event.button() == Qt.MouseButton.LeftButton:
            x = event.position().x()
            star_index = x // (self._star_size + self._spacing)
            if 0 <= star_index < self._star_count:
                new_rating = star_index + 1
                if self._rating == new_rating:  # 같은 별을 다시 클릭하면 취소
                    new_rating = 0
                self._rating = new_rating
                self.ratingChanged.emit(float(self._rating))
                self.update()
    
    def get_rating(self) -> float:
        """현재 별점 반환"""
        return float(self._rating)
    
    def set_rating(self, rating: float):
        """별점 설정"""
        if 0 <= rating <= self._star_count:
            self._rating = rating
            self.update()

class BookCard(QWidget):
    bookSelected = pyqtSignal(Book)
    ratingChanged = pyqtSignal(Book, float)
    
    def __init__(self, book: Book, thumbnail_manager: ThumbnailManager):
        super().__init__()
        self.book = book
        self.thumbnail_manager = thumbnail_manager
        self.init_ui()
        
    def init_ui(self):
        layout = QVBoxLayout(self)
        
        # 섬네일
        first_image = next(self.book.path.glob("*.jpg"), None) or \
                     next(self.book.path.glob("*.png"), None)
        if first_image:
            thumb_path = self.thumbnail_manager.get_thumbnail(first_image)
            if thumb_path:
                image_label = QLabel()
                pixmap = QPixmap(thumb_path)
                image_label.setPixmap(pixmap)
                image_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
                layout.addWidget(image_label)
        
        # 제목
        title = self.book.title[:10] + "..." if len(self.book.title) > 10 else self.book.title
        title_label = QLabel(title)
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title_label)
        
        # 페이지 정보
        current = self.book.get_current_page() + 1  # 1-based 페이지 번호
        page_info = f"{current}/{self.book.total_pages}"
        if self.book.is_read:
            page_info += " (완독)"
        
        page_label = QLabel(page_info)
        page_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(page_label)
        
        # 평점
        rating_widget = StarRating(self.book.rating)
        rating_widget.set_rating(self.book.rating)  # 초기 별점 설정
        rating_widget.ratingChanged.connect(self._on_rating_changed)
        layout.addWidget(rating_widget)
        
        self.setFixedSize(220, 350)
        
    def mouseDoubleClickEvent(self, event: QMouseEvent):
        if event.button() == Qt.MouseButton.LeftButton:
            self.bookSelected.emit(self.book)
            
    def _on_rating_changed(self, rating: float):
        self.book.rating = rating
        self.ratingChanged.emit(self.book, rating)

class LibraryWidget(QWidget):
    bookSelected = pyqtSignal(Book)
    
    def __init__(self):
        super().__init__()
        self.thumbnail_manager = ThumbnailManager()
        self.init_ui()
        
    def init_ui(self):
        # 메인 레이아웃
        main_layout = QVBoxLayout(self)
        
        # 스크롤 영역 생성
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        scroll.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        
        # 그리드를 포함할 컨테이너 위젯
        self.container = QWidget()
        self.grid_layout = QGridLayout(self.container)
        self.grid_layout.setSpacing(20)
        
        # 스크롤 영역에 컨테이너 설정
        scroll.setWidget(self.container)
        
        # 메인 레이아웃에 스크롤 영역 추가
        main_layout.addWidget(scroll)
        
    def update_books(self, books: List[Book]):
        # 기존 위젯 제거
        while self.grid_layout.count():
            item = self.grid_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        
        # 책 카드 배치
        columns = max(1, (self.width() - 40) // 250)  # 여백 고려
        for i, book in enumerate(books):
            row = i // columns
            col = i % columns
            
            card = BookCard(book, self.thumbnail_manager)
            card.bookSelected.connect(self.bookSelected.emit)
            card.ratingChanged.connect(self._on_book_rating_changed)
            self.grid_layout.addWidget(card, row, col)
        
        # 빈 공간을 채우기 위한 스트레치 추가
        self.grid_layout.setRowStretch(self.grid_layout.rowCount(), 1)
        
    def resizeEvent(self, event):
        """창 크기가 변경될 때 그리드를 다시 계산"""
        super().resizeEvent(event)
        if hasattr(self, 'grid_layout') and self.grid_layout.count() > 0:
            books = []
            # 현재 표시된 책들 수집
            for i in range(self.grid_layout.count()):
                item = self.grid_layout.itemAt(i)
                if item and item.widget():
                    widget = item.widget()
                    if isinstance(widget, BookCard):
                        books.append(widget.book)
            # 그리드 다시 계산
            if books:
                self.update_books(books)
    
    def _on_book_rating_changed(self, book: Book, rating: float):
        from models.library import Library
        library = Library()
        library.update_book(book)

    def update_theme(self, theme):
        """테마를 업데이트합니다."""
        self.setStyleSheet(f"""
            QWidget {{
                background-color: {theme.window_background};
                color: {theme.window_text};
            }}
        """)
        # 모든 책 카드 업데이트
        for i in range(self.grid_layout.count()):
            item = self.grid_layout.itemAt(i)
            if item and item.widget():
                widget = item.widget()
                if isinstance(widget, BookCard):
                    widget.setStyleSheet(f"""
                        QLabel {{
                            color: {theme.window_text};
                        }}
                    """) 