from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QPushButton, QHBoxLayout,
    QSizePolicy, QMessageBox, QGridLayout, QDialog,QFrame
)
from PyQt5.QtCore import Qt, QSize
from PyQt5.QtGui import QIcon, QPixmap
from ui.resizable_image import ResizableImage, _get_image_path # Ensure this path is correct
from ui.style_constants import DARK_BG_COLOR, WHITE_TEXT # Ensure this path is correct
from core.game_controller import GameController
import re

# --- HoverButton (메뉴 및 등장인물용) ---
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
        # self.resize(self.sizeHint()) # Can cause minor jitter, often not needed
        super().enterEvent(event)

    def leaveEvent(self, event):
        self.setStyleSheet(self.get_stylesheet(self.default_font_size))
        self.setMinimumHeight(self.default_min_height)
        # self.resize(self.sizeHint()) # Can cause minor jitter
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
class MicButton(QPushButton):
    def __init__(self, icon_path, on_icon_path):
        super().__init__()
        self.icon_path = icon_path
        self.on_icon_path = on_icon_path
        self.default_icon_size = QSize(80, 80)
        self.hover_icon_size = QSize(95, 95) # Slightly larger on hover
        self.fixed_box_size = QSize(120, 120) # The button's own size

        self.setFixedSize(self.fixed_box_size)
        self.setIcon(QIcon(_get_image_path(self.icon_path)))
        self.setIconSize(self.default_icon_size) # Initial icon size

        self.setStyleSheet("""
            QPushButton {
                background-color: #2f5a68; /* Button background */
                border-radius: 12px; /* Rounded corners */
            }
        """)

    def enterEvent(self, event):
        self.setIconSize(self.hover_icon_size) # Larger icon on hover
        super().enterEvent(event)

    def leaveEvent(self, event):
        self.setIconSize(self.default_icon_size) # Revert icon size
        super().leaveEvent(event)

    def set_icon_on(self, is_on):
        icon_file = self.on_icon_path if is_on else self.icon_path
        self.setIcon(QIcon(_get_image_path(icon_file)))


# --- 이름 매핑 ---
KOREAN_TO_ENGLISH_MAP = {
    "은영": "Eunyoung", "봄달": "Bomdal", "지훈": "Jihoon", "소현": "Sohyun",
    "영화": "Younghwa", "성일": "Sungil", "기효": "Kihyo", "승표": "Seungpyo",
    "주안": "Jooahn", "선희": "Sunhee", "민영": "Minyoung", "상도": "Sangdo",
    "기서": "Kiseo", "원탁": "Wontak", "이안": "Ian"
}

def get_profile_pixmap(name: str):
    # Extract the actual name part if full name like '김은영' is passed
    simple_name = name.split(" ")[-1] # Get last part e.g. '은영' from '김은영'
    if len(simple_name) > 2 and simple_name[0] in ['김', '이', '박', '최', '정', '강', '조', '윤', '장', '임', '오', '한', '신', '서', '권', '황', '안', '송', '유', '홍']: # Common Korean surnames
         simple_name = simple_name[1:]


    romanized = KOREAN_TO_ENGLISH_MAP.get(simple_name)
    if not romanized and len(name) >= 2: # Fallback for original name if mapping fails
        romanized = KOREAN_TO_ENGLISH_MAP.get(name[1:]) if len(name) > 1 else KOREAN_TO_ENGLISH_MAP.get(name)

    if romanized:
        path = _get_image_path(f"profile/{romanized}.png")
        if QPixmap(path).isNull(): # Check if image actually loaded
             print(f"Warning: Profile image not found or failed to load: {path}")
             return None
        return QPixmap(path)
    print(f"Warning: Could not find romanized name for profile: {name} (tried {simple_name})")
    return None


def extract_name_and_role(title_line):
    # Regex to find "이름: 실제이름 (역할)"
    match = re.search(r"이름\s*:\s*(\S+)\s*\((피고|피해자|목격자|참고인)\)", title_line)
    if match:
        return match.group(1).strip(), match.group(2).strip() # Name, Role
    return None, None

