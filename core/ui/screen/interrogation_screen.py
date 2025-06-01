from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QPushButton, QHBoxLayout,
    QSizePolicy, QFrame, QMessageBox # QMessageBox는 placeholder 메소드에서 사용
)
from PyQt5.QtCore import Qt, QSize
from PyQt5.QtGui import QPixmap, QIcon # QPixmap, QIcon은 직접 사용
# from ui.resizable_image import _get_image_path, _get_profile_image_path # 이 줄은 제거
from ui.style_constants import DARK_BG_COLOR, WHITE_TEXT
# Removed: from core.game_controller import GameController
import re
# import os # 직접적인 경로 문자열을 사용하므로 os 모듈이 필수는 아님 (필요시 추가)

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

# get_profile_pixmap 함수 수정: 직접 경로 사용
def get_profile_pixmap(name: str):
    romanized = KOREAN_TO_ENGLISH_MAP.get(name)
    if not romanized and len(name) >= 2:
        if name[0] in ['김', '이', '박', '최', '정', '강', '조', '윤', '장', '임', '오', '한', '신', '서', '권', '황', '안', '송', '유', '홍'] and len(name) > 1:
            romanized = KOREAN_TO_ENGLISH_MAP.get(name[1:])
        else:
            romanized = KOREAN_TO_ENGLISH_MAP.get(name)

    if romanized:
        # 직접 경로 문자열 사용 (프로젝트 루트 기준)
        image_path = f"core/assets/profile/{romanized}.png"
        pixmap = QPixmap(image_path)
        if pixmap.isNull():
            print(f"Warning: Profile pixmap failed to load: {image_path} for name {name} (romanized: {romanized})")
            return None
        return pixmap
    print(f"Warning: Could not get profile pixmap for {name} (romanized name not found in map)")
    return None


# MicButton 클래스 수정: 직접 경로 사용
class MicButton(QPushButton):
    def __init__(self, icon_filename, on_icon_filename):
        super().__init__()
        self.icon_filename = icon_filename
        self.on_icon_filename = on_icon_filename
        self.default_icon_size = QSize(80, 80)
        self.hover_icon_size = QSize(95, 95)
        self.fixed_box_size = QSize(120, 120)

        self.setFixedSize(self.fixed_box_size)
        # 직접 경로 문자열 사용 (프로젝트 루트 기준)
        default_icon_path = f"core/assets/{self.icon_filename}"
        self.setIcon(QIcon(default_icon_path))
        if self.icon().isNull():
             print(f"Warning: MicButton default icon failed to load: {default_icon_path}")
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
        # 직접 경로 문자열 사용 (프로젝트 루트 기준)
        current_icon_path = f"core/assets/{icon_file_to_use}"
        new_icon = QIcon(current_icon_path)
        if new_icon.isNull():
            print(f"Warning: MicButton icon failed to load: {current_icon_path}")
        self.setIcon(new_icon)


