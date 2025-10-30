from PyQt5.QtWidgets import QPushButton, QLabel, QMessageBox, QDialog, QVBoxLayout, QHBoxLayout, QFrame
from PyQt5.QtCore import Qt, QSize
from PyQt5.QtGui import QIcon, QPixmap, QFont
from ui.resizable_image import _get_image_path, _get_profile_image_path # Relative to ui/
import re
import random

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
    # Fallback: try original name if simple_name (e.g. '민영' from '우민영') is not in map but '우민영' might be (less likely)
    # Or if name itself is short e.g. "이안"
    if not romanized:
        romanized = KOREAN_TO_ENGLISH_MAP.get(name) 
    
    if romanized:
        path = _get_profile_image_path(f"{romanized}.png")
        pix = QPixmap(path)
        if pix.isNull():
            print(f"Warning: Profile image not found or failed to load: {path} for name {name} (tried {simple_name}, {romanized})")
            return QPixmap(_get_profile_image_path(f"{random.choice(list(KOREAN_TO_ENGLISH_MAP.values()))}.png"))
        return pix
    print(f"Warning: Could not find romanized name for profile: {name} (tried {simple_name})")
    return QPixmap(_get_profile_image_path(f"{random.choice(list(KOREAN_TO_ENGLISH_MAP.values()))}.png"))


def extract_name_and_role(title_line):
    match = re.search(r"이름\s*:\s*(\S+(?:\s\S+)?)\s*\((피고|피해자|목격자|참고인)\)", title_line) # Allow space in name
    if match:
        return match.group(1).strip(), match.group(2).strip()
    return None, None


class HoverButton(QPushButton):
    def __init__(self, text, min_height=80, max_height=110):
        super().__init__(text)
        self.default_font_size = 26
        self.hover_font_size = 34
        self.default_min_height = min_height
        self.hover_min_height = max_height
        
        self.font_regular = QFont()
        self.font_regular.setPointSize(self.default_font_size)
        self.font_regular.setBold(True)

        self.font_hover = QFont()
        self.font_hover.setPointSize(self.hover_font_size)
        self.font_hover.setBold(True)

        self.setFont(self.font_regular)
        self.setStyleSheet(self.get_stylesheet(self.default_font_size)) # Initial style
        self.setMinimumHeight(self.default_min_height)
        # self.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Preferred) # Default is fine

    def enterEvent(self, event):
        self.setFont(self.font_hover)
        # self.setStyleSheet(self.get_stylesheet(self.hover_font_size)) # Font change is enough
        self.setMinimumHeight(self.hover_min_height)
        super().enterEvent(event)

    def leaveEvent(self, event):
        self.setFont(self.font_regular)
        # self.setStyleSheet(self.get_stylesheet(self.default_font_size))
        self.setMinimumHeight(self.default_min_height)
        super().leaveEvent(event)

    def get_stylesheet(self, font_size): # font_size param might be redundant if using setFont
        return """
        QPushButton {{
            background-color: transparent;
            color: white;
            /* font-size: {font_size}px; */ /* Controlled by setFont now */
            /* font-weight: bold; */  /* Controlled by setFont now */
            border: none;
            padding: 16px;
            text-align: left;
        }}
        """.format(font_size=font_size)


class MicButton(QPushButton):
    def __init__(self, icon_filename, on_icon_filename):
        super().__init__()
        self.icon_filename = icon_filename
        self.on_icon_filename = on_icon_filename
        self.default_icon_size = QSize(80, 80)
        self.hover_icon_size = QSize(95, 95)
        self.fixed_box_size = QSize(120, 120)

        self.setFixedSize(self.fixed_box_size)
        self.setIcon(QIcon(_get_image_path(self.icon_filename)))
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
        icon_file = self.on_icon_filename if is_on else self.icon_filename
        self.setIcon(QIcon(_get_image_path(icon_file)))


def show_case_dialog_common(parent, case_summary_text):
    if not case_summary_text:
        QMessageBox.information(parent, "정보", "사건 개요 정보가 없습니다.", QMessageBox.Ok)
        return
    lines = case_summary_text.strip().split('\n')
    filtered_lines = [line for line in lines if not any(tag in line for tag in ["[피고", "[피해자", "[증인1", "[증인2"])]
    clean_text = "\n".join(filtered_lines)
    QMessageBox.information(parent, "사건 개요", clean_text, QMessageBox.Ok)


