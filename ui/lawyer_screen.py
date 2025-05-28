from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QPushButton, QHBoxLayout,
    QSizePolicy, QMessageBox, QGridLayout, QDialog, QFrame
)
from PyQt5.QtCore import Qt, QSize
from PyQt5.QtGui import QIcon, QPixmap
from ui.resizable_image import ResizableImage, _get_image_path # Ensure this path is correct
from ui.style_constants import DARK_BG_COLOR, WHITE_TEXT # Ensure this path is correct
from core.game_controller import GameController
import re

# --- HoverButton (메뉴 및 등장인물용) ---
# (Copy HoverButton class from prosecutor.py or make it a common UI component)
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
        super().enterEvent(event)

    def leaveEvent(self, event):
        self.setStyleSheet(self.get_stylesheet(self.default_font_size))
        self.setMinimumHeight(self.default_min_height)
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

# --- MicButton ---
# (Copy MicButton class from prosecutor.py or make it a common UI component)
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
            QPushButton { background-color: #2f5a68; border-radius: 12px; }
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

# --- 이름 매핑 및 유틸리티 함수 ---
# (Copy KOREAN_TO_ENGLISH_MAP, get_profile_pixmap, extract_name_and_role from prosecutor.py or common UI file)
KOREAN_TO_ENGLISH_MAP = {
    "은영": "Eunyoung", "봄달": "Bomdal", "지훈": "Jihoon", "소현": "Sohyun",
    "영화": "Younghwa", "성일": "Sungil", "기효": "Kihyo", "승표": "Seungpyo",
    "주안": "Jooahn", "선희": "Sunhee", "민영": "Minyoung", "상도": "Sangdo",
    "기서": "Kiseo", "원탁": "Wontak", "이안": "Ian"
}

def get_profile_pixmap(name: str):
    simple_name = name.split(" ")[-1] 
    if len(simple_name) > 2 and simple_name[0] in ['김', '이', '박', '최', '정', '강', '조', '윤', '장', '임', '오', '한', '신', '서', '권', '황', '안', '송', '유', '홍']:
         simple_name = simple_name[1:]
    romanized = KOREAN_TO_ENGLISH_MAP.get(simple_name)
    if not romanized and len(name) >= 2:
        romanized = KOREAN_TO_ENGLISH_MAP.get(name[1:]) if len(name) > 1 else KOREAN_TO_ENGLISH_MAP.get(name)
    if romanized:
        path = _get_image_path(f"profile/{romanized}.png")
        if QPixmap(path).isNull():
             print(f"Warning: Profile image not found or failed to load: {path}")
             return None
        return QPixmap(path)
    print(f"Warning: Could not find romanized name for profile: {name} (tried {simple_name})")
    return None

def extract_name_and_role(title_line):
    match = re.search(r"이름\s*:\s*(\S+)\s*\((피고|피해자|목격자|참고인)\)", title_line)
    if match:
        return match.group(1).strip(), match.group(2).strip()
    return None, None


class LawyerScreen(QWidget):
    def __init__(self, case_summary="", profiles="",
                 on_switch_to_prosecutor=None, on_request_judgement=None, on_interrogate=None): # Modified callbacks
        super().__init__()
        self.case_summary = case_summary
        self.profiles_text = profiles
        self.on_switch_to_prosecutor = on_switch_to_prosecutor
        self.on_request_judgement = on_request_judgement
        self.on_interrogate = on_interrogate
        self.evidences = GameController._evidences or []
        self.mic_on = False
        self.init_ui()

    def init_ui(self):
        self.setStyleSheet(f"background-color: {DARK_BG_COLOR}; color: {WHITE_TEXT};")

        title_label = QLabel("변호사 변론")
        title_label.setAlignment(Qt.AlignCenter)
        title_label.setStyleSheet("""
            background-color: black; color: white; font-size: 40px;
            font-weight: bold; padding: 10px; border-radius: 6px;
        """)
        title_label.setFixedWidth(260)

        title_wrapper = QHBoxLayout()
        title_wrapper.addStretch(1)
        title_wrapper.addWidget(title_label)
        title_wrapper.addStretch(1)

        def make_button(text, handler=None):
            btn = HoverButton(text)
            if handler:
                btn.clicked.connect(handler)
            return btn

        menu_layout = QVBoxLayout()
        menu_layout.setSpacing(15)
        menu_layout.addWidget(make_button("사건개요", self.show_case_dialog))
        menu_layout.addWidget(make_button("증거품 확인", self.show_evidences))
        menu_layout.addWidget(make_button("텍스트입력", self.show_text_input_placeholder))
        menu_layout.addWidget(make_button("➤ 심문하기", self.handle_interrogate))
        menu_layout.addStretch()

        summary_lines = ["등장인물"]
        if self.profiles_text:
            for part in self.profiles_text.split('--------------------------------'):
                part = part.strip()
                if not part: continue
                lines = part.split('\n')
                if not lines: continue
                title = lines[0]
                name, role = extract_name_and_role(title)
                if name and role:
                    summary_lines.append(f"• {name} : {role}")
        summary_text = "\n".join(summary_lines)

        profile_button = HoverButton(summary_text, min_height=100, max_height=130)
        profile_button.clicked.connect(self.show_full_profiles_dialog)

        self.btn_mic = MicButton("mike.png", "mike_on.png") # Ensure these images are in ui/image/
        self.btn_mic.clicked.connect(self.toggle_mic_icon)

        # --- Action Buttons ---
        self.btn_to_prosecutor = QPushButton("검사측 주장으로")
        self.btn_to_prosecutor.setFixedSize(250, 80)
        self.btn_to_prosecutor.setStyleSheet("""
            QPushButton { background-color: #2f5a68; color: white; border-radius: 12px; font-size: 22px; font-weight: bold; }
            QPushButton:hover { font-size: 24px; }
        """)
        self.btn_to_prosecutor.clicked.connect(self.handle_switch_to_prosecutor)

        self.btn_req_judgement = QPushButton("판결 요청")
        self.btn_req_judgement.setFixedSize(250, 80)
        self.btn_req_judgement.setStyleSheet("""
            QPushButton { background-color: #28a745; color: white; border-radius: 12px; font-size: 22px; font-weight: bold; }
            QPushButton:hover { font-size: 24px; }
        """) # Green color
        self.btn_req_judgement.clicked.connect(self.handle_request_judgement)

        action_buttons_layout = QHBoxLayout()
        action_buttons_layout.addStretch()
        action_buttons_layout.addWidget(self.btn_to_prosecutor)
        action_buttons_layout.addStretch()
        action_buttons_layout.addWidget(self.btn_req_judgement)
        action_buttons_layout.addStretch()

        # --- Right Panel (Controls are on the right for Lawyer) ---
        right_panel_grid = QGridLayout()
        right_panel_grid.setSpacing(20)
        right_panel_grid.addLayout(menu_layout, 0, 0)
        right_panel_grid.addWidget(profile_button, 0, 1)
        right_panel_grid.addWidget(self.btn_mic, 1, 0, 1, 2, alignment=Qt.AlignCenter)


        right_wrapper = QVBoxLayout() # This is the control panel for Lawyer
        right_wrapper.setContentsMargins(40, 30, 20, 30)
        right_wrapper.setSpacing(20)
        right_wrapper.addLayout(title_wrapper)
        right_wrapper.addStretch(1)
        right_wrapper.addLayout(right_panel_grid)
        right_wrapper.addSpacing(20)
        right_wrapper.addLayout(action_buttons_layout)
        right_wrapper.addStretch(2)

        # --- Left Panel (Image is on the left for Lawyer) ---
        image_label = ResizableImage(_get_image_path("profile/lawyer.png"))
        image_label.setMaximumWidth(420)
        image_label.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

        left_image_layout = QVBoxLayout()
        left_image_layout.addStretch()
        left_image_layout.addWidget(image_label, alignment=Qt.AlignLeft) # Align to left
        left_image_layout.addStretch()

        # --- Main Layout (Image on Left, Controls on Right) ---
        main_layout = QHBoxLayout()
        main_layout.setContentsMargins(60, 30, 40, 30) # Adjusted margins
        main_layout.setSpacing(30)
        main_layout.addLayout(left_image_layout, 2) # Image panel
        main_layout.addLayout(right_wrapper, 3)   # Control panel

        self.setLayout(main_layout)


    def toggle_mic_icon(self):
        self.mic_on = not self.mic_on
        self.btn_mic.set_icon_on(self.mic_on)

    def handle_switch_to_prosecutor(self):
        if self.on_switch_to_prosecutor:
            self.on_switch_to_prosecutor()

    def handle_request_judgement(self):
        if self.on_request_judgement:
            self.on_request_judgement()

    def handle_interrogate(self):
        if self.on_interrogate:
            self.on_interrogate()

    # Copy show_case_dialog, show_evidences, show_text_input_placeholder, show_full_profiles_dialog
    # from ProsecutorScreen, as they are identical utility methods.
    def show_case_dialog(self):
        if not self.case_summary:
            QMessageBox.information(self, "정보", "사건 개요 정보가 없습니다.", QMessageBox.Ok)
            return
        lines = self.case_summary.strip().split('\n')
        filtered_lines = [line for line in lines if not any(tag in line for tag in ["[피고", "[피해자", "[증인1", "[증인2"])]
        clean_text = "\n".join(filtered_lines)
        QMessageBox.information(self, "사건 개요", clean_text, QMessageBox.Ok)

    def show_evidences(self):
        if not self.evidences:
            QMessageBox.information(self, "증거품", "등록된 증거물이 없습니다.", QMessageBox.Ok)
            return
        prosecutors = []
        attorneys = []
        for e in self.evidences:
            desc_summary = e.description[0] if isinstance(e.description, (list, tuple)) and e.description else e.description
            summary = f"• {e.name}: {desc_summary}"
            if e.type == "prosecutor":
                prosecutors.append(summary)
            elif e.type == "attorney":
                attorneys.append(summary)
        parts = []
        if attorneys: # For Lawyer screen, maybe show attorney evidence first or only attorney
            parts.append("🔶 변호사 측 증거품\n" + "\n".join(attorneys))
        if prosecutors:
            parts.append("🔷 검사 측 증거품\n" + "\n".join(prosecutors))
        text = "\n\n".join(parts) if parts else "표시할 증거물이 없습니다."
        QMessageBox.information(self, "모든 증거품", text, QMessageBox.Ok)

    def show_text_input_placeholder(self):
        QMessageBox.information(self, "텍스트입력", "입력 기능은 추후 구현 예정입니다.", QMessageBox.Ok)

    def show_full_profiles_dialog(self):
        if not self.profiles_text:
            QMessageBox.information(self, "정보", "등장인물 정보가 없습니다.", QMessageBox.Ok)
            return
        dialog = QDialog(self)
        dialog.setWindowTitle("등장인물 정보")
        dialog.setStyleSheet("background-color: #0f2a45; color: white; font-size: 14px;")
        layout = QVBoxLayout()
        for part in self.profiles_text.split('--------------------------------'):
            part = part.strip()
            if not part: continue
            lines = part.split('\n')
            if not lines: continue
            title_line = lines[0]
            info_text = "\n".join(lines[1:])
            row_layout = QHBoxLayout()
            left_text_layout = QVBoxLayout()
            title_label = QLabel(f"<b>{title_line}</b>")
            title_label.setWordWrap(True)
            left_text_layout.addWidget(title_label)
            info_label = QLabel(info_text)
            info_label.setWordWrap(True)
            left_text_layout.addWidget(info_label)
            left_text_layout.addStretch()
            row_layout.addLayout(left_text_layout, 3)
            name, role = extract_name_and_role(title_line)
            if name:
                pixmap = get_profile_pixmap(name)
                if pixmap:
                    img_label = QLabel()
                    img_label.setPixmap(pixmap.scaledToWidth(150, Qt.SmoothTransformation))
                    img_label.setFixedSize(150, 200)
                    img_label.setAlignment(Qt.AlignCenter)
                    row_layout.addWidget(img_label, 1)
            layout.addLayout(row_layout)
            separator = QFrame()
            separator.setFrameShape(QFrame.HLine)
            separator.setFrameShadow(QFrame.Sunken)
            separator.setStyleSheet("background-color: #2f5a68;")
            layout.addWidget(separator)
        dialog.setLayout(layout)
        dialog.setMinimumWidth(600)
        dialog.setMinimumHeight(500)
        dialog.exec_()