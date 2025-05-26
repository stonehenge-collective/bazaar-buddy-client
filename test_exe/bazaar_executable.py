import sys
import os
from PyQt6.QtWidgets import QApplication, QWidget, QLabel, QVBoxLayout, QComboBox
from PyQt6.QtGui import QPixmap
from PyQt6.QtCore import Qt

def resource_path(relative_path):
    """
    Get absolute path to resource, works for dev and PyInstaller.

    PyInstaller stores bundled files in a temporary folder at runtime,
    available via sys._MEIPASS.
    """
    if hasattr(sys, '_MEIPASS'):
        return os.path.join(sys._MEIPASS, relative_path)
    return os.path.abspath(relative_path)

class ImageViewer(QWidget):
    def __init__(self, images_dir="images"):
        super().__init__()
        self.setWindowTitle("The Bazaar Test")

        # Load image files from directory
        abs_images_dir = resource_path(images_dir)
        self.images = [
            f for f in os.listdir(abs_images_dir)
            if f.lower().endswith(('.png', '.jpg', '.jpeg', '.bmp', '.gif'))
        ]
        self.images_dir = abs_images_dir

        # Set up UI
        self.layout = QVBoxLayout()

        # Combo box for selecting images
        self.combo = QComboBox()
        self.combo.addItems(self.images)
        self.combo.currentIndexChanged.connect(self.load_pixmap)
        self.layout.addWidget(self.combo)

        # Label to show image
        self.label = QLabel()
        self.label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.layout.addWidget(self.label)

        self.setLayout(self.layout)

        # Show first image by default
        if self.images:
            self.load_pixmap(0)

    def load_pixmap(self, index):
        image_name = self.images[index]
        image_path = os.path.join(self.images_dir, image_name)
        self.current_pixmap = QPixmap(image_path)
        self.update_scaled_image()

    def resizeEvent(self, event):
        self.update_scaled_image()
        super().resizeEvent(event)

    def update_scaled_image(self):
        if not self.current_pixmap:
            return

        label_width = self.label.width()
        label_height = self.label.height()

        scaled_pixmap = self.current_pixmap.scaled(
            label_width,
            label_height,
            Qt.AspectRatioMode.KeepAspectRatio,
            Qt.TransformationMode.SmoothTransformation

        )
        self.label.setPixmap(scaled_pixmap)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    viewer = ImageViewer()
    viewer.show()
    sys.exit(app.exec())