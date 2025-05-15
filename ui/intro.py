from PyQt5.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QTextEdit, QPushButton
from PyQt5.QtGui import QPixmap
from PyQt5.QtCore import Qt

from ui.style_constants import (
    DARK_BG_COLOR, SECONDARY_BLUE, COMMON_PANEL_LABEL_STYLE,
    DEFAULT_BUTTON_STYLE, TEXT_EDIT_STYLE_TRANSPARENT_BG, WHITE_TEXT,
    HTML_H3_STYLE, HTML_P_STYLE, HTML_LI_STYLE, BLACK_COLOR
)
from ui.resizable_image import _get_image_path
from core.data_models import Evidence
import re

KOREAN_TO_ENGLISH_MAP = {
    "은영":"Eunyoung",
    "봄달":"Bomdal",
    "지훈":"Jihoon",
    "소현": "Sohyun",
    "영화": "Younghwa",
    "성일": "Sungil",
    "기효": "Kihyo",
    "승표": "Seungpyo",
    "주안": "Jooahn",
    "선희": "Sunhee",
    "민영": "Minyoung",
    "상도": "Sangdo",
    "기서": "Kiseo",
    "원탁": "Wontak",
    "이안": "Ian",
}

def extract_name_from_title(title: str) -> str:
    match = re.search(r":\s*(.+?)\s*\(", title)
    if match:
        return match.group(1)
    return ""

def get_profile_image_label(name: str) -> QLabel:
    label = QLabel()
    try:
        # 전체 이름으로 먼저 매핑 시도
        romanized_name = KOREAN_TO_ENGLISH_MAP.get(name)

        # 없다면 이름만으로 다시 시도 (두 번째 글자부터)
        if not romanized_name and len(name) >= 2:
            first_name = name[1:]
            romanized_name = KOREAN_TO_ENGLISH_MAP.get(first_name)

        if romanized_name:
            path = _get_image_path(f"profile/{romanized_name}.png")
            pixmap = QPixmap(path)
            if not pixmap.isNull():
                label.setPixmap(pixmap.scaled(200, 260, Qt.KeepAspectRatio, Qt.SmoothTransformation))
            else:
                label.setText("이미지 없음")
        else:
            label.setText("이미지 없음")
    except:
        label.setText("이미지 오류")

    label.setAlignment(Qt.AlignCenter)
    return label

