import sys
import os
from PyQt5.QtWidgets import QDialog, QApplication
from PyQt5 import uic
import asyncio

class BaseCourtWindow(QDialog):
    def __init__(self, uiController, gameController, case_data, ui_file_name, parent=None):
        super().__init__(parent)
        
        self.uc = uiController
        self.gc = gameController
        self.case_data = case_data
        self.mic_on = False  # 마이크 상태 초기화
        
        # UI 파일 로드 (파일명만 다르게)
        ui_path = os.path.join(os.path.dirname(__file__), '..', ui_file_name)
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
        # TODO: 주장 종료 처리
        self.gc.done()
        self._turn_change()
    
    def _toggle_mic(self):
        """마이크 온/오프 토글"""
        # TODO: 마이크 기능 구현
        if not self.mic_on:
            asyncio.create_task(self.gc.record_start())
            self.toggle_mic_state()
        else:
            asyncio.create_task(self.gc.record_end())
            self.toggle_mic_state()
    
    def show_profile(self, profile_num):
        """등장인물 프로필 표시"""
        print(f"등장인물 {profile_num} 버튼 클릭됨")
        # TODO: 등장인물 프로필 창 열기 근데 없음 

class ProsecutorWindow(BaseCourtWindow):
    def __init__(self, uiController, gameController, case_data, parent=None):
        super().__init__(uiController, gameController, case_data, 'prosecutorWindow.ui', parent)
        self.turnButton.clicked.connect(self._turn_change)
        # self.endButton.clicked.connect(self._end_turn)

    def _turn_change(self):
        self.uc.open_lawyer_window()
        self.gc._switch_turn()
        self.close()

    # def _end_turn(self):
    #     self.gc.done()
    #     self.close()


class LawyerWindow(BaseCourtWindow):
    def __init__(self, uiController, gameController, case_data, parent=None):
        super().__init__(uiController, gameController, case_data, 'lawyerWindow.ui', parent)
        self.turnButton.clicked.connect(self._turn_change)
        # self.endButton.clicked.connect(self._end_turn)

    def _turn_change(self):
        self.uc.open_prosecutor_window()
        self.gc._switch_turn()
        self.close()

    # def _end_turn(self):
        # self.gc.done()
        # self.close()


# 테스트용 메인 함수
if __name__ == "__main__":
    import asyncio
    
    async def main():
        app = QApplication(sys.argv)
        # from ui.qt_designer.UiController import uiController  # UI 컨트롤러 임포트
        from game_controller import GameController  # 게임 컨트롤러 임포트
        from ui.UiController import UiController

        uc= UiController().get_instance()  # UI 컨트롤러 인스턴스
        gc = GameController().get_instance()  # 게임 컨트롤러 인스턴스
        
        # GameController 초기화 (비동기)
        await gc.initialize()
        await gc.start_game()
        cd = gc._case_data

        # window = ProsecutorWindow(ui_controller, game_controller, case_data)
        window = ProsecutorWindow(uc, gc, cd)
        window.show()
        sys.exit(app.exec_())
    
    # 비동기 함수 실행
    asyncio.run(main())
