from PyQt5.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QTextEdit, QPushButton, QSizePolicy, QFrame
from PyQt5.QtGui import QPixmap
from PyQt5.QtCore import Qt

from ui.style_constants import (
    DARK_BG_COLOR, SECONDARY_BLUE, COMMON_PANEL_LABEL_STYLE,
    DEFAULT_BUTTON_STYLE, TEXT_EDIT_STYLE_TRANSPARENT_BG, WHITE_TEXT,
    HTML_H3_STYLE, HTML_P_STYLE, HTML_LI_STYLE
)
from ui.resizable_image import _get_image_path
from core.data_models import Evidence
import re

# 한글 이름을 영문 파일명으로 매핑
KOREAN_TO_ENGLISH_MAP = {
    "은영": "Eunyoung",
    "봄달": "Bomdal",
    "지훈": "Jihoon",
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

# 제목 문자열에서 이름 추출
def extract_name_from_title(title: str) -> str:
    match = re.search(r"이름\s*:\s*(\S+)", title)
    if match:
        full_name = match.group(1)
        return full_name[-2:]  # 예: '김소현' → '소현'
    return ""

# 이름에 해당하는 프로필 이미지 QLabel 생성
def get_profile_image_label(name: str) -> QLabel:
    label = QLabel()
    try:
        romanized = KOREAN_TO_ENGLISH_MAP.get(name)
        if not romanized and len(name) >= 2:
            romanized = KOREAN_TO_ENGLISH_MAP.get(name[1:])
        if romanized:
            img_path = _get_image_path(f"profile/{romanized}.png")
            pix = QPixmap(img_path)
            label.setPixmap(pix)
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

        # 1) 사건개요 + 증거목록 HTML
        title_html = f"<h3 style='{HTML_H3_STYLE}'>사건개요</h3>"
        lines = [ln.strip() for ln in self.case_summary.split('\n')
                 if ln.strip() and not any(tag in ln for tag in ["[피고", "[피해자", "[증인1", "[증인2"])]
        content_html = ''.join(f"<p style='{HTML_P_STYLE}'>{ln}</p>" for ln in lines)
        proc = [e.name for e in self.evidences if e.type == 'prosecutor']
        att = [e.name for e in self.evidences if e.type == 'attorney']
        evidence_html = (
            f"<h3 style='{HTML_H3_STYLE}'>검사측 증거물</h3><ul>" + ''.join(f"<li style='{HTML_LI_STYLE}'>{i}</li>" for i in proc) + "</ul>"
            f"<h3 style='{HTML_H3_STYLE}'>변호사측 증거물</h3><ul>" + ''.join(f"<li style='{HTML_LI_STYLE}'>{i}</li>" for i in att) + "</ul>"
        )
        self.display_blocks.append(title_html + content_html + evidence_html)

        # 2) 판사 이미지
        judge_lbl = QLabel()
        judge_pix = QPixmap(_get_image_path("profile/judge.png"))
        judge_lbl.setPixmap(judge_pix)
        judge_lbl.setAlignment(Qt.AlignCenter)
        self.image_blocks.append(judge_lbl)

        # 3) 등장인물 정보 + 프로필 이미지
        for part in self.profiles_text.split('--------------------------------'):
            part = part.strip()
            if not part: continue
            lines = part.split('\n')
            head = lines[0]
            head_html = f"<h3 style='{HTML_H3_STYLE}'>{head}</h3>"
            rest = lines[1:]
            body_html = ''
            bullets = [r.lstrip('- ').strip() for r in rest if r.strip().startswith('-')]
            if bullets:
                body_html += '<ul>' + ''.join(f"<li style='{HTML_LI_STYLE}'>{b}</li>" for b in bullets) + '</ul>'
            paras = [r for r in rest if not r.strip().startswith('-')]
            body_html += ''.join(f"<p style='{HTML_P_STYLE}'>{p}</p>" for p in paras)
            self.display_blocks.append(head_html + body_html)
            name = extract_name_from_title(head)
            self.image_blocks.append(get_profile_image_label(name))

        self.init_ui()
        self.show_next_block()

    def init_ui(self):
        # 전체 배경은 어두운 색상 유지
        self.setStyleSheet(f"background-color: {DARK_BG_COLOR};")

        # QTextEdit, QPushButton 스타일 추가
        style = (
            f"QTextEdit {{ {TEXT_EDIT_STYLE_TRANSPARENT_BG} }}"
            f"QPushButton {{ {DEFAULT_BUTTON_STYLE} }}"
            f"QLabel {{ color: {WHITE_TEXT}; background-color: transparent; }}"
        )
        self.setStyleSheet(self.styleSheet() + style)

        # 메인 레이아웃
        self.main_layout = QHBoxLayout(self)
        self.main_layout.setContentsMargins(30, 30, 30, 30)
        self.main_layout.setSpacing(40)

        # 좌측: 섹션명 + 본문 + 버튼
        left = QVBoxLayout()
        hdr = QHBoxLayout()
        hdr.addStretch()
        self.label_section = QLabel("사건설명")
        self.label_section.setFixedWidth(200)
        self.label_section.setAlignment(Qt.AlignCenter)
        self.label_section.setStyleSheet(f"background-color: {SECONDARY_BLUE}; {COMMON_PANEL_LABEL_STYLE}")
        hdr.addWidget(self.label_section)
        hdr.addStretch()
        left.addLayout(hdr)
        self.text_display = QTextEdit()
        self.text_display.setReadOnly(True)
        left.addWidget(self.text_display, 1)
        self.next_button = QPushButton("다음")
        self.next_button.setFixedHeight(50)
        self.next_button.clicked.connect(self.show_next_block)
        left.addWidget(self.next_button, alignment=Qt.AlignRight)

        # 우측: 배경 프레임 + 이미지
        right_frame = QFrame()
        right_frame.setStyleSheet(
            f"background-image: url({_get_image_path('background1.png')});"
            "background-repeat: no-repeat;"
            "background-position: center;"
            "background-size: cover;"
        )
        right_layout = QVBoxLayout(right_frame)
        right_layout.setContentsMargins(0, 0, 0, 0)
        right_layout.setSpacing(0)
        self.image_label = QLabel()
        self.image_label.setAlignment(Qt.AlignCenter)
        self.image_label.setScaledContents(True)
        self.image_label.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        right_layout.addWidget(self.image_label)
        right_layout.addStretch()

        # 레이아웃 배치 (좌 3: 우 2)
        self.main_layout.addLayout(left, 3)
        self.main_layout.addWidget(right_frame, 2)

    def show_next_block(self):
        self.current_block_index += 1
        if self.current_block_index < len(self.display_blocks):
            self.text_display.setHtml(self.display_blocks[self.current_block_index])
            img_widget = self.image_blocks[self.current_block_index]
            if img_widget and img_widget.pixmap():
                self.image_label.setPixmap(img_widget.pixmap())
            else:
                self.image_label.clear()
            is_last = self.current_block_index == len(self.display_blocks) - 1
            self.next_button.setText("재판 시작" if is_last else "다음")
        else:
            if self.on_intro_finished:
                self.on_intro_finished()
