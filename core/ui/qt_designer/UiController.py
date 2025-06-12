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

import ui.qt_designer.resource_rc 

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
        self.turn = "prosecutor"  # 초기 턴은 검사로 설정

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
        self.lawyerWindowInstance = LawyerWindow(self._instance, self.game_controller, self.case_data)
        self.prosecutorWindowInstance = ProsecutorWindow(self._instance, self.game_controller, self.case_data)
        self.textInputWindowInstance = None
        self.evidenceWindowInstance = EvidenceWindow(self.case_data.evidences) #evidence: List
        self.warningWindowInstance = WarningWindow("재판과 관련 없는 내용입니다.")
        #이하는 테스트
        self.descriptionWindowInstance.show()
        self.prosecutorWindowInstance.show()
        self.evidenceWindowInstance.show()
        self.judgeWindowInstance.show()
        self.overviewWindowInstance.show()
        self.lawyerWindowInstance.show()
        self.warningWindowInstance.show()

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


    @pyqtSlot(str, object)
    def receive_game_signal(self, code: str, arg=None):
        print(f"[{self.__class__.__name__}] Signal Received: Code='{code}', ArgType='{type(arg)}', ArgValue='{str(arg)[:100]}...'") # Log arg value safely

        if code == "no_context":
            if isinstance(arg, dict):
                QMessageBox.warning(self, arg.get("role", "알림"), arg.get("message", "관련 없는 내용입니다."))
            else:
                QMessageBox.warning(self, "알림", "재판과 관련 없는 내용입니다.")

        elif code == "interrogation_accepted":
            if isinstance(arg, dict):
                print(f"Interrogation accepted for {arg.get('type')}. Judge: {arg.get('message')}")
                if self.interrogation_screen_instance and self.stacked_layout.currentWidget() == self.interrogation_screen_instance:
                    self.interrogation_screen_instance.update_dialogue(arg.get("role", "판사"), arg.get("message","심문을 시작합니다."))

        elif code == "objection":
            if isinstance(arg, dict):
                QMessageBox.information(self, f"{arg.get('role', '')}의 이의 제기", arg.get("message", "이의 있습니다!"))

        elif code == "judgement": # GameController에서 'judgement'로 판결 시작을 알림
             if isinstance(arg, dict) and arg.get('role') == '판사':
                print(f"Judgement phase initiated by {arg.get('role')}: {arg.get('message')}")
                if self.result_screen_instance and self.stacked_layout.currentWidget() == self.result_screen_instance:
                    # ResultScreen.prepare_for_results()가 이미 호출되었을 것이므로,
                    # 여기서는 추가적인 메시지 업데이트나 로깅만 할 수 있습니다.
                    # GameController에서 판결 내용 스트리밍을 위한 별도 시그널(예: "verdict_chunk")을 사용할 것으로 예상됩니다.
                    pass


        elif code == "initialized":
            print("Signal 'initialized' received from GameController.")
            if arg is None : # GameController.initialize()의 반환값이 None일 경우에 대한 방어 코드
                print("ERROR: 'initialized' signal received with None argument. Attempting re-initialization.")
                self.is_gc_initialized = False
                self.case_data = None
                QMessageBox.critical(self, "초기화 오류", "게임 데이터 초기화에 실패했습니다. 다시 시도합니다.")
                self.init_game_controller() # 재시도
                return

            self.case_data = arg # GameController.initialize()가 CaseData 객체를 반환하고, 그것이 arg로 전달된다고 가정
            self.is_gc_initialized = True
            self._update_start_button("시작하기", True)
            if self.loading_dialog:
                self.loading_dialog.accept()
                self.loading_dialog = None
            print("GameController initialized successfully. Case data loaded.")
            # print(f"Loaded CaseData: Outline='{self.case_data.case.outline[:50]}...' Profiles={len(self.case_data.profiles)} Evidences={len(self.case_data.evidences)}")


        elif code == "evidence_changed":
            print(f"Evidence changed: {arg}")
            # GameController에서 Evidence 객체 또는 dict가 온다고 가정
            # self.case_data.evidences 리스트 업데이트 로직 필요

        elif code == "evidence_tagged": # 또는 "evidence_taged" (이슈의 오타일 수 있음)
            print(f"Evidence tagged: {arg}")
            # self.case_data.evidences 리스트 업데이트 로직 필요

        elif code == "interrogation": # GameController의 user_input에서 이 시그널을 사용 ("interrogation_dialogue" 대신)
            if self.interrogation_screen_instance and self.stacked_layout.currentWidget() == self.interrogation_screen_instance:
                if isinstance(arg, dict): # GameController에서 {"role": str, "message": str} 형태로 보냄
                    self.interrogation_screen_instance.update_dialogue(arg.get("role","??"), arg.get("message","..."))
                else:
                    self.interrogation_screen_instance.update_dialogue("AI", str(arg)) # 단순 문자열로 올 경우

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
            print("Signal 'record_start' received. Turning mic button ON.")
            current_screen = self.stacked_layout.currentWidget()
            if hasattr(current_screen, 'set_mic_button_state'):
                current_screen.set_mic_button_state(True)

        elif code == "record_stop":
            print("Signal 'record_stop' received. Turning mic button OFF.")
            current_screen = self.stacked_layout.currentWidget()
            if hasattr(current_screen, 'set_mic_button_state'):
                current_screen.set_mic_button_state(False)
        
        elif code == "error_occurred":
            error_message = str(arg) if arg else "알 수 없는 오류가 발생했습니다."
            QMessageBox.critical(self, "오류 발생", error_message)
            if self.loading_dialog: self.loading_dialog.accept()
            # 오류 상황에 따라 UI 상태 복구 또는 재시도 버튼 활성화
            if not self.is_gc_initialized :
                 self._update_start_button("오류 발생 (재시도)", True)

        else:
            print(f"[{self.__class__.__name__}] Unknown signal code: {code}")
    
    def open_prosecutor_window(self):
        self.prosecutorWindowInstance.show()
        self.turn = "prosecutor"
        
    def open_lawyer_window(self):
        self.lawyerWindowInstance.show()    
        self.turn = "lawyer"

    def open_judge_window(self):
        self.judgeWindowInstance.show()

    def open_evidence_window(self):
        self.evidenceWindowInstance.show()
    
    def open_overview_window(self):
        self.overviewWindowInstance.show()
    
    def open_description_window(self):
        self.descriptionWindowInstance.show()
    




if __name__ == "__main__" :
    #QApplication : 프로그램을 실행시켜주는 클래스
    app = QApplication(sys.argv) 

    #startWindowClass의 인스턴스 생성
    # startWindow = startWindowClass()

    #프로그램 화면을 보여주는 코드
    # startWindow.show()

    #프로그램을 이벤트루프로 진입시키는(프로그램을 작동시키는) 코드
    app.exec_()