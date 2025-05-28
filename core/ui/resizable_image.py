from PyQt5.QtWidgets import QLabel, QSizePolicy
from PyQt5.QtGui import QPixmap
from PyQt5.QtCore import Qt
import os

def _get_image_path(filename: str) -> str:
    """일반 이미지 경로 (core/assets/ 내부)"""
    path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "assets", filename))
    print("[DEBUG] 이미지 경로:", path)
    print("[DEBUG] 실제 존재?:", os.path.exists(path))
    return path

def _get_profile_image_path(filename: str) -> str:
    """프로필 이미지 전용 경로 (core/assets/profile/ 내부)"""
    path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "assets", "profile", filename))
    print("[DEBUG] 프로필 이미지 경로:", path)
    print("[DEBUG] 실제 존재?:", os.path.exists(path))
    return path

class ResizableImage(QLabel):
    def __init__(self, image_path, width_limit=None, height_limit=None):
        super().__init__()
        self.image_path = image_path
        self.original_pixmap = QPixmap(self.image_path)
        self.setAlignment(Qt.AlignCenter)
        self.setScaledContents(False)
        self.width_limit = width_limit
        self.height_limit = height_limit

        self.setStyleSheet("background-color: transparent;")
        self.setSizePolicy(QSizePolicy.Ignored, QSizePolicy.Ignored)
        self.setMinimumSize(1, 1)
        self.setMaximumSize(16777215, 16777215)
        self.update_scaled_pixmap()

    def resizeEvent(self, event):
        self.update_scaled_pixmap()
        super().resizeEvent(event)

    def update_scaled_pixmap(self):
        if self.original_pixmap.isNull():
            self.setText("이미지를 불러올 수 없습니다.")
            return

        current_width = self.width()
        current_height = self.height()

        target_width = max(1, self.width_limit if self.width_limit else current_width)
        target_height = max(1, self.height_limit if self.height_limit else current_height)

        if not self.width_limit or self.width_limit > current_width:
            target_width = current_width
        if not self.height_limit or self.height_limit > current_height:
            target_height = current_height

        scaled = self.original_pixmap.scaled(
            int(target_width),
            int(target_height),
            Qt.KeepAspectRatio,
            Qt.SmoothTransformation
        )
        self.setPixmap(scaled)

    def set_image(self, image_path):
        self.image_path = image_path
        self.original_pixmap = QPixmap(image_path)
        if self.original_pixmap.isNull():
            print(f"Warning: Could not load image from {image_path}")
        self.update_scaled_pixmap()
