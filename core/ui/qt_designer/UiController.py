import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

import asyncio
from PyQt5.QtWidgets import *
from PyQt5 import uic
from PyQt5.QtGui import QFont
from PyQt5.QtCore import Qt, pyqtSignal, pyqtSlot, QTimer
from data_models import CaseData, Evidence, Profile
from game_controller import GameController

from windows.gameDescriptionWindow import GameDescriptionWindow
from windows.evidenceWindow import EvidenceWindow
from windows.common import BaseCourtWindow
from windows.overviewWindow import OverviewWindow
from windows.judgeWindow import JudgeWindow

import resource_rc

class UiController():
    _instance = None

    @classmethod
    def get_instance(cls):
        if cls._instance is None:
            cls._instance = UiController()
        return cls._instance
    
    def __init__(self):
        if UiController._instance is not None:
            raise Exception("싱글톤 클래스는 직접 생성할 수 없습니다. get_instance() 메서드를 사용하세요.")
        UiController._instance = self
        self.game_controller = GameController.get_instance()
        self.init_game_controller()
        self.startWindow()
        self.createWindowInstance()

    def startWindow(self):
        # app = QApplication(sys.argv)
        # window = StartWindow()
        # window.show()
        # app.exec_()
        pass

    def init_game_controller(self):
        print("Requesting GameController initialization...")
        self.setStartButtonState(False, "컨트롤러 초기화 중...")
        if hasattr(GameController, '_is_initialized'):
            if GameController._is_initialized:
                print("GameController is already initialized. Loading case data...")
                self.is_gc_initialized = True
                self.case_data = GameController._case_data
                self.setStartButtonState(True, "게임 시작")
                self.createWindowInstance()
            else:
                print("GameController is not initialized. Attempting to initialize...")
                asyncio.ensure_future(GameController.initialize())
        else:
            print("ERROR: GameController does not have a class method 'initialize'.")
            self.setStartButtonState(False, "컨트롤러 오류 (재시도)")
    
    def createWindowInstance(self):
        self.startWindowInstance = None
        self.descriptionWindowInstance = GameDescriptionWindow()
        self.generateWindowInstance = None
        self.generateWindow2Instance = None
        self.interrogationWindowInstance = None
        self.judgeWindowInstance = JudgeWindow(self._instance, self.game_controller, self.case_data)
        self.overviewWindowInstance = OverviewWindow(self.case_data.case.outline)
        self.lawyerWindowInstance = BaseCourtWindow(self._instance, self.game_controller, self.case_data, "lawyerWindow.ui")
        self.prosecutorWindowInstance = BaseCourtWindow(self._instance, self.game_controller, self.case_data, "prosecutorWindow.ui")
        self.textInputWindowInstance = None
        self.evidenceWindowInstance = EvidenceWindow(self.case_data.evidences) #evidence: List
        #이하는 테스트
        self.descriptionWindowInstance.show()
        self.prosecutorWindowInstance.show()
        self.evidenceWindowInstance.show()
        self.judgeWindowInstance.show()
        self.overviewWindowInstance.show()
        self.lawyerWindowInstance.show()
        # QMessageBox.warning(self.prosecutorWindowInstance, "알림", "재판과 관련 없는 내용입니다.")

    async def restart_game_flow(self): #최종 판결문에서 뒤로가기 버튼 누를 시 호출
        print("Restarting game flow...")
        QApplication.processEvents()

        self.is_gc_initialized = False
        self.case_data = None
        self.setStartButtonState(False)
        #시작화면 불러오기 넣으셈
        
        # GameController 재초기화 (initialize 클래스 메소드 호출)
        if hasattr(GameController, 'initialize'):
             await GameController.initialize() # initialize가 CaseData를 반환하지만, 시그널로도 받을 것이므로 여기서는 호출만.
        else:
            print("ERROR: GameController has no 'initialize' method for re-initialization.")
            QMessageBox.critical(self, "초기화 오류", "게임 데이터 초기화에 실패했습니다.")
        # "initialized" 시그널이 GameController로부터 오면 is_gc_initialized, case_data가 설정되고 로딩 다이얼로그가 닫힘.

    def setStartButtonState(self, state: bool, msg: str):
        if msg == None:
            msg = "게임 시작"
        # 시작 버튼 상태 설정
        # startWindowInstance.setStartButtonState(state, msg)
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