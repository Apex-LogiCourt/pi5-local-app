from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QPushButton, QHBoxLayout,
    QSizePolicy, QFrame, QMessageBox
)
from PyQt5.QtCore import Qt, QSize
from PyQt5.QtGui import QPixmap, QIcon

# Assuming resizable_image.py is in the parent directory 'ui'
# and _get_profile_image_path expects a filename relative to 'assets/profile/'
from ui.resizable_image import _get_image_path, _get_profile_image_path
from ui.style_constants import DARK_BG_COLOR, WHITE_TEXT
# Removed: from core.game_controller import GameController
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
    if not romanized and len(name) >= 2: # Try removing first char if it's a common surname initial
        if name[0] in ['김', '이', '박', '최', '정', '강', '조', '윤', '장', '임', '오', '한', '신', '서', '권', '황', '안', '송', '유', '홍'] and len(name) > 1:
             romanized = KOREAN_TO_ENGLISH_MAP.get(name[1:])
        else: # Fallback for two-character names that might not be full names
            romanized = KOREAN_TO_ENGLISH_MAP.get(name)

    if romanized:
        # _get_profile_image_path expects only the filename, not the "profile/" prefix
        return QPixmap(_get_profile_image_path(f"{romanized}.png"))
    print(f"Warning: Could not get profile pixmap for {name}")
    return None


class MicButton(QPushButton):
    def __init__(self, icon_filename, on_icon_filename): # Filenames instead of full paths
        super().__init__()
        self.icon_filename = icon_filename
        self.on_icon_filename = on_icon_filename
        self.default_icon_size = QSize(80, 80)
        self.hover_icon_size = QSize(95, 95)
        self.fixed_box_size = QSize(120, 120)

        self.setFixedSize(self.fixed_box_size)
        self.setIcon(QIcon(_get_image_path(self.icon_filename))) # Use _get_image_path
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
        icon_file_to_use = self.on_icon_filename if is_on else self.icon_filename
        self.setIcon(QIcon(_get_image_path(icon_file_to_use)))


