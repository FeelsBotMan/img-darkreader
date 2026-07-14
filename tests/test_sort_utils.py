"""natural_sort_key 단위 테스트."""
from dark_reader.utils.sort_utils import natural_sort_key


def test_natural_sort_numeric_order():
    names = ["image_10.png", "image_2.png", "image_1.png", "image_100.png"]
    sorted_names = sorted(names, key=natural_sort_key)
    assert sorted_names == [
        "image_1.png",
        "image_2.png",
        "image_10.png",
        "image_100.png",
    ]


def test_natural_sort_case_insensitive():
    names = ["B.jpg", "a.jpg", "C.jpg"]
    sorted_names = sorted(names, key=natural_sort_key)
    assert sorted_names == ["a.jpg", "B.jpg", "C.jpg"]
