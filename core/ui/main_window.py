import sys
import os
import asyncio

# 프로젝트 루트를 sys.path에 추가 (main.py에서 ui 패키지를 찾기 위함)
# main_window.py가 ui/ 폴더에 있으므로, 한 단계 위인 프로젝트 루트를 추가합니다.
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))


from PyQt5.QtWidgets import (
    QApplication, QWidget, QPushButton, QLabel,
    QVBoxLayout, QHBoxLayout, QStackedLayout, QFrame, QMessageBox, QDialog, QInputDialog, QListWidget, QListWidgetItem
)
from PyQt5.QtGui import QFont
from PyQt5.QtCore import Qt, pyqtSignal, pyqtSlot, QTimer

# game_controller는 core 패키지에 있음
from game_controller import GameController
from data_models import CaseData, Evidence, Profile # 필요시 타입 힌팅용

# 현재 파일(main_window.py)이 ui 폴더에 있으므로,
# screen 폴더 및 다른 ui 모듈은 상대 경로로 import 합니다.
from ui.screen.intro_screen import IntroScreen
from ui.screen.prosecutor_screen import ProsecutorScreen
from ui.screen.lawyer_screen import LawyerScreen
from ui.screen.result_screen import ResultScreen, LoadingDialog
from ui.resizable_image import ResizableImage, _get_image_path, _get_profile_image_path
from ui.screen.description_screen import GameDescriptionScreen
from ui.screen.interrogation_screen import InterrogationScreen
from ui.style_constants import *


class MainWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Logicourt AI")
        self.resize(1280, 800)

        # GameController 인스턴스를 싱글톤 방식으로 가져옵니다.
        self.game_controller = GameController.get_instance()
        # GameController의 클래스 변수인 _signal에 연결합니다.
        # GameController 내부의 _send_signal 메소드에서 이 _signal을 사용해 emit합니다.
        self.game_controller._signal.connect(self.receive_game_signal)

        self.case_data = None
        self.is_gc_initialized = False

        self.type_map = {
            "defendant": "피고", "victim": "피해자",
            "witness": "목격자", "reference": "참고인"
        }
        self.gender_map = {"male": "남성", "female": "여성", "other": "기타"}

        self.intro_screen_instance = None
        self.prosecutor_screen_instance = None
        self.lawyer_screen_instance = None
        self.interrogation_screen_instance = None
        self.result_screen_instance = None
        self.game_description_screen_instance = None

        self.previous_screen_for_interrogation = None
        self.loading_dialog = None

        self.init_ui()
        self.init_game_controller()


    def init_ui(self):
        self.stacked_layout = QStackedLayout()

        self.start_screen = self.create_start_screen()
        # GameDescriptionScreen 생성 시 game_controller 인스턴스를 전달합니다.
        # (GameDescriptionScreen에서 실제로 사용하지 않더라도 일관성을 위해 전달 가능)
        self.game_description_screen_instance = GameDescriptionScreen(
            on_back_callback=self.show_start_screen,
            game_controller=self.game_controller
        )

        self.stacked_layout.addWidget(self.start_screen)
        self.stacked_layout.addWidget(self.game_description_screen_instance)

        self.setLayout(self.stacked_layout)
        self.setStyleSheet(f"background-color: {DARK_BG_COLOR};")


    def init_game_controller(self):
        print("Requesting GameController initialization...")
        self._update_start_button("컨트롤러 초기화 중...", False)

        # GameController.initialize()는 클래스 메소드이므로 클래스에서 직접 호출합니다.
        # 그리고 이는 비동기 함수이므로 asyncio.ensure_future로 실행합니다.
        if hasattr(GameController, '_is_initialized'):
            if GameController._is_initialized:
                print("GameController is already initialized. Loading case data...")
                self._update_start_button("게임 시작", True)
                self.is_gc_initialized = True
            else:
                print("GameController is not initialized. Attempting to initialize...")
                asyncio.ensure_future(GameController.initialize())
        # GameController.init_game()은 존재하지 않는 것으로 보입니다.
        # elif hasattr(GameController, 'init_game'):
        #     asyncio.ensure_future(GameController.init_game())
        else:
            print("ERROR: GameController does not have a class method 'initialize'.")
            self._update_start_button("컨트롤러 오류 (재시도)", True)


    def _update_start_button(self, text: str, enabled: bool):
        if hasattr(self, 'start_button_on_start_screen') and self.start_button_on_start_screen:
            self.start_button_on_start_screen.setText(text)
            self.start_button_on_start_screen.setEnabled(enabled)


    def create_start_screen(self):
        screen = QWidget()
        layout = QHBoxLayout(screen)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        logo_label = ResizableImage(_get_image_path, "logo.png") # _get_image_path는 ui.resizable_image에 정의
        logo_label.setStyleSheet(f"background-color: {DARK_BG_COLOR};")

        left_frame = QFrame()
        left_layout = QVBoxLayout(left_frame)
        left_layout.addWidget(logo_label)
        left_frame.setFixedWidth(self.width() // 2)
        left_frame.setStyleSheet(f"background-color: {DARK_BG_COLOR};")

        right_layout_container = QFrame()
        right_layout_container.setStyleSheet(f"background-color: {DARK_BG_COLOR};")
        right_layout = QVBoxLayout(right_layout_container)
        right_layout.setContentsMargins(50, 50, 50, 50)
        right_layout.setSpacing(20)

        title = QLabel("LogiCourt AI")
        title.setAlignment(Qt.AlignCenter)
        title.setFont(QFont("Arial", 36, QFont.Bold))
        title.setStyleSheet(f"color: {GOLD_ACCENT}; background-color: transparent;")

        subtitle = QLabel("당신의 논리, 상대의 허점, AI가 지켜보는 심문의 무대! 이 법정, 지성의 승부처")
        subtitle.setAlignment(Qt.AlignCenter)
        subtitle.setFont(QFont("Arial", 18))
        subtitle.setStyleSheet(f"color: {WHITE_TEXT}; background-color: transparent; line-height: 1.5;")
        subtitle.setWordWrap(True)

        btn_game_desc = QPushButton("게임설명")
        btn_game_desc.setStyleSheet(
            f"background-color: {DARK_GRAY_BTN_COLOR}; color: {WHITE_TEXT}; font-size: 18px; "
            f"border-radius: 10px; padding: 12px 20px; border: 1px solid #444;"
        )
        btn_game_desc.setFixedHeight(50)
        btn_game_desc.clicked.connect(self.show_game_description_screen)

        self.start_button_on_start_screen = QPushButton()
        self.start_button_on_start_screen.setStyleSheet(
            f"background-color: {PRIMARY_BLUE}; color: {WHITE_TEXT}; font-size: 20px; "
            f"border-radius: 10px; padding: 15px 25px; border: 1px solid #0056b3;"
        )
        self.start_button_on_start_screen.setFixedHeight(60)
        self._update_start_button("데이터 로딩 중...", False)
        self.start_button_on_start_screen.clicked.connect(self.handle_start_game_button)

        btn_text_mode = QPushButton("텍스트모드 (미구현)")
        btn_text_mode.setStyleSheet(
            f"background-color: {MEDIUM_GRAY_BTN_COLOR}; color: {LIGHT_GRAY_TEXT}; font-size: 18px; "
            f"border-radius: 10px; padding: 12px 20px; border: 1px solid #666;"
        )
        btn_text_mode.setFixedHeight(50)
        btn_text_mode.clicked.connect(lambda: QMessageBox.information(self, "알림", "텍스트 모드는 현재 지원되지 않습니다."))

        right_layout.addStretch(1)
        right_layout.addWidget(title)
        right_layout.addSpacing(15)
        right_layout.addWidget(subtitle)
        right_layout.addStretch(2)
        right_layout.addWidget(btn_game_desc)
        right_layout.addWidget(self.start_button_on_start_screen)
        right_layout.addWidget(btn_text_mode)
        right_layout.addStretch(1)

        layout.addWidget(left_frame)
        layout.addWidget(right_layout_container, 1)
        return screen

    def resizeEvent(self, event):
        super().resizeEvent(event)
        if hasattr(self, 'start_screen') and self.start_screen:
            left_frame = self.start_screen.layout().itemAt(0).widget()
            if left_frame:
                left_frame.setFixedWidth(self.width() // 2)

    def show_start_screen(self):
        self.stacked_layout.setCurrentWidget(self.start_screen)

    def show_game_description_screen(self):
        self.stacked_layout.setCurrentWidget(self.game_description_screen_instance)

    def _cleanup_screen(self, screen_attr_name):
        screen_instance = getattr(self, screen_attr_name, None)
        if screen_instance:
            if self.stacked_layout.indexOf(screen_instance) != -1:
                self.stacked_layout.removeWidget(screen_instance)
            screen_instance.deleteLater()
            setattr(self, screen_attr_name, None)
            print(f"Cleaned up screen: {screen_attr_name}")

    def handle_start_game_button(self):
        if not self.is_gc_initialized or not self.case_data:
            QMessageBox.warning(self, "준비 중", "게임 데이터를 아직 로드 중입니다. 잠시 후 다시 시도해주세요.")
            if not self.is_gc_initialized: # 초기화 시도 (만약 실패했었다면)
                self.init_game_controller()
            return
        
        # GameController의 start_game() 호출 (비동기)
        if hasattr(GameController, 'start_game'):
            asyncio.ensure_future(GameController.start_game())
            self.start_intro_sequence() # UI 전환은 start_game 성공 여부와 관계없이 일단 진행될 수 있음
                                         # 또는 start_game의 결과를 기다려 진행할 수도 있음 (시그널 사용)
        else:
            QMessageBox.critical(self, "오류", "게임 시작 로직을 찾을 수 없습니다.")


    def _get_profiles_as_list_of_dicts(self):
        if not self.case_data or not self.case_data.profiles:
            return []
        profile_list = []
        for p_obj in self.case_data.profiles: # CaseData의 profiles가 Profile 객체 리스트라고 가정
            profile_list.append({
                "name": p_obj.name, "type": p_obj.type, "gender": p_obj.gender,
                "age": p_obj.age, "context": p_obj.context
            })
        return profile_list

    def _get_evidences_as_list_of_dicts(self):
        if not self.case_data or not self.case_data.evidences:
            return []
        evidence_list = []
        for e_obj in self.case_data.evidences: # CaseData의 evidences가 Evidence 객체 리스트라고 가정
            evidence_list.append({
                "id": e_obj.id, "name": e_obj.name, "type": e_obj.type,
                "description": e_obj.description,
                # GameController에서 is_presented 관련 필드가 없으므로 일단 제외하거나 기본값 설정
                # "is_presented_by_prosecutor": e_obj.is_presented_by_prosecutor,
                # "is_presented_by_defense": e_obj.is_presented_by_defense
            })
        return evidence_list

    def start_intro_sequence(self):
        if not self.case_data:
            print("Case data not available for intro. Aborting.")
            QMessageBox.critical(self, "오류", "사건 데이터를 불러올 수 없습니다. 앱을 재시작해주세요.")
            return

        self._cleanup_screen('intro_screen_instance')
        self._cleanup_screen('prosecutor_screen_instance')
        self._cleanup_screen('lawyer_screen_instance')
        self._cleanup_screen('interrogation_screen_instance')
        self._cleanup_screen('result_screen_instance')

        summary = self.case_data.case.outline # CaseData 객체 구조에 따라 case.outline 접근
        profiles_list = self._get_profiles_as_list_of_dicts()
        evidences_list = self._get_evidences_as_list_of_dicts()

        self.intro_screen_instance = IntroScreen(
            game_controller=self.game_controller, # game_controller 인스턴스 전달
            on_intro_finished_callback=self.show_prosecutor_screen,
            summary_text=summary,
            profiles_data=profiles_list,
            evidences_data=evidences_list
        )
        self.stacked_layout.addWidget(self.intro_screen_instance)
        self.stacked_layout.setCurrentWidget(self.intro_screen_instance)

    def show_prosecutor_screen(self):
        if not self.case_data: return
        self._cleanup_screen('intro_screen_instance')
        self._cleanup_screen('lawyer_screen_instance')
        self._cleanup_screen('prosecutor_screen_instance')

        self.prosecutor_screen_instance = ProsecutorScreen(
            game_controller=self.game_controller,
            on_switch_to_lawyer=self.show_lawyer_screen,
            on_request_judgement=self.prepare_for_judgement,
            on_interrogate=lambda: self.initiate_interrogation('prosecutor'),
            case_summary_text=self.case_data.case.outline,
            profiles_data_list=self._get_profiles_as_list_of_dicts(),
            evidences_data_list=self._get_evidences_as_list_of_dicts()
        )
        self.stacked_layout.addWidget(self.prosecutor_screen_instance)
        self.stacked_layout.setCurrentWidget(self.prosecutor_screen_instance)

    def show_lawyer_screen(self):
        if not self.case_data: return
        self._cleanup_screen('prosecutor_screen_instance')
        self._cleanup_screen('lawyer_screen_instance')

        self.lawyer_screen_instance = LawyerScreen(
            game_controller=self.game_controller,
            on_switch_to_prosecutor=self.show_prosecutor_screen,
            on_request_judgement=self.prepare_for_judgement,
            on_interrogate=lambda: self.initiate_interrogation('lawyer'),
            case_summary_text=self.case_data.case.outline,
            profiles_data_list=self._get_profiles_as_list_of_dicts(),
            evidences_data_list=self._get_evidences_as_list_of_dicts()
        )
        self.stacked_layout.addWidget(self.lawyer_screen_instance)
        self.stacked_layout.setCurrentWidget(self.lawyer_screen_instance)

    def initiate_interrogation(self, calling_screen_type: str):
        if not self.case_data or not self.case_data.profiles:
            QMessageBox.warning(self, "정보 없음", "심문할 등장인물 정보가 없습니다.")
            return

        dialog = QDialog(self)
        dialog.setWindowTitle("심문 대상 선택")
        dialog.setMinimumWidth(300)
        layout = QVBoxLayout(dialog)
        
        list_widget = QListWidget()
        for p_obj in self.case_data.profiles:
            item_text = f"{p_obj.name} ({self.type_map.get(p_obj.type, p_obj.type)})"
            list_item = QListWidgetItem(item_text)
            # GameController에 전달할 정보로 Profile 객체 자체나 고유 ID를 저장하는 것이 더 좋을 수 있습니다.
            # 여기서는 GameController에서 Profile 객체를 이름으로 찾을 수 있다고 가정하고 title을 저장합니다.
            list_item.setData(Qt.UserRole, {"name": p_obj.name, "role_display": self.type_map.get(p_obj.type, p_obj.type)})
            list_widget.addItem(list_item)
        
        layout.addWidget(QLabel("심문할 대상을 선택하세요:"))
        layout.addWidget(list_widget)
        
        buttons = QHBoxLayout()
        ok_button = QPushButton("확인")
        cancel_button = QPushButton("취소")
        buttons.addStretch()
        buttons.addWidget(ok_button)
        buttons.addWidget(cancel_button)
        layout.addLayout(buttons)

        selected_character_data = None

        def accept_selection():
            nonlocal selected_character_data
            currentItem = list_widget.currentItem()
            if currentItem:
                selected_character_data = currentItem.data(Qt.UserRole)
                dialog.accept()
            else:
                QMessageBox.warning(dialog, "선택 필요", "심문할 대상을 선택해주세요.")

        ok_button.clicked.connect(accept_selection)
        list_widget.itemDoubleClicked.connect(accept_selection)
        cancel_button.clicked.connect(dialog.reject)

        if dialog.exec_() == QDialog.Accepted and selected_character_data:
            # InterrogationScreen에 전달할 title 문자열 생성
            target_character_title = f"이름: {selected_character_data['name']} ({selected_character_data['role_display']})"
            self.show_interrogation_screen(calling_screen_type, target_character_title)
            # GameController에 심문 대상 알림 (GameController가 Profile 객체를 이름으로 찾도록 함)
            if hasattr(self.game_controller._interrogator, 'set_current_profile_by_name'): # Interrogator에 메소드가 있다고 가정
                self.game_controller._interrogator.set_current_profile_by_name(selected_character_data['name'])


    def show_interrogation_screen(self, previous_screen_type: str, target_character_title: str):
        self.previous_screen_for_interrogation = previous_screen_type

        if previous_screen_type == 'prosecutor':
            self._cleanup_screen('prosecutor_screen_instance')
        elif previous_screen_type == 'lawyer':
            self._cleanup_screen('lawyer_screen_instance')
        
        self._cleanup_screen('interrogation_screen_instance')

        self.interrogation_screen_instance = InterrogationScreen(
            game_controller=self.game_controller,
            on_back_callback=self.handle_interrogation_back,
            case_summary_text=self.case_data.case.outline if self.case_data else "N/A",
            profiles_text=self._generate_profiles_text_for_display(),
            target_character_title=target_character_title
        )
        self.stacked_layout.addWidget(self.interrogation_screen_instance)
        self.stacked_layout.setCurrentWidget(self.interrogation_screen_instance)

    def _generate_profiles_text_for_display(self):
        if not self.case_data or not self.case_data.profiles: return ""
        profile_texts = []
        for p_obj in self.case_data.profiles:
            text = (f"이름: {p_obj.name} ({self.type_map.get(p_obj.type, p_obj.type)})\n"
                    f"성별: {self.gender_map.get(p_obj.gender, p_obj.gender)}, 나이: {p_obj.age}세\n"
                    f"사연: {p_obj.context}")
            profile_texts.append(text)
        return "\n--------------------------------\n".join(profile_texts)

    def handle_interrogation_back(self):
        self._cleanup_screen('interrogation_screen_instance')
        # GameController.interrogation_end()는 클래스 메소드
        if hasattr(GameController, 'interrogation_end'):
            GameController.interrogation_end()

        if self.previous_screen_for_interrogation == 'prosecutor':
            self.show_prosecutor_screen()
        elif self.previous_screen_for_interrogation == 'lawyer':
            self.show_lawyer_screen()
        else:
            self.show_start_screen()
        self.previous_screen_for_interrogation = None

    def prepare_for_judgement(self):
        print("Preparing for judgement...")
        self._cleanup_screen('prosecutor_screen_instance')
        self._cleanup_screen('lawyer_screen_instance')
        self._cleanup_screen('interrogation_screen_instance')
        self._cleanup_screen('result_screen_instance')

        self.result_screen_instance = ResultScreen(
            game_controller=self.game_controller,
            on_restart_callback=self.restart_game_flow
        )
        if self.case_data:
            self.result_screen_instance.set_initial_data(
                self.case_data.case.outline,
                self._generate_profiles_text_for_display()
            )
        self.result_screen_instance.prepare_for_results()

        self.stacked_layout.addWidget(self.result_screen_instance)
        self.stacked_layout.setCurrentWidget(self.result_screen_instance)

        # GameController의 done() 클래스 메소드 호출 (판결 시작 트리거로 가정)
        if hasattr(GameController, 'done'):
            GameController.done()
        else:
            print("ERROR: GameController does not have 'done' method to trigger final verdict.")
            if self.result_screen_instance:
                self.result_screen_instance.display_error("판결 생성 요청 실패.")

    async def restart_game_flow(self):
        print("Restarting game flow...")
        if self.loading_dialog:
            self.loading_dialog.accept()
            self.loading_dialog = None

        self.loading_dialog = LoadingDialog("게임 재시작 중...", parent=self)
        self.loading_dialog.show()
        QApplication.processEvents()

        self._cleanup_screen('result_screen_instance')
        self._cleanup_screen('prosecutor_screen_instance')
        self._cleanup_screen('lawyer_screen_instance')
        self._cleanup_screen('intro_screen_instance')
        self._cleanup_screen('interrogation_screen_instance')

        self.is_gc_initialized = False
        self.case_data = None # case_data 초기화
        self._update_start_button("데이터 로딩 중...", False)
        self.stacked_layout.setCurrentWidget(self.start_screen)
        
        # GameController 재초기화 (initialize 클래스 메소드 호출)
        if hasattr(GameController, 'initialize'):
             await GameController.initialize() # initialize가 CaseData를 반환하지만, 시그널로도 받을 것이므로 여기서는 호출만.
        # GameController.reset_and_reinitialize()는 없으므로 주석 처리
        # elif hasattr(GameController, 'reset_and_reinitialize'):
        #     await GameController.reset_and_reinitialize()
        else:
            print("ERROR: GameController has no 'initialize' method for re-initialization.")
            if self.loading_dialog: self.loading_dialog.accept()
            self._update_start_button("초기화 실패 (재시도)", True)
        # "initialized" 시그널이 GameController로부터 오면 is_gc_initialized, case_data가 설정되고 로딩 다이얼로그가 닫힘.

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