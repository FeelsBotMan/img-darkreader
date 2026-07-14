from __future__ import annotations

import math
from typing import List, Optional

from PyQt6.QtCore import QPointF, Qt, QTimer, pyqtSignal
from PyQt6.QtGui import (
    QAction,
    QColor,
    QFontMetrics,
    QMouseEvent,
    QPainter,
    QPen,
    QPixmap,
    QPolygonF,
)
from PyQt6.QtWidgets import (
    QComboBox,
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMenu,
    QProgressBar,
    QPushButton,
    QScrollArea,
    QSizePolicy,
    QStackedWidget,
    QToolButton,
    QVBoxLayout,
    QWidget,
)

from ..config.settings import Theme
from ..models.book import Book
from ..utils.thumbnail_manager import ThumbnailManager
from ..utils.zip_archive import ZipImageArchive, cache_key_for_member


def _hex_to_qcolor(hex_str: str) -> QColor:
    c = QColor(hex_str)
    return c if c.isValid() else QColor(200, 200, 200)


class StarRating(QWidget):
    """별점 위젯 (테마 색으로 채움/외곽선)."""

    ratingChanged = pyqtSignal(float)

    def __init__(self, rating: float = 0):
        super().__init__()
        self._rating = rating
        self._hover_rating = 0
        self._star_count = 5
        self._star_size = 20
        self._spacing = 5
        self._fill = QColor(255, 215, 0)
        self._outline = QColor(255, 215, 0)

        total_width = (self._star_size * self._star_count) + (
            self._spacing * (self._star_count - 1)
        )
        self.setFixedSize(total_width, self._star_size)
        self.setMouseTracking(True)

    def set_theme_colors(self, fill: QColor, outline: QColor) -> None:
        self._fill = fill
        self._outline = outline
        self.update()

    def _draw_star(self, painter: QPainter, x: int, filled: bool = False) -> None:
        points = []
        center = QPointF(x + self._star_size / 2, self._star_size / 2)
        outer_radius = self._star_size / 2
        inner_radius = self._star_size / 4

        for i in range(10):
            angle = math.pi / 2 + (2 * math.pi * i) / 10
            radius = outer_radius if i % 2 == 0 else inner_radius
            points.append(
                QPointF(
                    center.x() + radius * math.cos(angle),
                    center.y() - radius * math.sin(angle),
                )
            )

        star = QPolygonF(points)
        if filled:
            painter.setBrush(self._fill)
        else:
            painter.setBrush(Qt.BrushStyle.NoBrush)
        painter.drawPolygon(star)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.setPen(QPen(self._outline, 1))

        for i in range(self._star_count):
            x = i * (self._star_size + self._spacing)
            rating_to_use = (
                self._hover_rating if self._hover_rating > 0 else self._rating
            )
            self._draw_star(painter, x, filled=(i < rating_to_use))

    def mouseMoveEvent(self, event: QMouseEvent):
        x = event.position().x()
        star_index = int(x // (self._star_size + self._spacing))
        if 0 <= star_index < self._star_count:
            self._hover_rating = star_index + 1
        else:
            self._hover_rating = 0
        self.update()

    def leaveEvent(self, event):
        self._hover_rating = 0
        self.update()

    def mousePressEvent(self, event: QMouseEvent):
        if event.button() == Qt.MouseButton.LeftButton:
            x = event.position().x()
            star_index = int(x // (self._star_size + self._spacing))
            if 0 <= star_index < self._star_count:
                new_rating = star_index + 1
                if self._rating == new_rating:
                    new_rating = 0
                self._rating = new_rating
                self.ratingChanged.emit(float(self._rating))
                self.update()

    def get_rating(self) -> float:
        return float(self._rating)

    def set_rating(self, rating: float):
        if 0 <= rating <= self._star_count:
            self._rating = rating
            self.update()


class BookCard(QWidget):
    bookSelected = pyqtSignal(Book)
    ratingChanged = pyqtSignal(Book, float)
    readStatusChanged = pyqtSignal(Book)
    removeRequested = pyqtSignal(Book)

    _TITLE_MAX_WIDTH_PX = 200

    def __init__(
        self,
        book: Book,
        thumbnail_manager: ThumbnailManager,
        theme: Optional[Theme] = None,
    ):
        super().__init__()
        self.setObjectName("BookCard")
        self.book = book
        self.thumbnail_manager = thumbnail_manager
        self._theme = theme
        self._rating_widget: Optional[StarRating] = None
        self.init_ui()

    def init_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(4)

        thumbnail_container = QWidget()
        thumbnail_container.setFixedSize(200, 300)
        thumbnail_container.setObjectName("thumbContainer")
        thumbnail_layout = QVBoxLayout(thumbnail_container)
        thumbnail_layout.setContentsMargins(0, 0, 0, 0)

        image_label = QLabel()
        image_label.setFixedSize(200, 300)
        image_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        image_label.setStyleSheet("background: transparent;")

        loaded = False
        if (
            self.book.path.suffix.lower() == ".zip"
            and self.book.path.is_file()
        ):
            try:
                with ZipImageArchive(self.book.path) as archive:
                    if archive.members:
                        member = archive.members[0]
                        data = archive.read_bytes(member)
                        cache_id = cache_key_for_member(self.book.path, member)
                        thumb_path = self.thumbnail_manager.get_thumbnail_bytes(
                            data, cache_id
                        )
                        if thumb_path:
                            pixmap = QPixmap(thumb_path)
                            if not pixmap.isNull():
                                scaled_pixmap = pixmap.scaled(
                                    200,
                                    300,
                                    Qt.AspectRatioMode.KeepAspectRatio,
                                    Qt.TransformationMode.SmoothTransformation,
                                )
                                image_label.setPixmap(scaled_pixmap)
                                loaded = True
            except Exception as e:
                print(f"썸네일 로드 실패 ({self.book.path}): {e}")

        if not loaded:
            image_label.setText("이미지 없음")
            image_label.setStyleSheet(
                "background: transparent; color: #888888; font-size: 11pt;"
            )

        thumbnail_layout.addWidget(image_label)
        layout.addWidget(thumbnail_container)

        title_label = QLabel()
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title_label.setWordWrap(True)
        title_label.setMaximumWidth(self._TITLE_MAX_WIDTH_PX + 20)
        fm = QFontMetrics(title_label.font())
        elided = fm.elidedText(
            self.book.title,
            Qt.TextElideMode.ElideRight,
            self._TITLE_MAX_WIDTH_PX,
        )
        title_label.setText(elided)
        title_label.setToolTip(self.book.title)
        title_label.setStyleSheet("font-weight: bold; margin-top: 4px;")
        layout.addWidget(title_label)

        current = self.book.get_current_page() + 1
        page_info = f"{current}/{self.book.total_pages}"
        if self.book.is_read:
            page_info += " (완독)"

        page_label = QLabel(page_info)
        page_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(page_label)

        total = max(self.book.total_pages, 1)
        pct = min(100, max(0, int(round(100 * current / total))))
        progress = QProgressBar()
        progress.setRange(0, 100)
        progress.setValue(pct)
        progress.setTextVisible(False)
        progress.setFixedHeight(6)
        progress.setSizePolicy(
            QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed
        )
        layout.addWidget(progress)

        rating_widget = StarRating(self.book.rating)
        rating_widget.set_rating(self.book.rating)
        rating_widget.ratingChanged.connect(self._on_rating_changed)
        self._rating_widget = rating_widget
        layout.addWidget(rating_widget)

        menu_btn = QToolButton()
        menu_btn.setText("⋯")
        menu_btn.setToolTip("메뉴")
        menu_btn.setAutoRaise(True)
        menu = QMenu(menu_btn)
        read_act = QAction("완독으로 표시", menu)
        read_act.setCheckable(True)
        read_act.setChecked(self.book.is_read)
        read_act.setToolTip("이 책을 완독한 것으로 표시하거나 해제합니다.")
        read_act.triggered.connect(self._on_read_status_action)
        menu.addAction(read_act)
        menu.addSeparator()
        remove_act = menu.addAction("라이브러리에서 제거…")
        remove_act.setToolTip("목록에서만 삭제합니다. ZIP 파일은 유지됩니다.")
        remove_act.triggered.connect(lambda: self.removeRequested.emit(self.book))
        menu_btn.setMenu(menu)
        menu_btn.setPopupMode(QToolButton.ToolButtonPopupMode.InstantPopup)
        layout.addWidget(menu_btn, alignment=Qt.AlignmentFlag.AlignCenter)

        self.setFixedWidth(220)
        self.setFixedHeight(458)
        self.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.customContextMenuRequested.connect(self._show_context_menu)

    def _show_context_menu(self, pos):
        menu = QMenu(self)
        read_act = QAction("완독으로 표시", menu)
        read_act.setCheckable(True)
        read_act.setChecked(self.book.is_read)
        read_act.setToolTip("이 책을 완독한 것으로 표시하거나 해제합니다.")
        read_act.triggered.connect(self._on_read_status_action)
        menu.addAction(read_act)
        menu.addSeparator()
        act = menu.addAction("라이브러리에서 제거…")
        act.triggered.connect(lambda: self.removeRequested.emit(self.book))
        menu.exec(self.mapToGlobal(pos))

    def _on_read_status_action(self, checked: bool) -> None:
        self.book.is_read = checked
        self.readStatusChanged.emit(self.book)

    def mouseDoubleClickEvent(self, event: QMouseEvent):
        if event.button() == Qt.MouseButton.LeftButton:
            self.bookSelected.emit(self.book)

    def _on_rating_changed(self, rating: float):
        self.book.rating = rating
        self.ratingChanged.emit(self.book, rating)

    def apply_theme(self, theme: Theme) -> None:
        self._theme = theme
        wt = theme.window_text
        bg = theme.window_background
        base = _hex_to_qcolor(wt)
        fill = QColor(base)
        fill.setAlpha(220)
        outline = QColor(base)
        outline.setAlpha(180)
        if self._rating_widget:
            self._rating_widget.set_theme_colors(fill, outline)

        self.setStyleSheet(
            f"""
            QWidget#BookCard {{
                background-color: {bg};
                border: 1px solid rgba(128, 128, 128, 0.35);
                border-radius: 8px;
            }}
            QWidget#BookCard:hover {{
                border: 1px solid {wt};
            }}
            QWidget#thumbContainer {{
                background-color: rgba(128, 128, 128, 0.12);
                border-radius: 5px;
            }}
            QLabel {{
                color: {wt};
            }}
            QToolButton {{
                color: {wt};
                background: transparent;
                border: none;
                min-width: 28px;
                font-size: 14pt;
            }}
            QToolButton:hover {{
                background-color: rgba(128, 128, 128, 0.2);
                border-radius: 4px;
            }}
            QProgressBar {{
                border: none;
                background-color: rgba(128, 128, 128, 0.25);
                border-radius: 3px;
            }}
            QProgressBar::chunk {{
                background-color: {wt};
                border-radius: 3px;
            }}
            """
        )


class LibraryWidget(QWidget):
    bookSelected = pyqtSignal(Book)
    bookRemoveRequested = pyqtSignal(Book)
    openZipRequested = pyqtSignal()

    SORT_RECENT_OPEN = 0
    SORT_TITLE = 1
    SORT_RATING_DESC = 2
    SORT_PROGRESS_DESC = 3
    SORT_READ_FIRST = 4

    # 별점 필터: 전체, 미평가, ★1…★5
    FILTER_RATING_ALL = 0
    FILTER_RATING_UNRATED = 1
    FILTER_RATING_STARS_START = 2  # 인덱스 2~6 → 별 1~5

    # 읽기 상태: 전체, 완독, 읽는 중, 읽지 않음
    FILTER_READ_ALL = 0
    FILTER_READ_COMPLETED = 1
    FILTER_READ_IN_PROGRESS = 2
    FILTER_READ_NOT_STARTED = 3

    def __init__(self):
        super().__init__()
        self.thumbnail_manager = ThumbnailManager()
        self._source_books: List[Book] = []
        self._display_books: List[Book] = []
        self._theme: Optional[Theme] = None
        self._resize_timer = QTimer(self)
        self._resize_timer.setSingleShot(True)
        self._resize_timer.timeout.connect(self._on_resize_debounced)
        self._pending_resize_relayout = False
        self.init_ui()

    def init_ui(self) -> None:
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(8, 8, 8, 8)
        main_layout.setSpacing(6)

        toolbar = QHBoxLayout()
        title = QLabel("라이브러리")
        title.setStyleSheet("font-size: 16px; font-weight: bold;")
        toolbar.addWidget(title)

        self._search = QLineEdit()
        self._search.setPlaceholderText("제목 검색…")
        self._search.setClearButtonEnabled(True)
        self._search.setMaximumWidth(240)
        self._search.textChanged.connect(self._on_filter_sort_changed)
        toolbar.addWidget(self._search)

        self._sort_combo = QComboBox()
        self._sort_combo.addItems(
            [
                "최근 읽음",
                "제목",
                "별점 (높은 순)",
                "진행률 (높은 순)",
                "완독 우선",
            ]
        )
        self._sort_combo.setMinimumWidth(160)
        self._sort_combo.setCurrentIndex(self.SORT_RECENT_OPEN)
        self._sort_combo.currentIndexChanged.connect(self._on_filter_sort_changed)
        toolbar.addWidget(self._sort_combo)

        toolbar.addStretch()

        self._open_btn = QPushButton("ZIP 열기")
        self._open_btn.setToolTip(
            "이미지가 들어 있는 ZIP을 선택해 책으로 추가합니다 (단축키 O)"
        )
        self._open_btn.clicked.connect(self.openZipRequested.emit)
        toolbar.addWidget(self._open_btn)

        main_layout.addLayout(toolbar)

        filter_bar = QHBoxLayout()
        filter_bar.addWidget(QLabel("별점"))
        self._rating_filter = QComboBox()
        self._rating_filter.addItems(
            ["전체", "미평가", "★1", "★2", "★3", "★4", "★5"]
        )
        self._rating_filter.setMinimumWidth(120)
        self._rating_filter.currentIndexChanged.connect(self._on_filter_sort_changed)
        filter_bar.addWidget(self._rating_filter)

        filter_bar.addWidget(QLabel("읽기"))
        self._reading_filter = QComboBox()
        self._reading_filter.addItems(["전체", "완독", "읽는 중", "읽지 않음"])
        self._reading_filter.setMinimumWidth(130)
        self._reading_filter.currentIndexChanged.connect(self._on_filter_sort_changed)
        filter_bar.addWidget(self._reading_filter)

        filter_bar.addStretch()
        main_layout.addLayout(filter_bar)

        self._hint = QLabel(
            "카드를 더블클릭하면 읽기 시작 · 우측 ⋯ 또는 우클릭으로 목록에서 제거"
        )
        self._hint.setObjectName("libraryHint")
        self._hint.setWordWrap(True)
        main_layout.addWidget(self._hint)

        self._stack = QStackedWidget()
        main_layout.addWidget(self._stack, stretch=1)

        self._empty_full = QWidget()
        empty_layout = QVBoxLayout(self._empty_full)
        empty_layout.addStretch()
        msg = QLabel(
            "등록된 책이 없습니다.\n\n"
            "「ZIP 열기」로 이미지 ZIP을 추가하거나 단축키 O 를 누르세요."
        )
        msg.setAlignment(Qt.AlignmentFlag.AlignCenter)
        msg.setWordWrap(True)
        empty_layout.addWidget(msg)
        empty_open = QPushButton("ZIP 열기")
        empty_open.setToolTip("이미지가 들어 있는 ZIP을 선택합니다 (단축키 O)")
        empty_open.clicked.connect(self.openZipRequested.emit)
        empty_layout.addWidget(empty_open, alignment=Qt.AlignmentFlag.AlignCenter)
        empty_layout.addStretch()

        self._scroll = QScrollArea()
        self._scroll.setWidgetResizable(True)
        self._scroll.setHorizontalScrollBarPolicy(
            Qt.ScrollBarPolicy.ScrollBarAlwaysOff
        )
        self._scroll.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self._scroll.setFrameShape(QFrame.Shape.NoFrame)
        self._scroll.setStyleSheet("QScrollArea { border: none; }")

        self._grid_host = QWidget()
        self._grid_layout = QGridLayout(self._grid_host)
        self._grid_layout.setSpacing(20)
        self._scroll.setWidget(self._grid_host)

        self._empty_search = QWidget()
        es_layout = QVBoxLayout(self._empty_search)
        es_layout.addStretch()
        es_label = QLabel("검색 결과가 없습니다.")
        es_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        es_layout.addWidget(es_label)
        es_layout.addStretch()

        self._stack.addWidget(self._empty_full)
        self._stack.addWidget(self._scroll)
        self._stack.addWidget(self._empty_search)

    def update_books(self, books: List[Book]) -> None:
        self._source_books = list(books)
        self._apply_filter_sort_and_rebuild()

    def _on_filter_sort_changed(self) -> None:
        if not self._source_books:
            return
        self._apply_filter_sort_and_rebuild()

    def _filter_books(self, books: List[Book]) -> List[Book]:
        q = self._search.text().strip().lower()
        if q:
            out = [b for b in books if q in b.title.lower()]
        else:
            out = list(books)

        ri = self._rating_filter.currentIndex()
        if ri != self.FILTER_RATING_ALL:
            if ri == self.FILTER_RATING_UNRATED:
                out = [b for b in out if b.rating == 0]
            else:
                star = ri - self.FILTER_RATING_STARS_START + 1
                out = [b for b in out if round(b.rating) == star]

        wi = self._reading_filter.currentIndex()
        if wi != self.FILTER_READ_ALL:
            out = [b for b in out if self._matches_reading_filter(b, wi)]

        return out

    @staticmethod
    def _matches_reading_filter(b: Book, mode: int) -> bool:
        if mode == LibraryWidget.FILTER_READ_COMPLETED:
            return b.is_read
        if mode == LibraryWidget.FILTER_READ_IN_PROGRESS:
            return not b.is_read and b.get_current_page() > 0
        if mode == LibraryWidget.FILTER_READ_NOT_STARTED:
            return not b.is_read and b.get_current_page() == 0
        return True

    def _sort_books(self, books: List[Book]) -> List[Book]:
        mode = self._sort_combo.currentIndex()
        out = list(books)

        def progress_ratio(b: Book) -> float:
            total = max(b.total_pages, 1)
            return (b.get_current_page() + 1) / total

        if mode == self.SORT_RECENT_OPEN:
            out.sort(
                key=lambda b: (
                    b.last_opened_at is None,
                    -(b.last_opened_at or 0.0),
                    b.title.lower(),
                )
            )
        elif mode == self.SORT_TITLE:
            out.sort(key=lambda b: b.title.lower())
        elif mode == self.SORT_RATING_DESC:
            out.sort(key=lambda b: (-b.rating, b.title.lower()))
        elif mode == self.SORT_PROGRESS_DESC:
            out.sort(key=lambda b: (-progress_ratio(b), b.title.lower()))
        elif mode == self.SORT_READ_FIRST:
            # 완독한 책 먼저, 그다음 진행률·제목
            out.sort(
                key=lambda b: (
                    -int(b.is_read),
                    -progress_ratio(b),
                    b.title.lower(),
                )
            )
        return out

    def _apply_filter_sort_and_rebuild(self) -> None:
        if not self._source_books:
            self._stack.setCurrentWidget(self._empty_full)
            self._clear_grid()
            self._display_books = []
            return

        filtered = self._filter_books(self._source_books)
        self._display_books = self._sort_books(filtered)

        if not self._display_books:
            self._stack.setCurrentWidget(self._empty_search)
            self._clear_grid()
            return

        self._stack.setCurrentWidget(self._scroll)
        self._rebuild_grid()

    def _clear_grid(self) -> None:
        while self._grid_layout.count():
            item = self._grid_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

    def _column_count(self) -> int:
        return max(1, (self.width() - 48) // 250)

    def _rebuild_grid(self) -> None:
        self._clear_grid()
        books = self._display_books
        columns = self._column_count()
        theme = self._theme
        for i, book in enumerate(books):
            row = i // columns
            col = i % columns
            card = BookCard(book, self.thumbnail_manager, theme=theme)
            if theme:
                card.apply_theme(theme)
            card.bookSelected.connect(self.bookSelected.emit)
            card.ratingChanged.connect(self._on_book_rating_changed)
            card.readStatusChanged.connect(self._on_book_read_status_changed)
            card.removeRequested.connect(self.bookRemoveRequested.emit)
            self._grid_layout.addWidget(card, row, col)
        self._grid_layout.setRowStretch(self._grid_layout.rowCount(), 1)

    def _on_resize_debounced(self) -> None:
        if not self._pending_resize_relayout:
            return
        self._pending_resize_relayout = False
        if (
            self._stack.currentWidget() == self._scroll
            and self._display_books
        ):
            self._rebuild_grid()

    def resizeEvent(self, event):
        super().resizeEvent(event)
        if self._display_books and self.isVisible():
            self._pending_resize_relayout = True
            self._resize_timer.start(90)

    def _on_book_rating_changed(self, book: Book, rating: float):
        from ..models.library import Library

        library = Library()
        library.update_book(book)

    def _on_book_read_status_changed(self, book: Book) -> None:
        from ..models.library import Library

        library = Library()
        library.update_book(book)
        self._apply_filter_sort_and_rebuild()

    def update_theme(self, theme: Theme) -> None:
        self._theme = theme
        bg_l = theme.window_background.strip().lower()
        hint_color = (
            "rgba(90, 90, 90, 0.95)"
            if bg_l in ("#ffffff", "#fff", "white")
            else "rgba(180, 180, 180, 0.85)"
        )
        self.setStyleSheet(
            f"""
            QWidget {{
                background-color: {theme.window_background};
                color: {theme.window_text};
            }}
            QLineEdit {{
                background-color: {theme.window_background};
                color: {theme.window_text};
                border: 1px solid rgba(128, 128, 128, 0.5);
                border-radius: 4px;
                padding: 4px 8px;
            }}
            QComboBox {{
                background-color: {theme.window_background};
                color: {theme.window_text};
                border: 1px solid rgba(128, 128, 128, 0.5);
                border-radius: 4px;
                padding: 4px 8px;
            }}
            QPushButton {{
                background-color: rgba(128, 128, 128, 0.2);
                color: {theme.window_text};
                border: 1px solid rgba(128, 128, 128, 0.4);
                border-radius: 4px;
                padding: 6px 12px;
            }}
            QPushButton:hover {{
                background-color: rgba(128, 128, 128, 0.35);
            }}
            QLabel#libraryHint {{
                font-size: 11px;
                color: {hint_color};
            }}
            """
        )
        for i in range(self._grid_layout.count()):
            item = self._grid_layout.itemAt(i)
            if item and item.widget():
                w = item.widget()
                if isinstance(w, BookCard):
                    w.apply_theme(theme)
