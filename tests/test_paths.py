"""캐시 경로 / AppPaths 테스트."""
from dark_reader.config.paths import AppPaths
from dark_reader.utils.zip_archive import cache_key_for_member


def test_app_paths_under_dark_reader(tmp_path, monkeypatch):
    monkeypatch.setattr(
        AppPaths, "root", staticmethod(lambda: tmp_path / ".dark_reader")
    )
    AppPaths.ensure_dirs()
    assert AppPaths.config_file().parent == AppPaths.root()
    assert AppPaths.library_file().name == "library.json"
    assert AppPaths.thumbnails_dir().exists()
    assert AppPaths.upscale_cache_dir().exists()
    assert "img-darkreader" not in str(AppPaths.upscale_cache_dir())


def test_cache_key_includes_mode_when_requested(tmp_path):
    p = tmp_path / "x.zip"
    p.write_bytes(b"dummy")
    base = cache_key_for_member(p, "a.jpg")
    dark = cache_key_for_member(p, "a.jpg", mode="dark")
    assert base != dark
