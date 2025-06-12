import sys
import os
from PyQt5.QtWidgets import QDialog, QApplication
from PyQt5 import uic

class ProsecutorWindow(QDialog):
    # 시그널 정의
    
    def __init__(self, uiController, gameController, case_data, parent=None):
        super().__init__(parent)

        self.uiController = uiController
        self.gameController = gameController
        self.case_data = case_data
        
        # UI 파일 로드
        ui_path = os.path.join(os.path.dirname(__file__), '..', 'prosecutorWindow.ui')
        uic.loadUi(ui_path, self)
        
        # 초기 설정
        self.setup_ui()
        self.setup_connections()
    
    def setup_ui(self):
        """UI 초기 설정"""
        # 프로필 버튼들 초기 텍스트 설정
        self.profileButton1.setText("등장인물 1")
        self.profileButton2.setText("등장인물 2") 
        self.profileButton3.setText("등장인물 3")
        self.profileButton4.setText("등장인물 4")
    
    def setup_connections(self):
        """버튼 연결 설정"""
        # 주요 기능 버튼들
        self.overviewButton.clicked.connect(self.show_case_overview)
        self.evidenceButton.clicked.connect(self.show_evidence)
        self.textButton.clicked.connect(self.show_text_input)
        self.endButton.clicked.connect(self.end_argument)
        self.micButton.clicked.connect(self.toggle_mic)
        
        # 프로필 버튼들
        self.profileButton1.clicked.connect(lambda: self.show_profile(1))
        self.profileButton2.clicked.connect(lambda: self.show_profile(2))
        self.profileButton3.clicked.connect(lambda: self.show_profile(3))
        self.profileButton4.clicked.connect(lambda: self.show_profile(4))
    
    def show_case_overview(self):
        """사건 개요 표시"""
        print("사건 개요 버튼 클릭됨")
        # TODO: 사건 개요 창 열기
    
    def show_evidence(self):
        """증거품 확인 창 표시"""
        print("증거품 확인 버튼 클릭됨")
        # TODO: 증거품 확인 창 열기
    
    def show_text_input(self):
        """텍스트 입력 창 표시"""
        print("텍스트 입력 버튼 클릭됨")
        # TODO: 텍스트 입력 창 열기
    
    def end_argument(self):
        """주장 종료"""
        print("주장 종료 버튼 클릭됨")
        # TODO: 주장 종료 처리
        self.back_to_main.emit()
    
    def toggle_mic(self):
        """마이크 온/오프 토글"""
        print("마이크 버튼 클릭됨")
        # TODO: 마이크 기능 구현
    
    def show_profile(self, profile_num):
        """등장인물 프로필 표시"""
        print(f"등장인물 {profile_num} 버튼 클릭됨")
        # TODO: 등장인물 프로필 창 열기
    
    def set_profile_names(self, names_list):
        """등장인물 이름 설정"""
        buttons = [self.profileButton1, self.profileButton2, 
                  self.profileButton3, self.profileButton4]
        
        for i, name in enumerate(names_list):
            if i < len(buttons):
                buttons[i].setText(name)

# 테스트용 메인 함수
if __name__ == "__main__":
    app = QApplication(sys.argv)
    from ui.qt_designer.ui_controller import uiController  # UI 컨트롤러 임포트
    from game_controller import GameController  # 게임 컨트롤러 임포트

    ui_controller = uiController().get_instance()  # UI 컨트롤러 인스턴스
    game_controller = GameController().get_instance()  # 게임 컨트롤러 인스턴스
    case_data = game_controller._case_data

    window = ProsecutorWindow(ui_controller, game_controller, case_data)
    window = ProsecutorWindow(None, None, None)
    window.show()
    sys.exit(app.exec_())
