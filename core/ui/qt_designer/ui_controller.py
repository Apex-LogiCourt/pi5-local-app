import sys
import os
import asyncio
from PyQt5.QtWidgets import *
from PyQt5 import uic
from PyQt5.QtGui import QFont
from PyQt5.QtCore import Qt, pyqtSignal, pyqtSlot, QTimer
from data_models import CaseData, Evidence, Profile
from game_controller import GameController

sys.path.append(os.path.dirname(os.path.abspath(__file__)))
import resource_rc

#UI 연결. 단, UI파일은 Python 코드 파일과 같은 디렉토리에 위치해야한다.
startWindowUi = uic.loadUiType("core/ui/qt_designer/startWindow.ui")[0]
descriptionWindowUi = uic.loadUiType("core/ui/qt_designer/gameDescriptionWindow.ui")[0]
generateWindowUi = uic.loadUiType("core/ui/qt_designer/generateWindow.ui")[0]
generateWindow2Ui = uic.loadUiType("core/ui/qt_designer/generateWindow2.ui")[0]
interrogationWindowUi = uic.loadUiType("core/ui/qt_designer/interrogationWindow.ui")[0]
judgeWindowUi = uic.loadUiType("core/ui/qt_designer/judgeWindow.ui")[0]
lawyerWindowUi = uic.loadUiType("core/ui/qt_designer/lawyerWindow.ui")[0]
overviewWindowUi = uic.loadUiType("core/ui/qt_designer/overviewWindow.ui")[0]
prosecutorWindowUi = uic.loadUiType("core/ui/qt_designer/prosecutorWindow.ui")[0]
textInputWindowUi = uic.loadUiType("core/ui/qt_designer/textInputWindow.ui")[0]
evidenceWindowUi = uic.loadUiType("core/ui/qt_designer/evidenceWindow.ui")[0]


def init_game_controller(self):
    print("Requesting GameController initialization...")
    self._update_start_button("컨트롤러 초기화 중...", False)
    if hasattr(GameController, '_is_initialized'):
        if GameController._is_initialized:
            print("GameController is already initialized. Loading case data...")
            self._update_start_button("게임 시작", True)
            self.is_gc_initialized = True
            self.case_data = GameController._case_data
        else:
            print("GameController is not initialized. Attempting to initialize...")
            asyncio.ensure_future(GameController.initialize())
    else:
        print("ERROR: GameController does not have a class method 'initialize'.")
        self._update_start_button("컨트롤러 오류 (재시도)", True)



if __name__ == "__main__" :
    #QApplication : 프로그램을 실행시켜주는 클래스
    app = QApplication(sys.argv) 

    #startWindowClass의 인스턴스 생성
    # startWindow = startWindowClass()

    #프로그램 화면을 보여주는 코드
    # startWindow.show()

    #프로그램을 이벤트루프로 진입시키는(프로그램을 작동시키는) 코드
    app.exec_()