class InterrogationScreen(QWidget):
    def __init__(self, game_controller, on_back_callback, case_summary_text=None, profiles_text=None, target_character_title=""):
        super().__init__()
        self.game_controller = game_controller
        self.on_back_callback = on_back_callback # Renamed from on_back
        self.case_summary = case_summary_text # Data passed in
        self.profiles = profiles_text # Data passed in
        self.mic_on = False

        self.profile_title = target_character_title # e.g., "이름 : 우민영 (피고)"
        self.dialogue_text = "저는 아무것도 모릅니다" # Initial placeholder
        self.question_text = "무엇을 보았죠?" # Initial placeholder for user's question

        self.init_ui()

    def init_ui(self):
        self.setStyleSheet(f"background-color: {DARK_BG_COLOR}; color: {WHITE_TEXT};")
        layout = QVBoxLayout()
        layout.setContentsMargins(30, 30, 30, 30)
        layout.setSpacing(20)

        name, role = extract_name_and_role(self.profile_title)
        if not name:
            name = "대상" # Default if parsing fails
            print(f"Warning: Could not parse name/role from '{self.profile_title}'")

        char_pixmap = get_profile_pixmap(name) if name else None
        bg_pixmap = QPixmap(_get_image_path("background1.png"))

        image_frame = QFrame()
        image_frame.setFixedSize(1200, 550) # Consider making this responsive
        image_frame.setStyleSheet("background-color: transparent;")

        background_label = QLabel(image_frame)
        if not bg_pixmap.isNull():
            background_label.setPixmap(bg_pixmap.scaled(1200, 550, Qt.KeepAspectRatioByExpanding, Qt.SmoothTransformation))
        background_label.setGeometry(0, 0, 1200, 550)

        char_label = QLabel(image_frame)
        if char_pixmap and not char_pixmap.isNull():
            char_label.setPixmap(char_pixmap.scaled(500, 500, Qt.KeepAspectRatio, Qt.SmoothTransformation))
        else:
            char_label.setText(f"{name}\n(이미지 없음)")
            char_label.setAlignment(Qt.AlignCenter)
        char_label.setGeometry(350, 80, 500, 500)
        char_label.setStyleSheet("background: transparent; color: white; font-size: 20px;")
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
        self.dialog_label.setGeometry(30, 470, 1140, 80) # Covers bottom part of image_frame
        self.dialog_label.setAlignment(Qt.AlignCenter)
        self.dialog_label.setWordWrap(True)
        self.dialog_label.raise_()

        back_button = QPushButton(image_frame) # Parent set
        back_button.setGeometry(1090, 10, 80, 70)
        back_button.setIcon(QIcon(_get_image_path("back_arrow.png")))
        back_button.setIconSize(QSize(60, 60))
        back_button.clicked.connect(self.handle_back)
        back_button.setStyleSheet("""
            QPushButton { background-color: #2f5a68; border-radius: 12px; }
        """)
        back_button.raise_()

        evidence_button = QPushButton(image_frame) # Parent set
        evidence_button.setGeometry(30, 10, 80, 70)
        evidence_button.setIcon(QIcon(_get_image_path("evidence_icon.png")))
        evidence_button.setIconSize(QSize(60, 60))
        evidence_button.clicked.connect(self.show_evidences_placeholder) # Placeholder
        evidence_button.setStyleSheet("""
            QPushButton { background-color: #2f5a68; border-radius: 12px; }
        """)
        evidence_button.raise_()

        layout.addWidget(image_frame, alignment=Qt.AlignCenter)

        box_frame = QFrame()
        box_frame.setStyleSheet("background-color: black;") # Or DARK_BG_COLOR for consistency
        box_layout = QHBoxLayout()
        box_layout.setContentsMargins(20, 20, 20, 20)
        box_layout.setSpacing(30)

        text_input_btn = QPushButton("텍스트 입력") # Placeholder for actual text input field later
        text_input_btn.setFixedSize(200, 120)
        text_input_btn.clicked.connect(self.handle_text_input_placeholder)
        text_input_btn.setStyleSheet("""
            QPushButton {
                background-color: #2f5a68; color: white;
                font-size: 25px; font-weight: bold; border-radius: 10px;
            }
            QPushButton:hover { font-size: 30px; } /* Adjusted hover size */
        """)

        self.question_label = QLabel(f"당신의 질문 : {self.question_text}") # Changed "검사측"
        self.question_label.setStyleSheet("color: white; font-size: 20px; font-weight: bold;")
        self.question_label.setAlignment(Qt.AlignCenter)
        self.question_label.setWordWrap(True)

        self.btn_mic = MicButton("mike.png", "mike_on.png")
        self.btn_mic.clicked.connect(self.toggle_mic)

        box_layout.addWidget(text_input_btn)
        box_layout.addWidget(self.question_label, 1) # Give question label more space
        box_layout.addWidget(self.btn_mic)
        box_frame.setLayout(box_layout)
        layout.addWidget(box_frame)

        self.setLayout(layout)

    def handle_text_input_placeholder(self):
        # This should eventually open a QInputDialog or a custom input widget
        # For now, it might send a predefined question or open a simple dialog
        # from PyQt5.QtWidgets import QInputDialog
        # text, ok = QInputDialog.getText(self, '질문 입력', '질문할 내용을 입력하세요:')
        # if ok and text:
        #     self.question_text = text
        #     self.question_label.setText(f"당신의 질문 : {self.question_text}")
        #     if self.game_controller:
        #         # self.game_controller.user_input(text) # Example
        #         print(f"User input sent (placeholder): {text}")
        QMessageBox.information(self, "알림", "텍스트 입력 기능은 구현 중입니다.")


    def show_evidences_placeholder(self):
        QMessageBox.information(self, "증거 확인", "심문 중 증거 확인 기능은 구현 중입니다.")


    def update_dialogue(self, speaker_name, text):
        self.dialog_label.setText(f"{speaker_name} : {text}")

    def update_user_question(self, text):
        self.question_text = text
        self.question_label.setText(f"당신의 질문 : {self.question_text}")

    def set_mic_button_state(self, is_on):
        """Called by MainWindow based on record_start/stop signals"""
        self.mic_on = is_on
        self.btn_mic.set_icon_on(self.mic_on)

    def toggle_mic(self):
        # self.mic_on = not self.mic_on # State will be set by signal
        # self.btn_mic.set_icon_on(self.mic_on)
        if self.game_controller:
            if not self.mic_on: # If mic is currently off, send record_start
                self.game_controller.record_start()
            else: # If mic is currently on, send record_end
                self.game_controller.record_end()
        else:
            print("GameController not available in InterrogationScreen")


    def handle_back(self):
        if self.game_controller:
            self.game_controller.interrogation_end() # Notify controller
        if self.on_back_callback:
            self.on_back_callback()