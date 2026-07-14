"""정렬 유틸리티 - 자연 정렬(natural sort) 지원."""
import re
from pathlib import Path


def natural_sort_key(path: Path | str) -> list:
    """
    자연 정렬을 위한 키 함수.

    image_1, image_2, image_10, image_100 순으로 정렬됩니다.
    문자열 정렬과 달리 숫자 부분을 수치로 비교합니다.
    Path 또는 파일명 문자열( zip 멤버명 등)을 받을 수 있습니다.
    """
    name = path.name if isinstance(path, Path) else Path(path).name
    parts = re.split(r"(\d+)", name)
    return [int(p) if p.isdigit() else p.lower() for p in parts]
