import sys
import os
import asyncio
from PyQt5.QtWidgets import (
    QApplication, QWidget, QPushButton, QLabel,
    QVBoxLayout, QHBoxLayout, QStackedLayout, QFrame, QTextEdit, QSizePolicy
)
from PyQt5.QtGui import QPixmap, QFont
from PyQt5.QtCore import Qt

# 프로젝트 루트 경로를 PYTHONPATH에 추가
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from core.controller import CaseDataManager, get_judge_result_wrapper

class MainWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Logicourt AI")
        self.setGeometry(100, 100, 1280, 720)
        self.init_ui()

    def init_ui(self):
        self.stacked_layout = QStackedLayout()
        self.start_screen = self.create_start_screen()
        self.trial_screen = self.create_trial_screen()
        self.result_screen = self.create_result_screen()

        self.stacked_layout.addWidget(self.start_screen)
        self.stacked_layout.addWidget(self.trial_screen)
        self.stacked_layout.addWidget(self.result_screen)
        self.setLayout(self.stacked_layout)

    def create_start_screen(self):
        screen = QWidget()
        layout = QHBoxLayout()

        logo_label = QLabel()
        logo_pixmap = QPixmap("ui/image/logo.png")
        logo_label.setPixmap(logo_pixmap)
        logo_label.setScaledContents(True)
        logo_label.setFixedWidth(640)

        message = QLabel("서로 변호사와 검사가 되어\n서로의 논리를 기반으로 토론하여 승리를 쟁취하십시오")
        message.setWordWrap(True)
        message.setStyleSheet("color: white; background-color: #222; padding: 10px; border-radius: 10px;")
        message.setFont(QFont("Arial", 20))

        start_button = QPushButton("시작하기")
        start_button.setFixedHeight(60)
        start_button.setStyleSheet("background-color: #007bff; color: white; font-size: 20px; border-radius: 10px;")
        start_button.clicked.connect(lambda: asyncio.ensure_future(self.generate_case_and_show()))

        right_layout = QVBoxLayout()
        right_layout.addStretch(1)
        right_layout.addWidget(message, alignment=Qt.AlignTop)
        right_layout.addStretch(1)
        right_layout.addWidget(start_button, alignment=Qt.AlignBottom)

        right_frame = QFrame()
        right_frame.setStyleSheet("background-color: #1e1e1e;")
        right_frame.setLayout(right_layout)

        layout.addWidget(logo_label)
        layout.addWidget(right_frame)
        screen.setLayout(layout)
        return screen

    def create_trial_screen(self):
        screen = QWidget()
        layout = QHBoxLayout()

        self.left_panel = QTextEdit()
        self.left_panel.setReadOnly(True)
        self.left_panel.setStyleSheet("background-color: #1e1e1e; color: white; font-size: 14px;")
        self.left_panel.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

        to_result_button = QPushButton("판결 화면으로 이동")
        to_result_button.setStyleSheet("background-color: #28a745; color: white; font-size: 16px; border-radius: 10px; padding: 10px;")
        to_result_button.setFixedHeight(50)
        to_result_button.clicked.connect(lambda: asyncio.ensure_future(self.show_judgement()))

        right_layout = QVBoxLayout()
        right_layout.addStretch(1)
        right_layout.addWidget(to_result_button, alignment=Qt.AlignBottom | Qt.AlignRight)

        right_frame = QFrame()
        right_frame.setStyleSheet("background-color: #1e1e1e;")
        right_frame.setLayout(right_layout)
        right_frame.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

        layout.addWidget(self.left_panel)
        layout.addWidget(right_frame)
        screen.setLayout(layout)
        return screen

    def create_result_screen(self):
        screen = QWidget()
        layout = QHBoxLayout()

        self.result_text = QTextEdit()
        self.result_text.setReadOnly(True)
        self.result_text.setStyleSheet("background-color: #1e1e1e; color: white; font-size: 16px;")

        label_ai_judge = QLabel("AI_판사")
        label_ai_judge.setStyleSheet("background-color: #007bff; color: white; font-size: 24px; border-radius: 15px; padding: 10px;")
        label_ai_judge.setAlignment(Qt.AlignCenter)
        label_ai_judge.setFixedSize(160, 50)

        result_image = QLabel()
        result_pixmap = QPixmap("ui/image/judge.png")
        result_image.setPixmap(result_pixmap.scaled(500, 400, Qt.KeepAspectRatio))
        result_image.setAlignment(Qt.AlignCenter)

        retry_button = QPushButton("다시하기")
        retry_button.setStyleSheet("background-color: #007bff; color: white; font-size: 22px; border-radius: 15px; padding: 15px;")
        retry_button.setFixedSize(200, 60)
        retry_button.clicked.connect(lambda: self.stacked_layout.setCurrentIndex(0))

        button_layout = QHBoxLayout()
        button_layout.addStretch(1)
        button_layout.addWidget(label_ai_judge)
        button_layout.addWidget(retry_button)
        button_layout.addStretch(1)

        right_layout = QVBoxLayout()
        right_layout.addLayout(button_layout)
        right_layout.addSpacing(30)
        right_layout.addWidget(result_image, alignment=Qt.AlignCenter)
        right_layout.addStretch(1)

        right_frame = QFrame()
        right_frame.setStyleSheet("background-color: #1e1e1e;")
        right_frame.setLayout(right_layout)

        layout.addWidget(self.result_text)
        layout.addWidget(right_frame)
        screen.setLayout(layout)
        return screen

    async def generate_case_and_show(self):
        self.left_panel.setPlainText("[사건 개요를 생성 중입니다...]")
        self.stacked_layout.setCurrentIndex(1)
        await asyncio.sleep(0.3)

        def update_ui(content, full_text):
            self.left_panel.setPlainText(full_text + "▌")
            QApplication.processEvents()

        case_summary = await CaseDataManager.generate_case_stream(callback=update_ui)
        profiles = await CaseDataManager.generate_profiles_stream(callback=update_ui)

        full_text = f"[사건 개요]\n{case_summary.strip()}\n\n[등장인물]\n{profiles.strip()}"
        self.left_panel.setPlainText(full_text)

    async def show_judgement(self):
        self.stacked_layout.setCurrentIndex(2)
        await asyncio.sleep(0.3)
        self.result_text.setPlainText("AI 판사의 판결을 생성 중입니다...")
        await asyncio.sleep(0.3)

        case_summary = self.left_panel.toPlainText()
        full_result = "🧑‍⚖️ 판결 요약:\n"

        def update_ui_judgement(chunk, accumulated):
            self.result_text.setPlainText(full_result + accumulated + "▌")
            QApplication.processEvents()

        judgement_result = get_judge_result_wrapper([
            {"role": "system", "content": case_summary}
        ])
        full_result += judgement_result.strip() + "\n\n🕵️ 사건의 진실:\n"
        self.result_text.setPlainText(full_result + "▌")
        QApplication.processEvents()

        async def update_case_behind():
            result = ""
            def callback(chunk, accumulated):
                nonlocal result
                result = accumulated
                self.result_text.setPlainText(full_result + result + "▌")
                QApplication.processEvents()
            await CaseDataManager.generate_case_behind(callback=callback)
        await update_case_behind()

if __name__ == "__main__":
    from qasync import QEventLoop
    app = QApplication(sys.argv)
    loop = QEventLoop(app)
    asyncio.set_event_loop(loop)
    window = MainWindow()
    window.show()
    with loop:
        loop.run_forever()
