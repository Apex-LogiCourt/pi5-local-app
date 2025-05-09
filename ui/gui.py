import sys
import os
import asyncio
from PyQt5.QtWidgets import (
    QApplication, QWidget, QPushButton, QLabel,
    QVBoxLayout, QHBoxLayout, QStackedLayout, QFrame, QTextEdit, QSizePolicy
)
from PyQt5.QtGui import QPixmap, QFont
from PyQt5.QtCore import Qt

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from core.controller import CaseDataManager, get_judge_result_wrapper
from ui.intro import IntroScreen

class MainWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Logicourt AI")
        self.setGeometry(100, 100, 1280, 720)
        self.case_summary = ""
        self.profiles = ""
        self.init_ui()
        asyncio.ensure_future(self.load_case_data())

    def init_ui(self):
        self.stacked_layout = QStackedLayout()
        self.start_screen = self.create_start_screen()
        self.trial_screen = self.create_trial_screen()
        self.result_screen = self.create_result_screen()

        self.stacked_layout.addWidget(self.start_screen)
        self.stacked_layout.addWidget(self.trial_screen)
        self.stacked_layout.addWidget(self.result_screen)

        self.setLayout(self.stacked_layout)

    async def load_case_data(self):
        def dummy_callback(chunk, accumulated):
            pass
        CaseDataManager._case = None
        CaseDataManager._profiles = None
        CaseDataManager._evidences = None
        CaseDataManager._case_data = None

        self.case_summary = await CaseDataManager.generate_case_stream(callback=dummy_callback)
        self.profiles = await CaseDataManager.generate_profiles_stream(callback=dummy_callback)

    def create_start_screen(self):
        screen = QWidget()
        layout = QHBoxLayout()

        logo_label = QLabel()
        logo_pixmap = QPixmap("ui/image/logo.png")
        logo_label.setPixmap(logo_pixmap)
        logo_label.setScaledContents(True)
        logo_label.setFixedWidth(640)

        right_frame = QFrame()
        right_frame.setStyleSheet("background-color: #1e1e1e;")
        right_layout = QVBoxLayout()

        message = QLabel("서로 변호사와 검사가 되어\n서로의 논리를 기반으로 토론하여 승리를 쟁취하십시오")
        message.setWordWrap(True)
        message.setStyleSheet("color: white; background-color: #222; padding: 10px; border-radius: 10px;")
        message.setFont(QFont("Arial", 20))

        start_button = QPushButton("시작하기")
        start_button.setFixedHeight(60)
        start_button.setStyleSheet("background-color: #007bff; color: white; font-size: 20px; border-radius: 10px;")
        start_button.clicked.connect(self.start_intro_sequence)

        right_layout.addStretch(1)
        right_layout.addWidget(message, alignment=Qt.AlignTop)
        right_layout.addStretch(1)
        right_layout.addWidget(start_button, alignment=Qt.AlignBottom)

        right_frame.setLayout(right_layout)

        layout.addWidget(logo_label)
        layout.addWidget(right_frame)
        screen.setLayout(layout)
        return screen

    def start_intro_sequence(self):
        self.intro_screen = IntroScreen(
            summary=self.case_summary,
            profiles=self.profiles,
            on_intro_finished=self.enter_trial_screen
        )
        self.stacked_layout.addWidget(self.intro_screen)
        self.stacked_layout.setCurrentWidget(self.intro_screen)

    def enter_trial_screen(self):
        self.stacked_layout.setCurrentWidget(self.trial_screen)
        self.trial_left_panel.setPlainText("[사건 개요 및 등장인물 확인 완료]")

    def create_trial_screen(self):
        screen = QWidget()
        layout = QHBoxLayout()

        self.trial_left_panel = QTextEdit()
        self.trial_left_panel.setReadOnly(True)
        self.trial_left_panel.setStyleSheet("background-color: #1e1e1e; color: white; font-size: 14px;")
        self.trial_left_panel.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

        right_frame = QFrame()
        right_frame.setStyleSheet("background-color: #1e1e1e;")
        right_layout = QVBoxLayout()

        to_result_button = QPushButton("판결 화면으로 이동")
        to_result_button.setStyleSheet("background-color: #28a745; color: white; font-size: 16px; border-radius: 10px; padding: 10px;")
        to_result_button.setFixedHeight(50)
        to_result_button.clicked.connect(lambda: asyncio.ensure_future(self.show_judgement()))

        right_layout.addStretch(1)
        right_layout.addWidget(to_result_button, alignment=Qt.AlignBottom | Qt.AlignRight)

        right_frame.setLayout(right_layout)
        right_frame.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

        layout.addWidget(self.trial_left_panel)
        layout.addWidget(right_frame)
        screen.setLayout(layout)
        return screen

    def create_result_screen(self):
        screen = QWidget()
        layout = QHBoxLayout()

        self.result_text = QTextEdit()
        self.result_text.setReadOnly(True)
        self.result_text.setStyleSheet("background-color: #1e1e1e; color: white; font-size: 16px;")
        self.result_text.setText("AI 판사의 판결\n\n사건의 진실이 이곳에 표시됩니다...")

        right_frame = QFrame()
        right_frame.setStyleSheet("background-color: #1e1e1e;")
        right_layout = QVBoxLayout()

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
        retry_button.clicked.connect(lambda: asyncio.ensure_future(self.restart_game()))

        button_layout = QHBoxLayout()
        button_layout.addStretch(1)
        button_layout.addWidget(label_ai_judge)
        button_layout.addWidget(retry_button)
        button_layout.addStretch(1)

        right_layout.addLayout(button_layout)
        right_layout.addSpacing(30)
        right_layout.addWidget(result_image, alignment=Qt.AlignCenter)
        right_layout.addStretch(1)

        right_frame.setLayout(right_layout)
        layout.addWidget(self.result_text)
        layout.addWidget(right_frame)
        screen.setLayout(layout)
        return screen

    async def restart_game(self):
        CaseDataManager._case = None
        CaseDataManager._profiles = None
        CaseDataManager._evidences = None
        CaseDataManager._case_data = None
        await self.load_case_data()
        self.stacked_layout.setCurrentIndex(0)

    async def show_judgement(self):
        try:
            self.stacked_layout.setCurrentIndex(2)
            self.result_text.setPlainText("AI 판사의 판결을 생성 중입니다...")
            await asyncio.sleep(0.3)

            case_summary = self.case_summary
            full_result = "🧑‍⚖️ 판결 요약:\n"

            judgement_result = get_judge_result_wrapper([
                {"role": "system", "content": case_summary.strip() + "\n" + self.profiles.strip()}
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

        except Exception as e:
            print("판결 생성 오류:", e)
            self.result_text.setPlainText("⚠️ 판결 생성에 실패했습니다.")

if __name__ == "__main__":
    from qasync import QEventLoop
    app = QApplication(sys.argv)
    loop = QEventLoop(app)
    asyncio.set_event_loop(loop)
    window = MainWindow()
    window.show()
    with loop:
        loop.run_forever()
