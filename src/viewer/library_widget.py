from PyQt6.QtWidgets import (QWidget, QGridLayout, QLabel, 
                           QVBoxLayout, QHBoxLayout)
from PyQt6.QtCore import Qt, pyqtSignal, QRect
from PyQt6.QtGui import QPixmap, QMouseEvent, QPainter, QColor
from pathlib import Path
from models.book import Book
from utils.thumbnail_manager import ThumbnailManager
from typing import List
import math

class StarRating(QWidget):
    ratingChanged = pyqtSignal(float)
    
    def __init__(self, rating: float = 0):
        super().__init__()
        self.rating = rating
        self.hover_rating = 0
        self.setMouseTracking(True)
        self.setFixedSize(100, 20)
        
    def paintEvent(self, event):
        painter = QPainter(self)
        star_width = self.width() // 5
        
        # 별 그리기
        for i in range(5):
            x = i * star_width
            rect = QRect(x, 0, star_width-2, 20)
            if i < math.floor(self.hover_rating or self.rating):
                painter.fillRect(rect, QColor(255, 215, 0))
            else:
                painter.fillRect(rect, QColor(128, 128, 128))
    
    def mouseMoveEvent(self, event: QMouseEvent):
        self.hover_rating = (event.position().x() / self.width()) * 5
        self.update()
    
    def leaveEvent(self, event):
        self.hover_rating = 0
        self.update()
    
    def mouseReleaseEvent(self, event: QMouseEvent):
        if event.button() == Qt.MouseButton.LeftButton:
            self.rating = (event.position().x() / self.width()) * 5
            self.ratingChanged.emit(self.rating)
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
        self.layout = QGridLayout(self)
        self.layout.setSpacing(20)
        
    def update_books(self, books: List[Book]):
        # 기존 위젯 제거
        while self.layout.count():
            item = self.layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        
        # 책 카드 배치
        columns = max(1, self.width() // 250)  # 한 행에 표시할 카드 수
        for i, book in enumerate(books):
            row = i // columns
            col = i % columns
            
            card = BookCard(book, self.thumbnail_manager)
            card.bookSelected.connect(self.bookSelected.emit)
            card.ratingChanged.connect(self._on_book_rating_changed)
            self.layout.addWidget(card, row, col)
            
    def _on_book_rating_changed(self, book: Book, rating: float):
        from models.library import Library
        library = Library()
        library.update_book(book) 