import sys
import os
from PyQt5.QtWidgets import QWidget
from PyQt5 import uic
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QPixmap
import asyncio


class InterrogationPage(QWidget):
    """심문 페이지 - QWidget 기반"""

    def __init__(self, uiController, gameController, profile, parent=None):
        super().__init__(parent)
        self.uc = uiController
        self.gc = gameController
        self.profile = profile
        self.mic_on = False

        # UI 파일 로드
        ui_path = os.path.join(os.path.dirname(__file__), '..', 'qt_designer', 'interrogationWindow.ui')
        uic.loadUi(ui_path, self)

        type_mapping = {
            "witness": "증인",
            "reference": "참고인",
            "defendant": "피고인",
            "victim": "피해자"
        }
        self.type = type_mapping.get(profile.type, "알 수 없음")

        self._setup_ui()
        self._setup_connections()

    def _setup_ui(self):
        """UI 초기 설정"""
        # 기본 텍스트 설정
        self.textLabel.setText("심문을 시작합니다.")
        self.profileTextLabel.setText("")
        self.profileImage.setPixmap(QPixmap(f":/assets/profile/{self.profile.image}"))
        
        # 마이크 초기 상태 설정
        self.micButton.setProperty("mic_state", "off")

    def _setup_connections(self):
        """버튼 연결 설정"""
        self.backButton.clicked.connect(self._go_back)
        self.textButton.clicked.connect(self._open_text_input)
        self.micButton.clicked.connect(self._toggle_mic)

    def evidence_tagged(self):
        """증거 태그 표시"""
        self.smallEvidenceLabel.setVisible(False)
        self.largeEvidenceLabel.setVisible(True)

    def evidence_tag_reset(self):
        """증거 태그 리셋"""
        self.smallEvidenceLabel.setVisible(True)
        self.largeEvidenceLabel.setVisible(False)

    def show_profile(self):
        """프로필 표시"""
        pass

    def update_dialogue(self, message):
        """대화 업데이트"""
        self.textLabel.setText(f"[{self.type}]: {message}")

    def update_profile_text_label(self, message):
        """프로필 텍스트 라벨 업데이트"""
        lbl = self.profileTextLabel
        lbl.setWordWrap(True)
        lbl.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        lbl.setText(f"[{self.type}]: {message}")

        # 텍스트 길어지면 줄바꿈 하는 코드
        fm = lbl.fontMetrics()
        max_width = lbl.contentsRect().width()

        rect = fm.boundingRect(0, 0, max_width, 1000,
                               Qt.TextWordWrap, message)

        lbl.setFixedHeight(rect.height() + 10)

    def set_main_text(self, text):
        """메인 텍스트 설정"""
        self.textLabel.setText(text)

    def _go_back(self):
        """뒤로 가기"""
        self.gc.interrogation_end()
        self.uc.isInterrogation = False
        if self.uc.isTurnProsecutor:
            self.uc.switch_to_prosecutor_page()
        else:
            self.uc.switch_to_lawyer_page()

    def _open_text_input(self):
        """텍스트 입력창 열기"""
        self.uc.open_text_input_window()

    def _toggle_mic(self):
        """마이크 온/오프 토글"""
        self.mic_on = not self.mic_on
        self.micButton.setProperty("mic_state", "on" if self.mic_on else "off")
        self.micButton.style().unpolish(self.micButton)
        self.micButton.style().polish(self.micButton)
        
        if self.gc:
            if self.mic_on:
                asyncio.create_task(self.gc.record_start())
            else:
                asyncio.create_task(self.gc.record_end())

    def _show_evidence(self):
        """증거품 창 표시"""
        if self.uc:
            self.uc.open_evidence_window()

    def set_mic_button_state(self, is_on):
        """마이크 버튼 상태 설정 (외부에서 호출용)"""
        self.mic_on = is_on
        self.micButton.setProperty("mic_state", "on" if is_on else "off")
        self.micButton.style().unpolish(self.micButton)
        self.micButton.style().polish(self.micButton)
