import sys
import os
from PyQt5.QtWidgets import QDialog, QApplication
from PyQt5 import uic

class OverviewWindow(QDialog):
    def __init__(self, case_outline, parent=None):
        super().__init__(parent)

        self.case_outline = case_outline
        
        # UI 파일 로드
        ui_path = os.path.join(os.path.dirname(__file__), '..', 'overviewWindow.ui')
        uic.loadUi(ui_path, self)
        
        # 초기 설정
        self.setup_ui()
        self.setup_connections()
    
    def setup_ui(self):
        """UI 초기 설정"""
        # 사건 개요 초기 텍스트 설정
        self.set_overview_text(self.case_outline)
    
    def set_overview_text(self, text):
        """사건 개요 텍스트 설정"""
        self.overviewText.setPlainText(text)

# 테스트용 메인 함수
if __name__ == "__main__":
    app = QApplication(sys.argv)
    case_outline = "사건 개요 예시 텍스트"
    window = OverviewWindow(case_outline)
    window.show()
    sys.exit(app.exec_())
