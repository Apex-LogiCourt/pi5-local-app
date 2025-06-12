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


class uiController():
    _instance = None

    @classmethod
    def get_instance(cls):
        if cls._instance is None:
            cls._instance = uiController()
        return cls._instance
    
    def __init__(self):
        if uiController._instance is not None:
            raise Exception("싱글톤 클래스는 직접 생성할 수 없습니다. get_instance() 메서드를 사용하세요.")
        uiController._instance = self

    def init_game_controller(self):
        print("Requesting GameController initialization...")
        self._update_start_button("컨트롤러 초기화 중...", False)
        if hasattr(GameController, '_is_initialized'):
            if GameController._is_initialized:
                print("GameController is already initialized. Loading case data...")
                self.setStartButtonState(True)
                self.is_gc_initialized = True
                self.case_data = GameController._case_data
                self.createWindowInstance()
            else:
                print("GameController is not initialized. Attempting to initialize...")
                asyncio.ensure_future(GameController.initialize())
        else:
            print("ERROR: GameController does not have a class method 'initialize'.")
            self.setStartButtonState(False)
    
    def createWindowInstance(self):
        self.startWindowInstance = None
        self.descriptionWindowInstance = None
        self.generateWindowInstance = None
        self.generateWindow2Instance = None
        self.interrogationWindowInstance = None
        self.judgeWindowInstance = None
        self.lawyerWindowInstance = None
        self.overviewWindowInstance = None
        self.prosecutorWindowInstance = None
        self.textInputWindowInstance = None
        self.evidenceWindowInstance = None

    async def restart_game_flow(self): #최종 판결문에서 뒤로가기 버튼 누를 시 호출
        print("Restarting game flow...")
        QApplication.processEvents()

        self.is_gc_initialized = False
        self.case_data = None
        self.setStartButtonState(False)
        #시작화면 불러오기
        
        # GameController 재초기화 (initialize 클래스 메소드 호출)
        if hasattr(GameController, 'initialize'):
             await GameController.initialize() # initialize가 CaseData를 반환하지만, 시그널로도 받을 것이므로 여기서는 호출만.
        else:
            print("ERROR: GameController has no 'initialize' method for re-initialization.")
            QMessageBox.critical(self, "초기화 오류", "게임 데이터 초기화에 실패했습니다.")
        # "initialized" 시그널이 GameController로부터 오면 is_gc_initialized, case_data가 설정되고 로딩 다이얼로그가 닫힘.

    def setStartButtonState(state: bool):
        # 시작 버튼 상태 설정(데이터 로딩 중 ...)
        # 이하 기존 코드
        # self._update_start_button("게임 시작", True)
        # self._update_start_button("컨트롤러 오류 (재시도)", True)
        pass

if __name__ == "__main__" :
    #QApplication : 프로그램을 실행시켜주는 클래스
    app = QApplication(sys.argv) 

    #startWindowClass의 인스턴스 생성
    # startWindow = startWindowClass()

    #프로그램 화면을 보여주는 코드
    # startWindow.show()

    #프로그램을 이벤트루프로 진입시키는(프로그램을 작동시키는) 코드
    app.exec_()