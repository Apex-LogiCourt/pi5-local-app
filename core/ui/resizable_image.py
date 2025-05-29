from PyQt5.QtWidgets import QLabel, QSizePolicy
from PyQt5.QtGui import QPixmap
from PyQt5.QtCore import Qt
import os

# Ensure this path correctly points to your top-level assets directory
# If resizable_image.py is in LogiCourt_AI/ui/resizable_image.py
# and assets is in LogiCourt_AI/assets/
# then os.path.dirname(__file__) is LogiCourt_AI/ui/
# and os.path.join(os.path.dirname(__file__), "..", "assets", filename) is LogiCourt_AI/assets/filename
ROOT_ASSETS_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "assets"))

def _get_image_path(filename: str) -> str:
    """General image path (within assets directory)"""
    path = os.path.join(ROOT_ASSETS_DIR, filename)
    # print(f"[DEBUG] Image Path: {path}, Exists: {os.path.exists(path)}")
    if not os.path.exists(path):
        print(f"[WARNING] Image not found: {path}")
    return path

def _get_profile_image_path(filename: str) -> str:
    """Profile image path (within assets/profile directory)"""
    path = os.path.join(ROOT_ASSETS_DIR, "profile", filename)
    # print(f"[DEBUG] Profile Image Path: {path}, Exists: {os.path.exists(path)}")
    if not os.path.exists(path):
        print(f"[WARNING] Profile image not found: {path}")
    return path

class ResizableImage(QLabel):
    def __init__(self, image_path_func, image_filename, width_limit=None, height_limit=None):
        super().__init__()
        # Use the provided function to get the full image path
        self.image_path = image_path_func(image_filename)
        self.original_pixmap = QPixmap(self.image_path)
        if self.original_pixmap.isNull():
            print(f"Failed to load image: {self.image_path}")
            self.setText(f"Cannot load: {image_filename}")

        self.setAlignment(Qt.AlignCenter)
        self.setScaledContents(False) # Important for quality
        self.width_limit = width_limit
        self.height_limit = height_limit

        self.setStyleSheet("background-color: transparent;")
        self.setSizePolicy(QSizePolicy.Ignored, QSizePolicy.Ignored)
        self.setMinimumSize(1, 1)
        # self.setMaximumSize(16777215, 16777215) # Generally not needed with Ignored policy
        self.update_scaled_pixmap()

    def resizeEvent(self, event):
        self.update_scaled_pixmap()
        super().resizeEvent(event)

    def update_scaled_pixmap(self):
        if self.original_pixmap.isNull():
            # self.setText("Image load error.") # Already set in __init__ if error
            return

        current_width = self.width()
        current_height = self.height()

        if current_width <= 1 or current_height <= 1: # Avoid issues with zero or tiny sizes
            return

        target_width = current_width
        target_height = current_height

        if self.width_limit and self.width_limit < current_width :
            target_width = self.width_limit
        if self.height_limit and self.height_limit < current_height:
            target_height = self.height_limit
        
        # Scale while keeping aspect ratio
        scaled = self.original_pixmap.scaled(
            int(target_width),
            int(target_height),
            Qt.KeepAspectRatio,
            Qt.SmoothTransformation
        )
        self.setPixmap(scaled)

    def set_image(self, image_path_func, image_filename):
        self.image_path = image_path_func(image_filename)
        self.original_pixmap = QPixmap(self.image_path)
        if self.original_pixmap.isNull():
            print(f"Warning: Could not load image from {self.image_path}")
            self.setText(f"Error: {image_filename}")
        self.update_scaled_pixmap()