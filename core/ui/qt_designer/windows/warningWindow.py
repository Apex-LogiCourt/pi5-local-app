import sys
import os
from PyQt5.QtWidgets import QDialog, QApplication
from PyQt5.QtCore import Qt
from PyQt5 import uic

class WarningWindow(QDialog):
    def __init__(self, msg, parent=None):
        super().__init__(parent)
        
        # UI 파일 로드
        ui_path = os.path.join(os.path.dirname(__file__), '..', 'warningWindow.ui')
        uic.loadUi(ui_path, self)

        self.msg = msg
        if msg == None: msg=""
        self.set_label_text(self.msg)
    
    def set_label_text(self, text):
        self.textLabel.setText(text)

# 테스트용 메인 함수
if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = WarningWindow()
    window.show()
    sys.exit(app.exec_())
