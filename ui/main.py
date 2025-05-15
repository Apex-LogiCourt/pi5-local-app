# 전체 코드가 길어지므로 요약하여 상단 주석을 표시합니다
# ※ 코드 전체에 대해 리사이즈 비율 자동 조절되도록 조정됨
# ※ IntroScreen 기능 및 게임 설명 화면 통합됨
# ※ 비동기 데이터 로딩 및 화면 전환 로직 개선
# ※ 리팩토링: 중복 코드 및 미사용 코드 정리, 상수 활용

import sys
import os
import asyncio
import platform

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from PyQt5.QtWidgets import (
    QApplication, QWidget, QPushButton, QLabel,
    QVBoxLayout, QHBoxLayout, QStackedLayout, QFrame, QTextEdit
)
from PyQt5.QtGui import QFont, QFontDatabase
from PyQt5.QtCore import Qt

from qasync import QEventLoop
from core.controller import CaseDataManager, get_judge_result_wrapper  # type: ignore

from ui.intro import IntroScreen
from ui.prosecutor import ProsecutorScreen
from ui.lawyer import LawyerScreen
from ui.result import ResultScreen
from ui.resizable_image import ResizableImage, _get_image_path
from ui.game_description import GameDescriptionScreen
from ui.style_constants import *



class MainWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Logicourt AI")
        self.resize(1280, 720)

        self.case_summary_data = ""
        self.profiles_data = ""
        self.intro_screen_instance = None

        self.init_ui()
        asyncio.ensure_future(self.preload_case_data())

    def init_ui(self):
        self.stacked_layout = QStackedLayout()

        self.start_screen = self.create_start_screen()
        self.game_description_screen = GameDescriptionScreen(
            on_back_callback=lambda: self.stacked_layout.setCurrentWidget(self.start_screen)
        )
        self.result_screen = ResultScreen(on_restart=self.restart_game_flow)

        self.stacked_layout.addWidget(self.start_screen)
        self.stacked_layout.addWidget(self.game_description_screen)
        self.stacked_layout.addWidget(self.result_screen)

        self.setLayout(self.stacked_layout)
        self.setStyleSheet(f"background-color: {DARK_BG_COLOR};")

    def _update_start_button(self, text: str, enabled: bool):
        if hasattr(self, 'start_button_on_start_screen'):
            self.start_button_on_start_screen.setText(text)
            self.start_button_on_start_screen.setEnabled(enabled)

    async def preload_case_data(self):
        def dummy_callback(chunk, accumulated):
            pass

        CaseDataManager._case = None
        CaseDataManager._profiles = None

        try:
            print("Preloading case data...")
            self.case_summary_data = await CaseDataManager.generate_case_stream(callback=dummy_callback)
            self.profiles_data = await CaseDataManager.generate_profiles_stream(callback=dummy_callback)
            print("Case data preloaded.")
            self._update_start_button("시작하기", True)
        except Exception as e:
            print(f"Error preloading case data: {e}")
            self._update_start_button("데이터 로드 실패 (재시도)", False)

    def create_start_screen(self):
        screen = QWidget()
        layout = QHBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        logo_label = ResizableImage(_get_image_path("logo.png"))
        logo_label.setStyleSheet(f"background-color: {DARK_BG_COLOR};")

        left_frame = QFrame()
        left_layout = QVBoxLayout()
        left_layout.addWidget(logo_label)
        left_frame.setLayout(left_layout)
        left_frame.setFixedWidth(self.width() // 2)
        left_frame.setStyleSheet(f"background-color: {DARK_BG_COLOR};")

        right_layout = QVBoxLayout()
        right_layout.setContentsMargins(50, 50, 50, 50)
        right_layout.setSpacing(20)

        title = QLabel("logiCourt_AI")
        title.setAlignment(Qt.AlignCenter)
        title.setFont(QFont("Arial", 36, QFont.Bold))
        title.setStyleSheet(f"color: {GOLD_ACCENT}; background-color: transparent;")

        subtitle = QLabel("당신의 논리, 상대의 허점, AI가 지켜보는 심문의 무대! 이 법정, 지성의 승부처")
        subtitle.setAlignment(Qt.AlignCenter)
        subtitle.setFont(QFont("Arial", 18))
        subtitle.setStyleSheet(f"color: {WHITE_TEXT}; background-color: transparent; line-height: 1.5;")
        subtitle.setWordWrap(True)

        btn_game_desc = QPushButton("게임설명")
        btn_game_desc.setStyleSheet(
            f"background-color: {DARK_GRAY_BTN_COLOR}; color: {WHITE_TEXT}; font-size: 18px; "
            f"border-radius: 10px; padding: 12px 20px; border: 1px solid #444;"
        )
        btn_game_desc.setFixedHeight(50)
        btn_game_desc.clicked.connect(self.show_game_description)

        self.start_button_on_start_screen = QPushButton()
        self.start_button_on_start_screen.setStyleSheet(
            f"background-color: {PRIMARY_BLUE}; color: {WHITE_TEXT}; font-size: 20px; "
            f"border-radius: 10px; padding: 15px 25px; border: 1px solid #0056b3;"
        )
        self.start_button_on_start_screen.setFixedHeight(60)
        self._update_start_button("데이터 로딩 중...", False)
        self.start_button_on_start_screen.clicked.connect(self.start_intro_sequence)

        btn_text_mode = QPushButton("텍스트모드 (미구현)")
        btn_text_mode.setStyleSheet(
            f"background-color: {MEDIUM_GRAY_BTN_COLOR}; color: {LIGHT_GRAY_TEXT}; font-size: 18px; "
            f"border-radius: 10px; padding: 12px 20px; border: 1px solid #666;"
        )
        btn_text_mode.setFixedHeight(50)
        btn_text_mode.clicked.connect(self.enter_text_mode)

        right_layout.addStretch(1)
        right_layout.addWidget(title)
        right_layout.addSpacing(15)
        right_layout.addWidget(subtitle)
        right_layout.addStretch(2)
        right_layout.addWidget(btn_game_desc)
        right_layout.addWidget(self.start_button_on_start_screen)
        right_layout.addWidget(btn_text_mode)
        right_layout.addStretch(1)

        right_frame = QFrame()
        right_frame.setStyleSheet(f"background-color: {DARK_BG_COLOR};")
        right_frame.setLayout(right_layout)

        layout.addWidget(left_frame)
        layout.addWidget(right_frame, 1)
        screen.setLayout(layout)
        return screen

    def resizeEvent(self, event):
        super().resizeEvent(event)
        if hasattr(self, 'start_screen'):
            left_frame = self.start_screen.layout().itemAt(0).widget()
            if left_frame:
                left_frame.setFixedWidth(self.width() // 2)

    def show_game_description(self):
        self.stacked_layout.setCurrentWidget(self.game_description_screen)

    def enter_text_mode(self):
        print("텍스트모드 버튼 클릭됨 (현재 미구현 상태)")

    def start_intro_sequence(self):
        if not self.case_summary_data or not self.profiles_data:
            asyncio.ensure_future(self.preload_case_data())
            return

        if self.intro_screen_instance and self.stacked_layout.indexOf(self.intro_screen_instance) != -1:
            self.stacked_layout.removeWidget(self.intro_screen_instance)
            self.intro_screen_instance.deleteLater()

        self.intro_screen_instance = IntroScreen(
            summary=self.case_summary_data,
            profiles=self.profiles_data,
            on_intro_finished_callback=self.show_prosecutor_screen
        )
        self.stacked_layout.addWidget(self.intro_screen_instance)
        self.stacked_layout.setCurrentWidget(self.intro_screen_instance)

    def show_prosecutor_screen(self):
        if self.intro_screen_instance:
            if self.stacked_layout.indexOf(self.intro_screen_instance) != -1:
                self.stacked_layout.removeWidget(self.intro_screen_instance)
            self.intro_screen_instance.deleteLater()
            self.intro_screen_instance = None

        self.prosecutor_screen = ProsecutorScreen(
            case_summary=self.case_summary_data,
            profiles=self.profiles_data,
            on_next=self.show_lawyer_screen
        )
        self.stacked_layout.addWidget(self.prosecutor_screen)
        self.stacked_layout.setCurrentWidget(self.prosecutor_screen)

    def show_lawyer_screen(self):
        self.lawyer_screen = LawyerScreen(
            case_summary=self.case_summary_data,
            profiles=self.profiles_data,
            on_next=lambda: asyncio.ensure_future(self.show_judgement())
        )
        self.stacked_layout.addWidget(self.lawyer_screen)
        self.stacked_layout.setCurrentWidget(self.lawyer_screen)

        if hasattr(self, 'prosecutor_screen'):
            self.stacked_layout.removeWidget(self.prosecutor_screen)
            self.prosecutor_screen.deleteLater()

    async def show_judgement(self):
        self.result_screen.set_case_data(self.case_summary_data, self.profiles_data)
        self.stacked_layout.setCurrentWidget(self.result_screen)
        await self.result_screen.show_result()

    async def restart_game_flow(self):
        self.case_summary_data = ""
        self.profiles_data = ""
        self._update_start_button("데이터 로딩 중...", False)
        self.stacked_layout.setCurrentWidget(self.start_screen)
        await self.preload_case_data()


if __name__ == "__main__":
    app = QApplication(sys.argv)

    loop = QEventLoop(app)
    asyncio.set_event_loop(loop)
    window = MainWindow()
    window.show()
    try:
        loop.run_forever()
    except KeyboardInterrupt:
        print("Program interrupted")
    finally:
        loop.close()

