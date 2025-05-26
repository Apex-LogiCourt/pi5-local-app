from PyQt5.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton
from PyQt5.QtCore import Qt

from ui.resizable_image import ResizableImage, _get_image_path
from ui.style_constants import (
    DARK_BG_COLOR, GOLD_ACCENT, WHITE_TEXT, PRIMARY_BLUE
)

class GameDescriptionScreen(QWidget):
    def __init__(self, on_back_callback):
        super().__init__()
        self.on_back_callback = on_back_callback
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
        image_label = ResizableImage(_get_image_path("stand.png"), width_limit=400)

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
        right_panel_layout.addStretch(0)

        layout.addLayout(left_panel_layout, 2)
        layout.addLayout(right_panel_layout, 1)
        self.setLayout(layout)
