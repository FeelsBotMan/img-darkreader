"""ImageUpscaler 큐/캐시 단위 테스트."""
import time
from pathlib import Path

import numpy as np
from PIL import Image

from dark_reader.utils.upscaler import ImageUpscaler


def _png_bytes(size: int = 16) -> bytes:
    from io import BytesIO

    img = Image.new("RGB", (size, size), color=(120, 80, 40))
    buf = BytesIO()
    img.save(buf, format="PNG")
    return buf.getvalue()


def test_upscale_dedupe_and_cache(tmp_path: Path):
    upscaler = ImageUpscaler(
        memory_cache_size=3,
        disk_cache_max_bytes=50 * 1024 * 1024,
        cache_dir=tmp_path / "cache",
    )
    data = _png_bytes()
    key = "testkey123"

    completed: list[str] = []

    def on_done(k: str) -> None:
        completed.append(k)

    assert upscaler.upscale(key, data, callback=on_done, priority=True) is None
    # 동일 키 재요청은 큐에 넣지 않음
    assert upscaler.upscale(key, data, callback=on_done, priority=False) is None

    deadline = time.time() + 5.0
    while time.time() < deadline and not upscaler.is_cached(key):
        time.sleep(0.05)

    assert upscaler.is_cached(key)
    cached = upscaler.get_cached(key)
    assert cached is not None
    assert isinstance(cached, np.ndarray)
    # 2배
    assert cached.shape[0] == 32
    assert cached.shape[1] == 32

    # 캐시 히트 시 cache_key 반환, 추가 enqueue 없음
    before = len(completed)
    assert upscaler.upscale(key, data, callback=on_done) == key
    time.sleep(0.15)
    assert len(completed) == before
    assert not upscaler.is_processing(key)
