import sys
import os
import asyncio
from PyQt5.QtWidgets import QWidget, QMessageBox
from PyQt5 import uic
from qasync import asyncSlot


class StartPage(QWidget):
    """시작 페이지 - QWidget 기반"""

    def __init__(self, uiController, gameController, parent=None):
        super().__init__(parent)
        # UI 파일 로드
        ui_path = os.path.join(os.path.dirname(__file__), '..', 'qt_designer', 'startWindow.ui')
        uic.loadUi(ui_path, self)
        self.uc = uiController
        self.gc = gameController
        self._setup_connections()

    def _setup_connections(self):
        """버튼 연결 설정"""
        self.gameStartButton.clicked.connect(self.on_game_start)
        self.gameDescriptionButton.clicked.connect(self.on_game_description)
        self.gameTextModeButton.clicked.connect(self.on_text_mode)

    @asyncSlot()
    async def on_game_start(self):
        """게임 시작 버튼 클릭 - 초기화 시작"""
        self.set_button_state(False, "사건 생성 중...")

        try:
            await self.gc.initialize()
            await self.gc.prepare_case_data()
            self.uc.switch_to_generate_page()

        except TimeoutError as e:
            print(f"타임아웃: {e}")
            self.set_button_state(True, "게임 시작 (재시도)")
            QMessageBox.warning(self, "시간 초과", f"초기화 시간이 초과되었습니다:\n{str(e)}")

        except Exception as e:
            print(f"게임 시작 오류: {e}")
            import traceback
            traceback.print_exc()
            self.set_button_state(True, "게임 시작 (재시도)")
            QMessageBox.critical(self, "오류", f"게임 시작 중 오류가 발생했습니다:\n{str(e)}")

    def on_game_description(self):
        """게임 설명 버튼 클릭"""
        self.uc.open_description_window()

    @asyncSlot()
    async def on_text_mode(self):
        """테스트모드: stub 데이터로 빠르게 게임 시작"""
        self.set_button_state(False, "테스트 모드 시작 중...")

        try:
            # stub 데이터로 초기화
            self.gc.initialize_with_stub()
            # 바로 게임 시작 (prepare_case_data 스킵)
            self.uc.switch_to_generate_page()

        except Exception as e:
            print(f"테스트모드 시작 오류: {e}")
            import traceback
            traceback.print_exc()
            self.set_button_state(True, "게임 시작 (재시도)")
            QMessageBox.critical(self, "오류", f"테스트모드 시작 중 오류가 발생했습니다:\n{str(e)}")

    def set_button_state(self, state: bool, msg: str):
        """버튼 상태 설정"""
        self.gameStartButton.setEnabled(state)
        self.gameStartButton.setText(msg)

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

        # 왼쪽 이미지 (비율 유지하면서 크기 조정)
        img_w = int(781 * ratio_w)
        img_h = int(701 * ratio_h)
        self.startImage.setGeometry(10, 10, img_w, img_h)

        # 오른쪽 영역 시작 위치
        right_x = img_w + 20
        right_w = w - right_x - 20

        # 로고 (상단)
        self.startLogo.setGeometry(right_x, 10, right_w, int(161 * ratio_h))

        # 설명 텍스트 (중간)
        self.label.setGeometry(right_x, int(180 * ratio_h), right_w, int(291 * ratio_h))

        # 버튼들 (하단) - 세로 간격 유지
        btn_h = int(71 * ratio_h)
        btn_spacing = int(10 * ratio_h)

        start_y = h - (btn_h * 3 + btn_spacing * 3 + 10)
        self.gameStartButton.setGeometry(right_x, start_y, right_w, btn_h)
        self.gameDescriptionButton.setGeometry(right_x, start_y + btn_h + btn_spacing, right_w, btn_h)
        self.gameTextModeButton.setGeometry(right_x, start_y + (btn_h + btn_spacing) * 2, right_w, btn_h)
