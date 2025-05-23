from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QPushButton, QHBoxLayout,
    QSizePolicy, QMessageBox, QGridLayout, QDialog
)
from PyQt5.QtCore import Qt, QSize
from PyQt5.QtGui import QIcon, QPixmap
from ui.resizable_image import ResizableImage, _get_image_path
from ui.style_constants import DARK_BG_COLOR, WHITE_TEXT
from core.controller import CaseDataManager
import re

# HoverButton
class HoverButton(QPushButton):
    def __init__(self, text, min_height=80, max_height=110):
        super().__init__(text)
        self.default_font_size = 26
        self.hover_font_size = 34
        self.default_min_height = min_height
        self.hover_min_height = max_height
        self.setStyleSheet(self.get_stylesheet(self.default_font_size))
        self.setMinimumHeight(self.default_min_height)
        self.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Preferred)

    def enterEvent(self, event):
        self.setStyleSheet(self.get_stylesheet(self.hover_font_size))
        self.setMinimumHeight(self.hover_min_height)
        self.resize(self.sizeHint())
        super().enterEvent(event)

    def leaveEvent(self, event):
        self.setStyleSheet(self.get_stylesheet(self.default_font_size))
        self.setMinimumHeight(self.default_min_height)
        self.resize(self.sizeHint())
        super().leaveEvent(event)

    def get_stylesheet(self, font_size):
        return f"""
        QPushButton {{
            background-color: transparent;
            color: white;
            font-size: {font_size}px;
            font-weight: bold;
            border: none;
            padding: 16px;
            text-align: left;
        }}
        """

# MicButton
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

# 이름 한글→영문 변환 맵
KOREAN_TO_ENGLISH_MAP = {
    "은영": "Eunyoung", "봄달": "Bomdal", "지훈": "Jihoon", "소현": "Sohyun",
    "영화": "Younghwa", "성일": "Sungil", "기효": "Kihyo", "승표": "Seungpyo",
    "주안": "Jooahn", "선희": "Sunhee", "민영": "Minyoung", "상도": "Sangdo",
    "기서": "Kiseo", "원탁": "Wontak", "이안": "Ian"
}

def get_profile_pixmap(name: str):
    romanized = KOREAN_TO_ENGLISH_MAP.get(name)
    if not romanized and len(name) >= 2:
        romanized = KOREAN_TO_ENGLISH_MAP.get(name[1:])
    if romanized:
        return QPixmap(_get_image_path(f"profile/{romanized}.png"))
    return None

def extract_name_and_role(title_line):
    match = re.search(r"(피고|피해자|목격자|참고인)\s*:\s*(\S+)", title_line)
    if match:
        return match.group(2), match.group(1)
    return None, None

