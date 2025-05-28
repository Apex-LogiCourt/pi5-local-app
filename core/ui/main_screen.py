import sys
import os
import asyncio

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from PyQt5.QtWidgets import (
    QApplication, QWidget, QPushButton, QLabel,
    QVBoxLayout, QHBoxLayout, QStackedLayout, QFrame
)
from PyQt5.QtGui import QFont
from PyQt5.QtCore import Qt
from qasync import QEventLoop

from core.game_controller import GameController
from ui.intro_screen import IntroScreen
from ui.prosecutor_screen import ProsecutorScreen
from core.ui.lawyer_screen import LawyerScreen
from ui.result_screen import ResultScreen
from ui.resizable_image import ResizableImage, _get_image_path
from ui.description_screen import GameDescriptionScreen
from ui.interrogation_screen import InterrogationScreen
from ui.style_constants import *

class MainWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Logicourt AI")
        self.resize(1280, 720)

        self.type_map = {
            "defendant": "피고",
            "victim": "피해자",
            "witness": "목격자",
            "reference": "참고인"
        }
        self.gender_map = {
            "남자": "남성",
            "여성": "여성"
        }

        self.intro_screen_instance = None
        self.prosecutor_screen = None # Instance holder
        self.lawyer_screen = None     # Instance holder
        self.interrogation_screen_instance = None # Instance holder
        self.previous_screen_for_interrogation = None
        self.init_ui()
        asyncio.ensure_future(self.preload_case_data())

    def init_ui(self):
        self.stacked_layout = QStackedLayout()

        self.start_screen = self.create_start_screen()
        self.game_description_screen = GameDescriptionScreen(
            on_back_callback=lambda: self.stacked_layout.setCurrentWidget(self.start_screen)
        )
        # ResultScreen is created when needed or can be pre-created if preferred
        # self.result_screen = ResultScreen(on_restart=self.restart_game_flow)

        self.stacked_layout.addWidget(self.start_screen)
        self.stacked_layout.addWidget(self.game_description_screen)
        # self.stacked_layout.addWidget(self.result_screen) # Add when shown

        self.setLayout(self.stacked_layout)
        self.setStyleSheet(f"background-color: {DARK_BG_COLOR};")

    def _update_start_button(self, text: str, enabled: bool):
        if hasattr(self, 'start_button_on_start_screen'):
            self.start_button_on_start_screen.setText(text)
            self.start_button_on_start_screen.setEnabled(enabled)

    async def preload_case_data(self):
        try:
            print("Preloading case data via GameController...")
            self._update_start_button("데이터 로딩 중...", False)
            await GameController.initialize()
            print("GameController initialized.")
            self._update_start_button("시작하기", True)
        except Exception as e:
            print(f"Error initializing GameController: {e}")
            self._update_start_button("데이터 로드 실패 (재시도)", True) # Allow retry

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
        if hasattr(self, 'start_screen') and self.start_screen:
            left_frame = self.start_screen.layout().itemAt(0).widget()
            if left_frame:
                left_frame.setFixedWidth(self.width() // 2)

    def show_game_description(self):
        self.stacked_layout.setCurrentWidget(self.game_description_screen)

    def enter_text_mode(self):
        print("텍스트모드 버튼 클릭됨 (현재 미구현 상태)")

    def _generate_profiles_text(self):
        if not GameController._profiles: return ""
        return "\n--------------------------------\n".join(
            f"이름: {p.name} ({self.type_map.get(p.type, p.type)})\n"
            f"성별: {self.gender_map.get(p.gender, p.gender)}, 나이: {p.age}세\n"
            f"사연: {p.context}"
            for p in GameController._profiles
        )

    def _cleanup_screen(self, screen_attr_name):
        """Safely removes and deletes a screen attribute."""
        screen_instance = getattr(self, screen_attr_name, None)
        if screen_instance:
            if self.stacked_layout.indexOf(screen_instance) != -1:
                self.stacked_layout.removeWidget(screen_instance)
            screen_instance.deleteLater()
            setattr(self, screen_attr_name, None)

    def start_intro_sequence(self):
        if not GameController._case or not GameController._profiles:
             # Try to reload data if button is clicked and data isn't ready
            asyncio.ensure_future(self.preload_case_data())
            print("Data not ready for intro, attempting reload.")
            return

        summary = GameController._case.outline
        profiles_text = self._generate_profiles_text()
        evidences = GameController._evidences

        self._cleanup_screen('intro_screen_instance')
        self._cleanup_screen('prosecutor_screen')
        self._cleanup_screen('lawyer_screen')


        self.intro_screen_instance = IntroScreen(
            summary=summary,
            profiles=profiles_text,
            evidences=evidences,
            on_intro_finished_callback=self.show_prosecutor_screen
        )
        self.stacked_layout.addWidget(self.intro_screen_instance)
        self.stacked_layout.setCurrentWidget(self.intro_screen_instance)

    def show_prosecutor_screen(self):
        summary = GameController._case.outline
        profiles_text = self._generate_profiles_text()

        self._cleanup_screen('intro_screen_instance')
        self._cleanup_screen('lawyer_screen')
        self._cleanup_screen('prosecutor_screen') # Clean up old instance if any (e.g. from interrogation return)


        self.prosecutor_screen = ProsecutorScreen(
            case_summary=summary,
            profiles=profiles_text,
            on_switch_to_lawyer=self.show_lawyer_screen,
            on_request_judgement=lambda: asyncio.ensure_future(self.show_judgement()),
            on_interrogate=lambda: self.show_interrogation_screen(previous='prosecutor')
        )
        self.stacked_layout.addWidget(self.prosecutor_screen)
        self.stacked_layout.setCurrentWidget(self.prosecutor_screen)


    def show_lawyer_screen(self):
        summary = GameController._case.outline
        profiles_text = self._generate_profiles_text()

        self._cleanup_screen('prosecutor_screen')
        self._cleanup_screen('lawyer_screen') # Clean up old instance if any (e.g. from interrogation return)

        self.lawyer_screen = LawyerScreen(
            case_summary=summary,
            profiles=profiles_text,
            on_switch_to_prosecutor=self.show_prosecutor_screen,
            on_request_judgement=lambda: asyncio.ensure_future(self.show_judgement()),
            on_interrogate=lambda: self.show_interrogation_screen(previous='lawyer')
        )
        self.stacked_layout.addWidget(self.lawyer_screen)
        self.stacked_layout.setCurrentWidget(self.lawyer_screen)


    def show_interrogation_screen(self, previous):
        self.previous_screen_for_interrogation = previous

        # Clean up the screen we are coming from before showing interrogation
        if previous == 'prosecutor':
            self._cleanup_screen('prosecutor_screen')
        elif previous == 'lawyer':
            self._cleanup_screen('lawyer_screen')
        
        self._cleanup_screen('interrogation_screen_instance')


        self.interrogation_screen_instance = InterrogationScreen(
            case_summary=GameController._case.outline,
            profiles=self._generate_profiles_text(), # Pass the generated string
            on_back=self.handle_interrogation_back
        )
        self.stacked_layout.addWidget(self.interrogation_screen_instance)
        self.stacked_layout.setCurrentWidget(self.interrogation_screen_instance)

    def handle_interrogation_back(self):
        self._cleanup_screen('interrogation_screen_instance')

        if self.previous_screen_for_interrogation == 'prosecutor':
            self.show_prosecutor_screen()
        elif self.previous_screen_for_interrogation == 'lawyer':
            self.show_lawyer_screen()
        self.previous_screen_for_interrogation = None


    async def show_judgement(self):
        self._cleanup_screen('prosecutor_screen')
        self._cleanup_screen('lawyer_screen')
        self._cleanup_screen('interrogation_screen_instance')
        self._cleanup_screen('result_screen') # Clean up old result screen if any

        summary = GameController._case.outline
        profiles_text = self._generate_profiles_text()
        
        self.result_screen = ResultScreen(on_restart=self.restart_game_flow)
        self.result_screen.set_case_data(summary, profiles_text)
        
        self.stacked_layout.addWidget(self.result_screen)
        self.stacked_layout.setCurrentWidget(self.result_screen)
        await self.result_screen.show_result() # Make sure ResultScreen has show_result async

    async def restart_game_flow(self):
        self._cleanup_screen('result_screen')
        self._cleanup_screen('prosecutor_screen')
        self._cleanup_screen('lawyer_screen')
        self._cleanup_screen('intro_screen_instance')
        self._cleanup_screen('interrogation_screen_instance')

        self._update_start_button("데이터 로딩 중...", False)
        self.stacked_layout.setCurrentWidget(self.start_screen)
        # GameController.initialize() should reset necessary internal states if any
        await self.preload_case_data()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    loop = QEventLoop(app)
    asyncio.set_event_loop(loop)
    
    # Ensure image directory and dummy images exist (optional, for testing)
    current_dir = os.path.dirname(__file__) # Assuming main.py is in ui directory
    image_dir_abs = os.path.abspath(os.path.join(current_dir, "image"))
    os.makedirs(image_dir_abs, exist_ok=True)
    
    profile_dir_abs = os.path.join(image_dir_abs, "profile")
    os.makedirs(profile_dir_abs, exist_ok=True)

    dummy_images_root = ["logo.png", "stand.png", "mike.png", "mike_on.png", "background1.png"]
    dummy_images_profile = ["judge.png", "Prosecutor.png", "lawyer.png"] # Add other profile names as needed

    try:
        from PIL import Image
        pillow_available = True
    except ImportError:
        pillow_available = False
        print("Pillow not installed. Cannot create dummy images. Please create them manually or install Pillow.")

    if pillow_available:
        for img_name in dummy_images_root:
            path = os.path.join(image_dir_abs, img_name)
            if not os.path.exists(path):
                try:
                    Image.new('RGB', (50, 50), color = 'blue').save(path)
                    print(f"Created dummy image: {path}")
                except Exception as e:
                    print(f"Error creating dummy image {img_name}: {e}")
        for img_name in dummy_images_profile:
            path = os.path.join(profile_dir_abs, img_name)
            if not os.path.exists(path):
                try:
                    Image.new('RGB', (50, 50), color = 'red').save(path)
                    print(f"Created dummy image: {path}")
                except Exception as e:
                    print(f"Error creating dummy image {img_name}: {e}")
                    
    window = MainWindow()
    window.show()
    try:
        loop.run_forever()
    except KeyboardInterrupt:
        print("Program interrupted")
    finally:
        loop.close()