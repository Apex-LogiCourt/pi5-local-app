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
        #self.setup_connections()
    
    def setup_ui(self):
        """UI 초기 설정"""
        # HTML strong/b 태그 스타일은 document().setDefaultStyleSheet로 설정
        # UI 파일에 이미 QSS가 적용되어 있으므로 여기서는 HTML 태그 스타일만 추가
        self.overviewText.document().setDefaultStyleSheet("""
            strong { font-family: "나눔고딕 ExtraBold"; }
            b { font-family: "나눔고딕 ExtraBold"; }
        """)
        # 사건 개요 초기 텍스트 설정
        self.set_overview_text(self.case_outline)
    
    def set_overview_text(self, text):
        """사건 개요 텍스트 설정 (마크다운을 HTML로 변환하여 표시)"""
        from tools.service import markdown_to_html
        html_text = markdown_to_html(text)
        self.overviewText.setHtml(html_text)


# 테스트용 메인 함수
if __name__ == "__main__":
    app = QApplication(sys.argv)
    case_outline = "사건 개요 예시 텍스트"
    window = OverviewWindow(case_outline)
    window.show()
    sys.exit(app.exec_())
