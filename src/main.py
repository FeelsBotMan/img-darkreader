from PyQt6.QtWidgets import QApplication
import sys
from viewer.image_viewer import ImageViewer

def main():
    app = QApplication(sys.argv)
    
    # 다크 테마 적용
    app.setStyle('Fusion')
    
    viewer = ImageViewer()
    viewer.show()
    
    sys.exit(app.exec())

if __name__ == '__main__':
    main() 