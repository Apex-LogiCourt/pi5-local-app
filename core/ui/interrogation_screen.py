from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QPushButton, QHBoxLayout,
    QSizePolicy, QFrame
)
from PyQt5.QtCore import Qt, QSize
from PyQt5.QtGui import QPixmap, QIcon

from ui.resizable_image import _get_image_path
from ui.style_constants import DARK_BG_COLOR, WHITE_TEXT
from core.game_controller import GameController
import re

KOREAN_TO_ENGLISH_MAP = {
    "은영": "Eunyoung", "봄달": "Bomdal", "지훈": "Jihoon", "소현": "Sohyun",
    "영화": "Younghwa", "성일": "Sungil", "기효": "Kihyo", "승표": "Seungpyo",
    "주안": "Jooahn", "선희": "Sunhee", "민영": "Minyoung", "상도": "Sangdo",
    "기서": "Kiseo", "원탁": "Wontak", "이안": "Ian"
}

def extract_name_and_role(title_line):
    match = re.search(r"이름\s*:\s*(\S+)\s*\((피고|피해자|목격자|참고인)\)", title_line)
    if match:
        return match.group(1), match.group(2)
    return None, None

def get_profile_pixmap(name: str):
    romanized = KOREAN_TO_ENGLISH_MAP.get(name)
    if not romanized and len(name) >= 2:
        romanized = KOREAN_TO_ENGLISH_MAP.get(name[1:])
    if romanized:
        return QPixmap(_get_image_path(f"profile/{romanized}.png"))
    return None

class MicButton(QPushButton):
    def __init__(self, icon_path, on_icon_path):
        super().__init__()
        self.icon_path = icon_path
        self.on_icon_path = on_icon_path
        self.default_icon_size = QSize(80, 80)
        self.hover_icon_size = QSize(95, 95)
        self.fixed_box_size = QSize(120, 120)

        self.setFixedSize(self.fixed_box_size)
        self.setIcon(QIcon(_get_image_path(self.icon_path)))
        self.setIconSize(self.default_icon_size)

        self.setStyleSheet("""
            QPushButton {
                background-color: #2f5a68;
                border-radius: 12px;
            }
        """)

    def enterEvent(self, event):
        self.setIconSize(self.hover_icon_size)
        super().enterEvent(event)

    def leaveEvent(self, event):
        self.setIconSize(self.default_icon_size)
        super().leaveEvent(event)

    def set_icon_on(self, is_on):
        icon_file = self.on_icon_path if is_on else self.icon_path
        self.setIcon(QIcon(_get_image_path(icon_file)))

class InterrogationScreen(QWidget):
    def __init__(self, case_summary=None, profiles=None, on_back=None):
        super().__init__()
        self.case_summary = case_summary or GameController._case.outline
        self.profiles = profiles or GameController._profiles
        self.on_back = on_back
        self.mic_on = False

        self.profile_title = "이름 : 우민영 (피고)"
        self.dialogue_text = "저는 아무것도 모릅니다"
        self.question_text = "무엇을 보았죠?"

        self.init_ui()

    def init_ui(self):
        self.setStyleSheet(f"background-color: {DARK_BG_COLOR}; color: {WHITE_TEXT};")
        layout = QVBoxLayout()
        layout.setContentsMargins(30, 30, 30, 30)
        layout.setSpacing(20)

        name, _ = extract_name_and_role(self.profile_title)
        char_pixmap = get_profile_pixmap(name)
        bg_pixmap = QPixmap(_get_image_path("background1.png"))

        image_frame = QFrame()
        image_frame.setFixedSize(1200, 550)
        image_frame.setStyleSheet("background-color: transparent;")

        background_label = QLabel(image_frame)
        background_label.setPixmap(bg_pixmap.scaled(1200, 550, Qt.KeepAspectRatioByExpanding, Qt.SmoothTransformation))
        background_label.setGeometry(0, 0, 1200, 550)

        char_label = QLabel(image_frame)
        if char_pixmap:
            char_label.setPixmap(char_pixmap.scaled(500, 500, Qt.KeepAspectRatio, Qt.SmoothTransformation))
        char_label.setGeometry(350, 80, 500, 500)
        char_label.setStyleSheet("background: transparent;")
        char_label.setAlignment(Qt.AlignCenter)
        char_label.raise_()

        self.dialog_label = QLabel(f"{name} : {self.dialogue_text}", image_frame)
        self.dialog_label.setStyleSheet("""
            color: white;
            font-size: 20px;
            font-weight: bold;
            background-color: rgba(0,0,0,100);
            padding: 12px 0px;
            min-width: 1140px;
        """)
        self.dialog_label.setGeometry(30, 470, 1140, 80)
        self.dialog_label.setAlignment(Qt.AlignCenter)
        self.dialog_label.raise_()

        back_button = QPushButton()
        back_button.setParent(image_frame)
        back_button.setGeometry(1090, 10, 80, 70)
        back_button.setIcon(QIcon(_get_image_path("back_arrow.png")))
        back_button.setIconSize(QSize(60, 60))
        back_button.clicked.connect(self.handle_back)
        back_button.setStyleSheet("""
            QPushButton {
                background-color: #2f5a68;
                border-radius: 12px;
            }
        """)
        back_button.raise_()

        evidence_button = QPushButton()
        evidence_button.setParent(image_frame)
        evidence_button.setGeometry(30, 10, 80, 70)
        evidence_button.setIcon(QIcon(_get_image_path("evidence_icon.png")))
        evidence_button.setIconSize(QSize(60, 60))
        evidence_button.setStyleSheet("""
            QPushButton {
                background-color: #2f5a68;
                border-radius: 12px;
            }
        """)
        evidence_button.raise_()

        layout.addWidget(image_frame, alignment=Qt.AlignCenter)

        box_frame = QFrame()
        box_frame.setStyleSheet("background-color: black;")
        box_layout = QHBoxLayout()
        box_layout.setContentsMargins(20, 20, 20, 20)
        box_layout.setSpacing(30)

        text_input_btn = QPushButton("텍스트 입력")
        text_input_btn.setFixedSize(200, 120)
        text_input_btn.setStyleSheet("""
            QPushButton {
                background-color: #2f5a68;
                color: white;
                font-size: 25px;
                font-weight: bold;
                border-radius: 10px;
            }       
            QPushButton:hover {
                font-size: 35px;
            }
        """)

        self.question_label = QLabel(f"검사측 질문 : {self.question_text}")
        self.question_label.setStyleSheet("color: white; font-size: 20px; font-weight: bold;")
        self.question_label.setAlignment(Qt.AlignCenter)

        self.btn_mic = MicButton("mike.png", "mike_on.png")
        self.btn_mic.clicked.connect(self.toggle_mic)

        box_layout.addWidget(text_input_btn)
        box_layout.addWidget(self.question_label)
        box_layout.addWidget(self.btn_mic)
        box_frame.setLayout(box_layout)
        layout.addWidget(box_frame)

        self.setLayout(layout)

    def toggle_mic(self):
        self.mic_on = not self.mic_on
        self.btn_mic.set_icon_on(self.mic_on)

    def handle_back(self):
        if self.on_back:
            self.on_back()
