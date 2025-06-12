import sys
import os
from PyQt5.QtWidgets import QDialog, QApplication
from PyQt5 import uic
from PyQt5.QtCore import pyqtSignal
import asyncio

class TextInputWindow(QDialog):
    # 텍스트 입력 완료 시그널 정의
    def __init__(self, uiController, gameController, parent=None):
        super().__init__(parent)
        
        # UI 파일 로드
        ui_path = os.path.join(os.path.dirname(__file__), '..', 'textInputWindow.ui')
        uic.loadUi(ui_path, self)
        
        self._setup_connections()
        self.uc = uiController
        self.gc = gameController
        
    def _setup_connections(self):
        """버튼 연결 설정"""
        self.textButton.clicked.connect(self._submit_text)
        
    async def _submit_text(self):
        """텍스트 입력 처리"""
        text = self.inputTextBox.toPlainText().strip()
        if text:
            turn_check = await self.gc.user_input(text)
            if turn_check:
                self.uc.turn 
            
            self.inputTextBox.clear()
            self.close()
    

# 테스트용 메인 함수
if __name__ == "__main__":
    app = QApplication(sys.argv)
    
    def on_text_submitted(text):
        print(f"입력된 텍스트: {text}")
    
    window = TextInputWindow()
    window.text_submitted.connect(on_text_submitted)
    window.set_placeholder_text("여기에 텍스트를 입력하세요...")
    window.show()
    
    sys.exit(app.exec_())
