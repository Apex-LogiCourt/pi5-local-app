import sys
import os
from PyQt5.QtWidgets import QDialog, QApplication
from PyQt5 import uic

class JudgeWindow(QDialog):
    """ 이거는 한줄씩 판결 생성될 때마다 pysignal로 받아서 이벤트 처리인데
        굳이 인자가 이렇게 필요할 것 같지도 않고 고민입니다 ."""
    def __init__(self, uiController, gameController, case_data, parent=None):
        super().__init__(parent)

        self.uiController = uiController
        self.gameController = gameController
        
        
        # UI 파일 로드
        ui_path = os.path.join(os.path.dirname(__file__), '..', 'judgeWindow.ui')
        uic.loadUi(ui_path, self)
        
        # 초기 설정
        self.setup_ui()
        self.setup_connections()
    
    def setup_ui(self):
        """UI 초기 설정"""
        # 판결문 초기 텍스트 설정
        self.set_judge_text("판결문이 여기에 표시됩니다.")
    
    def setup_connections(self):
        """버튼 연결 설정"""
        self.backButton.clicked.connect(self.go_back)
    
    def set_judge_text(self, text):
        """판결문 텍스트 설정"""
        self.judgeText.setPlainText(text)
    
    def set_judge_text_add(self, text):
        self.judgeText.setPlainText(self.judgeText.toPlainText() + text)
    
    def go_back(self):
        self.uiController.restart_game_flow()
        # self.uiController.nowJudgement = False
        self.close()
        self.uiController.hideAllWindow()
        self.uiController.open_start_window()

# 테스트용 메인 함수
if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = JudgeWindow(None, None, None, None)
    window.show()
    sys.exit(app.exec_())
