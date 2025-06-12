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

from ui.qt_designer.windows.gameDescriptionWindow import GameDescriptionWindow
from ui.qt_designer.windows.evidenceWindow import EvidenceWindow
from ui.qt_designer.windows.common import BaseCourtWindow, LawyerWindow, ProsecutorWindow
from ui.qt_designer.windows.overviewWindow import OverviewWindow
from ui.qt_designer.windows.judgeWindow import JudgeWindow
from ui.qt_designer.windows.warningWindow import WarningWindow
from ui.qt_designer.windows.generateWindow import GenerateWindow
from ui.qt_designer.windows.interrogationWindow import InterrogationWindow
from ui.qt_designer.windows.textInputWindow import TextInputWindow
from ui.qt_designer.windows.startWindow import StartWindow
from PyQt5.QtCore import pyqtSignal, QObject, pyqtSlot

import ui.qt_designer.resource_rc 




class UiController(QObject):
    _instance = None

    @classmethod
    def get_instance(cls):
        if cls._instance is None:
            cls._instance = UiController()
        return cls._instance
    
    def __init__(self):
        super().__init__()  # QObject 초기화 추가
        if UiController._instance is not None:
            raise Exception("싱글톤 클래스는 직접 생성할 수 없습니다. get_instance() 메서드를 사용하세요.")
        UiController._instance = self
        self.game_controller = GameController.get_instance()
        self.init_game_controller()
        self.isTurnProsecutor = True # 처음에는 검사 턴으로 시작
        print("슬롯 연결 직전:", self.receive_game_signal)

        self.game_controller._signal.connect(self.receive_game_signal)

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
                self.startWindowInstance.show()
            else:
                print("GameController is not initialized. Attempting to initialize...")
                asyncio.ensure_future(GameController.initialize())
        else:
            print("ERROR: GameController does not have a class method 'initialize'.")
            self.setStartButtonState(False, "컨트롤러 오류 (재시도)")
    
    def createWindowInstance(self):
        self.startWindowInstance = StartWindow(self._instance, self.game_controller)
        self.descriptionWindowInstance = GameDescriptionWindow(self._instance)
        self.generateWindowInstance = GenerateWindow(self._instance, self.case_data.case.outline)
        self.interrogationWindowInstance = None
        # self.interrogationWindowInstance = InterrogationWindow(self._instance, self.game_controller, self.case_data.profiles)
        self.judgeWindowInstance = JudgeWindow(self._instance, self.game_controller, self.case_data)
        self.overviewWindowInstance = OverviewWindow(self.case_data.case.outline)
        self.lawyerWindowInstance = LawyerWindow(self._instance, self.game_controller, self.case_data)
        self.prosecutorWindowInstance = ProsecutorWindow(self._instance, self.game_controller, self.case_data)
        self.textInputWindowInstance = TextInputWindow(self._instance, self.game_controller)
        self.evidenceWindowInstance = EvidenceWindow(self.case_data.evidences) #evidence: List
        self.warningWindowInstance = WarningWindow("재판과 관련 없는 내용입니다.")

    def hideAllWindow(self):
        self.startWindowInstance.hide()
        self.descriptionWindowInstance.hide()
        self.generateWindowInstance.hide()
        # self.interrogationWindowInstance.hide()
        self.judgeWindowInstance.hide()
        self.overviewWindowInstance.hide()
        self.lawyerWindowInstance.hide()
        self.prosecutorWindowInstance.hide()
        self.textInputWindowInstance.hide()
        self.evidenceWindowInstance.hide()
        self.warningWindowInstance.hide()

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
            QMessageBox.critical(None, "초기화 오류", "게임 데이터 초기화에 실패했습니다.")
        # "initialized" 시그널이 GameController로부터 오면 is_gc_initialized, case_data가 설정되고 로딩 다이얼로그가 닫힘.

    def setStartButtonState(self, state: bool, msg: str):
        if msg == None:
            msg = "게임 시작"
        # 시작 버튼 상태 설정
        # startWindowInstance.setStartButtonState(state, msg)
        pass


    @pyqtSlot(str, object)
    def receive_game_signal(self, code: str, arg=None):
        print(f"[{self.__class__.__name__}] Signal Received: Code='{code}', ArgType='{type(arg)}', ArgValue='{str(arg)[:100]}...'") # Log arg value safely

        if code == "no_context":
            if isinstance(arg, dict):
                self.warningWindowInstance.set_label_text(arg.get("message"))
                self.warningWindowInstance.show()
            else:
                self.warningWindowInstance.set_label_text("재판과 관련 없는 내용입니다.")
                self.warningWindowInstance.show()

        elif code == "interrogation_accepted":
            if isinstance(arg, dict):
                print(f"Interrogation accepted for {arg.get('type')}. Judge: {arg.get('message')}")
                ip = None
                for i in self.case_data.profiles:
                    if i.type == arg.get('type'):
                        ip = i
                        break
                self.interrogationWindowInstance = InterrogationWindow(self._instance, self.game_controller, ip)
                self.interrogationWindowInstance.update_dialogue(arg.get("role", "판사") + " : " + arg.get("message","심문을 시작합니다."))
                self.interrogationWindowInstance.evidence_tag_reset()
                self.hideAllWindow()
                self.interrogationWindowInstance.show()

        elif code == "objection":
            if isinstance(arg, dict):
                self.warningWindowInstance.set_label_text(f"{arg.get('role', '')}의 이의 제기" + "\n" + arg.get("message", "이의 있습니다!"))
                self.warningWindowInstance.show()

        elif code == "judgement": # GameController에서 'judgement'로 판결 시작을 알림
            if isinstance(arg, dict) and arg.get('role') == '판사':
                print(f"Judgement phase initiated by {arg.get('role')}: {arg.get('message')}")
                if hasattr(GameController, 'done'):
                    self.hideAllWindow()
                    self.judgeWindowInstance.show()
                    GameController.done()
                else:
                    print("ERROR: GameController does not have 'done' method to trigger final verdict.")

        elif code == "evidence_changed":
            pass


        elif code == "evidence_tagged": # 또는 "evidence_taged" (이슈의 오타일 수 있음)
            print(f"Evidence tagged: {arg}")
            self.interrogationWindowInstance.evidence_tagged()


        elif code == "interrogation": # GameController의 user_input에서 이 시그널을 사용 ("interrogation_dialogue" 대신)
            self.isInterrogation = True
            if isinstance(arg, dict):
                self.interrogationWindowInstance.update_profile_text_label(arg.get("role","??") + " : " + arg.get("message","..."))
            else:
                self.interrogationWindowInstance.update_profile_text_label("AI" + " : " + str(arg))
        

        # GameController 이슈에 명시된 'verdict' 시그널은 판결 '내용' 스트리밍을 위한 것일 수 있습니다.
        # 현재 GameController 코드에서는 'judgement' 시그널로 판결 '시작'을 알리고 있습니다.
        # 만약 판결 내용이 스트리밍된다면, 별도의 시그널 이름(예: "verdict_chunk", "truth_chunk")을 사용하거나
        # 'verdict' 시그널의 arg가 실제 판결 내용 문자열이어야 합니다.
        # 아래는 임시로 "verdict" 시그널이 판결 내용 청크라고 가정하고 작성.
        elif code == "verdict": # 판결 내용 청크 (가정)
            if self.result_screen_instance and self.stacked_layout.currentWidget() == self.result_screen_instance:
                self.result_screen_instance.append_judgement_chunk(str(arg)) # 또는 append_truth_chunk

        # 만약 GameController가 판결 요약과 진실을 구분해서 보낸다면,
        # "verdict_summary_chunk", "verdict_summary_done", "truth_chunk", "truth_done" 같은
        # 더 세분화된 시그널 코드를 사용하는 것이 좋습니다. 현재 코드에는 이 부분이 명확하지 않습니다.


        elif code == "record_start":
            if self.isInterrogation:
                self.interrogationWindowInstance.set_mic_button_state(True)
                return

            if self.isTurnProsecutor:
                self.prosecutorWindowInstance.toggle_mic_state()
            else:
                self.lawyerWindowInstance.toggle_mic_state()

        elif code == "record_stop":
            if self.isInterrogation:
                self.interrogationWindowInstance.set_mic_button_state(False)
                return

            if self.isTurnProsecutor:
                self.prosecutorWindowInstance.toggle_mic_state()
            else:
                self.lawyerWindowInstance.toggle_mic_state()
        
        elif code == "error_occurred":
            error_message = str(arg) if arg else "알 수 없는 오류가 발생했습니다."
            QMessageBox.critical(None, "오류 발생", error_message)
            if self.loading_dialog: self.loading_dialog.accept()
            # 오류 상황에 따라 UI 상태 복구 또는 재시도 버튼 활성화
            if not self.is_gc_initialized :
                 self._update_start_button("오류 발생 (재시도)", True)

        else:
            print(f"[{self.__class__.__name__}] Unknown signal code: {code}")
    
    def open_generate_window(self):
        self.generateWindowInstance.show()

    def open_prosecutor_window(self):
        self.prosecutorWindowInstance.show()
        self.isTurnProsecutor = True
        
    def open_lawyer_window(self):
        self.lawyerWindowInstance.show()    
        self.isTurnProsecutor = False

    def open_judge_window(self):
        self.judgeWindowInstance.show()

    def open_evidence_window(self):
        self.evidenceWindowInstance.show()
    
    def open_overview_window(self):
        self.overviewWindowInstance.show()
    
    def open_description_window(self):
        self.descriptionWindowInstance.show()
    
    def open_text_input_window(self):
        self.textInputWindowInstance.show()

    def open_start_window(self):
        self.startWindowInstance.show()
        
    def _handle_text_input(self, text):
        """텍스트 입력 처리"""
        print(f"입력받은 텍스트: {text}")




if __name__ == "__main__" :
    #QApplication : 프로그램을 실행시켜주는 클래스
    app = QApplication(sys.argv) 

    #startWindowClass의 인스턴스 생성
    # startWindow = startWindowClass()

    #프로그램 화면을 보여주는 코드
    # startWindow.show()

    #프로그램을 이벤트루프로 진입시키는(프로그램을 작동시키는) 코드
    app.exec_()