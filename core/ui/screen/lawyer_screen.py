from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QPushButton, QHBoxLayout,
    QSizePolicy, QMessageBox, QGridLayout
)
from PyQt5.QtCore import Qt
# from PyQt5.QtGui import QIcon, QPixmap # Not directly needed if using common components

from ..resizable_image import ResizableImage, _get_image_path, _get_profile_image_path
from ..style_constants import DARK_BG_COLOR, WHITE_TEXT
# Removed: from core.game_controller import GameController (instance will be passed)
# Import common components
from .common_components import (
    HoverButton, MicButton, extract_name_and_role,
    show_case_dialog_common, show_evidences_common, show_full_profiles_dialog_common
)
import re


class LawyerScreen(QWidget):
    def __init__(self, game_controller,
                 on_switch_to_prosecutor, on_request_judgement, on_interrogate,
                 case_summary_text="", profiles_data_list=None, evidences_data_list=None):
        super().__init__()
        self.game_controller = game_controller
        self.on_switch_to_prosecutor = on_switch_to_prosecutor
        self.on_request_judgement = on_request_judgement
        self.on_interrogate = on_interrogate

        # Data passed from MainWindow
        self.case_summary = case_summary_text
        self.profiles_list = profiles_data_list if profiles_data_list is not None else []
        self.evidences_list = evidences_data_list if evidences_data_list is not None else []
        
        self.mic_on = False # Local state for icon, actual recording state by GC
        self.init_ui()

    def init_ui(self):
        self.setStyleSheet(f"background-color: {DARK_BG_COLOR}; color: {WHITE_TEXT};")

        title_label = QLabel("변호사 변론")
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
        menu_layout.addWidget(make_button("텍스트입력", self.show_text_input_placeholder))
        menu_layout.addWidget(make_button("➤ 심문하기", self.handle_interrogate))
        menu_layout.addStretch()

        # Generate summary text for profile button from passed profiles_list
        summary_lines = ["등장인물"]
        type_map = {"defendant": "피고", "victim": "피해자", "witness": "목격자", "reference": "참고인"}
        if self.profiles_list:
            for p_info in self.profiles_list:
                name = p_info.get('name', 'N/A')
                role_key = p_info.get('type', 'N/A')
                role = type_map.get(role_key, role_key)
                # Construct a title line similar to how extract_name_and_role expects if needed elsewhere
                # For button, just name and role is fine.
                summary_lines.append(f"• {name} : {role}")
        summary_text_for_btn = "\n".join(summary_lines)

        profile_button = HoverButton(summary_text_for_btn, min_height=100, max_height=130)
        profile_button.clicked.connect(self.show_full_profiles_dialog)

        self.btn_mic = MicButton("mike.png", "mike_on.png")
        self.btn_mic.clicked.connect(self.toggle_mic_action) # Connect to action

        # --- Action Buttons ---
        self.btn_to_prosecutor = QPushButton("검사측 주장으로")
        self.btn_to_prosecutor.setFixedSize(250, 80)
        self.btn_to_prosecutor.setStyleSheet("""
            QPushButton { background-color: #2f5a68; color: white; border-radius: 12px; font-size: 22px; font-weight: bold; }
            QPushButton:hover { font-size: 24px; }
        """)
        self.btn_to_prosecutor.clicked.connect(self.handle_switch_to_prosecutor)

        self.btn_req_judgement = QPushButton("판결 요청")
        self.btn_req_judgement.setFixedSize(250, 80)
        self.btn_req_judgement.setStyleSheet("""
            QPushButton { background-color: #28a745; color: white; border-radius: 12px; font-size: 22px; font-weight: bold; }
            QPushButton:hover { font-size: 24px; }
        """)
        self.btn_req_judgement.clicked.connect(self.handle_request_judgement)

        action_buttons_layout = QHBoxLayout()
        action_buttons_layout.addStretch()
        action_buttons_layout.addWidget(self.btn_to_prosecutor)
        action_buttons_layout.addStretch()
        action_buttons_layout.addWidget(self.btn_req_judgement)
        action_buttons_layout.addStretch()

        # --- Right Panel (Controls are on the right for Lawyer) ---
        right_panel_grid = QGridLayout()
        right_panel_grid.setSpacing(20)
        right_panel_grid.addLayout(menu_layout, 0, 0)
        right_panel_grid.addWidget(profile_button, 0, 1)
        right_panel_grid.addWidget(self.btn_mic, 1, 0, 1, 2, alignment=Qt.AlignCenter)

        right_wrapper = QVBoxLayout()
        right_wrapper.setContentsMargins(40, 30, 20, 30)
        right_wrapper.setSpacing(20)
        right_wrapper.addLayout(title_wrapper)
        right_wrapper.addStretch(1)
        right_wrapper.addLayout(right_panel_grid)
        right_wrapper.addSpacing(20)
        right_wrapper.addLayout(action_buttons_layout)
        right_wrapper.addStretch(2)

        # --- Left Panel (Image is on the left for Lawyer) ---
        image_label = ResizableImage(_get_profile_image_path, "lawyer.png") # Pass func and filename
        image_label.setMaximumWidth(420)
        image_label.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

        left_image_layout = QVBoxLayout()
        left_image_layout.addStretch()
        left_image_layout.addWidget(image_label, alignment=Qt.AlignLeft)
        left_image_layout.addStretch()

        main_layout = QHBoxLayout(self) # Set main layout for self
        main_layout.setContentsMargins(60, 30, 40, 30)
        main_layout.setSpacing(30)
        main_layout.addLayout(left_image_layout, 2)
        main_layout.addLayout(right_wrapper, 3)

    def set_mic_button_state(self, is_on):
        """Called by MainWindow based on record_start/stop signals"""
        self.mic_on = is_on
        self.btn_mic.set_icon_on(self.mic_on)

    def toggle_mic_action(self):
        if self.game_controller:
            if not self.mic_on: # If mic is currently off, tell GC to start
                self.game_controller.record_start()
            else: # If mic is currently on, tell GC to stop
                self.game_controller.record_end()
        # The icon state (self.mic_on) will be updated via signal from GC -> MainWindow -> self.set_mic_button_state

    def handle_switch_to_prosecutor(self):
        if self.on_switch_to_prosecutor:
            self.on_switch_to_prosecutor()

    def handle_request_judgement(self):
        # UI informs controller, controller will eventually send signal for verdict
        if self.game_controller:
            self.game_controller.user_input("판결을 요청합니다.") # Or a more specific method
            # self.game_controller.done() # If this is the final action before judgement
        if self.on_request_judgement: # This callback likely triggers MainWindow to switch to ResultScreen
            self.on_request_judgement()


    def handle_interrogate(self):
        # This callback will likely trigger MainWindow to switch to InterrogationScreen
        # The specific character to interrogate might be chosen via a dialog here
        # For now, let's assume MainWindow handles the switch and potential character selection UI.
        # Or, the on_interrogate callback in MainWindow could pop up a character selection dialog.
        if self.on_interrogate:
             # The on_interrogate callback in MainWindow will handle showing a dialog to pick character
             # and then switching to InterrogationScreen
            self.on_interrogate()


    def show_case_dialog(self):
        show_case_dialog_common(self, self.case_summary)

    def show_evidences(self):
        show_evidences_common(self, self.evidences_list, attorney_first=True)

    def show_text_input_placeholder(self):
        # Eventually, this would allow typing arguments.
        # For now, it might just send a generic statement or do nothing.
        # text, ok = QInputDialog.getText(self, "변론 입력", "주장할 내용을 입력하세요:")
        # if ok and text and self.game_controller:
        #     self.game_controller.user_input(text)
        QMessageBox.information(self, "텍스트입력", "변호사측 텍스트 입력 기능은 구현 중입니다.", QMessageBox.Ok)


    def show_full_profiles_dialog(self):
        show_full_profiles_dialog_common(self, self.profiles_list)