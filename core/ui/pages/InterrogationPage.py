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

        # 여백
        margin = int(30 * ratio_w)

        # 뒤로가기 버튼 (오른쪽 상단)
        back_btn_w = int(121 * ratio_w)
        back_btn_h = int(81 * ratio_h)
        self.backButton.setGeometry(w - back_btn_w - margin, margin, back_btn_w, back_btn_h)

        # 배경 이미지 (상단 영역)
        bg_h = int(491 * ratio_h)
        self.backgroundImage.setGeometry(margin, margin, w - margin * 2, bg_h)

        # 프로필 이미지 (중앙)
        profile_w = int(501 * ratio_w)
        profile_h = int(501 * ratio_h)
        profile_x = (w - profile_w) // 2
        profile_y = margin + int(2 * ratio_h)
        self.profileImage.setGeometry(profile_x, profile_y, profile_w, profile_h)

        # 증거 아이콘 (왼쪽 상단)
        small_evidence_size = int(71 * min(ratio_w, ratio_h))
        self.smallEvidenceLabel.setGeometry(margin, margin, small_evidence_size, small_evidence_size)

        large_evidence_size = int(141 * min(ratio_w, ratio_h))
        self.largeEvidenceLabel.setGeometry(margin, margin, large_evidence_size, large_evidence_size)

        # doNotChange 라벨들 (증거 아이콘 코너 처리용)
        corner_size = int(41 * min(ratio_w, ratio_h))
        self.doNotChange_2.setGeometry(margin, margin, corner_size, corner_size)
        self.doNotChange.setGeometry(w - margin - corner_size, margin, corner_size, corner_size)

        # 프로필 텍스트 라벨 (배경 하단)
        profile_text_h = int(91 * ratio_h)
        profile_text_y = margin + bg_h - profile_text_h
        self.profileTextLabel.setGeometry(margin, profile_text_y, w - margin * 2, profile_text_h)

        # 하단 영역 (텍스트 + 버튼들)
        bottom_y = margin + bg_h + int(20 * ratio_h)
        bottom_h = h - bottom_y - margin

        # 텍스트 입력 버튼 (왼쪽 하단)
        text_btn_w = int(161 * ratio_w)
        self.textButton.setGeometry(margin, bottom_y, text_btn_w, bottom_h)

        # 마이크 버튼 (오른쪽 하단)
        mic_btn_w = int(161 * ratio_w)
        self.micButton.setGeometry(w - margin - mic_btn_w, bottom_y, mic_btn_w, bottom_h)

        # 텍스트 라벨 (중앙 하단)
        text_label_x = margin + text_btn_w + int(10 * ratio_w)
        text_label_w = w - text_label_x - mic_btn_w - margin - int(10 * ratio_w)
        self.textLabel.setGeometry(text_label_x, bottom_y, text_label_w, bottom_h)
