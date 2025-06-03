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

        logo_label = ResizableImage(_get_image_path, "start.png")
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
        # CaseData 객체의 profiles가 실제 객체 리스트라고 가정 (예: Profile 클래스 인스턴스)
        # 만약 self.case_data.profiles가 이미 dict 리스트라면 이 변환은 필요 없음
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
        # CaseData 객체의 evidences가 실제 객체 리스트라고 가정 (예: Evidence 클래스 인스턴스)
        for e_obj in self.case_data.evidences:
            evidence_list.append({
                "id": e_obj.id, "name": e_obj.name, "type": e_obj.type,
                "description": e_obj.description, # description이 리스트일 수도, 문자열일 수도 있음
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

        # self.case_data.case.outline이 문자열이라고 가정
        summary = self.case_data.case.outline
        profiles_list = self._get_profiles_as_list_of_dicts() # CaseData.profiles가 객체 리스트일 경우 변환
        evidences_list = self._get_evidences_as_list_of_dicts() # CaseData.evidences가 객체 리스트일 경우 변환

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
        for p_obj in self.case_data.profiles: # self.case_data.profiles가 Profile 객체들의 리스트라고 가정
            item_text = f"{p_obj.name} ({self.type_map.get(p_obj.type, p_obj.type)})"
            list_item = QListWidgetItem(item_text)
            # GameController에 심문 대상의 이름(고유 ID 역할)을 전달하기 위함
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
        list_widget.itemDoubleClicked.connect(accept_selection) # 더블 클릭으로도 선택 가능
        cancel_button.clicked.connect(dialog.reject)

        if dialog.exec_() == QDialog.Accepted and selected_character_data:
            target_character_name = selected_character_data['name']
            target_character_role_display = selected_character_data['role_display']
            target_character_title = f"이름: {target_character_name} ({target_character_role_display})"
            
            # GameController에 심문 대상 설정 (interrogator 모듈이 있다면)
            # GameController의 interrogator가 set_current_profile_by_name 같은 메소드를 가지고 있다고 가정
            if hasattr(self.game_controller, '_interrogator') and \
               hasattr(self.game_controller._interrogator, 'set_current_profile_by_name'):
                self.game_controller._interrogator.set_current_profile_by_name(target_character_name)
            else:
                print(f"Warning: GameController._interrogator.set_current_profile_by_name not found. Character '{target_character_name}' may not be set in controller.")

            self.show_interrogation_screen(calling_screen_type, target_character_title)


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
            profiles_text=self._generate_profiles_text_for_display(), # 전체 프로필 정보
            target_character_title=target_character_title # "이름: OOO (역할)"
        )
        self.stacked_layout.addWidget(self.interrogation_screen_instance)
        self.stacked_layout.setCurrentWidget(self.interrogation_screen_instance)

    def _generate_profiles_text_for_display(self):
        if not self.case_data or not self.case_data.profiles: return ""
        profile_texts = []
        for p_obj in self.case_data.profiles: # p_obj는 Profile 객체라고 가정
            text = (f"이름: {p_obj.name} ({self.type_map.get(p_obj.type, p_obj.type)})\n"
                    f"성별: {self.gender_map.get(p_obj.gender, p_obj.gender)}, 나이: {p_obj.age}세\n"
                    f"사연: {p_obj.context}")
            profile_texts.append(text)
        return "\n--------------------------------\n".join(profile_texts)

    def handle_interrogation_back(self):
        self._cleanup_screen('interrogation_screen_instance')
        # GameController에 심문 종료 알림 (Jira 요구사항)
        if hasattr(self.game_controller, 'interrogation_end'):
            self.game_controller.interrogation_end()
        else:
            # GameController 클래스 자체에 interrogation_end 스태틱/클래스 메소드가 있을 수도 있음
            if hasattr(GameController, 'interrogation_end'):
                 GameController.interrogation_end() # 이 경우는 self.game_controller 인스턴스 메소드가 아님
            else:
                print("Warning: GameController.interrogation_end method not found.")


        if self.previous_screen_for_interrogation == 'prosecutor':
            self.show_prosecutor_screen()
        elif self.previous_screen_for_interrogation == 'lawyer':
            self.show_lawyer_screen()
        else:
            self.show_start_screen() # 기본값
        self.previous_screen_for_interrogation = None

    def prepare_for_judgement(self):
        print("Preparing for judgement...")
        self._cleanup_screen('prosecutor_screen_instance')
        self._cleanup_screen('lawyer_screen_instance')
        self._cleanup_screen('interrogation_screen_instance')
        self._cleanup_screen('result_screen_instance')

        self.result_screen_instance = ResultScreen(
            game_controller=self.game_controller,
            on_restart_callback=self.restart_game_flow # 비동기 함수를 콜백으로 전달
        )
        if self.case_data:
            self.result_screen_instance.set_initial_data(
                self.case_data.case.outline,
                self._generate_profiles_text_for_display()
            )
        self.result_screen_instance.prepare_for_results()

        self.stacked_layout.addWidget(self.result_screen_instance)
        self.stacked_layout.setCurrentWidget(self.result_screen_instance)

        # GameController에 발언 종료 및 판결 요청 (Jira 요구사항)
        if hasattr(self.game_controller, 'done'):
            self.game_controller.done()
        else:
            # GameController 클래스 자체에 done 스태틱/클래스 메소드가 있을 수도 있음
            if hasattr(GameController, 'done'):
                GameController.done() # 이 경우는 self.game_controller 인스턴스 메소드가 아님
            else:
                print("ERROR: GameController does not have 'done' method to trigger final verdict.")
                if self.result_screen_instance:
                    self.result_screen_instance.display_error("판결 생성 요청 실패.")

    async def restart_game_flow(self): # 비동기로 선언
        print("Restarting game flow...")
        if self.loading_dialog:
            self.loading_dialog.accept()
            self.loading_dialog = None

        self.loading_dialog = LoadingDialog("게임 재시작 중...", parent=self)
        self.loading_dialog.show()
        QApplication.processEvents() # 로딩 다이얼로그가 즉시 표시되도록

        self._cleanup_screen('result_screen_instance')
        self._cleanup_screen('prosecutor_screen_instance')
        self._cleanup_screen('lawyer_screen_instance')
        self._cleanup_screen('intro_screen_instance')
        self._cleanup_screen('interrogation_screen_instance')

        self.is_gc_initialized = False
        self.case_data = None 
        self._update_start_button("데이터 로딩 중...", False)
        self.stacked_layout.setCurrentWidget(self.start_screen)
        
        # GameController 재초기화 로직은 main.py에서 담당하거나,
        # GameController 자체에 reset/re-initialize 기능이 필요합니다.
        # 현재 MainWindow는 "initialized" 시그널을 다시 기다리는 상태가 됩니다.
        # 만약 GameController에 reset 메소드가 있다면 여기서 호출할 수 있습니다.
        # 예: if hasattr(self.game_controller, 'reset_game'): await self.game_controller.reset_game()
        # 지금은 main.py나 GameController의 시그널 재발송에 의존합니다.
        print("MainWindow: Waiting for GameController to re-initialize for restart...")
        # main.py에서 GameController.initialize()를 다시 호출하고,
        # 성공하면 "initialized" 시그널이 와서 self.loading_dialog가 닫히고 버튼이 활성화될 것입니다.
        # 만약 이 과정이 오래 걸리거나 실패하면 로딩 다이얼로그가 계속 떠 있을 수 있습니다.
        # GameController의 재초기화가 성공적으로 "initialized" 시그널을 보내는지 확인이 중요합니다.

    @pyqtSlot(str, object)
    def receive_game_signal(self, code: str, arg=None):
        print(f"[{self.__class__.__name__}] Signal Received: Code='{code}', ArgType='{type(arg)}', ArgValue='{str(arg)[:100]}...'")

        # 1. 메시지 기반 코드 처리 (주로 dict 형태의 arg)
        if code == "no_context":
            # 예시: {"role": "판사", "message": "__측은 재판과 상관 있는 말을 하세요"}
            if isinstance(arg, dict):
                QMessageBox.warning(self, arg.get("role", "알림"), arg.get("message", "관련 없는 내용입니다."))
            else:
                QMessageBox.warning(self, "알림", "재판과 관련 없는 내용입니다." if isinstance(arg, str) else "부적절한 컨텐츠입니다.")

        elif code == "interrogation_accepted":
            # 예시: {"role": "판사", "message": "피고인 심문을 진행하세요", "type": "defendant"}
            if isinstance(arg, dict):
                print(f"Interrogation accepted for {arg.get('type')}. Judge: {arg.get('message')}")
                # 현재 화면이 InterrogationScreen일 경우, 판사 메시지 업데이트
                if self.interrogation_screen_instance and self.stacked_layout.currentWidget() == self.interrogation_screen_instance:
                    self.interrogation_screen_instance.update_dialogue(arg.get("role", "판사"), arg.get("message", "심문을 시작합니다."))
                else:
                    # 일반적인 정보 메시지로 표시할 수도 있습니다.
                    QMessageBox.information(self, arg.get("role", "알림"), arg.get("message", "심문이 수락되었습니다."))


        elif code == "objection":
            # 예시: {"role": "변호사", "message": "이의 있음!"}
            if isinstance(arg, dict):
                QMessageBox.information(self, f"{arg.get('role', '이의 제기')}의 이의", arg.get("message", "이의 있습니다!"))
            else:
                QMessageBox.information(self, "이의 제기", str(arg) if isinstance(arg, str) else "이의가 제기되었습니다.")

        elif code == "judgement": # 이슈의 "verdict_accepted" 에 해당될 수 있음
            # 예시: {"role": "판사", "message": "최종 판결을 시작하겠습니다"}
            # 이 시그널은 최종 판결 *시작*을 알리는 용도일 수 있습니다.
            # 실제 판결 내용은 "verdict" 시그널로 스트리밍됩니다.
            if isinstance(arg, dict) and arg.get('role') == '판사':
                print(f"Judgement phase initiated by {arg.get('role')}: {arg.get('message')}")
                if self.result_screen_instance and self.stacked_layout.currentWidget() == self.result_screen_instance:
                    # ResultScreen의 특정 메소드를 호출하여 판결 시작을 알릴 수 있습니다.
                    # 예: self.result_screen_instance.display_message(arg.get("message"))
                    # 현재 ResultScreen은 prepare_for_results() 후 verdict 시그널을 기다리므로, 여기서는 로그만 남겨도 될 수 있습니다.
                    pass # ResultScreen의 prepare_for_results()가 이미 호출되었을 것이므로, 추가 UI 변경은 필요 없을 수 있음
            else:
                print(f"Judgement signal received with arg: {arg}")


        # 2. 객체 관련 처리
        elif code == "initialized":
            # arg: CaseData 객체
            print("Signal 'initialized' received from GameController.")
            if arg is None: # CaseData 객체가 와야 함
                print("ERROR: 'initialized' signal received with None argument. Cannot start game.")
                self.is_gc_initialized = False
                self.case_data = None
                QMessageBox.critical(self, "초기화 오류", "게임 데이터 초기화에 실패했습니다. 앱을 재시작하거나 관리자에게 문의하세요.")
                self._update_start_button("초기화 실패", False)
                if self.loading_dialog: # 재시작 시 로딩 다이얼로그가 떠 있었다면 닫기
                    self.loading_dialog.accept()
                    self.loading_dialog = None
                return

            # 여기서 arg는 CaseData 타입의 객체여야 합니다.
            # from core.data_models import CaseData # 타입 확인용
            # if not isinstance(arg, CaseData):
            #    print(f"ERROR: 'initialized' signal received with unexpected data type: {type(arg)}")
            #    # ... 오류 처리 ...
            #    return

            self.case_data = arg # CaseData 객체 저장
            self.is_gc_initialized = True
            self._update_start_button("시작하기", True)
            if self.loading_dialog: # 로딩 다이얼로그가 있다면 닫기
                self.loading_dialog.accept()
                self.loading_dialog = None
            print("GameController initialized successfully. Case data loaded and ready.")


        elif code == "evidence_changed":
            # arg: Evidence 객체
            # TODO: 증거품 변경 시 UI 업데이트 로직 (예: 현재 화면의 증거 목록 새로고침)
            print(f"Signal 'evidence_changed' received. Evidence data: {arg}")
            # if self.prosecutor_screen_instance and self.stacked_layout.currentWidget() == self.prosecutor_screen_instance:
            #     self.prosecutor_screen_instance.update_evidence_display(arg) # 예시
            # elif self.lawyer_screen_instance and self.stacked_layout.currentWidget() == self.lawyer_screen_instance:
            #     self.lawyer_screen_instance.update_evidence_display(arg) # 예시
            pass # 구체적인 UI 업데이트 요구사항이 없으므로 pass

        elif code == "evidence_tagged": # 오타 수정됨 (evidence_taged -> evidence_tagged)
            # arg: Evidence 객체
            # TODO: 증거품 태그 시 UI 업데이트 로직
            print(f"Signal 'evidence_tagged' received. Evidence data: {arg}")
            pass # 구체적인 UI 업데이트 요구사항이 없으므로 pass

        # 3. LLM 응답 (문장 단위, str)
        elif code == "interrogation":
            # arg: str (심문 중 LLM의 답변 문장)
            if self.interrogation_screen_instance and self.stacked_layout.currentWidget() == self.interrogation_screen_instance:
                if isinstance(arg, dict): # 기존 코드 호환성 유지 (role, message)
                    self.interrogation_screen_instance.update_dialogue(arg.get("role","AI"), arg.get("message","..."))
                elif isinstance(arg, str):
                     # GameController에서 오는 "interrogation" 시그널은 보통 {"role": "캐릭터명", "message": "대사"} 형태일 수 있습니다.
                     # 만약 순수 문자열만 온다면, 화자를 "AI" 또는 현재 심문 대상으로 설정해야 합니다.
                     # GameController와의 약속에 따라 처리해야 합니다.
                     # 여기서는 arg가 단순 문자열일 경우 화자를 "AI"로 가정합니다.
                     # 실제로는 GameController가 보낸 데이터 형식에 맞춰 화자를 결정해야 합니다.
                     # 예: self.interrogation_screen_instance.update_dialogue(self.interrogation_screen_instance.current_character_name_or_role, arg)
                    self.interrogation_screen_instance.update_dialogue("상대방", arg) # 혹은 현재 심문 대상의 이름/역할
                else:
                    self.interrogation_screen_instance.update_dialogue("AI", str(arg))
            else:
                print(f"Interrogation response received but screen not active: {arg}")

        elif code == "verdict":
            # arg: str (판결 내용 스트림)
            if self.result_screen_instance and self.stacked_layout.currentWidget() == self.result_screen_instance:
                # ResultScreen의 append_judgement_chunk 또는 유사한 메소드로 전달
                # GameController가 "판결 요약"과 "사건의 진실"을 구분해서 보낼 경우,
                # 이 시그널의 arg에 추가 정보가 있거나, 별도의 시그널을 사용해야 할 수 있습니다.
                # 현재는 하나의 스트림으로 가정하고 ResultScreen의 append_judgement_chunk 호출
                self.result_screen_instance.append_judgement_chunk(str(arg))
                # 모든 판결 내용 수신 후, GameController에서 "verdict_end" 같은 시그널을 보내면
                # self.result_screen_instance.finalize_results() 등을 호출할 수 있습니다.
            else:
                print(f"Verdict stream received but screen not active: {arg}")

        # 4. 녹음 컨트롤 (변경된 시그널)
        elif code == "record_toggled":
            # arg: bool (True: 녹음 시작됨, False: 녹음 중지됨)
            is_recording = bool(arg)
            print(f"Signal 'record_toggled' received. Is recording: {is_recording}")
            current_screen = self.stacked_layout.currentWidget()
            if hasattr(current_screen, 'set_mic_button_state'):
                current_screen.set_mic_button_state(is_recording)
            else:
                print(f"Current screen {type(current_screen).__name__} does not have set_mic_button_state method.")

        # 5. 기타 게임 상태/오류 처리
        elif code == "error_occurred":
            # arg: str (에러 메시지)
            error_message = str(arg) if arg else "알 수 없는 오류가 발생했습니다."
            QMessageBox.critical(self, "오류 발생", error_message)
            if self.loading_dialog:
                self.loading_dialog.accept()
                self.loading_dialog = None
            # 초기화 중 에러였다면 시작 버튼 상태 업데이트
            if not self.is_gc_initialized:
                self._update_start_button("오류 발생 (재시도)", True) # 또는 False로 두어 재시작 유도

        else:
            print(f"[{self.__class__.__name__}] Unknown or unhandled signal code: {code}")
            # 해당 code에 대한 처리가 필요하면 여기에 추가
            pass