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
    
    def set_judge_html(self, html_text):
        """판결문 HTML 텍스트 설정"""
        self.judgeText.setHtml(html_text)
    
    def go_back(self):
        """뒤로가기"""
        print("뒤로가기 버튼 클릭됨")
        # TODO: 이전 화면으로 돌아가기
        self.close()

# 테스트용 메인 함수
if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = JudgeWindow(None, None, None, None)
    window.show()
    sys.exit(app.exec_())