# LawyerScreen
class LawyerScreen(QWidget):
    def __init__(self, case_summary="", profiles="", on_next=None):
        super().__init__()
        self.case_summary = case_summary
        self.profiles_text = profiles
        self.on_next = on_next
        self.evidences = CaseDataManager.get_evidences() or []
        self.mic_on = False
        self.init_ui()

    def init_ui(self):
        self.setStyleSheet(f"background-color: {DARK_BG_COLOR}; color: {WHITE_TEXT};")

        title_label = QLabel("변호사 변론")
        title_label.setAlignment(Qt.AlignCenter)
        title_label.setStyleSheet("""
            background-color: black;
            color: white;
            font-size: 40px;
            font-weight: bold;
            padding: 10px;
            border-radius: 6px;
        """)
        title_label.setFixedWidth(260)

        title_wrapper = QHBoxLayout()
        title_wrapper.addStretch(1)
        title_wrapper.addWidget(title_label)
        title_wrapper.addStretch(1)

        def make_invisible_button(text, handler=None):
            btn = HoverButton(text)
            if handler:
                btn.clicked.connect(handler)
            return btn

        menu_layout = QVBoxLayout()
        menu_layout.setSpacing(15)
        menu_layout.addWidget(make_invisible_button("사건개요", self.show_case_dialog))
        menu_layout.addWidget(make_invisible_button("증거품 확인", self.show_evidences))
        menu_layout.addWidget(make_invisible_button("텍스트입력", self.show_text_input_placeholder))
        menu_layout.addStretch()

        summary_lines = ["등장인물"]
        for part in self.profiles_text.split('--------------------------------'):
            part = part.strip()
            if not part:
                continue
            lines = part.split('\n')
            title = lines[0]
            name, role = extract_name_and_role(title)
            if name and role:
                summary_lines.append(f"• {name} : {role}")
        summary_text = "\n".join(summary_lines)

        profile_button = HoverButton(summary_text, min_height=100, max_height=130)
        profile_button.clicked.connect(self.show_full_profiles_dialog)

        self.btn_mic = MicButton("mike.png", "mike_on.png")
        self.btn_mic.clicked.connect(self.toggle_mic_icon)

        btn_next = QPushButton("주장종료")
        btn_next.setFixedSize(250, 100)
        btn_next.setStyleSheet("""
            QPushButton {
                background-color: #2f5a68;
                color: white;
                border-radius: 12px;
                font-size: 26px;
                font-weight: bold;
            }
            QPushButton:hover {
                font-size: 30px;
            }
        """)
        btn_next.clicked.connect(self.proceed_to_next)

        # 오른쪽 버튼 패널
        right_button_grid = QGridLayout()
        right_button_grid.setSpacing(30)
        right_button_grid.addLayout(menu_layout, 0, 0)
        right_button_grid.addWidget(profile_button, 0, 1)
        right_button_grid.addWidget(self.btn_mic, 1, 0, alignment=Qt.AlignCenter)
        right_button_grid.addWidget(btn_next, 1, 1, alignment=Qt.AlignLeft)

        right_wrapper = QVBoxLayout()
        right_wrapper.setContentsMargins(40, 30, 20, 30)
        right_wrapper.setSpacing(20)
        right_wrapper.addLayout(title_wrapper)
        right_wrapper.addStretch(1)
        right_wrapper.addLayout(right_button_grid)
        right_wrapper.addStretch(2)

        image_label = ResizableImage(_get_image_path("profile/lawyer.png"))
        image_label.setMaximumWidth(420)
        image_label.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

        left_layout = QVBoxLayout()
        left_layout.addStretch()
        left_layout.addWidget(image_label, alignment=Qt.AlignLeft)
        left_layout.addStretch()

        main_layout = QHBoxLayout()
        main_layout.setContentsMargins(40, 30, 100, 30)
        main_layout.setSpacing(30)
        main_layout.addLayout(left_layout, 2)      # 이미지 오른쪽
        main_layout.addLayout(right_wrapper, 3)    # 버튼 왼쪽

        self.setLayout(main_layout)

    def toggle_mic_icon(self):
        self.mic_on = not self.mic_on
        self.btn_mic.set_icon_on(self.mic_on)

    def proceed_to_next(self):
        if self.on_next:
            self.on_next()

    def show_case_dialog(self):
        lines = self.case_summary.strip().split('\n')
        filtered_lines = [line for line in lines if not any(tag in line for tag in ["[피고", "[피해자", "[증인1", "[증인2"])]
        clean_text = "\n".join(filtered_lines)

        msg = QMessageBox(self)
        msg.setWindowTitle("사건 개요")
        msg.setText(clean_text)
        msg.setStyleSheet("QLabel { font-size: 16px; }")
        msg.setStandardButtons(QMessageBox.Ok)
        msg.exec_()

    def show_evidences(self):
        prosecutors = []
        attorneys = []
        for e in self.evidences:
            summary = f"• {e.name}: {e.description[0]}"
            if e.type == "prosecutor":
                prosecutors.append(summary)
            elif e.type == "attorney":
                attorneys.append(summary)
        parts = []
        if attorneys:
            parts.append("🔶 변호사 측 증거품\n" + "\n".join(attorneys))
        if prosecutors:
            parts.append("🔷 검사 측 증거품\n" + "\n".join(prosecutors))
        text = "\n\n".join(parts) if parts else "등록된 증거물이 없습니다."

        msg = QMessageBox(self)
        msg.setWindowTitle("모든 증거품")
        msg.setText(text)
        msg.setStyleSheet("QLabel { font-size: 16px; }")
        msg.setStandardButtons(QMessageBox.Ok)
        msg.exec_()

    def show_text_input_placeholder(self):
        msg = QMessageBox(self)
        msg.setWindowTitle("텍스트입력")
        msg.setText("입력 기능은 추후 구현 예정입니다.")
        msg.setStyleSheet("QLabel { font-size: 16px; }")
        msg.setStandardButtons(QMessageBox.Ok)
        msg.exec_()

    def show_full_profiles_dialog(self):
        dialog = QDialog(self)
        dialog.setWindowTitle("등장인물 정보")
        dialog.setStyleSheet("background-color: #0f2a45; color: white; font-size: 15px;")
        layout = QVBoxLayout()

        for part in self.profiles_text.split('--------------------------------'):
            part = part.strip()
            if not part:
                continue
            lines = part.split('\n')
            title = lines[0]
            info_text = "\n".join(lines[1:])

            row_layout = QHBoxLayout()
            left = QVBoxLayout()

            title_label = QLabel(f"<b>{title}</b>")
            title_label.setStyleSheet("font-size: 15px;")
            left.addWidget(title_label)

            info_label = QLabel(info_text)
            info_label.setWordWrap(True)
            info_label.setStyleSheet("font-size: 15px;")
            left.addWidget(info_label)

            name_match = re.search(r":\s*(.+?)\s*[\(\[]", title)
            if name_match:
                name = name_match.group(1)
                pixmap = get_profile_pixmap(name)
                if pixmap:
                    img_label = QLabel()
                    img_label.setPixmap(pixmap.scaledToWidth(150, Qt.SmoothTransformation))
                    row_layout.addLayout(left, 3)
                    row_layout.addWidget(img_label, 1)
                    layout.addLayout(row_layout)
                    continue

            layout.addLayout(left)

        dialog.setLayout(layout)
        dialog.setMinimumWidth(500)
        dialog.exec_()