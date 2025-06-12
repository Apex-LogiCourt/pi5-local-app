import sys
import os
from PyQt5.QtWidgets import QDialog, QApplication
from PyQt5.QtCore import Qt
from PyQt5 import uic

class GameDescriptionWindow(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        
        # UI 파일 로드
        ui_path = os.path.join(os.path.dirname(__file__), '..', 'gameDescriptionWindow.ui')
        uic.loadUi(ui_path, self)
        
        # 초기 설정
        self.setup_ui()
        self.setup_connections()
    
    def setup_ui(self):
        """UI 초기 설정"""
        # descriptionText 폰트 크기 조정
        font = self.descriptionText.font()
        font.setPointSize(14)  # 20pt에서 14pt로 변경
        self.descriptionText.setFont(font)
        
        # descriptionText에 기본 텍스트 설정
        self.set_description_text("LogiCourt AI에 오신 것을 환영합니다!\n\n"
            "본 게임은 AI가 생성한 가상의 사건을 바탕으로 진행되는 토론 및 추리 게임입니다.\n\n"
            "1. 사건 개요 확인: '시작하기'를 누르면 AI가 생성한 사건의 개요와 등장인물 정보가 순차적으로 제공됩니다.\n"
            "2. 역할 배정 (가상): 플레이어들은 각각 변호사와 검사의 역할을 맡게 됩니다.\n"
            "3. 자유 토론: 제공된 정보를 바탕으로 토론하며 사건의 진실을 파헤치세요.\n"
            "4. 증거 제출 및 반박: 증거 제시와 반론 기능이 구현됩니다.\n"
            "5. AI 판결: 토론 후 AI 판사의 판결과 사건의 진실을 확인합니다.\n\n"
            "승리 조건: 상대방의 논리적 허점을 찾아내고, AI 또는 청중을 설득하는 것입니다.\n\n"
            "팁: 등장인물의 관계, 알리바이, 숨겨진 동기를 주의 깊게 살펴보세요!")
    
    def setup_connections(self):
        """버튼 연결 설정"""
        # 뒤로가기 버튼 연결
        self.backButton.clicked.connect(self.close)
    
    def set_description_text(self, text):
        """descriptionText에 텍스트 설정"""
        self.descriptionText.setPlainText(text)
    

# 테스트용 메인 함수
if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = GameDescriptionWindow()
    window.show()
    sys.exit(app.exec_())
