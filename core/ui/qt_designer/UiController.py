import sys
import os
# qasync 설치 필요: pip install qasync
# 비동기(asyncio)와 PyQt를 함께 쓰기 위해 필수입니다.
import asyncio
from qasync import QEventLoop 

from PyQt5.QtWidgets import QApplication, QMainWindow, QStackedWidget, QWidget, QMessageBox
from PyQt5.QtCore import pyqtSlot, QObject

# 데이터 모델 및 컨트롤러 임포트 (기존 유지)
from data_models import CaseData
from game_controller import GameController
from ui.type_writer import Typewriter

# 각 윈도우 클래스 임포트 (기존 유지)
# 주의: 스택에 들어갈 윈도우들은 가능한 QMainWindow가 아닌 QWidget을 상속받는 것이 깔끔합니다.
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

# PyQt5.QtWidgets에 QSizePolicy 상수가 있으므로 import 추가
# 이 부분 필수
from PyQt5.QtWidgets import QApplication, QMainWindow, QStackedWidget, QWidget, QMessageBox, QSizePolicy
from PyQt5.QtCore import pyqtSlot, QObject, QSize # QSize 추가 (선택 사항)

# 1. 메인 애플리케이션 윈도우 (껍데기) 정의
class MainAppWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("AI 재판 게임")
        
        # [수정 필요] 초기 크기를 최소 크기로 설정 (필수 아님, 디자인에 따라 다름)
        self.resize(1280, 720) 
        
        # 중앙에 QStackedWidget 배치
        self.stack = QStackedWidget()
        
        # [핵심 수정 부분] QStackedWidget의 크기 정책을 Expanding으로 설정
        # 이렇게 해야 StackedWidget이 MainAppWindow의 크기에 맞춰 늘어납니다.
        size_policy = QSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.stack.setSizePolicy(size_policy)
        
        self.setCentralWidget(self.stack)
        
# 1. 메인 애플리케이션 윈도우 (껍데기) 정의
class MainAppWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("AI 재판 게임")
        self.resize(1280, 720) # 기본 해상도 설정

        # 중앙에 QStackedWidget 배치
        self.stack = QStackedWidget()
        self.setCentralWidget(self.stack)

