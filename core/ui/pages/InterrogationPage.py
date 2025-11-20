import sys
import os
from PyQt5.QtWidgets import QWidget
from PyQt5 import uic
from PyQt5.QtCore import Qt, QPropertyAnimation, QRect
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

    def evidence_tagged(self, evidence):
        """증거 태그 표시 - 크기 애니메이션과 함께"""
        # 증거 이미지 표시
        if evidence and hasattr(evidence, 'picture') and evidence.picture:
            # 절대 경로 또는 상대 경로 처리
            image_path = evidence.picture
            if not os.path.isabs(image_path):
                # 상대 경로인 경우 core 디렉토리 기준으로 절대 경로 생성
                default_path = os.path.join(os.path.dirname(__file__), '..', '..', '..')
                image_path = os.path.join(default_path, str(image_path))

            # 이미지 파일이 존재하는지 확인
            if os.path.exists(image_path):
                # 먼저 작은 크기로 이미지 설정
                pixmap_small = QPixmap(image_path).scaled(71, 71, aspectRatioMode=1)
                self.evidenceLabel.setPixmap(pixmap_small)

                # 크기 애니메이션: 71x71 -> 141x141
                self.animation = QPropertyAnimation(self.evidenceLabel, b"geometry")
                self.animation.setDuration(300)  # 300ms
                self.animation.setStartValue(QRect(30, 30, 71, 71))
                self.animation.setEndValue(QRect(30, 30, 141, 141))

                # 애니메이션 완료 후 큰 이미지로 교체
                def update_large_image():
                    pixmap_large = QPixmap(image_path).scaled(141, 141, aspectRatioMode=1)
                    self.evidenceLabel.setPixmap(pixmap_large)

                self.animation.finished.connect(update_large_image)
                self.animation.start()

                print(f"[InterrogationPage] 증거 이미지 표시: {image_path}")
            else:
                print(f"[InterrogationPage] 이미지 파일이 존재하지 않음: {image_path}")

    def evidence_tag_reset(self):
        """증거 태그 리셋 - 크기만 작게 (이미지는 유지)"""
        # 크기 애니메이션: 141x141 -> 71x71
        self.animation = QPropertyAnimation(self.evidenceLabel, b"geometry")
        self.animation.setDuration(300)  # 300ms
        self.animation.setStartValue(QRect(30, 30, 141, 141))
        self.animation.setEndValue(QRect(30, 30, 71, 71))
        self.animation.start()
        # 증거 이미지는 그대로 유지

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
        # evidenceLabel의 현재 크기에 비례하여 조정 (71 또는 141)
        current_evidence_size = self.evidenceLabel.width()
        scaled_evidence_size = int(current_evidence_size * min(ratio_w, ratio_h))
        self.evidenceLabel.setGeometry(margin, margin, scaled_evidence_size, scaled_evidence_size)

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
