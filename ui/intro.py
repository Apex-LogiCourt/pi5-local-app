import asyncio
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QTextEdit, QPushButton, QHBoxLayout
)
from PyQt5.QtCore import Qt


class IntroScreen(QWidget):
    def __init__(self, summary: str, profiles: str, on_intro_finished):
        super().__init__()
        self.case_summary = summary
        self.profiles_text = profiles
        self.on_intro_finished = on_intro_finished
        self.character_index = -1
        self.character_blocks = self.profiles_text.strip().split("--------------------------------")

        self.init_ui()
        self.show_next_block()

    def init_ui(self):
        self.layout = QVBoxLayout()
        self.text_display = QTextEdit()
        self.text_display.setReadOnly(True)
        self.text_display.setStyleSheet("background-color: #1e1e1e; color: white; font-size: 14px;")

        self.next_button = QPushButton("다음")
        self.next_button.setFixedHeight(50)
        self.next_button.setStyleSheet("background-color: #007bff; color: white; font-size: 16px; border-radius: 10px;")
        self.next_button.clicked.connect(self.show_next_block)

        self.layout.addWidget(self.text_display)
        self.layout.addWidget(self.next_button, alignment=Qt.AlignRight)
        self.setLayout(self.layout)

    def show_next_block(self):
        self.character_index += 1
        if self.character_index == 0:
            self.text_display.setPlainText(f"[사건 개요]\n{self.case_summary.strip()}")
        elif self.character_index <= len(self.character_blocks):
            block = self.character_blocks[self.character_index - 1].strip()
            self.text_display.setPlainText(block)
        else:
            # 등장인물 모두 보여줬으면 콜백으로 다음 화면 이동
            self.on_intro_finished()
