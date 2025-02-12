from setuptools import setup, find_packages

setup(
    name="dark_reader",
    version="0.1",
    packages=find_packages(),
    install_requires=[
        "PyQt6",
        "Pillow",
        "PyYAML",
        "numpy"
    ],
) 