def show_evidences_common(parent, evidences_list, attorney_first=False):
    if not evidences_list:
        QMessageBox.information(parent, "증거품", "등록된 증거물이 없습니다.", QMessageBox.Ok)
        return
    
    prosecutors = []
    attorneys = []

    for e_dict in evidences_list: # Expecting list of dicts
        name = e_dict.get('name', '이름 없음')
        desc_list = e_dict.get('description', [])
        e_type = e_dict.get('type', 'unknown')

        desc_summary = desc_list[0] if isinstance(desc_list, (list, tuple)) and desc_list else str(desc_list)
        summary = f"• {name}: {desc_summary}"
        if e_type == "prosecutor":
            prosecutors.append(summary)
        elif e_type == "attorney":
            attorneys.append(summary)

    parts = []
    evidence_order = []
    if attorney_first:
        if attorneys: evidence_order.append(("🔶 변호사 측 증거품", attorneys))
        if prosecutors: evidence_order.append(("🔷 검사 측 증거품", prosecutors))
    else:
        if prosecutors: evidence_order.append(("🔷 검사 측 증거품", prosecutors))
        if attorneys: evidence_order.append(("🔶 변호사 측 증거품", attorneys))
    
    for title, items in evidence_order:
        parts.append(title + "\n" + "\n".join(items))

    text = "\n\n".join(parts) if parts else "표시할 증거물이 없습니다."
    QMessageBox.information(parent, "모든 증거품", text, QMessageBox.Ok)


def show_full_profiles_dialog_common(parent, profiles_data_list): # Expects list of profile dicts
    if not profiles_data_list:
        QMessageBox.information(parent, "정보", "등장인물 정보가 없습니다.", QMessageBox.Ok)
        return
        
    dialog = QDialog(parent)
    dialog.setWindowTitle("등장인물 정보")
    dialog.setStyleSheet("background-color: #0f2a45; color: white; font-size: 14px;")
    layout = QVBoxLayout(dialog) # Set layout on dialog

    type_map = {"defendant": "피고", "victim": "피해자", "witness": "목격자", "reference": "참고인"}
    gender_map = {"male": "남성", "female": "여성"} # Assuming gender keys from data model

    for p_info in profiles_data_list:
        name = p_info.get('name', '이름 없음')
        role_key = p_info.get('type', 'unknown')
        role = type_map.get(role_key, role_key.capitalize())
        
        gender_key = p_info.get('gender', 'unknown')
        gender = gender_map.get(gender_key, gender_key.capitalize())
        age = p_info.get('age', 'N/A')
        context = p_info.get('context', '세부 정보 없음')

        title_line = f"이름: {name} ({role})" # For display and extraction
        info_text = f"성별: {gender}, 나이: {age}세\n사연: {context}"
        
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
        
        # Use the parsed name for pixmap
        parsed_name, _ = extract_name_and_role(title_line)
        if parsed_name: # Should usually be true
            pixmap = get_profile_pixmap(parsed_name)
            if pixmap:
                img_label = QLabel()
                img_label.setPixmap(pixmap.scaledToWidth(150, Qt.SmoothTransformation))
                img_label.setFixedSize(150, 200)
                img_label.setAlignment(Qt.AlignCenter)
                row_layout.addWidget(img_label, 1)
            else: # Add a placeholder if pixmap is None
                placeholder = QLabel(f"{parsed_name}\n(이미지 없음)")
                placeholder.setFixedSize(150,200)
                placeholder.setAlignment(Qt.AlignCenter)
                row_layout.addWidget(placeholder,1)

        layout.addLayout(row_layout)
        separator = QFrame()
        separator.setFrameShape(QFrame.HLine)
        separator.setFrameShadow(QFrame.Sunken)
        separator.setStyleSheet("background-color: #2f5a68; margin-top: 5px; margin-bottom: 5px;")
        layout.addWidget(separator)

    # dialog.setLayout(layout) # Already set with QVBoxLayout(dialog)
    dialog.setMinimumWidth(700) # Wider dialog
    dialog.setMinimumHeight(500)
    dialog.exec_()