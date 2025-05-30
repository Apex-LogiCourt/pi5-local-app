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
# from core.data_models import CaseData, Evidence, Profile # 필요시 타입 힌팅용

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
        self.init_game_controller_ui_setup() # 메서드 이름 변경 및 역할 명확화


    def init_ui(self):
        self.stacked_layout = QStackedLayout()

        self.start_screen = self.create_start_screen()
        self.game_description_screen_instance = GameDescriptionScreen(
            on_back_callback=self.show_start_screen,
            game_controller=self.game_controller
        )

        self.stacked_layout.addWidget(self.start_screen)
        self.stacked_layout.addWidget(self.game_description_screen_instance)

        self.setLayout(self.stacked_layout)
        self.setStyleSheet(f"background-color: {DARK_BG_COLOR};")


    def init_game_controller_ui_setup(self):
        # 이 메서드는 MainWindow UI가 GameController의 초기 상태를
        # (main.py에 의해 초기화될 때까지) 기다리는 UI 설정을 담당합니다.
        print("MainWindow: Waiting for GameController to be initialized by main.py...")
        self._update_start_button("컨트롤러 초기화 중...", False)
        # GameController.initialize() 호출은 main.py에서 수행하므로,
        # MainWindow 내부에서 다시 호출하지 않습니다.
        # if hasattr(GameController, 'initialize'):
        #     pass # 제거됨
        # else:
        #     print("ERROR: GameController does not have a class method 'initialize'.") # main.py에서 GameController 존재를 보장해야 함
        #     self._update_start_button("컨트롤러 오류 (재시도)", True)


    def _update_start_button(self, text: str, enabled: bool):
        if hasattr(self, 'start_button_on_start_screen') and self.start_button_on_start_screen:
            self.start_button_on_start_screen.setText(text)
            self.start_button_on_start_screen.setEnabled(enabled)


    def create_start_screen(self):
        screen = QWidget()
        layout = QHBoxLayout(screen)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        logo_label = ResizableImage(_get_image_path, "logo.png")
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
        # 초기 버튼 상태는 init_game_controller_ui_setup에서 설정됩니다.
        # self._update_start_button("데이터 로딩 중...", False) # init_game_controller_ui_setup으로 이동
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
            # main.py에서 GameController 초기화를 담당하므로, 여기서 재시도 호출은 제거하거나 신중히 결정해야 합니다.
            # if not self.is_gc_initialized:
            #     self.init_game_controller_ui_setup() # 무한 루프 가능성 주의
            return
        
        # GameController.start_game() 호출은 main.py에서 이미 수행되었으므로,
        # MainWindow의 이 메서드에서는 UI 전환만 담당합니다.
        # if hasattr(GameController, 'start_game'):
        #     asyncio.ensure_future(GameController.start_game()) # 제거됨
        self.start_intro_sequence()
        # else:
        #     QMessageBox.critical(self, "오류", "게임 시작 로직을 찾을 수 없습니다.")


    def _get_profiles_as_list_of_dicts(self):
        if not self.case_data or not self.case_data.profiles:
            return []
        profile_list = []
        for p_obj in self.case_data.profiles:
            profile_list.append({
                "name": p_obj.name, "type": p_obj.type, "gender": p_obj.gender,
                "age": p_obj.age, "context": p_obj.context
            })
        return profile_list

    def _get_evidences_as_list_of_dicts(self):
        if not self.case_data or not self.case_data.evidences:
            return []
        evidence_list = []
        for e_obj in self.case_data.evidences:
            evidence_list.append({
                "id": e_obj.id, "name": e_obj.name, "type": e_obj.type,
                "description": e_obj.description,
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

        summary = self.case_data.case.outline
        profiles_list = self._get_profiles_as_list_of_dicts()
        evidences_list = self._get_evidences_as_list_of_dicts()

        self.intro_screen_instance = IntroScreen(
            game_controller=self.game_controller,
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
            target_character_title = f"이름: {selected_character_data['name']} ({selected_character_data['role_display']})"
            self.show_interrogation_screen(calling_screen_type, target_character_title)
            if hasattr(self.game_controller._interrogator, 'set_current_profile_by_name'):
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
        self.case_data = None 
        self._update_start_button("데이터 로딩 중...", False) # restart 시 다시 로딩 중으로 표시
        self.stacked_layout.setCurrentWidget(self.start_screen)
        
        # GameController 재초기화 (main.py에서 이루어지므로, 여기서는 GameController의 특정 reset 메서드가 있다면 호출,
        # 없다면 GameController가 "initialized" 신호를 다시 보내도록 유도해야 합니다.)
        # 현재 구조에서는 main.py가 재시작 시 GameController.initialize()를 다시 호출하도록 해야 할 수 있습니다.
        # 여기서는 단순히 상태를 초기화하고 "initialized" 신호를 기다립니다.
        # GameController에 reset 기능이 있다면 호출:
        # if hasattr(self.game_controller, 'reset_for_new_game'): # 예시 메서드명
        #    await self.game_controller.reset_for_new_game()
        # elif hasattr(GameController, 'initialize'): # 또는 initialize를 다시 호출하여 신호를 받도록 함
        #    await GameController.initialize()
        # else:
        #    print("ERROR: GameController has no suitable method for re-initialization for restart.")
        #    if self.loading_dialog: self.loading_dialog.accept()
        #    self._update_start_button("재초기화 실패 (재시도)", True)
        # 위 주석 처리된 부분은 GameController의 실제 재시작 로직에 따라 달라집니다.
        # 지금은 main.py가 재시작을 어떻게 처리하는지에 따라 GameController.initialize()가 다시 호출되고
        # "initialized" 신호가 발생할 것으로 기대합니다.
        # 만약 UI에서 직접 재초기화 트리거가 필요하면 GameController에 해당 기능이 필요합니다.
        print("MainWindow: Waiting for GameController to re-initialize for restart...")


    @pyqtSlot(str, object)
    def receive_game_signal(self, code: str, arg=None):
        print(f"[{self.__class__.__name__}] Signal Received: Code='{code}', ArgType='{type(arg)}', ArgValue='{str(arg)[:100]}...'")

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

        elif code == "judgement": 
            if isinstance(arg, dict) and arg.get('role') == '판사':
                print(f"Judgement phase initiated by {arg.get('role')}: {arg.get('message')}")
                if self.result_screen_instance and self.stacked_layout.currentWidget() == self.result_screen_instance:
                    pass


        elif code == "initialized":
            print("Signal 'initialized' received from GameController.")
            if arg is None : 
                print("ERROR: 'initialized' signal received with None argument.")
                self.is_gc_initialized = False
                self.case_data = None
                QMessageBox.critical(self, "초기화 오류", "게임 데이터 초기화에 실패했습니다. 앱을 재시작하거나 관리자에게 문의하세요.")
                # main.py에서 초기화를 담당하므로, 여기서 무한 루프를 유발할 수 있는 재시도 호출은 제거합니다.
                # self.init_game_controller_ui_setup() 
                self._update_start_button("초기화 실패", False) # 버튼 비활성화 유지 또는 다른 적절한 상태로 변경
                if self.loading_dialog: # 재시작 중이었다면
                    self.loading_dialog.accept()
                    self.loading_dialog = None
                return

            self.case_data = arg 
            self.is_gc_initialized = True
            self._update_start_button("시작하기", True)
            if self.loading_dialog:
                self.loading_dialog.accept()
                self.loading_dialog = None
            print("GameController initialized successfully. Case data loaded.")


        elif code == "evidence_changed":
            print(f"Evidence changed: {arg}")

        elif code == "evidence_tagged": 
            print(f"Evidence tagged: {arg}")

        elif code == "interrogation": 
            if self.interrogation_screen_instance and self.stacked_layout.currentWidget() == self.interrogation_screen_instance:
                if isinstance(arg, dict): 
                    self.interrogation_screen_instance.update_dialogue(arg.get("role","??"), arg.get("message","..."))
                else:
                    self.interrogation_screen_instance.update_dialogue("AI", str(arg))

        elif code == "verdict": 
            if self.result_screen_instance and self.stacked_layout.currentWidget() == self.result_screen_instance:
                self.result_screen_instance.append_judgement_chunk(str(arg))


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
            if not self.is_gc_initialized :
                self._update_start_button("오류 발생 (재시도)", True) # 혹은 False로 두어 재시작 유도

        else:
            print(f"[{self.__class__.__name__}] Unknown signal code: {code}")