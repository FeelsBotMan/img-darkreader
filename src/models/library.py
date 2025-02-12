from pathlib import Path
import json
from typing import List, Optional
from .book import Book

class Library:
    def __init__(self):
        self.books: List[Book] = []
        self.config_dir = Path.home() / '.dark_reader'
        self.library_file = self.config_dir / 'library.json'
        self.load_library()
    
    def add_book(self, folder_path: str | Path) -> Book:
        """새로운 책을 라이브러리에 추가합니다."""
        path = Path(folder_path)
        
        # 이미 존재하는 책인지 확인
        existing_book = self.get_book(path)
        if existing_book:
            print(f"Found existing book: {existing_book.title}, current_page: {existing_book.current_page}")
            return existing_book
        
        # 새 책 생성
        book = Book.from_folder(folder_path)
        print(f"Created new book: {book.title}")
        self.books.append(book)
        self.save_library()
        return book
    
    def get_book(self, path: str | Path) -> Optional[Book]:
        """경로로 책을 찾습니다."""
        path = Path(path)
        return next((book for book in self.books if book.path == path), None)
    
    def update_book(self, book: Book) -> None:
        """책 정보를 업데이트합니다."""
        for i, b in enumerate(self.books):
            if b.path == book.path:
                self.books[i] = book
                break
        self.save_library()
    
    def load_library(self) -> None:
        """라이브러리 정보를 파일에서 불러옵니다."""
        if self.library_file.exists():
            with open(self.library_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                self.books = [Book.from_dict(book_data) for book_data in data]
    
    def save_library(self) -> None:
        """라이브러리 정보를 파일에 저장합니다."""
        self.config_dir.mkdir(parents=True, exist_ok=True)
        with open(self.library_file, 'w', encoding='utf-8') as f:
            json.dump([book.to_dict() for book in self.books], f, 
                     ensure_ascii=False, indent=2) 