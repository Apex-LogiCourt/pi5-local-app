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
