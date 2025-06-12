import sys
import os
from PyQt5.QtWidgets import QDialog, QApplication, QMessageBox
from PyQt5 import uic

class StartWindow(QDialog):
    def __init__(self, uiController, gameController, parent=None):
        super().__init__(parent)
        # UI 파일 로드
        ui_path = os.path.join(os.path.dirname(__file__), '..', 'startWindow.ui')
        uic.loadUi(ui_path, self)
        self.uc = uiController
        self.gc = gameController
        self._setup_connections()

    def _setup_connections(self):
        self.gameStartButton.clicked.connect(self.on_game_start)
        self.gameDescriptionButton.clicked.connect(self.on_game_description)
        self.gameTextModeButton.clicked.connect(self.on_text_mode)

    def on_game_start(self):
        print("게임 시작 버튼 클릭됨")
        self.uc.open_generate_window()
        self.close()

    def on_game_description(self):
        print("게임 설명 버튼 클릭됨")
        self.uc.open_description_window()
        self.close()

    def on_text_mode(self):
        print("텍스트 모드 버튼 클릭됨")
        QMessageBox.information(None, "info", "미구현")

    def set_button_state(self, state:bool, msg:str):
        self.gameStartButton.setEnabled(state)
        self.gameStartButton.setText(msg)

# 테스트용 메인
if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = StartWindow()
    window.show()
    sys.exit(app.exec_())