# --- ProsecutorScreen ---
class ProsecutorScreen(QWidget):
    def __init__(self, case_summary="", profiles="",
                 on_switch_to_lawyer=None, on_request_judgement=None, on_interrogate=None): # Modified callbacks
        super().__init__()
        self.case_summary = case_summary
        self.profiles_text = profiles
        self.on_switch_to_lawyer = on_switch_to_lawyer
        self.on_request_judgement = on_request_judgement
        self.on_interrogate = on_interrogate
        self.evidences = GameController._evidences or []
        self.mic_on = False
        self.init_ui()

    def init_ui(self):
        self.setStyleSheet(f"background-color: {DARK_BG_COLOR}; color: {WHITE_TEXT};")

        title_label = QLabel("검사 주장")
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
                if not part:
                    continue
                lines = part.split('\n')
                if not lines: continue
                title = lines[0]
                name, role = extract_name_and_role(title)
                if name and role:
                    summary_lines.append(f"• {name} : {role}")
        summary_text = "\n".join(summary_lines)

        profile_button = HoverButton(summary_text, min_height=100, max_height=130)
        profile_button.clicked.connect(self.show_full_profiles_dialog)

        self.btn_mic = MicButton("mike.png", "mike_on.png")
        self.btn_mic.clicked.connect(self.toggle_mic_icon)

        # --- Action Buttons ---
        self.btn_to_lawyer = QPushButton("변호사 변론으로")
        self.btn_to_lawyer.setFixedSize(250, 80)
        self.btn_to_lawyer.setStyleSheet("""
            QPushButton { background-color: #2f5a68; color: white; border-radius: 12px; font-size: 22px; font-weight: bold; }
            QPushButton:hover { font-size: 24px; }
        """)
        self.btn_to_lawyer.clicked.connect(self.handle_switch_to_lawyer)

        self.btn_req_judgement = QPushButton("판결 요청")
        self.btn_req_judgement.setFixedSize(250, 80)
        self.btn_req_judgement.setStyleSheet("""
            QPushButton { background-color: #28a745; color: white; border-radius: 12px; font-size: 22px; font-weight: bold; }
            QPushButton:hover { font-size: 24px; }
        """) # Green color for judgement
        self.btn_req_judgement.clicked.connect(self.handle_request_judgement)

        # Layout for action buttons
        action_buttons_layout = QHBoxLayout()
        action_buttons_layout.addStretch()
        action_buttons_layout.addWidget(self.btn_to_lawyer)
        action_buttons_layout.addStretch()
        action_buttons_layout.addWidget(self.btn_req_judgement)
        action_buttons_layout.addStretch()


        # --- Left Panel (Controls) ---
        left_panel_grid = QGridLayout() # Main grid for controls
        left_panel_grid.setSpacing(20)
        left_panel_grid.addLayout(menu_layout, 0, 0)       # Row 0, Col 0
        left_panel_grid.addWidget(profile_button, 0, 1)    # Row 0, Col 1
        left_panel_grid.addWidget(self.btn_mic, 1, 0, 1, 2, alignment=Qt.AlignCenter) # Row 1, spans 2 cols


        left_wrapper = QVBoxLayout()
        left_wrapper.setContentsMargins(40, 30, 20, 30)
        left_wrapper.setSpacing(20)
        left_wrapper.addLayout(title_wrapper)
        left_wrapper.addStretch(1)
        left_wrapper.addLayout(left_panel_grid) # Grid with menu, profile, mic
        left_wrapper.addSpacing(20)
        left_wrapper.addLayout(action_buttons_layout) # "To Lawyer" and "Request Judgement" buttons
        left_wrapper.addStretch(2)


        # --- Right Panel (Image) ---
        image_label = ResizableImage(_get_image_path("profile/Prosecutor.png"))
        image_label.setMaximumWidth(420) # Or your preferred max width
        image_label.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

        right_image_layout = QVBoxLayout()
        right_image_layout.addStretch()
        right_image_layout.addWidget(image_label, alignment=Qt.AlignRight) # Align to right
        right_image_layout.addStretch()


        # --- Main Layout ---
        main_layout = QHBoxLayout()
        main_layout.setContentsMargins(40, 30, 60, 30) # Adjusted right margin
        main_layout.setSpacing(30)
        main_layout.addLayout(left_wrapper, 3)  # Control panel takes more space
        main_layout.addLayout(right_image_layout, 2) # Image panel

        self.setLayout(main_layout)

    def toggle_mic_icon(self):
        self.mic_on = not self.mic_on
        self.btn_mic.set_icon_on(self.mic_on)

    def handle_switch_to_lawyer(self):
        if self.on_switch_to_lawyer:
            self.on_switch_to_lawyer()

    def handle_request_judgement(self):
        if self.on_request_judgement:
            self.on_request_judgement()

    def handle_interrogate(self):
        if self.on_interrogate:
            self.on_interrogate()

    def show_case_dialog(self):
        if not self.case_summary:
            QMessageBox.information(self, "정보", "사건 개요 정보가 없습니다.", QMessageBox.Ok)
            return
        lines = self.case_summary.strip().split('\n')
        # Filter out lines that might be character intros within the summary if any
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
            # Assuming e.description is a list/tuple and we take the first item, or it's a string
            desc_summary = e.description[0] if isinstance(e.description, (list, tuple)) and e.description else e.description
            summary = f"• {e.name}: {desc_summary}"
            if e.type == "prosecutor":
                prosecutors.append(summary)
            elif e.type == "attorney":
                attorneys.append(summary)

        parts = []
        if prosecutors:
            parts.append("🔷 검사 측 증거품\n" + "\n".join(prosecutors))
        if attorneys: # Also show attorney evidence if available
            parts.append("🔶 변호사 측 증거품\n" + "\n".join(attorneys))

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
            if not part:
                continue
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

            row_layout.addLayout(left_text_layout, 3) # Text takes more space

            name, role = extract_name_and_role(title_line)
            if name:
                pixmap = get_profile_pixmap(name)
                if pixmap:
                    img_label = QLabel()
                    img_label.setPixmap(pixmap.scaledToWidth(150, Qt.SmoothTransformation))
                    img_label.setFixedSize(150, 200) # Fixed size for image consistency
                    img_label.setAlignment(Qt.AlignCenter)
                    row_layout.addWidget(img_label, 1) # Image takes less space
            
            layout.addLayout(row_layout)
            separator = QFrame()
            separator.setFrameShape(QFrame.HLine)
            separator.setFrameShadow(QFrame.Sunken)
            separator.setStyleSheet("background-color: #2f5a68;")
            layout.addWidget(separator)


        dialog.setLayout(layout)
        dialog.setMinimumWidth(600) # Wider dialog
        dialog.setMinimumHeight(500)
        dialog.exec_()