from __future__ import annotations

import json
import logging
import os
import tempfile
from pathlib import Path
from typing import Optional

from ..config.paths import AppPaths
from .book import Book

logger = logging.getLogger(__name__)


def _normalize_path(path: str | Path) -> Path:
    p = Path(path)
    try:
        return p.resolve()
    except OSError:
        return p


class Library:
    def __init__(self, library_file: Path | None = None):
        self.books: list[Book] = []
        self.library_file = library_file or AppPaths.library_file()
        self.config_dir = self.library_file.parent
        self.load_library()

    def add_book(self, zip_path: str | Path) -> Book:
        """새로운 책을 라이브러리에 추가합니다."""
        path = _normalize_path(zip_path)
        if path.suffix.lower() != ".zip":
            raise ValueError(f"ZIP 파일만 지원합니다: {path}")

        existing_book = self.get_book(path)
        if existing_book:
            logger.debug(
                "기존 책: %s, current_page=%s",
                existing_book.title,
                existing_book.current_page,
            )
            return existing_book

        book = Book.from_zip(path)
        logger.info("새 책 추가: %s", book.title)
        self.books.append(book)
        self.save_library()
        return book

    def get_book(self, path: str | Path) -> Optional[Book]:
        """경로로 책을 찾습니다 (resolve 기준)."""
        path = _normalize_path(path)
        return next((book for book in self.books if book.path == path), None)

    def update_book(self, book: Book) -> None:
        """책 정보를 업데이트합니다."""
        path = _normalize_path(book.path)
        book.path = path
        updated = False
        for i, b in enumerate(self.books):
            if b.path == path:
                self.books[i] = book
                updated = True
                break
        if updated:
            self.save_library()
        else:
            logger.warning("update_book: 책을 찾지 못함 %s", path)

    def remove_book(self, book: Book) -> bool:
        """라이브러리 목록에서만 제거합니다. 디스크의 ZIP 파일은 삭제하지 않습니다."""
        path = _normalize_path(book.path)
        before = len(self.books)
        self.books = [b for b in self.books if b.path != path]
        if len(self.books) < before:
            self.save_library()
            return True
        return False

    def load_library(self) -> None:
        """라이브러리를 불러옵니다. 없는 ZIP은 orphan으로 유지합니다."""
        if not self.library_file.exists():
            self.books = []
            return
        try:
            with open(self.library_file, "r", encoding="utf-8") as f:
                data = json.load(f)
            if not isinstance(data, list):
                logger.error("library.json 형식이 배열이 아닙니다")
                self.books = []
                return
            books: list[Book] = []
            for book_data in data:
                try:
                    book = Book.from_dict(book_data)
                except (ValueError, TypeError, KeyError) as e:
                    logger.warning("잘못된 book 항목 skip: %s", e)
                    continue
                if book.path.suffix.lower() != ".zip":
                    continue
                if not book.is_available:
                    logger.info("orphan 책 유지: %s", book.path)
                books.append(book)
            self.books = books
        except (OSError, json.JSONDecodeError) as e:
            logger.error("라이브러리 로드 실패: %s", e)
            self.books = []

    def save_library(self) -> None:
        """원자적 쓰기로 라이브러리를 저장합니다."""
        try:
            self.config_dir.mkdir(parents=True, exist_ok=True)
            payload = json.dumps(
                [book.to_dict() for book in self.books],
                ensure_ascii=False,
                indent=2,
            )
            fd, tmp_name = tempfile.mkstemp(
                dir=str(self.config_dir),
                prefix="library_",
                suffix=".tmp",
            )
            try:
                with os.fdopen(fd, "w", encoding="utf-8") as f:
                    f.write(payload)
                Path(tmp_name).replace(self.library_file)
            except Exception:
                try:
                    os.unlink(tmp_name)
                except OSError:
                    pass
                raise
        except OSError as e:
            logger.error("라이브러리 저장 실패: %s", e)
