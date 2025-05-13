# 전체 코드가 길어지므로 요약하여 상단 주석을 표시합니다
# ※ 코드 전체에 대해 리사이즈 비율 자동 조절되도록 조정됨
# ※ IntroScreen 기능 및 게임 설명 화면 통합됨
# ※ 비동기 데이터 로딩 및 화면 전환 로직 개선
# ※ 리팩토링: 중복 코드 및 미사용 코드 정리, 상수 활용

import sys
import os
import asyncio
from PyQt5.QtWidgets import (
    QApplication, QWidget, QPushButton, QLabel,
    QVBoxLayout, QHBoxLayout, QStackedLayout, QFrame, QTextEdit, QSizePolicy
)
from PyQt5.QtGui import QPixmap, QFont
from PyQt5.QtCore import Qt

# Assuming core.controller is in a directory one level up
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from core.controller import CaseDataManager, get_judge_result_wrapper # type: ignore

# --- Style Constants ---
DARK_BG_COLOR = "#0f2748"
PRIMARY_BLUE = "#007bff"
SECONDARY_BLUE = "#2f5a68" # For intro section label
GOLD_ACCENT = "#f0c040"
WHITE_TEXT = "white"
LIGHT_GRAY_TEXT = "#ccc"
BLACK_COLOR = "black"
GREEN_BTN_COLOR = "#28a745"
DARK_GRAY_BTN_COLOR = "#3a3a3a"
MEDIUM_GRAY_BTN_COLOR = "#555"

# Common QSS parts
COMMON_PANEL_LABEL_STYLE = f"color: {WHITE_TEXT}; font-size: 22px; font-weight: bold; padding: 12px; border-radius: 12px;"
DEFAULT_BUTTON_STYLE = f"background-color: {PRIMARY_BLUE}; color: {WHITE_TEXT}; font-size: 18px; border-radius: 10px;"
TEXT_EDIT_STYLE_TRANSPARENT_BG = f"background-color: transparent; color: {WHITE_TEXT}; font-size: 15px; border: none;"
# Styles
ROLE_TITLE_STYLE = f"color: {GOLD_ACCENT}; font-size: 22px; font-weight: bold; background-color: {BLACK_COLOR}; padding: 12px; border-radius: 8px;"
SIDE_BUTTON_STYLE = f"background-color: #2a4a70; color: {WHITE_TEXT}; font-size: 16px; border-radius: 6px; padding: 10px;"
TEXT_INPUT_STYLE = f"background-color: {MEDIUM_GRAY_BTN_COLOR}; color: {WHITE_TEXT}; font-size: 16px; border-radius: 6px;"
MIC_BUTTON_STYLE = "background-color: #2a4a70; border-radius: 40px;"

# HTML Style Constants for IntroScreen
HTML_H3_STYLE = f"color: {WHITE_TEXT}; font-weight: bold;"
HTML_P_STYLE = f"color: {WHITE_TEXT}; margin: 5px 0;"
HTML_LI_STYLE = f"color: {WHITE_TEXT};"

# Image path helper
def _get_image_path(filename: str) -> str:
    return os.path.join(os.path.dirname(__file__), "image", filename)


class ResizableImage(QLabel):
    def __init__(self, image_path, width_limit=None, height_limit=None):
        super().__init__()
        self.image_path = image_path
        self.original_pixmap = QPixmap(self.image_path)
        self.setAlignment(Qt.AlignCenter)
        self.setScaledContents(False)  # Important for custom scaling
        self.width_limit = width_limit
        self.height_limit = height_limit

        self.setStyleSheet("background-color: transparent;") # Default to transparent
        self.setSizePolicy(QSizePolicy.Ignored, QSizePolicy.Ignored)
        self.setMinimumSize(1, 1)  # Must set minimum size
        self.setMaximumSize(16777215, 16777215)  # No artificial max size
        self.update_scaled_pixmap()

    def resizeEvent(self, event):
        self.update_scaled_pixmap()
        super().resizeEvent(event)

    def update_scaled_pixmap(self):
        if self.original_pixmap.isNull():
            self.setText("이미지를 불러올 수 없습니다.")
            return

        current_width = self.width()
        current_height = self.height()

        target_width = self.width_limit if self.width_limit else current_width
        target_height = self.height_limit if self.height_limit else current_height

        if not self.width_limit or self.width_limit > current_width:
            target_width = current_width
        if not self.height_limit or self.height_limit > current_height:
            target_height = current_height

        scaled = self.original_pixmap.scaled(
            int(target_width),
            int(target_height),
            Qt.KeepAspectRatio,
            Qt.SmoothTransformation
        )
        self.setPixmap(scaled)

    def set_image(self, image_path):
        self.image_path = image_path
        self.original_pixmap = QPixmap(image_path)
        if self.original_pixmap.isNull():
            print(f"Warning: Could not load image from {image_path}")
        self.update_scaled_pixmap()


