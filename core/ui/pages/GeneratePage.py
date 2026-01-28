import sys
import os
from PyQt5.QtWidgets import QWidget
from PyQt5 import uic
import asyncio


class GeneratePage(QWidget):
    """사건 생성 페이지 - QWidget 기반"""

    def __init__(self, uiController, case_outline, parent=None):
        super().__init__(parent)
        self.uc = uiController
        self.case_outline = case_outline

        # UI 파일 로드
        ui_path = os.path.join(os.path.dirname(__file__), '..', 'qt_designer', 'generateWindow.ui')
        uic.loadUi(ui_path, self)
        self.backButton.setEnabled(False)

        self._setup_ui()
        self._setup_connections()

    def _setup_ui(self):
        """UI 초기 설정"""
        from data_models import Case
        from ui.tools import Typewriter

        # QTextEdit에 QSS 적용 (strong, b 태그에 나눔고딕 ExtraBold 적용)
        self.overviewText.document().setDefaultStyleSheet("""
            strong { font-family: "나눔고딕 ExtraBold"; }
            b { font-family: "나눔고딕 ExtraBold"; }
        """)

        self.typewriter = Typewriter(update_fn=self.overviewText.setHtml, html_mode=True)
        self.typewriter.enqueue(self.case_outline)

    def _setup_connections(self):
        """버튼 연결 설정"""
        self.backButton.clicked.connect(self._on_forward_clicked)

    def _on_forward_clicked(self):
        """앞으로 버튼 클릭 - 다음 단계로 진행"""
        self.uc.switch_to_prosecutor_page()

    def update_overview_text(self, text):
        """사건 개요 텍스트 업데이트 (typewriter용)"""
        self.overviewText.setHtml(text)

    def update_case_outline(self, new_outline):
        """새로운 사건 개요로 업데이트"""
        self.case_outline = new_outline
        self.typewriter.enqueue(new_outline)

    def resizeEvent(self, event):
        """화면 크기 변경 시 위젯들을 반응형으로 재배치"""
        super().resizeEvent(event)
        w = self.width()
        h = self.height()

        # 기준 크기 (원본 디자인)
        base_w = 1280
        base_h = 720

        # 비율 계산
        ratio_w = w / base_w
        ratio_h = h / base_h

        # 상단 여백
        top_margin = int(40 * ratio_h)
        side_margin = int(30 * ratio_w)

        # 상단 라벨 높이
        label_h = int(71 * ratio_h)

        # 앞으로 버튼 크기
        btn_size = int(71 * min(ratio_w, ratio_h))

        # 상단 라벨 (왼쪽 여백 ~ 오른쪽 버튼 전까지)
        label_w = w - side_margin * 2 - btn_size - int(50 * ratio_w)
        self.caseGenerateLabel.setGeometry(
            side_margin + int(110 * ratio_w),
            top_margin,
            label_w,
            label_h
        )

        # 앞으로 버튼 (오른쪽 상단)
        self.backButton.setGeometry(
            w - btn_size - side_margin,
            top_margin,
            btn_size,
            btn_size
        )

        # 메인 컨텐츠 영역 (배경 + 텍스트 + 이미지)
        content_y = top_margin + label_h + int(49 * ratio_h)
        content_h = h - content_y - side_margin
        content_w = w - side_margin * 2

        # 배경 이미지
        self.backgroundImage.setGeometry(side_margin, content_y, content_w, content_h)

        # 프로필 이미지 (중앙)
        profile_w = int(521 * ratio_w)
        profile_h = int(511 * ratio_h)
        profile_x = (w - profile_w) // 2
        profile_y = content_y + int((content_h - profile_h) // 2)
        self.profileImage.setGeometry(profile_x, profile_y, profile_w, profile_h)

        # 텍스트 영역 (배경과 같은 크기)
        self.overviewText.setGeometry(side_margin, content_y, content_w, content_h)
