from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QSizePolicy, QMessageBox, QGridLayout # QFrame은 사용되지 않아 제거, QMessageBox는 placeholder 메소드에서 사용
)
from PyQt5.QtGui import QPixmap # QPixmap 직접 사용을 위해 import
from PyQt5.QtCore import Qt
# from PyQt5.QtGui import QIcon # QIcon은 MicButton에서 사용되지만, MicButton은 common_components에서 가져옴

# from ui.resizable_image import ResizableImage, _get_profile_image_path, _get_image_path # 이 줄은 제거
from ui.style_constants import DARK_BG_COLOR, WHITE_TEXT
# Removed: from core.game_controller import GameController
# Import common components
from ui.common_components import (
    HoverButton, MicButton, extract_name_and_role, # MicButton은 여기서 경로 수정 안 함
    show_case_dialog_common, show_evidences_common, show_full_profiles_dialog_common
)
import re
# import os # 직접 경로 문자열 사용 시 이 파일에서 os 모듈이 필수는 아님

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
        
        self.mic_on = False
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
        menu_layout.addWidget(make_button("텍스트입력", self.show_text_input_placeholder))
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

        # MicButton의 아이콘 경로는 common_components.py 내의 MicButton 클래스에서 수정 필요
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

        # --- Right Panel (Image is on the right for Prosecutor) ---
        # --- 검사 이미지 로드 방식 변경 ---
        prosecutor_image_path = "core/assets/profile/Prosecutor.png" # 직접 경로 문자열 사용
        
        image_pixmap = QPixmap(prosecutor_image_path)
        image_label = QLabel() # 표준 QLabel 사용

        if image_pixmap.isNull():
            print(f"오류: 검사 이미지를 불러올 수 없습니다 - {prosecutor_image_path}")
            image_label.setText("검사 이미지\n로드 실패")
        else:
            # 원본 ResizableImage는 setMaximumWidth(420)가 있었음
            # QLabel에 이미지를 표시하고 최대 너비를 설정 (비율 유지를 위해 scaled 사용)
            max_width = 420
            if image_pixmap.width() > max_width:
                scaled_pixmap = image_pixmap.scaledToWidth(max_width, Qt.SmoothTransformation)
                image_label.setPixmap(scaled_pixmap)
            else:
                image_label.setPixmap(image_pixmap)
        
        image_label.setMaximumWidth(420) # 최대 너비 제한은 유지
        image_label.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding) # 크기 정책 유지
        image_label.setAlignment(Qt.AlignCenter) # 중앙 정렬 추가 (선택 사항)
        # --- 이미지 처리 수정 완료 ---

        right_image_layout = QVBoxLayout()
        right_image_layout.addStretch()
        right_image_layout.addWidget(image_label, alignment=Qt.AlignRight) # 검사는 오른쪽에 정렬
        right_image_layout.addStretch()

        main_layout = QHBoxLayout(self)
        main_layout.setContentsMargins(40, 30, 60, 30)
        main_layout.setSpacing(30)
        main_layout.addLayout(left_wrapper, 3)
        main_layout.addLayout(right_image_layout, 2)


    def set_mic_button_state(self, is_on):
        self.mic_on = is_on
        self.btn_mic.set_icon_on(self.mic_on) # MicButton의 내부 로직에 따라 아이콘 변경

    def toggle_mic_action(self):
        if self.game_controller:
            if not self.mic_on:
                self.game_controller.record_start()
            else:
                self.game_controller.record_end()

    def handle_switch_to_lawyer(self):
        if self.on_switch_to_lawyer:
            self.on_switch_to_lawyer()

    def handle_request_judgement(self):
        if self.game_controller:
            self.game_controller.user_input("판결을 요청합니다.")
        if self.on_request_judgement:
            self.on_request_judgement()

    def handle_interrogate(self):
        if self.on_interrogate:
            self.on_interrogate()

    def show_case_dialog(self):
        show_case_dialog_common(self, self.case_summary)

    def show_evidences(self):
        show_evidences_common(self, self.evidences_list, attorney_first=False)

    def show_text_input_placeholder(self):
        QMessageBox.information(self, "텍스트입력", "검사측 텍스트 입력 기능은 구현 중입니다.", QMessageBox.Ok)

    def show_full_profiles_dialog(self):
        show_full_profiles_dialog_common(self, self.profiles_list)