class IntroScreen(QWidget):
    def __init__(self, summary: str, profiles: str, on_intro_finished_callback):
        super().__init__()
        self.case_summary = summary
        self.profiles_text = profiles
        self.on_intro_finished = on_intro_finished_callback
        self.current_block_index = -1
        self.display_blocks = []

        # --- Block 1: 사건 개요
        summary_title = f"<h3 style='{HTML_H3_STYLE}'>사건개요</h3>"
        summary_content = "".join([
            f"<p style='{HTML_P_STYLE}'>{line.strip()}</p>"
            for line in self.case_summary.strip().split('\n') if line.strip()
        ])
        self.display_blocks.append(summary_title + summary_content)

        # --- Block 2~: 등장인물/증거 등
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
        self.next_button.setFixedHeight(50) # Specific height, style from global QPushButton
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

class ProsecutorScreen(QWidget):
    def __init__(self, case_summary="", profiles="", on_next=None):
        super().__init__()
        self.case_summary = case_summary
        self.profiles = profiles
        self.on_next = on_next
        self.init_ui()

    def init_ui(self):
        self.setStyleSheet(f"background-color: {DARK_BG_COLOR}; color: {WHITE_TEXT};")

        # 좌측 레이아웃
        left_layout = QVBoxLayout()

        title_label = QLabel("검사 주장")
        title_label.setAlignment(Qt.AlignCenter)
        title_label.setStyleSheet(ROLE_TITLE_STYLE)

        btn_case = QPushButton("사건개요")
        btn_case.setStyleSheet(SIDE_BUTTON_STYLE)
        btn_char = QPushButton("등장인물")
        btn_char.setStyleSheet(SIDE_BUTTON_STYLE)
        btn_myproof = QPushButton("검사측 증거")
        btn_myproof.setStyleSheet(SIDE_BUTTON_STYLE)
        btn_otherproof = QPushButton("변호사측 증거")
        btn_otherproof.setStyleSheet(SIDE_BUTTON_STYLE)
        btn_text = QPushButton("텍스트 입력")
        btn_text.setStyleSheet(TEXT_INPUT_STYLE)

        btn_mic = QPushButton("🎤")
        btn_mic.setFixedSize(80, 80)
        btn_mic.setStyleSheet(MIC_BUTTON_STYLE)

        # Add Next button for continuing to lawyer screen
        btn_next = QPushButton("다음 단계로")
        btn_next.setStyleSheet(DEFAULT_BUTTON_STYLE)
        btn_next.clicked.connect(self.proceed_to_next)

        left_layout.addWidget(title_label)
        left_layout.addWidget(btn_case)
        left_layout.addWidget(btn_char)
        left_layout.addWidget(btn_myproof)
        left_layout.addWidget(btn_otherproof)
        left_layout.addWidget(btn_text)
        left_layout.addWidget(btn_mic, alignment=Qt.AlignCenter)
        left_layout.addStretch()
        left_layout.addWidget(btn_next)

        # 우측 이미지
        image_label = ResizableImage(_get_image_path("profile/Prosecutor.png"))
        image_label.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

        # 메인 레이아웃
        main_layout = QHBoxLayout()
        main_layout.addLayout(left_layout, 2)
        main_layout.addWidget(image_label, 3)

        self.setLayout(main_layout)
    
    def proceed_to_next(self):
        if self.on_next:
            self.on_next()

