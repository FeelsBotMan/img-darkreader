from __future__ import annotations

import logging
import time
from pathlib import Path
from typing import Optional

from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QImage, QPixmap
from PyQt6.QtWidgets import (
    QFileDialog,
    QFrame,
    QLabel,
    QMainWindow,
    QMessageBox,
    QScrollArea,
    QSizePolicy,
    QStackedWidget,
    QVBoxLayout,
    QWidget,
)

from ..config.settings import Settings
from ..models.book import Book
from ..models.library import Library
from ..utils.zip_archive import ZipImageArchive
from .image_processor import ImageProcessor
from .library_widget import LibraryWidget

logger = logging.getLogger(__name__)


class ImageViewer(QMainWindow):
    def __init__(self):
        super().__init__()
        self.settings = Settings()
        self.image_processor = ImageProcessor(self.settings)
        self.image_processor.set_reload_callback(self.reload_current_image)
        self.library = Library()
        self.current_book: Optional[Book] = None
        self.current_archive: Optional[ZipImageArchive] = None
        self.current_images: list[str] = []
        self.current_index = -1
        self._current_qimage: Optional[QImage] = None
        self._persist_page = True

        self._resize_timer = QTimer(self)
        self._resize_timer.setSingleShot(True)
        self._resize_timer.timeout.connect(self._on_resize_debounced)

        self.init_ui()
        self.apply_theme()

        self.status_label = QLabel()
        self.statusBar().addWidget(self.status_label)

    def init_ui(self):
        self.setWindowTitle("다크 리더")
        self.setGeometry(100, 100, 1200, 800)

        self.stack = QStackedWidget()
        self.setCentralWidget(self.stack)

        self.library_widget = LibraryWidget(library=self.library)
        self.library_widget.bookSelected.connect(self.open_book)
        self.library_widget.bookRemoveRequested.connect(self.confirm_remove_book)
        self.library_widget.openZipRequested.connect(self.open_zip)
        self.stack.addWidget(self.library_widget)

        self.reader_widget = QWidget()
        reader_layout = QVBoxLayout(self.reader_widget)
        reader_layout.setContentsMargins(0, 0, 0, 0)
        reader_layout.setSpacing(0)

        self.image_label = QLabel()
        self.image_label.setObjectName("image_label")
        self.image_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.image_label.setSizePolicy(
            QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding
        )
        self.image_label.setFocusPolicy(Qt.FocusPolicy.NoFocus)

        container = QWidget()
        container.setStyleSheet("background-color: transparent;")
        container.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        container_layout = QVBoxLayout(container)
        container_layout.setContentsMargins(0, 0, 0, 0)
        container_layout.addWidget(self.image_label)

        self.scroll_area = QScrollArea()
        self.scroll_area.setWidget(container)
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setHorizontalScrollBarPolicy(
            Qt.ScrollBarPolicy.ScrollBarAsNeeded
        )
        self.scroll_area.setVerticalScrollBarPolicy(
            Qt.ScrollBarPolicy.ScrollBarAsNeeded
        )
        self.scroll_area.setStyleSheet("QScrollArea { border: none; }")
        self.scroll_area.setFocusPolicy(Qt.FocusPolicy.NoFocus)

        reader_layout.addWidget(self.scroll_area)

        self._init_shortcuts_overlay()
        self.stack.addWidget(self.reader_widget)

        self.library_widget.update_books(self.library.books)

        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        self.reader_widget.setFocusPolicy(Qt.FocusPolicy.StrongFocus)

    def _init_shortcuts_overlay(self) -> None:
        self.shortcuts_overlay = QFrame(self.reader_widget)
        self.shortcuts_overlay.setObjectName("shortcuts_overlay")
        self.shortcuts_overlay.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        overlay_layout = QVBoxLayout(self.shortcuts_overlay)
        overlay_layout.setContentsMargins(32, 32, 32, 32)
        self.shortcuts_help_label = QLabel()
        self.shortcuts_help_label.setObjectName("shortcuts_help_label")
        self.shortcuts_help_label.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.shortcuts_help_label.setTextFormat(Qt.TextFormat.RichText)
        self.shortcuts_help_label.setWordWrap(True)
        self.shortcuts_help_label.setAlignment(
            Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignLeft
        )
        self._refresh_shortcuts_overlay_text()
        overlay_layout.addWidget(self.shortcuts_help_label)
        self.shortcuts_overlay.hide()
        self._update_shortcuts_overlay_geometry()

    def _refresh_shortcuts_overlay_text(self) -> None:
        self.shortcuts_help_label.setText(
            "<h3 style='margin-top:0;'>단축키</h3>"
            "<p><b>← / →</b> 이전·다음 페이지 &nbsp;·&nbsp; <b>Esc</b> 라이브러리</p>"
            "<p><b>H</b> 이 도움말 닫기</p>"
            "<hr/>"
            "<p><b>문제·정답</b></p>"
            "<p><b>X</b> 현재 페이지를 문제로 저장/해제 &nbsp;·&nbsp; "
            "<b>S</b> 정답으로 저장/해제</p>"
            "<p><b>Z</b> 문제 페이지로 이동 &nbsp;·&nbsp; "
            "<b>A</b> 정답 페이지로 이동</p>"
            "<hr/>"
            "<p><b>가독성</b></p>"
            "<p><b>[</b> / <b>]</b> 대비 감소·증가 &nbsp;·&nbsp; "
            "<b>-</b> / <b>=</b> 밝기 감소·증가</p>"
            "<p><b>,</b> / <b>.</b> 선명도 감소·증가</p>"
            "<hr/>"
            "<p><b>기타</b></p>"
            "<p><b>O</b> ZIP 열기 &nbsp;·&nbsp; <b>T</b> 테마 전환</p>"
        )

    def _update_shortcuts_overlay_geometry(self) -> None:
        if not hasattr(self, "shortcuts_overlay"):
            return
        self.shortcuts_overlay.setGeometry(
            0, 0, self.reader_widget.width(), self.reader_widget.height()
        )
        self.shortcuts_overlay.raise_()

    def toggle_shortcuts_overlay(self) -> None:
        if self.shortcuts_overlay.isVisible():
            self.shortcuts_overlay.hide()
        else:
            self._refresh_shortcuts_overlay_text()
            self._update_shortcuts_overlay_geometry()
            self.shortcuts_overlay.show()
            self.shortcuts_overlay.raise_()

    def keyPressEvent(self, event):
        key = event.key()
        if self.stack.currentWidget() == self.reader_widget:
            handled = self._handle_reader_key(key)
            if handled:
                event.accept()
                return

        if key == Qt.Key.Key_O:
            self.open_zip()
            event.accept()
            return
        if key == Qt.Key.Key_T:
            self.toggle_theme()
            event.accept()
            return

        event.ignore()

    def _handle_reader_key(self, key: int) -> bool:
        """리더 전용 단축키. 처리했으면 True."""
        if key == Qt.Key.Key_Escape:
            if self.shortcuts_overlay.isVisible():
                self.shortcuts_overlay.hide()
            else:
                self.show_library()
            return True

        actions = {
            Qt.Key.Key_Left: self.show_previous_image,
            Qt.Key.Key_Right: self.show_next_image,
            Qt.Key.Key_H: self.toggle_shortcuts_overlay,
            Qt.Key.Key_X: self.toggle_question_position,
            Qt.Key.Key_S: self.toggle_answer_position,
            Qt.Key.Key_Z: self.go_to_question,
            Qt.Key.Key_A: self.go_to_answer,
            Qt.Key.Key_BracketLeft: lambda: self.adjust_contrast(-0.1),
            Qt.Key.Key_BracketRight: lambda: self.adjust_contrast(0.1),
            Qt.Key.Key_Minus: lambda: self.adjust_brightness(-0.1),
            Qt.Key.Key_Equal: lambda: self.adjust_brightness(0.1),
            Qt.Key.Key_Comma: lambda: self.adjust_sharpness(-0.1),
            Qt.Key.Key_Period: lambda: self.adjust_sharpness(0.1),
        }
        action = actions.get(key)
        if action is None:
            return False
        action()
        return True

    def _close_archive(self) -> None:
        if self.current_archive is not None:
            self.current_archive.close()
            self.current_archive = None

    def open_book(self, book: Book):
        if book.path.suffix.lower() != ".zip" or not book.path.is_file():
            QMessageBox.warning(
                self,
                "오류",
                "유효한 ZIP 파일이 아닙니다.\n"
                "파일이 이동·삭제되었을 수 있습니다. ZIP을 다시 추가해 주세요.",
            )
            return
        self.load_zip(str(book.path))

    def show_library(self):
        if hasattr(self, "shortcuts_overlay"):
            self.shortcuts_overlay.hide()
        self._close_archive()
        self.current_images = []
        self.current_index = -1
        self.current_book = None
        self._current_qimage = None
        self.library_widget.update_books(self.library.books)
        self.stack.setCurrentWidget(self.library_widget)
        self.setWindowTitle("다크 리더")

    def confirm_remove_book(self, book: Book) -> None:
        reply = QMessageBox.question(
            self,
            "책 제거",
            f"'{book.title}'을(를) 라이브러리에서 제거할까요?\n\n"
            "디스크의 ZIP 파일은 삭제되지 않습니다.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        )
        if reply != QMessageBox.StandardButton.Yes:
            return
        if self.library.remove_book(book):
            self.library_widget.update_books(self.library.books)
            if self.current_book and self.current_book.path == book.path:
                self.current_book = None
                self._close_archive()

    def open_zip(self):
        zip_path, _ = QFileDialog.getOpenFileName(
            self,
            "ZIP 선택",
            "",
            "ZIP (*.zip)",
        )
        if zip_path:
            self.load_zip(zip_path)

    def load_zip(self, zip_path: str):
        logger.info("ZIP 로드: %s", zip_path)
        path = Path(zip_path)
        if path.suffix.lower() != ".zip":
            QMessageBox.warning(self, "오류", "ZIP 파일만 열 수 있습니다.")
            return

        self._close_archive()
        try:
            archive = ZipImageArchive(path)
        except (OSError, ValueError) as e:
            QMessageBox.warning(self, "오류", f"ZIP을 열 수 없습니다.\n{e}")
            return

        self.current_archive = archive
        self.current_images = list(archive.members)
        logger.debug("이미지 %d장", len(self.current_images))

        if not self.current_images:
            self._close_archive()
            QMessageBox.warning(
                self, "오류", "선택한 ZIP에 이미지 파일이 없습니다."
            )
            return

        try:
            self.current_book = self.library.add_book(path)
        except ValueError as e:
            self._close_archive()
            QMessageBox.warning(self, "오류", str(e))
            return

        self.current_book.last_opened_at = time.time()
        self.current_book.total_pages = len(self.current_images)
        self.library.update_book(self.current_book)
        self.current_index = self.current_book.get_current_page()
        if self.current_index >= len(self.current_images):
            self.current_index = 0
        self.show_current_image()
        self.stack.setCurrentWidget(self.reader_widget)

    def show_current_image(self, *, persist: bool = True):
        if self.current_archive is None or not (
            0 <= self.current_index < len(self.current_images)
        ):
            return

        member = self.current_images[self.current_index]
        try:
            data = self.current_archive.read_bytes(member)
        except Exception as e:
            logger.exception("멤버 읽기 실패: %s", member)
            QMessageBox.warning(
                self, "오류", f"이미지를 읽을 수 없습니다.\n{member}\n{e}"
            )
            return

        # 업스케일은 테마 무관 원본 키; 표시 시 테마는 ImageProcessor에서 적용
        cache_key = self.current_archive.member_cache_key(member)
        processed_image = self.image_processor.process_bytes(data, cache_key)
        self._current_qimage = processed_image
        self.display_image(processed_image)

        prefetch_items = list(
            self.current_archive.iter_prefetch(self.current_index, count=2)
        )
        if prefetch_items:
            self.image_processor.upscaler.prefetch_images(prefetch_items)

        if persist and self.current_book:
            self.current_book.update_current_page(self.current_index)
            self.library.update_book(self.current_book)
            self.setWindowTitle(
                f"다크 리더 - {self.current_book.title} "
                f"({self.current_index + 1}/{self.current_book.total_pages})"
            )

        if self.image_processor.upscaler.is_cached(cache_key):
            self.status_label.setText("업스케일링 완료")
        else:
            self.status_label.setText("업스케일링 처리 중...")

        self.setFocus()

    def show_next_image(self):
        if self.current_images and self.current_index < len(self.current_images) - 1:
            self.current_index += 1
            self.show_current_image()

    def show_previous_image(self):
        if self.current_images and self.current_index > 0:
            self.current_index -= 1
            self.show_current_image()

    def display_image(self, image: Optional[QImage]):
        if image is None or image.isNull():
            logger.warning("이미지가 유효하지 않습니다.")
            return

        scroll_size = self.scroll_area.viewport().size()
        if scroll_size.width() <= 0 or scroll_size.height() <= 0:
            return

        image_size = image.size()
        if image_size.height() <= 0:
            return
        image_ratio = image_size.width() / image_size.height()

        scaled_width = scroll_size.width()
        scaled_height = int(scaled_width / image_ratio)

        pixmap = QPixmap.fromImage(image)
        if pixmap.isNull():
            logger.warning("QPixmap 변환 실패")
            return

        scaled_pixmap = pixmap.scaled(
            scaled_width,
            scaled_height,
            Qt.AspectRatioMode.KeepAspectRatio,
            Qt.TransformationMode.SmoothTransformation,
        )
        if scaled_pixmap.isNull():
            return

        self.image_label.setPixmap(scaled_pixmap)
        self.image_label.setFixedSize(scaled_width, scaled_height)
        self.image_label.update()
        self.scroll_area.ensureVisible(0, 0)

    def toggle_theme(self):
        self.settings.toggle_theme()
        self.apply_theme()
        if self.current_archive and 0 <= self.current_index < len(self.current_images):
            self.show_current_image(persist=False)

    def apply_theme(self):
        theme = self.settings.current_theme
        self.setStyleSheet(
            f"""
            QMainWindow {{
                background-color: {theme.window_background};
                color: {theme.window_text};
            }}
            QLabel#image_label {{
                background-color: {theme.window_background};
                border: none;
            }}
            QScrollArea {{
                background-color: {theme.window_background};
                border: none;
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
            QFrame#shortcuts_overlay {{
                background-color: rgba(0, 0, 0, 210);
                border: 1px solid rgba(255, 255, 255, 90);
                border-radius: 8px;
            }}
            QLabel#shortcuts_help_label {{
                background-color: transparent;
                color: #f0f0f0;
                font-size: 14px;
            }}
        """
        )
        self.library_widget.update_theme(theme)

    def adjust_contrast(self, delta: float):
        theme = self.settings.current_theme
        theme.contrast = max(0.5, min(2.0, theme.contrast + delta))
        self.show_current_image(persist=False)

    def adjust_brightness(self, delta: float):
        theme = self.settings.current_theme
        theme.brightness = max(0.5, min(1.5, theme.brightness + delta))
        self.show_current_image(persist=False)

    def adjust_sharpness(self, delta: float):
        theme = self.settings.current_theme
        theme.sharpness = max(0.5, min(2.0, theme.sharpness + delta))
        self.show_current_image(persist=False)

    def reload_current_image(self):
        """업스케일 완료 후 메인 스레드에서 현재 이미지를 다시 표시합니다."""
        if self.current_archive and 0 <= self.current_index < len(self.current_images):
            self.show_current_image(persist=False)
            self.setFocus()

    def closeEvent(self, event):
        self._close_archive()
        super().closeEvent(event)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self._update_shortcuts_overlay_geometry()
        if (
            self.stack.currentWidget() == self.reader_widget
            and self._current_qimage is not None
        ):
            self._resize_timer.start(80)

    def _on_resize_debounced(self) -> None:
        """리사이즈 시 이미 로드된 QImage만 다시 스케일합니다."""
        if self._current_qimage is not None:
            self.display_image(self._current_qimage)

    def go_to_answer(self):
        if self.current_book and self.current_images:
            if self.current_book.answer_position is not None:
                self.current_index = self.current_book.answer_position
                self.show_current_image()
                self.status_label.setText(f"정답 {self.current_index + 1}로 이동")
            else:
                self.status_label.setText("저장된 정답이 없습니다")

    def go_to_question(self):
        if self.current_book and self.current_images:
            if self.current_book.question_position is not None:
                self.current_index = self.current_book.question_position
                self.show_current_image()
                self.status_label.setText(f"문제 {self.current_index + 1}로 이동")
            else:
                self.status_label.setText("저장된 문제가 없습니다")

    def toggle_answer_position(self):
        if self.current_book and self.current_images:
            if self.current_book.answer_position == self.current_index:
                self.current_book.clear_answer_position()
                self.status_label.setText("정답 위치 제거됨")
            else:
                self.current_book.set_answer_position(self.current_index)
                self.status_label.setText(f"정답 {self.current_index + 1} 저장됨")
            self.library.update_book(self.current_book)

    def toggle_question_position(self):
        if self.current_book and self.current_images:
            if self.current_book.question_position == self.current_index:
                self.current_book.clear_question_position()
                self.status_label.setText("문제 위치 제거됨")
            else:
                self.current_book.set_question_position(self.current_index)
                self.status_label.setText(f"문제 {self.current_index + 1} 저장됨")
            self.library.update_book(self.current_book)
