"""ZIP 아카이브에서 루트 이미지만 나열·읽는 유틸."""
from __future__ import annotations

import hashlib
import zipfile
from pathlib import Path
from typing import Iterator

from .sort_utils import natural_sort_key

IMAGE_EXTENSIONS = {".png", ".jpg", ".jpeg"}


def is_root_image_member(name: str) -> bool:
    """zip 루트의 이미지 멤버인지 판별합니다 (하위 디렉터리 제외)."""
    if not name or name.endswith("/") or name.endswith("\\"):
        return False
    if "/" in name or "\\" in name:
        return False
    return Path(name).suffix.lower() in IMAGE_EXTENSIONS


def list_root_images(zip_path: str | Path) -> list[str]:
    """ZIP 파일 루트의 이미지 멤버명을 자연 정렬하여 반환합니다."""
    path = Path(zip_path)
    with zipfile.ZipFile(path, "r") as zf:
        members = [n for n in zf.namelist() if is_root_image_member(n)]
    return sorted(members, key=natural_sort_key)


def cache_key_for_member(zip_path: str | Path, member: str) -> str:
    """업스케일·썸네일 캐시용 키 (zip 절대경로 + 멤버명)."""
    key = f"{Path(zip_path).resolve()}::{member}"
    return hashlib.md5(key.encode("utf-8")).hexdigest()


class ZipImageArchive:
    """열린 ZIP에서 루트 이미지만 페이지로 제공하는 소스."""

    def __init__(self, path: str | Path):
        self.path = Path(path)
        if self.path.suffix.lower() != ".zip":
            raise ValueError(f"ZIP 파일만 지원합니다: {self.path}")
        if not self.path.is_file():
            raise FileNotFoundError(f"ZIP 파일을 찾을 수 없습니다: {self.path}")
        self._zip = zipfile.ZipFile(self.path, "r")
        self.members: list[str] = sorted(
            [n for n in self._zip.namelist() if is_root_image_member(n)],
            key=natural_sort_key,
        )

    def __enter__(self) -> ZipImageArchive:
        return self

    def __exit__(self, exc_type, exc, tb) -> None:
        self.close()

    def close(self) -> None:
        if self._zip is not None:
            self._zip.close()
            self._zip = None

    def read_bytes(self, member: str) -> bytes:
        if self._zip is None:
            raise RuntimeError("이미 닫힌 아카이브입니다.")
        return self._zip.read(member)

    def iter_prefetch(
        self, start_index: int, count: int = 2
    ) -> Iterator[tuple[str, bytes]]:
        """다음 페이지들의 (cache_key, bytes)를 순회합니다."""
        for i in range(1, count + 1):
            idx = start_index + i
            if idx >= len(self.members):
                break
            member = self.members[idx]
            yield cache_key_for_member(self.path, member), self.read_bytes(member)

    def member_cache_key(self, member: str) -> str:
        return cache_key_for_member(self.path, member)
