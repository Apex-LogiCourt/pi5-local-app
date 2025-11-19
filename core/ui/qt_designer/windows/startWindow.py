import sys
import os
from PyQt5.QtWidgets import QDialog, QApplication, QMessageBox, QWidget # QWidget 추가
from PyQt5 import uic

# [수정 1] 이미지 리소스를 위한 임포트 추가 (경로는 프로젝트 구조에 맞춰주세요)
# 이 임포트가 있어야 .ui 파일의 이미지가 보입니다.
# 모든 수정 완료
try:
    import ui.qt_designer.resource_rc
except ImportError:
    pass 

# [수정 2] .ui 파일의 최상위 위젯 타입에 맞춰 QDialog를 상속
class StartWindow(QDialog): 
    def __init__(self, uiController, gameController, parent=None):
        super().__init__(parent)
        
        # UI 파일 로드 (이 파일에 레이아웃이 설정되어야 동적으로 작동합니다.)
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
        # [수정 3] self.close() 제거: StackedWidget에서는 화면 전환 시 필요 없습니다.
        # self.close() 

    def on_game_description(self):
        print("게임 설명 버튼 클릭됨")
        self.uc.open_description_window()
        # [수정 3] self.close() 제거
        # self.close()

    def on_text_mode(self):
        print("텍스트 모드 버튼 클릭됨")
        QMessageBox.information(self, "알림", "아직 구현되지 않은 기능입니다.")

    # [수정 4] UiController에서 호출하는 함수 이름에 맞춰 setStartButtonState로 변경
    def setStartButtonState(self, state: bool, msg: str):
        self.gameStartButton.setEnabled(state)
        self.gameStartButton.setText(msg)

# 테스트용 메인 (단독 실행 시 에러 방지용 Dummy Controller 포함)
if __name__ == "__main__":
    app = QApplication(sys.argv)
    
    class DummyController:
        def open_generate_window(self): print("화면 전환: 생성")
        def open_description_window(self): print("화면 전환: 설명")
        
    window = StartWindow(DummyController(), None)
    window.show()
    sys.exit(app.exec_())