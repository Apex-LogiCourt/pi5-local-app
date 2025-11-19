import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

import asyncio
from PyQt5.QtWidgets import *
from PyQt5 import uic
from PyQt5.QtGui import QFont
from PyQt5.QtCore import pyqtSlot, pyqtSignal, QObject
from data_models import CaseData, Evidence, Profile, Case
from game_controller import GameController

# MainWindow 및 Pages import
from ui.MainWindow import MainWindow
from ui.pages.StartPage import StartPage
from ui.pages.GeneratePage import GeneratePage
from ui.pages.CourtPages import ProsecutorPage, LawyerPage
from ui.pages.InterrogationPage import InterrogationPage

# Dialog들 import (기존 windows 폴더에서)
from ui.qt_designer.windows.gameDescriptionWindow import GameDescriptionWindow
from ui.qt_designer.windows.evidenceWindow import EvidenceWindow
from ui.qt_designer.windows.overviewWindow import OverviewWindow
from ui.qt_designer.windows.judgeWindow import JudgeWindow
from ui.qt_designer.windows.warningWindow import WarningWindow
from ui.qt_designer.windows.textInputWindow import TextInputWindow

from ui.tools import Typewriter

import ui.qt_designer.resource_rc


class UiController(QObject):
    """UI 컨트롤러 - MainWindow + QStackedWidget 기반으로 페이지 전환 관리"""
    _instance = None

    @classmethod
    def get_instance(cls):
        if cls._instance is None:
            cls._instance = UiController()
        return cls._instance

    def __init__(self):
        super().__init__()
        if UiController._instance is not None:
            raise Exception("싱글톤 클래스는 직접 생성할 수 없습니다. get_instance() 메서드를 사용하세요.")
        UiController._instance = self
        self.game_controller = GameController.get_instance()
        self.isTurnProsecutor = True  # 처음에는 검사 턴으로 시작
        self.isInterrogation = False

        # MainWindow 생성
        self.main_window = MainWindow()

        # StartPage 생성 및 추가
        self.startPage = StartPage(self, self.game_controller)
        self.main_window.add_page("start", self.startPage)
        self.startPage.set_button_state(True, "게임 시작")

        # Dialog 윈도우들 (팝업용)
        self.descriptionWindowInstance = GameDescriptionWindow(self._instance)

        # Typewriter 초기화
        self.typewriter = Typewriter(
            update_fn=None,
            char_interval=30,
            sentence_pause=1000
        )

        # GameController 시그널 연결
        self.game_controller._signal.connect(self.receive_game_signal)

        # MainWindow 표시 (StartPage가 기본으로 보임)
        self.main_window.show()

    def createPageInstances(self):
        """게임 시작 후 나머지 페이지들 생성 및 추가"""
        # GeneratePage가 아직 없으면 생성 (stub 데이터 등)
        if not hasattr(self, 'generatePage'):
            self.generatePage = GeneratePage(self, self.case_data.case.outline)
            self.main_window.add_page("generate", self.generatePage)
            self.generatePage.backButton.setEnabled(True)

        # ProsecutorPage
        self.prosecutorPage = ProsecutorPage(self, self.game_controller, self.case_data)
        self.main_window.add_page("prosecutor", self.prosecutorPage)

        # LawyerPage
        self.lawyerPage = LawyerPage(self, self.game_controller, self.case_data)
        self.main_window.add_page("lawyer", self.lawyerPage)

        # Dialog 윈도우들 생성
        self.judgeWindowInstance = JudgeWindow(self._instance, self.game_controller, self.case_data)
        self.overviewWindowInstance = OverviewWindow(self.case_data.case.outline)
        self.textInputWindowInstance = TextInputWindow(self._instance, self.game_controller)
        self.evidenceWindowInstance = EvidenceWindow(
            self.case_data.evidences if hasattr(self.case_data, 'evidences') else []
        )
        self.warningWindowInstance = WarningWindow("재판과 관련 없는 내용입니다.")

    def switch_to_start_page(self):
        """시작 페이지로 전환"""
        self.main_window.switch_to_page("start")

    def switch_to_generate_page(self):
        """사건 생성 페이지로 전환"""
        self.main_window.switch_to_page("generate")

    def switch_to_prosecutor_page(self):
        """검사 페이지로 전환"""
        # 변호사에서 검사로 넘어가므로 왼쪽으로 스와이프
        direction = 'right' if self.isTurnProsecutor == False else None
        self.main_window.switch_to_page("prosecutor", direction)
        self.isTurnProsecutor = True

    def switch_to_lawyer_page(self):
        """변호사 페이지로 전환"""
        # 검사에서 변호사로 넘어가므로 오른쪽으로 스와이프
        direction = 'left' if self.isTurnProsecutor == True else None
        self.main_window.switch_to_page("lawyer", direction)
        self.isTurnProsecutor = False

    def switch_to_interrogation_page(self, profile):
        """심문 페이지로 전환"""
        # InterrogationPage는 매번 새로 생성 (profile이 바뀔 수 있으므로)
        interrogationPage = InterrogationPage(self, self.game_controller, profile)

        # 기존 interrogation 페이지가 있다면 제거
        if "interrogation" in self.main_window.page_indices:
            old_index = self.main_window.page_indices["interrogation"]
            old_widget = self.main_window.stacked_widget.widget(old_index)
            self.main_window.stacked_widget.removeWidget(old_widget)
            old_widget.deleteLater()
            del self.main_window.page_indices["interrogation"]

        # 새 페이지 추가 및 전환
        self.main_window.add_page("interrogation", interrogationPage)
        self.main_window.switch_to_page("interrogation")
        self.isInterrogation = True
        return interrogationPage

    async def restart_game_flow(self):
        """게임 재시작"""
        print("Restarting game flow...")
        QApplication.processEvents()

        self.is_gc_initialized = False
        self.case_data = None
        self.switch_to_start_page()
        self.startPage.set_button_state(False, "초기화 중...")

        if hasattr(GameController, 'initialize'):
            await GameController.initialize()
        else:
            print("ERROR: GameController has no 'initialize' method for re-initialization.")
            QMessageBox.critical(None, "초기화 오류", "게임 데이터 초기화에 실패했습니다.")

    @pyqtSlot(str, object)
    def receive_game_signal(self, code: str, arg=None):
        """GameController로부터 시그널 수신"""
        print(f"[{self.__class__.__name__}] Signal Received: Code='{code}', ArgType='{type(arg)}', ArgValue='{str(arg)[:100]}...'")

        handler = self._signal_handlers.get(code)
        if handler:
            handler(self, arg)
        else:
            print(f"[{self.__class__.__name__}] Unknown signal code: {code}")

    def _handle_initialization_failed(self, arg):
        """초기화 실패 처리"""
        print(f"[UiController] ❌ 초기화 실패: {arg}")
        QMessageBox.critical(None, "초기화 실패", f"케이스 데이터 생성에 실패했습니다:\n{arg}")
        self.startPage.set_button_state(True, "게임 시작 (재시도)")

    def _handle_initialized(self, arg):
        """초기화 완료 처리"""
        if arg is not None:
            # 모든 데이터가 준비된 상태
            self.case_data = arg

            # GeneratePage가 이미 생성되어 있는 경우 (케이스만 먼저 생성된 경우)
            if hasattr(self, 'generatePage'):
                # 버튼 활성화
                self.generatePage.backButton.setEnabled(True)
                # 나머지 페이지들 생성
                self.createPageInstances()
            else:
                # 처음부터 모든 데이터가 준비된 경우 (stub 데이터 등)
                self.createPageInstances()

            # 모든 데이터가 준비된 후에만 start_game 호출
            self.game_controller.start_game()
        else:
            # 케이스만 생성된 상태 - generatePage만 생성
            self.case_data = self.game_controller._case_data
            self.generatePage = GeneratePage(self, self.case_data.case.outline)
            self.main_window.add_page("generate", self.generatePage)
            # 버튼은 비활성화 상태로 유지 (기본값)

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

            # InterrogationPage로 전환
            interrogationPage = self.switch_to_interrogation_page(ip)
            interrogationPage.update_dialogue(arg.get("role", "판사") + " : " + arg.get("message", "심문을 시작합니다."))
            interrogationPage.evidence_tag_reset()

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
                self.judgeWindowInstance.show()
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
        current_page = self.main_window.get_current_page()
        if isinstance(current_page, InterrogationPage):
            current_page.evidence_tagged()

    def _handle_interrogation(self, arg):
        """심문 대화 처리"""
        current_page = self.main_window.get_current_page()

        if isinstance(current_page, InterrogationPage):
            if self.typewriter.update_fn is not current_page.update_profile_text_label:
                self.typewriter.update_fn = current_page.update_profile_text_label

            if isinstance(arg, dict):
                msg = f"{arg.get('role', '??')} : {arg.get('message', '...')}"
                self.typewriter.enqueue(msg)

    def _handle_verdict(self, arg):
        """판결 결과 처리"""
        self.judgeWindowInstance.set_judge_text(str(arg))

    def _handle_record_toggled(self, arg):
        """녹음 토글 처리"""
        current_page = self.main_window.get_current_page()

        if isinstance(current_page, InterrogationPage):
            current_page.set_mic_button_state(arg)
        elif isinstance(current_page, ProsecutorPage):
            current_page.toggle_mic_state()
        elif isinstance(current_page, LawyerPage):
            current_page.toggle_mic_state()

    def _handle_error_occurred(self, arg):
        """에러 발생 처리"""
        error_message = str(arg) if arg else "알 수 없는 오류가 발생했습니다."
        QMessageBox.critical(None, "오류 발생", error_message)

    def _handle_switch(self, arg):
        """턴 전환 처리"""
        if self.isTurnProsecutor:
            self.switch_to_lawyer_page()
        else:
            self.switch_to_prosecutor_page()

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
        "switch": _handle_switch,
    }

    # Dialog 열기 메서드들
    def open_evidence_window(self):
        self.evidenceWindowInstance.show()

    def open_overview_window(self):
        self.overviewWindowInstance.show()

    def open_description_window(self):
        self.descriptionWindowInstance.show()

    def open_text_input_window(self):
        self.textInputWindowInstance.show()

    # 하위 호환성을 위한 메서드들 (구 Dialog들이 호출하는 메서드)
    def open_start_window(self):
        """하위 호환: 시작 페이지로 전환"""
        self.switch_to_start_page()

    def open_generate_window(self):
        """하위 호환: 사건 생성 페이지로 전환"""
        self.switch_to_generate_page()

    def open_prosecutor_window(self):
        """하위 호환: 검사 페이지로 전환"""
        self.switch_to_prosecutor_page()

    def open_lawyer_window(self):
        """하위 호환: 변호사 페이지로 전환"""
        self.switch_to_lawyer_page()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.exec_()
