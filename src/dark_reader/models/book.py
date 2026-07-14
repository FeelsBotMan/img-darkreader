from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Optional

from ..utils.zip_archive import list_root_images


@dataclass
class Book:
    title: str  # ZIP 파일명(확장자 제외)
    path: Path  # ZIP 파일 경로 (resolve된 절대경로 권장)
    total_pages: int  # 총 페이지 수
    rating: float = 0.0  # 평점 (기본값 0)
    is_read: bool = False  # 읽음 여부
    current_page: Optional[int] = None  # 현재 읽는 페이지 (기본값 None)
    answer_position: Optional[int] = None  # 정답 위치
    question_position: Optional[int] = None  # 문제 위치
    last_opened_at: Optional[float] = None  # Unix 시각(초), 리더에서 책을 열 때만 갱신

    @property
    def is_available(self) -> bool:
        """디스크에 ZIP 파일이 존재하는지 여부."""
        return self.path.is_file()

    @classmethod
    def from_zip(cls, zip_path: str | Path) -> "Book":
        """ZIP 경로로부터 Book 객체를 생성합니다."""
        path = Path(zip_path).resolve()
        if path.suffix.lower() != ".zip":
            raise ValueError(f"ZIP 파일만 지원합니다: {path}")
        images = list_root_images(path)

        return cls(
            title=path.stem,
            path=path,
            total_pages=len(images),
        )

    def to_dict(self) -> dict[str, Any]:
        """Book 객체를 딕셔너리로 변환합니다."""
        return {
            "title": self.title,
            "path": str(self.path),
            "total_pages": self.total_pages,
            "rating": self.rating,
            "current_page": self.current_page,
            "is_read": self.is_read,
            "answer_position": self.answer_position,
            "question_position": self.question_position,
            "last_opened_at": self.last_opened_at,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "Book":
        """딕셔너리로부터 Book 객체를 생성합니다 (누락 키는 기본값)."""
        raw_path = data.get("path")
        if not raw_path:
            raise ValueError("Book 데이터에 path가 없습니다")
        path = Path(raw_path)
        try:
            path = path.resolve()
        except OSError:
            path = Path(raw_path)

        title = data.get("title") or path.stem
        total_pages = int(data.get("total_pages") or 0)
        book = cls(title=title, path=path, total_pages=total_pages)
        book.current_page = data.get("current_page")
        book.is_read = bool(data.get("is_read", False))
        try:
            book.rating = float(data.get("rating", 0.0))
        except (TypeError, ValueError):
            book.rating = 0.0
        book.answer_position = data.get("answer_position")
        book.question_position = data.get("question_position")
        book.last_opened_at = data.get("last_opened_at")
        return book

    def get_current_page(self) -> int:
        """현재 페이지를 반환합니다. 없으면 0을 반환합니다."""
        if self.current_page is None:
            return 0
        if self.total_pages <= 0:
            return 0
        return max(0, min(self.current_page, self.total_pages - 1))

    def update_current_page(self, page: int) -> None:
        """현재 페이지를 업데이트하고 마지막 페이지인 경우 읽음 상태를 변경합니다."""
        if self.total_pages <= 0:
            self.current_page = 0
            return
        page = max(0, min(page, self.total_pages - 1))
        self.current_page = page
        if page == self.total_pages - 1:
            self.is_read = True

    def set_answer_position(self, position: int) -> None:
        self.answer_position = position

    def set_question_position(self, position: int) -> None:
        self.question_position = position

    def clear_answer_position(self) -> None:
        self.answer_position = None

    def clear_question_position(self) -> None:
        self.question_position = None
