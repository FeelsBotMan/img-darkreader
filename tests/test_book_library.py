"""Book / Library 모델 테스트."""
import json
import zipfile
from pathlib import Path

from dark_reader.models.book import Book
from dark_reader.models.library import Library


def _make_zip(path: Path, members: list[str] | None = None) -> Path:
    members = members or ["1.png", "2.png"]
    with zipfile.ZipFile(path, "w") as zf:
        for name in members:
            zf.writestr(name, b"\x89PNG\r\n\x1a\n" + b"\x00" * 8)
    return path


def test_book_from_dict_tolerant():
    book = Book.from_dict({"path": "/tmp/missing_book.zip", "title": "t"})
    assert book.title == "t"
    assert book.total_pages == 0
    assert book.current_page is None
    assert book.rating == 0.0
    assert book.is_read is False


def test_book_round_trip(tmp_path: Path):
    zip_path = _make_zip(tmp_path / "demo.zip")
    book = Book.from_zip(zip_path)
    book.current_page = 1
    book.rating = 4.0
    book.set_question_position(0)
    data = book.to_dict()
    restored = Book.from_dict(data)
    assert restored.title == book.title
    assert restored.path == book.path.resolve()
    assert restored.total_pages == 2
    assert restored.current_page == 1
    assert restored.rating == 4.0
    assert restored.question_position == 0


def test_library_path_identity(tmp_path: Path, monkeypatch):
    lib_file = tmp_path / "library.json"
    library = Library(library_file=lib_file)
    zip_path = _make_zip(tmp_path / "same.zip")

    b1 = library.add_book(zip_path)
    b2 = library.add_book(Path(str(zip_path)))
    assert b1 is b2
    assert len(library.books) == 1


def test_library_keeps_orphan(tmp_path: Path):
    lib_file = tmp_path / "library.json"
    missing = tmp_path / "gone.zip"
    payload = [
        {
            "title": "gone",
            "path": str(missing),
            "total_pages": 3,
            "rating": 0,
            "current_page": 1,
            "is_read": False,
        }
    ]
    lib_file.write_text(json.dumps(payload), encoding="utf-8")
    library = Library(library_file=lib_file)
    assert len(library.books) == 1
    assert library.books[0].is_available is False


def test_library_atomic_save(tmp_path: Path):
    lib_file = tmp_path / "library.json"
    library = Library(library_file=lib_file)
    zip_path = _make_zip(tmp_path / "ok.zip")
    library.add_book(zip_path)
    assert lib_file.exists()
    data = json.loads(lib_file.read_text(encoding="utf-8"))
    assert len(data) == 1
    assert data[0]["title"] == "ok"