class UiController(QObject):
    _instance = None

    @classmethod
    def get_instance(cls):
        if cls._instance is None:
            cls._instance = UiController()
        return cls._instance
    
    def __init__(self):
        super().__init__()
        if UiController._instance is not None:
            raise Exception("Singleton Error")
        UiController._instance = self
        
        # 메인 윈도우 생성 및 표시
        self.main_window = MainAppWindow()
        
        self.game_controller = GameController.get_instance()
        self.game_controller._signal.connect(self.receive_game_signal)
        
        self.isTurnProsecutor = True
        self.case_data = None
        self.is_gc_initialized = False

        # 타자기 효과 초기화
        self.typewriter = Typewriter(update_fn=None, char_interval=30, sentence_pause=1000)

        # 2. 페이지 관리 딕셔너리 (Lazy Loading 준비)
        # 인스턴스를 미리 만들지 않고, 필요할 때 생성하여 저장합니다.
        self.pages = {} 
        
        # 3. 팝업 창 (스택에 넣지 않고 따로 띄울 창들)
        self.evidenceWindowInstance = None
        self.warningWindowInstance = WarningWindow("경고")

        # 게임 컨트롤러 초기화 시도
        self.init_game_controller()

    # --- [핵심] 페이지 전환 및 관리 메서드 ---
    
    def switch_to_page(self, page_name, window_class, *args):
        """
        page_name: 식별자 (예: 'start', 'judge')
        window_class: 클래스 이름 (예: StartWindow)
        args: 클래스 생성자에 들어갈 인자들
        """
        # 1. 이미 생성된 페이지인지 확인
        if page_name not in self.pages:
            # 없으면 생성 (Lazy Initialization)
            print(f"[{page_name}] 페이지 최초 생성 중...")
            instance = window_class(*args)
            self.pages[page_name] = instance
            self.main_window.stack.addWidget(instance)
        
        # 2. 스택의 현재 페이지를 이걸로 변경
        widget = self.pages[page_name]
        self.main_window.stack.setCurrentWidget(widget)
        
        # 3. 메인 윈도우가 꺼져있다면 킴
        if not self.main_window.isVisible():
            self.main_window.show()

    # --- 개별 화면 열기 함수들 (수정됨) ---

    def open_start_window(self):
        # StartWindow 생성 시 필요한 인자 전달
        self.switch_to_page('start', StartWindow, self._instance, self.game_controller)
        
        # 시작 화면 열릴 때 버튼 상태 업데이트 로직 필요시 호출
        if hasattr(self.pages.get('start'), 'setStartButtonState'):
            if self.is_gc_initialized:
                self.pages['start'].setStartButtonState(True, "게임 시작")
            else:
                self.pages['start'].setStartButtonState(False, "로딩 중...")

    def open_description_window(self):
        self.switch_to_page('description', GameDescriptionWindow, self._instance)

    def open_generate_window(self):
        # case_data가 있을 때만 열도록 안전장치
        outline = self.case_data.case.outline if self.case_data else None
        self.switch_to_page('generate', GenerateWindow, self._instance, outline)

    def open_judge_window(self):
        self.switch_to_page('judge', JudgeWindow, self._instance, self.game_controller, self.case_data)

    def open_prosecutor_window(self):
        self.isTurnProsecutor = True
        self.switch_to_page('prosecutor', ProsecutorWindow, self._instance, self.game_controller, self.case_data)

    def open_lawyer_window(self):
        self.isTurnProsecutor = False
        self.switch_to_page('lawyer', LawyerWindow, self._instance, self.game_controller, self.case_data)
        
    def open_overview_window(self):
        outline = self.case_data.case.outline if self.case_data else None
        self.switch_to_page('overview', OverviewWindow, outline)

    def open_interrogation_window(self, profile):
        # 심문 창은 매번 대상이 바뀌므로 새로 생성하거나, 기존 인스턴스의 데이터를 업데이트해야 함
        # 여기서는 간단히 매번 새로 생성하여 스택에 추가하는 방식을 예시로 듦 (메모리 관리는 추후 고려)
        self.interrogationWindowInstance = InterrogationWindow(self._instance, self.game_controller, profile)
        self.main_window.stack.addWidget(self.interrogationWindowInstance)
        self.main_window.stack.setCurrentWidget(self.interrogationWindowInstance)
        
        # 타자기 타겟 업데이트
        self.typewriter.update_fn = self.interrogationWindowInstance.update_profile_text_label

    # --- 팝업 창 (스택 아님, 별도 윈도우) ---
    
    def open_evidence_window(self):
        # 증거 창은 게임 도중 언제든 봐야 하므로 별도 창으로 띄움
        if self.evidenceWindowInstance is None and self.case_data:
            self.evidenceWindowInstance = EvidenceWindow(self.case_data.evidences)
        
        if self.evidenceWindowInstance:
            self.evidenceWindowInstance.show()
            self.evidenceWindowInstance.raise_() # 맨 앞으로 가져오기

    def show_warning(self, title, message):
        self.warningWindowInstance.setWindowTitle(title)
        self.warningWindowInstance.set_label_text(message)
        self.warningWindowInstance.show()

    # --- 로직 메서드 ---

    def init_game_controller(self):
        print("Requesting GameController initialization...")
        # 시작 화면이 이미 떠있다면 버튼 비활성화
        if 'start' in self.pages:
             self.pages['start'].setStartButtonState(False, "컨트롤러 초기화 중...")
             
        if hasattr(GameController, '_is_initialized'):
            if GameController._is_initialized:
                print("GameController initialized.")
                self.is_gc_initialized = True
                self.case_data = GameController._case_data
                self.open_start_window() # 초기화 완료되면 시작 화면으로
            else:
                asyncio.ensure_future(GameController.initialize())
        else:
            print("ERROR: GameController initialize method missing.")

    @pyqtSlot(str, object)
    def receive_game_signal(self, code: str, arg=None):
        print(f"[UiController] Signal: {code}")

        if code == "interrogation_accepted":
            # 심문 시작: 스택 화면을 심문 창으로 전환
            target_type = arg.get('type')
            target_profile = next((p for p in self.case_data.profiles if p.type == target_type), None)
            
            if target_profile:
                self.open_interrogation_window(target_profile)
                self.interrogationWindowInstance.update_dialogue(
                    arg.get("role", "판사") + " : " + arg.get("message", "심문 시작")
                )

        elif code == "judgement":
            # 판결 시작: 스택 화면을 판사 창으로 전환
            self.open_judge_window()

        elif code == "objection":
            self.show_warning("이의 제기", arg.get("message", "이의 있습니다!"))

        elif code == "no_context":
            self.show_warning("경고", arg.get("message", "관련 없는 내용입니다."))

        # ... 나머지 시그널 처리 로직 (interrogation, verdict 등) ...
        elif code == "interrogation":
             if self.interrogationWindowInstance:
                msg = f"{arg.get('role', '??')} : {arg.get('message', '...')}"
                self.typewriter.enqueue(msg)

# --- 실행 부 (qasync 적용) ---
if __name__ == "__main__":
    app = QApplication(sys.argv)
    
    # asyncio 이벤트 루프를 PyQt와 통합
    loop = QEventLoop(app)
    asyncio.set_event_loop(loop)

    controller = UiController.get_instance()
    # 앱 시작 시 시작 화면 띄우기
    controller.open_start_window()

    with loop:
        loop.run_forever()