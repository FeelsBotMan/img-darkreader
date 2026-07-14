"""ZIP 아카이브 유틸 테스트."""
import zipfile
from pathlib import Path

from dark_reader.utils.zip_archive import (
    cache_key_for_member,
    is_root_image_member,
    list_root_images,
)


def test_is_root_image_member():
    assert is_root_image_member("page01.jpg")
    assert is_root_image_member("cover.PNG")
    assert not is_root_image_member("sub/page01.jpg")
    assert not is_root_image_member("folder/")
    assert not is_root_image_member("readme.txt")


def test_list_root_images(tmp_path: Path):
    zip_path = tmp_path / "book.zip"
    with zipfile.ZipFile(zip_path, "w") as zf:
        zf.writestr("2.png", b"fake")
        zf.writestr("10.png", b"fake")
        zf.writestr("1.png", b"fake")
        zf.writestr("nested/x.png", b"fake")
        zf.writestr("note.txt", b"x")
    members = list_root_images(zip_path)
    assert members == ["1.png", "2.png", "10.png"]


def test_cache_key_stable_and_mode(tmp_path: Path):
    zip_path = tmp_path / "a.zip"
    zip_path.write_bytes(b"PK\x05\x06" + b"\x00" * 18)
    k1 = cache_key_for_member(zip_path, "1.png")
    k2 = cache_key_for_member(zip_path, "1.png")
    assert k1 == k2
    assert len(k1) == 32
    k_dark = cache_key_for_member(zip_path, "1.png", mode="dark")
    k_light = cache_key_for_member(zip_path, "1.png", mode="light")
    assert k_dark != k1
    assert k_dark != k_light
