import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

import asyncio
from PyQt5.QtWidgets import *
from PyQt5 import uic
from PyQt5.QtGui import QFont
from PyQt5.QtCore import pyqtSlot
from data_models import CaseData, Evidence, Profile, Case
from game_controller import GameController

from ui.qt_designer.windows.gameDescriptionWindow import GameDescriptionWindow
from ui.qt_designer.windows.evidenceWindow import EvidenceWindow
from ui.qt_designer.windows.common import LawyerWindow, ProsecutorWindow
from ui.qt_designer.windows.overviewWindow import OverviewWindow
from ui.qt_designer.windows.judgeWindow import JudgeWindow
from ui.qt_designer.windows.warningWindow import WarningWindow
from ui.qt_designer.windows.generateWindow import GenerateWindow
from ui.qt_designer.windows.interrogationWindow import InterrogationWindow
from ui.qt_designer.windows.textInputWindow import TextInputWindow
from ui.qt_designer.windows.startWindow import StartWindow
from PyQt5.QtCore import pyqtSignal, QObject, pyqtSlot
from ui.type_writer import Typewriter

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
        self.isTurnProsecutor = True # 처음에는 검사 턴으로 시작

        self.startWindowInstance = StartWindow(self._instance, self.game_controller)
        self.startWindowInstance.set_button_state(True, "게임 시작")  # 시작 버튼 활성화

        # Typewriter 먼저 생성 (신호 연결 전에!)
        self.typewriter = Typewriter(
            update_fn=None, # overview에 출력
            char_interval=30,     # 글자 속도 (ms)
            sentence_pause=1000    # 한 문장 당 다 찍고 나서 쉬는 시간 (ms)
        )

        self.game_controller._signal.connect(self.receive_game_signal)
        self.startWindowInstance.show()

    def startWindow(self):
        # app = QApplication(sys.argv)
        # window = StartWindow()
        # window.show()
        # app.exec_()
        pass

    def init_game_controller(self):
        pass
    
    def createWindowInstance(self):
        self.descriptionWindowInstance = GameDescriptionWindow(self._instance)
        # self.generateWindowInstance = GenerateWindow(self._instance, self.case_data.case.outline)
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
    
    def hideCommon(self):
        self.lawyerWindowInstance.hide()
        self.prosecutorWindowInstance.hide()

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


            
        if code == "initialization_failed":
            # 초기화 실패 시 에러 메시지
            print(f"[UiController] ❌ 초기화 실패: {arg}")
            QMessageBox.critical(None, "초기화 실패", f"케이스 데이터 생성에 실패했습니다:\n{arg}")
            self.startWindowInstance.set_button_state(True, "게임 시작 (재시도)")

        elif code == "initialized":
            if arg is not None:
                self.case_data = arg
                self.createWindowInstance()
                self.generateWindowInstance.backButton.setEnabled(True)
                # 모든 데이터가 준비된 후에만 start_game 호출
                self.game_controller.start_game()
            else: 
                # 케이스만 생성된 상태 - generateWindow만 생성
                self.case_data = self.game_controller._case_data
                self.generateWindowInstance = GenerateWindow(self._instance, self.case_data.case.outline)
        elif code == "no_context":
            if isinstance(arg, dict):
                self.warningWindowInstance.set_label_text(arg.get("message"))
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
            # if self.nowJudgement: return
            # self.nowJudgement = True
            if isinstance(arg, dict) and arg.get('role') == '판사':
                print(f"Judgement phase initiated by {arg.get('role')}: {arg.get('message')}")
                if hasattr(GameController, 'done'):
                    self.hideAllWindow()
                    self.judgeWindowInstance.show()
                    self.hideCommon()
                else:
                    print("ERROR: GameController does not have 'done' method to trigger final verdict.")

        elif code == "evidence_changed":
            pass


        elif code == "evidence_tagged": # 또는 "evidence_taged" (이슈의 오타일 수 있음)
            print(f"Evidence tagged: {arg}")
            self.interrogationWindowInstance.evidence_tagged()


        elif code == "interrogation": # GameController의 user_input에서 이 시그널을 사용 ("interrogation_dialogue" 대신)
            self.isInterrogation = True
            if self.typewriter.update_fn is not self.interrogationWindowInstance.update_profile_text_label:
                self.typewriter.update_fn = self.interrogationWindowInstance.update_profile_text_label
            
            if isinstance(arg, dict):
                msg = f"{arg.get('role', '??')} : {arg.get('message', '...')}"
            self.typewriter.enqueue(msg)

        elif code == "verdict": 
            self.judgeWindowInstance.set_judge_text(str(arg))


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
        


if __name__ == "__main__" :
    #QApplication : 프로그램을 실행시켜주는 클래스
    app = QApplication(sys.argv) 

    #startWindowClass의 인스턴스 생성
    # startWindow = startWindowClass()

    #프로그램 화면을 보여주는 코드
    # startWindow.show()

    #프로그램을 이벤트루프로 진입시키는(프로그램을 작동시키는) 코드
    app.exec_()