class InterrogationScreen(QWidget):
    def __init__(self, game_controller, on_back_callback, case_summary_text=None, profiles_text=None, target_character_title=""):
        super().__init__()
        self.game_controller = game_controller
        self.on_back_callback = on_back_callback
        self.case_summary = case_summary_text
        self.profiles = profiles_text
        self.mic_on = False

        self.profile_title = target_character_title
        self.dialogue_text = "저는 아무것도 모릅니다"
        self.question_text = "무엇을 보았죠?"

        self.init_ui()

    def init_ui(self):
        self.setStyleSheet(f"background-color: {DARK_BG_COLOR}; color: {WHITE_TEXT};")
        layout = QVBoxLayout()
        layout.setContentsMargins(30, 30, 30, 30)
        layout.setSpacing(20)

        name, role = extract_name_and_role(self.profile_title)
        if not name:
            name = "대상"
            print(f"Warning: Could not parse name/role from '{self.profile_title}'")

        # get_profile_pixmap 함수는 이미 직접 경로를 사용하도록 수정됨
        char_pixmap = get_profile_pixmap(name) if name else None
        
        # 배경 이미지 경로 직접 지정
        background_image_path = "core/assets/background1.png"
        bg_pixmap = QPixmap(background_image_path)
        if bg_pixmap.isNull():
            print(f"Warning: Background image failed to load: {background_image_path}")


        image_frame = QFrame()
        image_frame.setFixedSize(1200, 550)
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
        self.dialog_label.setGeometry(30, 470, 1140, 80)
        self.dialog_label.setAlignment(Qt.AlignCenter)
        self.dialog_label.setWordWrap(True)
        self.dialog_label.raise_()

        back_button = QPushButton(image_frame)
        back_button.setGeometry(1090, 10, 80, 70)
        # 뒤로가기 버튼 아이콘 경로 직접 지정
        back_arrow_icon_path = "core/assets/back_arrow.png"
        back_arrow_icon = QIcon(back_arrow_icon_path)
        if back_arrow_icon.isNull():
            print(f"Warning: Back arrow icon failed to load: {back_arrow_icon_path}")
            back_button.setText("←") # 아이콘 로드 실패 시 텍스트 표시
        else:
            back_button.setIcon(back_arrow_icon)
        back_button.setIconSize(QSize(60, 60))
        back_button.clicked.connect(self.handle_back)
        back_button.setStyleSheet("""
            QPushButton { background-color: #2f5a68; border-radius: 12px; }
        """)
        back_button.raise_()

        evidence_button = QPushButton(image_frame)
        evidence_button.setGeometry(30, 10, 80, 70)
        # 증거 버튼 아이콘 경로 직접 지정
        evidence_icon_path = "core/assets/evidence_icon.png"
        evidence_icon = QIcon(evidence_icon_path)
        if evidence_icon.isNull():
            print(f"Warning: Evidence icon failed to load: {evidence_icon_path}")
            evidence_button.setText("증거") # 아이콘 로드 실패 시 텍스트 표시
        else:
            evidence_button.setIcon(evidence_icon)
        evidence_button.setIconSize(QSize(60, 60))
        evidence_button.clicked.connect(self.show_evidences_placeholder)
        evidence_button.setStyleSheet("""
            QPushButton { background-color: #2f5a68; border-radius: 12px; }
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
        text_input_btn.clicked.connect(self.handle_text_input_placeholder)
        text_input_btn.setStyleSheet("""
            QPushButton {
                background-color: #2f5a68; color: white;
                font-size: 25px; font-weight: bold; border-radius: 10px;
            }
            QPushButton:hover { font-size: 30px; }
        """)

        self.question_label = QLabel(f"당신의 질문 : {self.question_text}")
        self.question_label.setStyleSheet("color: white; font-size: 20px; font-weight: bold;")
        self.question_label.setAlignment(Qt.AlignCenter)
        self.question_label.setWordWrap(True)

        # MicButton 클래스는 이미 내부적으로 직접 경로를 사용하도록 수정됨
        self.btn_mic = MicButton("mike.png", "mike_on.png")
        self.btn_mic.clicked.connect(self.toggle_mic)

        box_layout.addWidget(text_input_btn)
        box_layout.addWidget(self.question_label, 1)
        box_layout.addWidget(self.btn_mic)
        box_frame.setLayout(box_layout)
        layout.addWidget(box_frame)

        self.setLayout(layout)

    def handle_text_input_placeholder(self):
        QMessageBox.information(self, "알림", "텍스트 입력 기능은 구현 중입니다.")

    def show_evidences_placeholder(self):
        QMessageBox.information(self, "증거 확인", "심문 중 증거 확인 기능은 구현 중입니다.")

    def update_dialogue(self, speaker_name, text):
        self.dialog_label.setText(f"{speaker_name} : {text}")

    def update_user_question(self, text):
        self.question_text = text
        self.question_label.setText(f"당신의 질문 : {self.question_text}")

    def set_mic_button_state(self, is_on):
        self.mic_on = is_on
        self.btn_mic.set_icon_on(self.mic_on)

    def toggle_mic(self):
        if self.game_controller:
            if not self.mic_on:
                self.game_controller.record_start()
            else:
                self.game_controller.record_end()
        else:
            print("GameController not available in InterrogationScreen")

    def handle_back(self):
        if self.game_controller:
            self.game_controller.interrogation_end()
        if self.on_back_callback:
            self.on_back_callback()