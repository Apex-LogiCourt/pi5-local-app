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
from ui.tools.type_writer import Typewriter

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

        self.descriptionWindowInstance = GameDescriptionWindow(self._instance)
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
        # self.descriptionWindowInstance = GameDescriptionWindow(self._instance)
        # self.generateWindowInstance = GenerateWindow(self._instance, self.case_data.case.outline)
        self.interrogationWindowInstance = None
        # self.interrogationWindowInstance = InterrogationWindow(self._instance, self.game_controller, self.case_data.profiles)
        self.judgeWindowInstance = JudgeWindow(self._instance, self.game_controller, self.case_data)
        self.overviewWindowInstance = OverviewWindow(self.case_data.case.outline)
        self.lawyerWindowInstance = LawyerWindow(self._instance, self.game_controller, self.case_data)
        self.prosecutorWindowInstance = ProsecutorWindow(self._instance, self.game_controller, self.case_data)
        self.textInputWindowInstance = TextInputWindow(self._instance, self.game_controller)
        # 증거품이 아직 없어도 evidenceWindow 생성 (빈 리스트면 "생성 중" 표시됨)
        self.evidenceWindowInstance = EvidenceWindow(self.case_data.evidences if hasattr(self.case_data, 'evidences') else [])
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
        print(f"[{self.__class__.__name__}] Signal Received: Code='{code}', ArgType='{type(arg)}', ArgValue='{str(arg)[:100]}...'")
        
        # 딕셔너리 디스패치 패턴
        handler = self._signal_handlers.get(code)
        if handler:
            handler(self, arg)
        else:
            print(f"[{self.__class__.__name__}] Unknown signal code: {code}")
    
    def _handle_initialization_failed(self, arg):
        """초기화 실패 처리"""
        print(f"[UiController] ❌ 초기화 실패: {arg}")
        QMessageBox.critical(None, "초기화 실패", f"케이스 데이터 생성에 실패했습니다:\n{arg}")
        self.startWindowInstance.set_button_state(True, "게임 시작 (재시도)")
    
    def _handle_initialized(self, arg):
        """초기화 완료 처리"""
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
    
    def _handle_no_context(self, arg):
        """맥락 없는 내용 경고 처리"""
        if isinstance(arg, dict):
            self.warningWindowInstance.set_label_text(arg.get("message"))
        else:
            self.warningWindowInstance.set_label_text("재판과 관련 없는 내용입니다.")
        self.warningWindowInstance.show()
    
    def _handle_interrogation_accepted(self, arg):
        """심문 수락 처리"""
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
    
    def _handle_objection(self, arg):
        """이의 제기 처리"""
        if isinstance(arg, dict):
            self.warningWindowInstance.set_label_text(f"{arg.get('role', '')}의 이의 제기" + "\n" + arg.get("message", "이의 있습니다!"))
            self.warningWindowInstance.show()
    
    def _handle_judgement(self, arg):
        """판결 시작 처리"""
        if isinstance(arg, dict) and arg.get('role') == '판사':
            print(f"Judgement phase initiated by {arg.get('role')}: {arg.get('message')}")
            if hasattr(GameController, 'done'):
                self.hideAllWindow()
                self.judgeWindowInstance.show()
                self.hideCommon()
            else:
                print("ERROR: GameController does not have 'done' method to trigger final verdict.")
    
    def _handle_evidences_ready(self, arg):
        """증거품 생성 완료 처리"""
        if arg and hasattr(self, 'evidenceWindowInstance'):
            print(f"[UiController] 증거품 생성 완료, evidenceWindow 업데이트")
            self.evidenceWindowInstance.update_evidences(arg)
    
    def _handle_evidence_images_ready(self, arg):
        """증거품 이미지 생성 완료 처리"""
        if arg and hasattr(self, 'evidenceWindowInstance'):
            print(f"[UiController] 증거품 이미지 생성 완료, evidenceWindow 업데이트")
            self.evidenceWindowInstance.update_evidences(arg)
    
    def _handle_evidence_changed(self, arg):
        """증거 변경 처리"""
        pass
    
    def _handle_evidence_tagged(self, arg):
        """증거 태그 처리"""
        print(f"Evidence tagged: {arg}")
        self.interrogationWindowInstance.evidence_tagged()
    
    def _handle_interrogation(self, arg):
        """심문 대화 처리"""
        self.isInterrogation = True
        if self.typewriter.update_fn is not self.interrogationWindowInstance.update_profile_text_label:
            self.typewriter.update_fn = self.interrogationWindowInstance.update_profile_text_label
        
        if isinstance(arg, dict):
            msg = f"{arg.get('role', '??')} : {arg.get('message', '...')}"
        self.typewriter.enqueue(msg)
    
    def _handle_verdict(self, arg):
        """판결 결과 처리"""
        self.judgeWindowInstance.set_judge_text(str(arg))
    
    def _handle_record_toggled(self, arg):
        """녹음 토글 처리"""
        # arg: True(녹음 시작) / False(녹음 종료)
        if self.isInterrogation:
            self.interrogationWindowInstance.set_mic_button_state(arg)
        else:
            if self.isTurnProsecutor:
                self.prosecutorWindowInstance.toggle_mic_state()
            else:
                self.lawyerWindowInstance.toggle_mic_state()
    
    def _handle_error_occurred(self, arg):
        """에러 발생 처리"""
        error_message = str(arg) if arg else "알 수 없는 오류가 발생했습니다."
        QMessageBox.critical(None, "오류 발생", error_message)
        if self.loading_dialog: 
            self.loading_dialog.accept()
        # 오류 상황에 따라 UI 상태 복구 또는 재시도 버튼 활성화
        if not self.is_gc_initialized:
            self._update_start_button("오류 발생 (재시도)", True)
    
    # 시그널 핸들러 매핑
    _signal_handlers = {
        "initialization_failed": _handle_initialization_failed,
        "initialized": _handle_initialized,
        "no_context": _handle_no_context,
        "interrogation_accepted": _handle_interrogation_accepted,
        "objection": _handle_objection,
        "judgement": _handle_judgement,
        "evidences_ready": _handle_evidences_ready,
        "evidence_images_ready": _handle_evidence_images_ready,
        "evidence_changed": _handle_evidence_changed,
        "evidence_tagged": _handle_evidence_tagged,
        "interrogation": _handle_interrogation,
        "verdict": _handle_verdict,
        "record_toggled": _handle_record_toggled,
        "error_occurred": _handle_error_occurred,
    }
    


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