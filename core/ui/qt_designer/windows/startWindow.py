import sys
import os
import asyncio
from PyQt5.QtWidgets import QDialog, QApplication, QMessageBox
from PyQt5 import uic
from qasync import asyncSlot

class StartWindow(QDialog):
    def __init__(self, uiController, gameController, parent=None):
        super().__init__(parent)
        # UI 파일 로드
        ui_path = os.path.join(os.path.dirname(__file__), '..', 'startWindow.ui')
        uic.loadUi(ui_path, self)
        self.uc = uiController
        self.gc = gameController
        self._setup_connections()

    def _setup_connections(self):
        self.gameStartButton.clicked.connect(self.on_game_start)
        self.gameDescriptionButton.clicked.connect(self.on_game_description)
        self.gameTextModeButton.clicked.connect(self.on_text_mode)

    @asyncSlot()
    async def on_game_start(self):
        """게임 시작 버튼 클릭 - 초기화 시작"""
        self.set_button_state(False, "케이스 생성 중...")
        
        try:
            await self.gc.initialize()
            await self.gc.prepare_case_data()
            self.uc.open_generate_window()
            self.close()
            
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
        self.uc.open_description_window()
        self.close()

    @asyncSlot()
    async def on_text_mode(self):
        """테스트모드: stub 데이터로 빠르게 게임 시작"""
        self.set_button_state(False, "테스트 모드 시작 중...")

        try:
            # stub 데이터로 초기화
            self.gc.initialize_with_stub()
            # 바로 게임 시작 (prepare_case_data 스킵)
            self.uc.open_generate_window()
            self.close()

        except Exception as e:
            print(f"테스트모드 시작 오류: {e}")
            import traceback
            traceback.print_exc()
            self.set_button_state(True, "게임 시작 (재시도)")
            QMessageBox.critical(self, "오류", f"테스트모드 시작 중 오류가 발생했습니다:\n{str(e)}")

    def set_button_state(self, state:bool, msg:str):
        self.gameStartButton.setEnabled(state)
        self.gameStartButton.setText(msg)

