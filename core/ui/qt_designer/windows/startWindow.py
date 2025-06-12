import sys
import os
from PyQt5.QtWidgets import QDialog, QApplication
from PyQt5 import uic

class StartWindow(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        # UI 파일 로드
        ui_path = os.path.join(os.path.dirname(__file__), '..', 'startWindow.ui')
        uic.loadUi(ui_path, self)

        self._setup_connections()

    def _setup_connections(self):
        self.gameStartButton.clicked.connect(self.on_game_start)
        self.gameDescriptionButton.clicked.connect(self.on_game_description)
        self.gameTextModeButton.clicked.connect(self.on_text_mode)

    def on_game_start(self):
        print("게임 시작 버튼 클릭됨")
        # TODO: 실제 게임 시작 로직과 창 전환

    def on_game_description(self):
        print("게임 설명 버튼 클릭됨")
        # TODO: 게임 설명 창 띄우기

    def on_text_mode(self):
        print("텍스트 모드 버튼 클릭됨")
        # TODO: 텍스트 모드 진입 로직

# 테스트용 메인
if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = StartWindow()
    window.show()
    sys.exit(app.exec_())
