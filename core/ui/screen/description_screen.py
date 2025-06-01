from PyQt5.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton
from PyQt5.QtGui import QPixmap # QPixmap을 직접 사용하기 위해 import
from PyQt5.QtCore import Qt
# from ui.resizable_image import ResizableImage, _get_image_path # 이 줄은 주석 처리 또는 삭제
from ui.style_constants import (
    DARK_BG_COLOR, GOLD_ACCENT, WHITE_TEXT, PRIMARY_BLUE
)
# import os # 현재 이 방식에서는 os 모듈이 직접적으로 필요하지 않을 수 있습니다.

class GameDescriptionScreen(QWidget):
    def __init__(self, on_back_callback, game_controller=None): # Added game_controller (optional for this screen)
        super().__init__()
        self.on_back_callback = on_back_callback
        self.game_controller = game_controller # Though not strictly needed here
        self.init_ui()

    def init_ui(self):
        self.setStyleSheet(f"background-color: {DARK_BG_COLOR};")
        layout = QHBoxLayout()
        layout.setContentsMargins(50, 30, 50, 30)
        layout.setSpacing(40)

        # 왼쪽 텍스트 영역
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
            "2. 역할 배정 (가상): 플레이어들은 각각 변호사와 검사의 역할을 맡게 됩니다.\n"
            "3. 자유 토론: 제공된 정보를 바탕으로 토론하며 사건의 진실을 파헤치세요.\n"
            "4. 증거 제출 및 반박: (예정) 추가 증거 제시와 반론 기능이 구현됩니다.\n"
            "5. AI 판결: 토론 후 AI 판사의 판결과 사건의 진실을 확인합니다.\n\n"
            "승리 조건: 상대방의 논리적 허점을 찾아내고, AI 또는 청중을 설득하는 것입니다.\n\n"
            "팁: 등장인물의 관계, 알리바이, 숨겨진 동기를 주의 깊게 살펴보세요!"
        )

        description_label = QLabel(description_text)
        description_label.setStyleSheet(f"color: {WHITE_TEXT}; font-size: 16px; line-height: 1.6;")
        description_label.setAlignment(Qt.AlignTop | Qt.AlignLeft)
        description_label.setWordWrap(True)

        left_panel_layout.addWidget(label_title)
        left_panel_layout.addSpacing(20)
        left_panel_layout.addWidget(description_label)
        left_panel_layout.addStretch(1)

        # 오른쪽 이미지 영역
        right_panel_layout = QVBoxLayout()
        
        # --- 이미지 경로를 직접 문자열로 지정하고 표준 QLabel 사용으로 변경 ---
        image_path_string = "core/assets/stand.png" # 경로 문자열 직접 사용

        image_pixmap = QPixmap(image_path_string)
        image_label = QLabel() # 표준 QLabel 사용

        if image_pixmap.isNull():
            print(f"오류: 이미지를 불러올 수 없습니다 - {image_path_string}")
            # 디버깅을 위해 현재 작업 디렉토리 출력 (필요시 주석 해제)
            # import os
            # print(f"현재 작업 디렉토리: {os.getcwd()}")
            image_label.setText("이미지 로드 실패\n(stand.png)") # os.path.basename 사용 안 함
        else:
            # 이미지를 QLabel 너비 400에 맞춰 비율 유지하며 스케일링
            # 이 코드는 UI 초기화 시 한 번만 실행됩니다.
            width_limit = 400
            scaled_pixmap = image_pixmap.scaledToWidth(width_limit, Qt.SmoothTransformation)
            image_label.setPixmap(scaled_pixmap)
        
        image_label.setAlignment(Qt.AlignCenter)
        # --- 이미지 처리 수정 완료 ---


        back_btn = QPushButton("\u2190 돌아가기")
        back_btn.setStyleSheet(
            f"background-color: {PRIMARY_BLUE}; color: {WHITE_TEXT}; font-size: 16px; "
            f"border-radius: 8px; padding: 10px 15px;"
        )
        back_btn.setFixedSize(150, 40)
        back_btn.clicked.connect(self.on_back_callback)

        top_btn_layout = QHBoxLayout()
        top_btn_layout.addStretch(1)
        top_btn_layout.addWidget(back_btn)

        right_panel_layout.addLayout(top_btn_layout)
        right_panel_layout.addSpacing(20)
        right_panel_layout.addWidget(image_label, 1)
        right_panel_layout.addStretch(0) # Adjusted stretch

        layout.addLayout(left_panel_layout, 2)
        layout.addLayout(right_panel_layout, 1)
        self.setLayout(layout)