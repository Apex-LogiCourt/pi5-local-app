import sys
import os
from PyQt5.QtWidgets import QWidget
from PyQt5 import uic
import asyncio


class BaseCourtPage(QWidget):
    """법정 페이지 기본 클래스 - QWidget 기반"""

    def __init__(self, uiController, gameController, case_data, ui_file_name, parent=None):
        super().__init__(parent)

        self.uc = uiController
        self.gc = gameController
        self.case_data = case_data
        self.mic_on = False  # 마이크 상태 초기화

        # UI 파일 로드 (파일명만 다르게)
        ui_path = os.path.join(os.path.dirname(__file__), '..', 'qt_designer', ui_file_name)
        uic.loadUi(ui_path, self)

        self._setup_ui()
        self._setup_connections()

    def show_case_overview(self):
        """사건 개요 표시"""
        self.uc.open_overview_window()

    def show_evidence(self):
        """증거품 확인 창 표시"""
        self.uc.open_evidence_window()

    def show_text_input(self):
        """텍스트 입력 창 표시"""
        self.uc.open_text_input_window()

    def _setup_ui(self):
        """공통 UI 초기 설정"""
        profiles = self.case_data.profiles
        self.profileButton1.setText(profiles[0].name if len(profiles) > 0 else "등장인물 1")
        self.profileButton2.setText(profiles[1].name if len(profiles) > 1 else "등장인물 2")
        self.profileButton3.setText(profiles[2].name if len(profiles) > 2 else "등장인물 3")
        self.profileButton4.setText(profiles[3].name if len(profiles) > 3 else "등장인물 4")

        # 마이크 초기 상태 설정
        self.micButton.setProperty("mic_state", "off")

    def _setup_connections(self):
        """버튼 연결 설정"""
        # 주요 기능 버튼들
        self.overviewButton.clicked.connect(self.show_case_overview)
        self.evidenceButton.clicked.connect(self.show_evidence)
        self.textButton.clicked.connect(self.show_text_input)
        self.endButton.clicked.connect(self._end_argument)
        self.micButton.clicked.connect(self._toggle_mic)

        # 프로필 버튼들 #이벤트함수 미구현으로 주석처리
        # self.profileButton1.clicked.connect(lambda: self.show_profile(1))
        # self.profileButton2.clicked.connect(lambda: self.show_profile(2))
        # self.profileButton3.clicked.connect(lambda: self.show_profile(3))
        # self.profileButton4.clicked.connect(lambda: self.show_profile(4))

    def toggle_mic_state(self):
        """마이크 상태 토글 (property 기반 스타일 변경)"""
        self.mic_on = not self.mic_on
        self.micButton.setProperty("mic_state", "on" if self.mic_on else "off")
        # 스타일 재적용
        self.micButton.style().unpolish(self.micButton)
        self.micButton.style().polish(self.micButton)

    def _end_argument(self):
        """주장 종료"""
        self.gc.done()
        self._turn_change()

    def _toggle_mic(self):
        """마이크 온/오프 토글"""
        if not self.mic_on:
            asyncio.create_task(self.gc.record_start())
            self.toggle_mic_state()
        else:
            asyncio.create_task(self.gc.record_end())
            self.toggle_mic_state()

    def show_profile(self, profile_num):
        """등장인물 프로필 표시"""
        print(f"등장인물 {profile_num} 버튼 클릭됨")
        # TODO: 등장인물 프로필 창 열기

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

        # 검사 페이지인지 변호사 페이지인지 확인
        is_prosecutor = self.__class__.__name__ == 'ProsecutorPage'

        # 상단 라벨 (중앙)
        self.nameLabel.setGeometry(
            int(390 * ratio_w), int(30 * ratio_h),
            int(421 * ratio_w), int(71 * ratio_h)
        )

        if is_prosecutor:
            # ========== 검사 화면 ==========
            # 프로필 이미지 (오른쪽 배경)
            self.profileImage.setGeometry(
                int(558 * ratio_w), int(110 * ratio_h),
                int(740 * ratio_w), int(521 * ratio_h)
            )

            # 프로필 캐릭터 이미지
            self.profile.setGeometry(
                int(800 * ratio_w), int(120 * ratio_h),
                int(250 * ratio_w), int(380 * ratio_h)
            )

            # 하단 버튼들 (왼쪽)
            self.micButton.setGeometry(
                int(30 * ratio_w), int(620 * ratio_h),
                int(161 * ratio_w), int(71 * ratio_h)
            )
            self.endButton.setGeometry(
                int(210 * ratio_w), int(620 * ratio_h),
                int(161 * ratio_w), int(71 * ratio_h)
            )
            self.turnButton.setGeometry(
                int(390 * ratio_w), int(620 * ratio_h),
                int(161 * ratio_w), int(71 * ratio_h)
            )

            # 왼쪽 기능 버튼들
            self.overviewButton.setGeometry(
                int(60 * ratio_w), int(180 * ratio_h),
                int(141 * ratio_w), int(51 * ratio_h)
            )
            self.evidenceButton.setGeometry(
                int(60 * ratio_w), int(310 * ratio_h),
                int(161 * ratio_w), int(51 * ratio_h)
            )
            self.textButton.setGeometry(
                int(60 * ratio_w), int(440 * ratio_h),
                int(161 * ratio_w), int(51 * ratio_h)
            )

            # 등장인물 영역 (중앙)
            self.profileTitleLabel.setGeometry(
                int(290 * ratio_w), int(180 * ratio_h),
                int(201 * ratio_w), int(31 * ratio_h)
            )
            self.profileButton1.setGeometry(
                int(310 * ratio_w), int(230 * ratio_h),
                int(170 * ratio_w), int(51 * ratio_h)
            )
            self.profileButton2.setGeometry(
                int(310 * ratio_w), int(310 * ratio_h),
                int(170 * ratio_w), int(51 * ratio_h)
            )
            self.profileButton3.setGeometry(
                int(310 * ratio_w), int(390 * ratio_h),
                int(170 * ratio_w), int(51 * ratio_h)
            )
            self.profileButton4.setGeometry(
                int(310 * ratio_w), int(470 * ratio_h),
                int(170 * ratio_w), int(51 * ratio_h)
            )

        else:
            # ========== 변호사 화면 ==========
            # 프로필 이미지 (왼쪽 배경)
            self.profileImage.setGeometry(
                int(-20 * ratio_w), int(120 * ratio_h),
                int(740 * ratio_w), int(520 * ratio_h)
            )
            
            # 프로필 캐릭터 이미지
            self.profile.setGeometry(
                int(200 * ratio_w), int(130 * ratio_h),
                int(250 * ratio_w), int(380 * ratio_h)
            )

            # 하단 버튼들 (오른쪽)
            self.turnButton.setGeometry(
                int(730 * ratio_w), int(620 * ratio_h),
                int(161 * ratio_w), int(71 * ratio_h)
            )
            self.endButton.setGeometry(
                int(910 * ratio_w), int(620 * ratio_h),
                int(161 * ratio_w), int(71 * ratio_h)
            )
            self.micButton.setGeometry(
                int(1090 * ratio_w), int(620 * ratio_h),
                int(161 * ratio_w), int(71 * ratio_h)
            )

            # 오른쪽 기능 버튼들
            self.overviewButton.setGeometry(
                int(740 * ratio_w), int(180 * ratio_h),
                int(141 * ratio_w), int(51 * ratio_h)
            )
            self.evidenceButton.setGeometry(
                int(740 * ratio_w), int(310 * ratio_h),
                int(161 * ratio_w), int(51 * ratio_h)
            )
            self.textButton.setGeometry(
                int(740 * ratio_w), int(440 * ratio_h),
                int(161 * ratio_w), int(51 * ratio_h)
            )

            # 등장인물 영역 (오른쪽)
            self.profileTitleLabel.setGeometry(
                int(930 * ratio_w), int(190 * ratio_h),
                int(221 * ratio_w), int(31 * ratio_h)
            )
            self.profileButton1.setGeometry(
                int(960 * ratio_w), int(240 * ratio_h),
                int(170 * ratio_w), int(51 * ratio_h)
            )
            self.profileButton2.setGeometry(
                int(960 * ratio_w), int(320 * ratio_h),
                int(170 * ratio_w), int(51 * ratio_h)
            )
            self.profileButton3.setGeometry(
                int(960 * ratio_w), int(400 * ratio_h),
                int(170 * ratio_w), int(51 * ratio_h)
            )
            self.profileButton4.setGeometry(
                int(960 * ratio_w), int(480 * ratio_h),
                int(170 * ratio_w), int(51 * ratio_h)
            )


class ProsecutorPage(BaseCourtPage):
    """검사 페이지 - BaseCourtPage 상속"""

    def __init__(self, uiController, gameController, case_data, parent=None):
        super().__init__(uiController, gameController, case_data, 'prosecutorWindow.ui', parent)
        self.turnButton.clicked.connect(self._turn_change)

    def _turn_change(self):
        """턴 변경 - 변호사로"""
        self.uc.switch_to_lawyer_page()
        self.gc._switch_turn()


class LawyerPage(BaseCourtPage):
    """변호사 페이지 - BaseCourtPage 상속"""

    def __init__(self, uiController, gameController, case_data, parent=None):
        super().__init__(uiController, gameController, case_data, 'lawyerWindow.ui', parent)
        self.turnButton.clicked.connect(self._turn_change)

    def _turn_change(self):
        """턴 변경 - 검사로"""
        self.uc.switch_to_prosecutor_page()
        self.gc._switch_turn()
