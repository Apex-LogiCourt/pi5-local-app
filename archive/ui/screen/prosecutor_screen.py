from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QPushButton, QHBoxLayout,
    QSizePolicy, QMessageBox, QGridLayout,QInputDialog
)
from PyQt5.QtCore import Qt
# from PyQt5.QtGui import QIcon, QPixmap # Not directly needed

from ui.resizable_image import ResizableImage, _get_profile_image_path, _get_image_path
from ui.style_constants import DARK_BG_COLOR, WHITE_TEXT
# Removed: from core.game_controller import GameController
# Import common components
from ui.common_components import (
    HoverButton, MicButton, extract_name_and_role,
    show_case_dialog_common, show_evidences_common, show_full_profiles_dialog_common
)
import re, asyncio
from qasync import asyncSlot


class ProsecutorScreen(QWidget):
    def __init__(self, game_controller,
                 on_switch_to_lawyer, on_request_judgement, on_interrogate,
                 case_summary_text="", profiles_data_list=None, evidences_data_list=None):
        super().__init__()
        self.game_controller = game_controller
        self.on_switch_to_lawyer = on_switch_to_lawyer
        self.on_request_judgement = on_request_judgement
        self.on_interrogate = on_interrogate

        self.case_summary = case_summary_text
        self.profiles_list = profiles_data_list if profiles_data_list is not None else []
        self.evidences_list = evidences_data_list if evidences_data_list is not None else []
        
        self.mic_on = False # Local state for icon
        self.init_ui()

    def init_ui(self):
        self.setStyleSheet(f"background-color: {DARK_BG_COLOR}; color: {WHITE_TEXT};")

        title_label = QLabel("검사 주장")
        title_label.setAlignment(Qt.AlignCenter)
        title_label.setStyleSheet("""
            background-color: black; color: white; font-size: 40px;
            font-weight: bold; padding: 10px; border-radius: 6px;
        """)
        title_label.setFixedWidth(260)

        title_wrapper = QHBoxLayout()
        title_wrapper.addStretch(1)
        title_wrapper.addWidget(title_label)
        title_wrapper.addStretch(1)

        def make_button(text, handler=None):
            btn = HoverButton(text)
            if handler:
                btn.clicked.connect(handler)
            return btn

        menu_layout = QVBoxLayout()
        menu_layout.setSpacing(15)
        menu_layout.addWidget(make_button("사건개요", self.show_case_dialog))
        menu_layout.addWidget(make_button("증거품 확인", self.show_evidences))
        menu_layout.addWidget(make_button("텍스트입력", self.show_text_input_dialog))

        menu_layout.addWidget(make_button("➤ 심문하기", self.handle_interrogate))
        menu_layout.addStretch()

        summary_lines = ["등장인물"]
        type_map = {"defendant": "피고", "victim": "피해자", "witness": "목격자", "reference": "참고인"}
        if self.profiles_list:
            for p_info in self.profiles_list:
                name = p_info.get('name', 'N/A')
                role_key = p_info.get('type', 'N/A')
                role = type_map.get(role_key, role_key)
                summary_lines.append(f"• {name} : {role}")
        summary_text_for_btn = "\n".join(summary_lines)


        profile_button = HoverButton(summary_text_for_btn, min_height=100, max_height=130)
        profile_button.clicked.connect(self.show_full_profiles_dialog)

        self.btn_mic = MicButton("mike.png", "mike_on.png")
        self.btn_mic.clicked.connect(self.toggle_mic_action)

        self.btn_to_lawyer = QPushButton("변호사 변론으로")
        self.btn_to_lawyer.setFixedSize(250, 80)
        self.btn_to_lawyer.setStyleSheet("""
            QPushButton { background-color: #2f5a68; color: white; border-radius: 12px; font-size: 22px; font-weight: bold; }
            QPushButton:hover { font-size: 24px; }
        """)
        self.btn_to_lawyer.clicked.connect(self.handle_switch_to_lawyer)

        self.btn_req_judgement = QPushButton("판결 요청")
        self.btn_req_judgement.setFixedSize(250, 80)
        self.btn_req_judgement.setStyleSheet("""
            QPushButton { background-color: #28a745; color: white; border-radius: 12px; font-size: 22px; font-weight: bold; }
            QPushButton:hover { font-size: 24px; }
        """)
        self.btn_req_judgement.clicked.connect(self.handle_request_judgement)

        action_buttons_layout = QHBoxLayout()
        action_buttons_layout.addStretch()
        action_buttons_layout.addWidget(self.btn_to_lawyer)
        action_buttons_layout.addStretch()
        action_buttons_layout.addWidget(self.btn_req_judgement)
        action_buttons_layout.addStretch()

        left_panel_grid = QGridLayout()
        left_panel_grid.setSpacing(20)
        left_panel_grid.addLayout(menu_layout, 0, 0)
        left_panel_grid.addWidget(profile_button, 0, 1)
        left_panel_grid.addWidget(self.btn_mic, 1, 0, 1, 2, alignment=Qt.AlignCenter)

        left_wrapper = QVBoxLayout()
        left_wrapper.setContentsMargins(40, 30, 20, 30)
        left_wrapper.setSpacing(20)
        left_wrapper.addLayout(title_wrapper)
        left_wrapper.addStretch(1)
        left_wrapper.addLayout(left_panel_grid)
        left_wrapper.addSpacing(20)
        left_wrapper.addLayout(action_buttons_layout)
        left_wrapper.addStretch(2)

        image_label = ResizableImage(_get_profile_image_path, "Prosecutor.png")
        image_label.setMaximumWidth(420)
        image_label.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

        right_image_layout = QVBoxLayout()
        right_image_layout.addStretch()
        right_image_layout.addWidget(image_label, alignment=Qt.AlignRight)
        right_image_layout.addStretch()

        main_layout = QHBoxLayout(self) # Set main layout for self
        main_layout.setContentsMargins(40, 30, 60, 30)
        main_layout.setSpacing(30)
        main_layout.addLayout(left_wrapper, 3)
        main_layout.addLayout(right_image_layout, 2)


    def set_mic_button_state(self, is_on):
        """Called by MainWindow based on record_start/stop signals"""
        self.mic_on = is_on
        self.btn_mic.set_icon_on(self.mic_on)

    def toggle_mic_action(self):
        print("Mic 버튼 클릭됨")

        if self.game_controller:
            print("game_controller 연결됨 → mic_on =", self.mic_on)

            if not self.mic_on:
                asyncio.create_task(self.game_controller.record_start())
            else:
                asyncio.create_task(self.game_controller.record_end())
        else:
            print("❌ game_controller 없음")

        # 버튼 상태 토글 (누락되었을 수 있으므로 추가)
        self.mic_on = not self.mic_on
        self.btn_mic.set_icon_on(self.mic_on)

    def handle_switch_to_lawyer(self):
        if self.on_switch_to_lawyer:
            self.on_switch_to_lawyer()

    def handle_request_judgement(self):
        if self.game_controller:
            self.game_controller.user_input("판결을 요청합니다.") # Or a more specific method
            # self.game_controller.done()
        if self.on_request_judgement:
            self.on_request_judgement()

    def handle_interrogate(self):
        if self.on_interrogate:
            self.on_interrogate() # MainWindow will handle choice + screen switch

    def show_case_dialog(self):
        show_case_dialog_common(self, self.case_summary)

    def show_evidences(self):
        show_evidences_common(self, self.evidences_list, attorney_first=False)

    @asyncSlot()
    async def show_text_input_dialog(self):
        text, ok = QInputDialog.getText(self, "텍스트 입력", "전송할 내용을 입력하세요:")
        if ok and text.strip():
            print(f"🧪 입력됨: {text}")
            if self.game_controller:
                await self.game_controller.user_input(text)
            else:
                print("❌ game_controller 없음")
        else:
            print("⛔ 입력 취소 또는 공백")

    def show_full_profiles_dialog(self):
        show_full_profiles_dialog_common(self, self.profiles_list)