class IntroScreen(QWidget):
    def __init__(self, summary: str, profiles: str, evidences: list[Evidence], on_intro_finished_callback):
        super().__init__()
        self.case_summary = summary
        self.profiles_text = profiles
        self.evidences = evidences
        self.on_intro_finished = on_intro_finished_callback
        self.current_block_index = -1
        self.display_blocks = []
        self.image_blocks = []

        # 사건 개요 + 증거품 목록
        summary_title = f"<h3 style='{HTML_H3_STYLE}'>사건개요</h3>"

        # 등장인물 이름/성별 라인 제거: '[피고]', '[피해자]', '[증인1]', '[증인2]' 항목 제거
        summary_lines = []
        for line in self.case_summary.strip().split('\n'):
            if any(tag in line for tag in ["[피고", "[피해자", "[증인1", "[증인2"]):
                continue
            summary_lines.append(line.strip())

        summary_content = "".join([
            f"<p style='{HTML_P_STYLE}'>{line}</p>" for line in summary_lines if line
        ])

        prosecutor_items = [e.name for e in self.evidences if e.type == "prosecutor"]
        attorney_items = [e.name for e in self.evidences if e.type == "attorney"]
        prosecutor_html = "".join([f"<li style='{HTML_LI_STYLE}'>{item}</li>" for item in prosecutor_items])
        attorney_html = "".join([f"<li style='{HTML_LI_STYLE}'>{item}</li>" for item in attorney_items])
        evidence_block = f"""
            <h3 style='{HTML_H3_STYLE}'>검사측 증거물</h3>
            <ul>{prosecutor_html}</ul>
            <h3 style='{HTML_H3_STYLE}'>변호사측 증거물</h3>
            <ul>{attorney_html}</ul>
        """
        self.display_blocks.append(summary_title + summary_content + evidence_block)

        # judge.png 이미지 추가
        judge_label = QLabel()
        judge_pixmap = QPixmap(_get_image_path("profile/judge.png"))
        if not judge_pixmap.isNull():
            judge_label.setPixmap(judge_pixmap.scaled(200, 260, Qt.KeepAspectRatio, Qt.SmoothTransformation))
        else:
            judge_label.setText("이미지 없음")
        judge_label.setAlignment(Qt.AlignCenter)
        self.image_blocks.append(judge_label)


        # 등장인물 블록
        profile_parts = self.profiles_text.strip().split("--------------------------------")
        for part in profile_parts:
            lines = part.strip().split('\n')
            if not lines:
                continue
            title = lines[0].strip()
            title_html = f"<h3 style='{HTML_H3_STYLE}'>{title}</h3>"
            content_html = ""
            bullet_items = [l.strip().lstrip('- ').strip() for l in lines[1:] if l.strip().startswith('-')]
            if bullet_items:
                content_html += "<ul>" + "".join([f"<li style='{HTML_LI_STYLE}'>{item}</li>" for item in bullet_items]) + "</ul>"
            paragraphs = [l.strip() for l in lines[1:] if not l.strip().startswith('-')]
            for p in paragraphs:
                content_html += f"<p style='{HTML_P_STYLE}'>{p}</p>"
            self.display_blocks.append(title_html + content_html)

            name = extract_name_from_title(title)
            self.image_blocks.append(get_profile_image_label(name))

        self.init_ui()
        self.show_next_block()

    def init_ui(self):
        self.setStyleSheet(f"""
            QWidget {{ background-color: {DARK_BG_COLOR}; }}
            QTextEdit {{ {TEXT_EDIT_STYLE_TRANSPARENT_BG} }}
            QPushButton {{ {DEFAULT_BUTTON_STYLE} }}
            QLabel {{ background-color: transparent; color: {WHITE_TEXT}; }}
        """)

        self.main_layout = QHBoxLayout()
        self.main_layout.setContentsMargins(30, 30, 30, 30)
        self.main_layout.setSpacing(40)

        self.left_layout = QVBoxLayout()
        label_section_container = QHBoxLayout()
        label_section_container.addStretch()
        self.label_section = QLabel("사건설명")
        self.label_section.setFixedWidth(200)
        self.label_section.setAlignment(Qt.AlignCenter)
        self.label_section.setStyleSheet(f"background-color: {SECONDARY_BLUE}; {COMMON_PANEL_LABEL_STYLE}")
        label_section_container.addWidget(self.label_section)
        label_section_container.addStretch()
        self.left_layout.addLayout(label_section_container)

        self.text_display = QTextEdit()
        self.text_display.setReadOnly(True)
        self.left_layout.addWidget(self.text_display, 1)

        self.next_button = QPushButton("다음")
        self.next_button.setFixedHeight(50)
        self.next_button.clicked.connect(self.show_next_block)
        self.left_layout.addWidget(self.next_button, alignment=Qt.AlignRight)

        self.right_layout = QVBoxLayout()
        self.image_label = QLabel()
        self.image_label.setAlignment(Qt.AlignCenter)
        self.right_layout.addWidget(self.image_label, alignment=Qt.AlignCenter)
        self.right_layout.addStretch()

        self.main_layout.addLayout(self.left_layout, 3)
        self.main_layout.addLayout(self.right_layout, 2)
        self.setLayout(self.main_layout)

    def show_next_block(self):
        self.current_block_index += 1
        if self.current_block_index < len(self.display_blocks):
            self.text_display.setHtml(self.display_blocks[self.current_block_index])
            image_widget = self.image_blocks[self.current_block_index]
            if image_widget:
                self.image_label.setPixmap(image_widget.pixmap())
            else:
                self.image_label.clear()
            self.next_button.setText("재판 시작" if self.current_block_index == len(self.display_blocks) - 1 else "다음")
        else:
            if self.on_intro_finished:
                self.on_intro_finished()
