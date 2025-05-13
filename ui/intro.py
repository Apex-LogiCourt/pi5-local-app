from PyQt5.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QTextEdit, QPushButton
from PyQt5.QtGui import QPixmap
from PyQt5.QtCore import Qt

from ui.style_constants import (
    DARK_BG_COLOR, SECONDARY_BLUE, COMMON_PANEL_LABEL_STYLE,
    DEFAULT_BUTTON_STYLE, TEXT_EDIT_STYLE_TRANSPARENT_BG, WHITE_TEXT,
    HTML_H3_STYLE, HTML_P_STYLE, HTML_LI_STYLE, BLACK_COLOR
)
from ui.resizable_image import _get_image_path


class IntroScreen(QWidget):
    def __init__(self, summary: str, profiles: str, on_intro_finished_callback):
        super().__init__()
        self.case_summary = summary
        self.profiles_text = profiles
        self.on_intro_finished = on_intro_finished_callback
        self.current_block_index = -1
        self.display_blocks = []

        summary_title = f"<h3 style='{HTML_H3_STYLE}'>사건개요</h3>"
        summary_content = "".join([
            f"<p style='{HTML_P_STYLE}'>{line.strip()}</p>"
            for line in self.case_summary.strip().split('\n') if line.strip()
        ])
        self.display_blocks.append(summary_title + summary_content)

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

        self.init_ui()
        self.show_next_block()

    def init_ui(self):
        self.setStyleSheet(f"""
            QWidget {{ background-color: {DARK_BG_COLOR}; }}
            QTextEdit {{ {TEXT_EDIT_STYLE_TRANSPARENT_BG} }}
            QPushButton {{ {DEFAULT_BUTTON_STYLE} }}
            QLabel {{ background-color: transparent; color: {WHITE_TEXT}; }}
        """)

        main_layout = QHBoxLayout()
        main_layout.setContentsMargins(30, 30, 30, 30)
        main_layout.setSpacing(40)

        left_layout = QVBoxLayout()
        label_section_container = QHBoxLayout()
        label_section_container.addStretch()
        self.label_section = QLabel("사건설명")
        self.label_section.setFixedWidth(200)
        self.label_section.setAlignment(Qt.AlignCenter)
        self.label_section.setStyleSheet(f"background-color: {SECONDARY_BLUE}; {COMMON_PANEL_LABEL_STYLE}")
        label_section_container.addWidget(self.label_section)
        label_section_container.addStretch()
        left_layout.addLayout(label_section_container)

        self.text_display = QTextEdit()
        self.text_display.setReadOnly(True)
        left_layout.addWidget(self.text_display, 1)

        self.next_button = QPushButton("다음")
        self.next_button.setFixedHeight(50)
        self.next_button.clicked.connect(self.show_next_block)
        left_layout.addWidget(self.next_button, alignment=Qt.AlignRight)

        right_layout = QVBoxLayout()
        judge_label_container = QHBoxLayout()
        judge_label_container.addStretch()
        self.judge_label = QLabel("AI판사")
        self.judge_label.setFixedWidth(200)
        self.judge_label.setAlignment(Qt.AlignCenter)
        self.judge_label.setStyleSheet(f"background-color: {BLACK_COLOR}; {COMMON_PANEL_LABEL_STYLE}")
        judge_label_container.addWidget(self.judge_label)
        judge_label_container.addStretch()
        right_layout.addLayout(judge_label_container)
        right_layout.addSpacing(10)

        self.judge_image_label = QLabel()
        pixmap = QPixmap(_get_image_path("judge.png"))
        if not pixmap.isNull():
            self.judge_image_label.setPixmap(pixmap.scaled(360, 480, Qt.KeepAspectRatio, Qt.SmoothTransformation))
        else:
            self.judge_image_label.setText("이미지 로드 실패")
            self.judge_image_label.setStyleSheet(f"color: {WHITE_TEXT};")
        self.judge_image_label.setAlignment(Qt.AlignCenter)
        right_layout.addWidget(self.judge_image_label, alignment=Qt.AlignCenter)
        right_layout.addStretch()

        main_layout.addLayout(left_layout, 3)
        main_layout.addLayout(right_layout, 2)
        self.setLayout(main_layout)

    def show_next_block(self):
        self.current_block_index += 1
        if self.current_block_index < len(self.display_blocks):
            self.text_display.setHtml(self.display_blocks[self.current_block_index])
            self.next_button.setText("재판 시작" if self.current_block_index == len(self.display_blocks) - 1 else "다음")
        else:
            if self.on_intro_finished:
                self.on_intro_finished()
