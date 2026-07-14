from __future__ import annotations

import logging
import sys

from PyQt6.QtWidgets import QApplication

from .viewer.image_viewer import ImageViewer


def _configure_logging() -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        datefmt="%H:%M:%S",
        stream=sys.stderr,
    )


def main():
    _configure_logging()
    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    viewer = ImageViewer()
    viewer.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
