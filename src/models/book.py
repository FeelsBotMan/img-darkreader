from dataclasses import dataclass
from pathlib import Path
from typing import Optional
import json
import os

@dataclass
class Book:
    title: str  # 폴더명
    path: Path  # 경로
    total_pages: int  # 총 페이지 수
    rating: float = 0.0  # 평점 (기본값 0)
    is_read: bool = False  # 읽음 여부
    current_page: Optional[int] = None  # 현재 읽는 페이지 (기본값 None)
    
    @classmethod
    def from_folder(cls, folder_path: str | Path) -> 'Book':
        """폴더 경로로부터 Book 객체를 생성합니다."""
        path = Path(folder_path)
        images = sorted([
            f for f in path.glob("*")
            if f.suffix.lower() in ('.png', '.jpg', '.jpeg')
        ])
        
        return cls(
            title=path.name,
            path=path,
            total_pages=len(images)
        )
    
    def to_dict(self) -> dict:
        """Book 객체를 딕셔너리로 변환합니다."""
        return {
            'title': self.title,
            'path': str(self.path),
            'total_pages': self.total_pages,
            'rating': self.rating,
            'current_page': self.current_page,
            'is_read': self.is_read
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> 'Book':
        """딕셔너리로부터 Book 객체를 생성합니다."""
        return cls(
            title=data['title'],
            path=Path(data['path']),
            total_pages=data['total_pages'],
            rating=data['rating'],
            current_page=data['current_page'],
            is_read=data.get('is_read', False)
        ) 