class LawyerScreen(QWidget):
    def __init__(self, case_summary="", profiles="", on_next=None):
        super().__init__()
        self.case_summary = case_summary
        self.profiles = profiles
        self.on_next = on_next
        self.init_ui()

    def init_ui(self):
        self.setStyleSheet(f"background-color: {DARK_BG_COLOR}; color: {WHITE_TEXT};")

        left_layout = QVBoxLayout()

        title_label = QLabel("변호사 반론")
        title_label.setAlignment(Qt.AlignCenter)
        title_label.setStyleSheet(ROLE_TITLE_STYLE)

        btn_case = QPushButton("사건개요")
        btn_case.setStyleSheet(SIDE_BUTTON_STYLE)
        btn_char = QPushButton("등장인물")
        btn_char.setStyleSheet(SIDE_BUTTON_STYLE)
        btn_myproof = QPushButton("변호사측 증거")
        btn_myproof.setStyleSheet(SIDE_BUTTON_STYLE)
        btn_otherproof = QPushButton("검사측 증거")
        btn_otherproof.setStyleSheet(SIDE_BUTTON_STYLE)
        btn_text = QPushButton("텍스트 입력")
        btn_text.setStyleSheet(TEXT_INPUT_STYLE)

        btn_mic = QPushButton("🔴")
        btn_mic.setFixedSize(80, 80)
        btn_mic.setStyleSheet(MIC_BUTTON_STYLE)

        # Add judgement button
        btn_judgement = QPushButton("판결 요청")
        btn_judgement.setStyleSheet(DEFAULT_BUTTON_STYLE)
        btn_judgement.clicked.connect(self.request_judgement)

        left_layout.addWidget(title_label)
        left_layout.addWidget(btn_case)
        left_layout.addWidget(btn_char)
        left_layout.addWidget(btn_myproof)
        left_layout.addWidget(btn_otherproof)
        left_layout.addWidget(btn_text)
        left_layout.addWidget(btn_mic, alignment=Qt.AlignCenter)
        left_layout.addStretch()
        left_layout.addWidget(btn_judgement)

        image_label = ResizableImage(_get_image_path("profile/lawyer.png"))
        image_label.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

        main_layout = QHBoxLayout()
        main_layout.addLayout(left_layout, 2)
        main_layout.addWidget(image_label, 3)

        self.setLayout(main_layout)
    
    def request_judgement(self):
        if self.on_next:
            self.on_next()

class MainWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Logicourt AI")
        self.resize(1280, 720)

        self.case_summary_data = ""
        self.profiles_data = ""
        self.intro_screen_instance = None # To manage the IntroScreen instance

        self.init_ui()
        asyncio.ensure_future(self.preload_case_data())

    def init_ui(self):
        self.stacked_layout = QStackedLayout()

        self.start_screen = self.create_start_screen()
        self.game_description_screen = self.create_game_description_screen()
        self.trial_screen = self.create_trial_screen()
        self.result_screen = self.create_result_screen()

        self.stacked_layout.addWidget(self.start_screen)
        self.stacked_layout.addWidget(self.game_description_screen)
        self.stacked_layout.addWidget(self.trial_screen)
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
        # CaseDataManager._evidences = None # Kept as in original, assuming external relevance
        # CaseDataManager._case_data = None # Kept as in original

        try:
            print("Preloading case data...")
            self.case_summary_data = await CaseDataManager.generate_case_stream(callback=dummy_callback)
            self.profiles_data = await CaseDataManager.generate_profiles_stream(callback=dummy_callback)
            print("Case data preloaded.")
            self._update_start_button("시작하기", True)
        except Exception as e:
            print(f"Error preloading case data: {e}")
            self._update_start_button("데이터 로드 실패 (재시도)", False) # Button remains disabled

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

        subtitle = QLabel("당신의 논리, 상대의 허점,\nAI가 지켜보는 심문의 무대!\n이 법정, 지성의 승부처")
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

        self.start_button_on_start_screen = QPushButton() # Text and enabled state set by _update_start_button
        self.start_button_on_start_screen.setStyleSheet(
            f"background-color: {PRIMARY_BLUE}; color: {WHITE_TEXT}; font-size: 20px; "
            f"border-radius: 10px; padding: 15px 25px; border: 1px solid #0056b3;"
        )
        self.start_button_on_start_screen.setFixedHeight(60)
        self._update_start_button("데이터 로딩 중...", False) # Initial state
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

    def create_game_description_screen(self):
        screen = QWidget()
        screen.setStyleSheet(f"background-color: {DARK_BG_COLOR};")
        layout = QHBoxLayout()
        layout.setContentsMargins(50, 30, 50, 30)
        layout.setSpacing(40)

        left_panel_layout = QVBoxLayout()
        label_title = QLabel("게임설명")
        label_title.setStyleSheet(
            f"color: {GOLD_ACCENT}; font-size: 28px; font-weight: bold; "
            f"padding-bottom: 10px; border-bottom: 2px solid {GOLD_ACCENT};"
        )
        label_title.setAlignment(Qt.AlignLeft)

        description_text = (
            "LogiCourt AI에 오신 것을 환영합니다!\n\n"
            "본 게임은 AI가 생성한 가상의 사건을 바탕으로 진행되는 토론 및 추리 게임입니다.\n\n"
            "1. 사건 개요 확인: '시작하기'를 누르면 AI가 생성한 사건의 개요와 등장인물 정보가 순차적으로 제공됩니다.\n"
            "2. 역할 배정 (가상): 플레이어들은 각각 변호사와 검사의 역할을 맡게 됩니다 (실제 게임에서는 역할 분담 후 토론).\n"
            "3. 자유 토론: 제공된 정보를 바탕으로 플레이어 간 자유롭게 토론하며 사건의 진실을 파헤치거나, 자신의 주장을 관철시키세요.\n"
            "4. 증거 제출 및 반박: (구현 예정) 게임 중 추가 증거를 요청하거나 상대방의 주장을 반박할 수 있습니다.\n"
            "5. AI 판결: 토론이 종료되면 '판결 화면으로 이동' 버튼을 눌러 AI 판사의 판결 및 사건의 숨겨진 진실을 확인합니다.\n\n"
            "승리 조건: 상대방의 논리적 허점을 찾아내고, AI 판사 또는 청중(가상)을 설득하여 자신의 주장이 옳았음을 증명하는 것입니다.\n\n"
            "팁: 등장인물의 관계, 알리바이, 숨겨진 동기 등을 주의 깊게 살펴보세요!"
        )
        description_label = QLabel(description_text)
        description_label.setStyleSheet(f"color: {WHITE_TEXT}; font-size: 16px; line-height: 1.6;")
        description_label.setAlignment(Qt.AlignTop | Qt.AlignLeft)
        description_label.setWordWrap(True)

        left_panel_layout.addWidget(label_title)
        left_panel_layout.addSpacing(20)
        left_panel_layout.addWidget(description_label)
        left_panel_layout.addStretch(1)

        right_panel_layout = QVBoxLayout()
        image_label = ResizableImage(_get_image_path("stand.png"), width_limit=400)
        image_label.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Expanding)

        back_btn = QPushButton("← 돌아가기")
        back_btn.setStyleSheet(
            f"background-color: {PRIMARY_BLUE}; color: {WHITE_TEXT}; font-size: 16px; "
            f"border-radius: 8px; padding: 10px 15px;"
        )
        back_btn.setFixedSize(150, 40)
        back_btn.clicked.connect(lambda: self.stacked_layout.setCurrentWidget(self.start_screen))

        top_btn_layout = QHBoxLayout()
        top_btn_layout.addStretch(1)
        top_btn_layout.addWidget(back_btn)

        right_panel_layout.addLayout(top_btn_layout)
        right_panel_layout.addSpacing(20)
        right_panel_layout.addWidget(image_label, 1)
        right_panel_layout.addStretch(0)

        layout.addLayout(left_panel_layout, 2)
        layout.addLayout(right_panel_layout, 1)
        screen.setLayout(layout)
        return screen

    def show_game_description(self):
        self.stacked_layout.setCurrentWidget(self.game_description_screen)

    def enter_text_mode(self):
        print("텍스트모드 버튼 클릭됨 (현재 미구현 상태)")

    def start_intro_sequence(self):
        if not self.case_summary_data or not self.profiles_data:
            print("Case data not loaded yet. Please wait or check for errors.")
            asyncio.ensure_future(self.preload_case_data()) # Try preloading again
            return

        # Remove existing intro screen if any
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
        self.trial_content_display.setPlainText(
            f"[사건 개요]\n{self.case_summary_data.strip()}\n\n"
            f"[등장인물]\n{self.profiles_data.strip()}\n\n"
            "--- 모든 정보 확인 완료 ---\n토론을 시작하거나 AI 판결을 요청할 수 있습니다."
        )
        self.stacked_layout.setCurrentWidget(self.trial_screen)
        
        if self.intro_screen_instance:
            # The instance might have already been removed if start_intro_sequence is called rapidly,
            # but setCurrentWidget would have made it the current one.
            # Check if it's still in the layout before removing, though deleteLater is safe.
            if self.stacked_layout.indexOf(self.intro_screen_instance) != -1:
                 self.stacked_layout.removeWidget(self.intro_screen_instance)
            self.intro_screen_instance.deleteLater()
            self.intro_screen_instance = None


    def create_trial_screen(self):
        screen = QWidget()
        layout = QHBoxLayout()
        layout.setContentsMargins(0,0,0,0)
        layout.setSpacing(0)

        self.trial_content_display = QTextEdit()
        self.trial_content_display.setReadOnly(True)
        self.trial_content_display.setStyleSheet(
            f"background-color: {DARK_BG_COLOR}; color: {WHITE_TEXT}; font-size: 15px; "
            "padding: 15px; border: none;"
        )
        self.trial_content_display.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.trial_content_display.setPlaceholderText("사건 정보가 여기에 표시됩니다...")

        right_frame = QFrame()
        right_frame.setStyleSheet(f"background-color: {DARK_BG_COLOR}; border-left: 1px solid #444;")
        right_frame.setFixedWidth(300)
        right_layout = QVBoxLayout()
        right_layout.setContentsMargins(20, 20, 20, 20)
        right_layout.setSpacing(15)

        trial_info_label = QLabel("재판 진행 화면")
        trial_info_label.setStyleSheet(f"color: {LIGHT_GRAY_TEXT}; font-size: 18px; font-weight: bold;")
        trial_info_label.setAlignment(Qt.AlignCenter)

        to_result_button = QPushButton("판결 화면으로 이동")
        to_result_button.setStyleSheet(
            f"background-color: {GREEN_BTN_COLOR}; color: {WHITE_TEXT}; font-size: 16px; "
            "border-radius: 8px; padding: 12px;"
        )
        to_result_button.setFixedHeight(50)
        to_result_button.clicked.connect(lambda: asyncio.ensure_future(self.show_judgement()))

        right_layout.addWidget(trial_info_label)
        right_layout.addStretch(1)
        right_layout.addWidget(to_result_button)
        right_frame.setLayout(right_layout)
        
        layout.addWidget(self.trial_content_display, 3)
        layout.addWidget(right_frame, 1)
        screen.setLayout(layout)
        return screen

    def show_prosecutor_screen(self):
       if self.intro_screen_instance:
        if self.stacked_layout.indexOf(self.intro_screen_instance) != -1:
            self.stacked_layout.removeWidget(self.intro_screen_instance)
        self.intro_screen_instance.deleteLater()
        self.intro_screen_instance = None
    
        # Create the prosecutor screen
        self.prosecutor_screen = ProsecutorScreen(
            case_summary=self.case_summary_data,
            profiles=self.profiles_data,
            on_next=self.show_lawyer_screen
        )
    
        # Add it to the stacked layout and show it
        self.stacked_layout.addWidget(self.prosecutor_screen)
        self.stacked_layout.setCurrentWidget(self.prosecutor_screen)

    def show_lawyer_screen(self):
        # Create the lawyer screen
        self.lawyer_screen = LawyerScreen(
            case_summary=self.case_summary_data,
            profiles=self.profiles_data,
            on_next=lambda: asyncio.ensure_future(self.show_judgement())
        )
        
        # Add it to the stacked layout and show it
        self.stacked_layout.addWidget(self.lawyer_screen)
        self.stacked_layout.setCurrentWidget(self.lawyer_screen)
        
        # Clean up the prosecutor screen if needed
        if hasattr(self, 'prosecutor_screen'):
            self.stacked_layout.removeWidget(self.prosecutor_screen)
            self.prosecutor_screen.deleteLater()

    def create_result_screen(self):
            screen = QWidget()
            layout = QHBoxLayout()
            layout.setContentsMargins(0,0,0,0)
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
            label_ai_judge.setStyleSheet(
                f"background-color: {PRIMARY_BLUE}; {COMMON_PANEL_LABEL_STYLE}" 
                # Overriding parts of common style if necessary, e.g. font-size or padding if different
                # For this case, COMMON_PANEL_LABEL_STYLE has font-size 22px which matches.
            )
            label_ai_judge.setAlignment(Qt.AlignCenter)
                
            self.result_image_label = ResizableImage(_get_image_path("judge.png"))
            self.result_image_label.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

            retry_button = QPushButton("처음으로")
            retry_button.setStyleSheet(
                f"background-color: {PRIMARY_BLUE}; color: {WHITE_TEXT}; font-size: 18px; "
                "border-radius: 8px; padding: 12px;"
            )
            retry_button.setFixedHeight(50)
            retry_button.clicked.connect(lambda: asyncio.ensure_future(self.restart_game_flow()))

            right_layout.addWidget(label_ai_judge, 0, Qt.AlignTop | Qt.AlignHCenter)
            right_layout.addSpacing(20)
            right_layout.addWidget(self.result_image_label, 1)
            right_layout.addSpacing(20)
            right_layout.addWidget(retry_button, 0, Qt.AlignBottom)
            right_frame.setLayout(right_layout)

            layout.addWidget(self.result_text_display, 2)
            layout.addWidget(right_frame, 1)
            screen.setLayout(layout)
            return screen

    async def show_judgement(self):
        self.stacked_layout.setCurrentWidget(self.result_screen)
        self.result_text_display.setPlainText("AI 판사의 판결을 생성 중입니다...")
        await asyncio.sleep(0.1) 

        if not self.case_summary_data or not self.profiles_data:
            self.result_text_display.setPlainText("⚠️ 사건 정보를 불러오지 못했습니다. 게임을 다시 시작해주세요.")
            return

        try:
            full_case_context = f"[사건 개요]\n{self.case_summary_data.strip()}\n\n[등장인물 정보]\n{self.profiles_data.strip()}"
            
            current_full_result_text = "🧑‍⚖️ AI 판결 요약:\n"
            self.result_text_display.setPlainText(current_full_result_text + "...")
            QApplication.processEvents()

            # --- Get Judgement Summary (Synchronous as per original) ---
            # The original get_judge_result_wrapper is synchronous.
            # If it were async and streamable, the callback logic would be used here too.
            judgement_summary_result = get_judge_result_wrapper(
                [{"role": "system", "content": "다음 사건의 판결을 내려주세요."},
                 {"role": "user", "content": full_case_context}] 
            )
            
            current_full_result_text += judgement_summary_result.strip() + "\n\n🕵️ 사건의 진실:\n"
            self.result_text_display.setPlainText(current_full_result_text + "...")
            QApplication.processEvents()

            # --- Get Case Behind Story (Truth - Streaming) ---
            temp_accumulated_behind = "" # Will be updated by callback

            def update_ui_case_behind_callback(chunk, accumulated_text):
                nonlocal temp_accumulated_behind # Required if modifying outer scope var not part of a class
                temp_accumulated_behind = accumulated_text
                self.result_text_display.setPlainText(current_full_result_text + temp_accumulated_behind + "▌")
                QApplication.processEvents()
            
            await CaseDataManager.generate_case_behind(callback=update_ui_case_behind_callback)
            # temp_accumulated_behind now holds the full streamed text for case_behind

            final_text = current_full_result_text + temp_accumulated_behind.strip()
            self.result_text_display.setPlainText(final_text)

        except Exception as e:
            print(f"판결 생성 오류: {e}")
            self.result_text_display.setPlainText(f"⚠️ 판결 생성에 실패했습니다: {e}")


    async def restart_game_flow(self):
        self.case_summary_data = ""
        self.profiles_data = ""
        
        self._update_start_button("데이터 로딩 중...", False)

        self.stacked_layout.setCurrentWidget(self.start_screen)
        
        if hasattr(self, 'trial_content_display'):
            self.trial_content_display.clear()
        if hasattr(self, 'result_text_display'):
            self.result_text_display.clear()

        await self.preload_case_data()


if __name__ == "__main__":
    current_dir = os.path.dirname(__file__)
    image_dir = os.path.join(current_dir, "image")
    os.makedirs(image_dir, exist_ok=True)

    dummy_images = ["logo.png", "stand.png", "judge.png"]
    try:
        from PIL import Image # PIL import is localized here
        pillow_available = True
    except ImportError:
        pillow_available = False
        print("Pillow not installed. Cannot create dummy images. Please create them manually or install Pillow.")

    if pillow_available:
        for img_name in dummy_images:
            path = os.path.join(image_dir, img_name)
            if not os.path.exists(path):
                try:
                    dummy_img = Image.new('RGB', (10, 10), color = 'red')
                    dummy_img.save(path)
                    print(f"Created dummy image: {path}")
                except Exception as e:
                    print(f"Error creating dummy image {img_name}: {e}")

    from qasync import QEventLoop 
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