from PyQt5.QtWidgets import QWidget, QHBoxLayout, QTextEdit, QFrame, QVBoxLayout, QLabel, QPushButton, QSizePolicy,QApplication
from PyQt5.QtCore import Qt
import asyncio

from ui.resizable_image import ResizableImage, _get_image_path
from ui.style_constants import (
    DARK_BG_COLOR, WHITE_TEXT, PRIMARY_BLUE, GREEN_BTN_COLOR, LIGHT_GRAY_TEXT,
    COMMON_PANEL_LABEL_STYLE
)
from core.controller import get_judge_result_wrapper, CaseDataManager


class ResultScreen(QWidget):
    def __init__(self, on_restart):
        super().__init__()
        self.on_restart = on_restart
        self.case_summary_data = ""
        self.profiles_data = ""
        self.init_ui()

    def set_case_data(self, summary: str, profiles: str):
        self.case_summary_data = summary
        self.profiles_data = profiles

    def init_ui(self):
        layout = QHBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        self.result_text_display = QTextEdit()
        self.result_text_display.setReadOnly(True)
        self.result_text_display.setStyleSheet(
            f"background-color: {DARK_BG_COLOR}; color: {WHITE_TEXT}; font-size: 16px; "
            "padding: 15px; border: none;"
        )
        self.result_text_display.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.result_text_display.setPlaceholderText("AI 판사의 판결이 여기에 표시됩니다...")

        right_frame = QFrame()
        right_frame.setStyleSheet(f"background-color: {DARK_BG_COLOR}; border-left: 1px solid #444;")
        right_frame.setFixedWidth(400)

        right_layout = QVBoxLayout()
        right_layout.setContentsMargins(20, 20, 20, 20)
        right_layout.setSpacing(20)

        label_ai_judge = QLabel("AI_판사")
        label_ai_judge.setStyleSheet(f"background-color: {PRIMARY_BLUE}; {COMMON_PANEL_LABEL_STYLE}")
        label_ai_judge.setAlignment(Qt.AlignCenter)

        self.result_image_label = ResizableImage(_get_image_path("judge.png"))
        self.result_image_label.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

        retry_button = QPushButton("처음으로")
        retry_button.setStyleSheet(
            f"background-color: {PRIMARY_BLUE}; color: {WHITE_TEXT}; font-size: 18px; "
            "border-radius: 8px; padding: 12px;"
        )
        retry_button.setFixedHeight(50)
        retry_button.clicked.connect(lambda: asyncio.ensure_future(self.on_restart()))

        right_layout.addWidget(label_ai_judge, 0, Qt.AlignTop | Qt.AlignHCenter)
        right_layout.addSpacing(20)
        right_layout.addWidget(self.result_image_label, 1)
        right_layout.addSpacing(20)
        right_layout.addWidget(retry_button, 0, Qt.AlignBottom)
        right_frame.setLayout(right_layout)

        layout.addWidget(self.result_text_display, 2)
        layout.addWidget(right_frame, 1)
        self.setLayout(layout)

    async def show_result(self):
        self.result_text_display.setPlainText("AI 판사의 판결을 생성 중입니다...")
        QApplication.processEvents()
        await asyncio.sleep(0.1)

        if not self.case_summary_data or not self.profiles_data:
            self.result_text_display.setPlainText("⚠️ 사건 정보를 불러오지 못했습니다. 게임을 다시 시작해주세요.")
            return

        try:
            full_case_context = f"[사건 개요]\n{self.case_summary_data.strip()}\n\n[등장인물 정보]\n{self.profiles_data.strip()}"
            current_text = "🧑‍⚖️ AI 판결 요약:\n"
            self.result_text_display.setPlainText(current_text + "...")
            QApplication.processEvents()

            # ✅ 메시지 형식 수정
            judgement_summary = get_judge_result_wrapper([
                {"role": "검사", "content": full_case_context},
                {"role": "변호사", "content": "(변호인 측 주장 요약이 여기에 들어갈 수 있습니다.)"}
            ])

            current_text += judgement_summary.strip() + "\n\n🕵️ 사건의 진실:\n"
            self.result_text_display.setPlainText(current_text + "...")
            QApplication.processEvents()

            accumulated_behind = ""

            def update_behind_callback(chunk, accumulated_text):
                nonlocal accumulated_behind
                accumulated_behind = accumulated_text
                self.result_text_display.setPlainText(current_text + accumulated_behind + "▌")
                QApplication.processEvents()

            await CaseDataManager.generate_case_behind(callback=update_behind_callback)
            self.result_text_display.setPlainText(current_text + accumulated_behind.strip())

        except Exception as e:
            print(f"판결 생성 오류: {e}")
            self.result_text_display.setPlainText(f"⚠️ 판결 생성에 실패했습니다: {e}")
