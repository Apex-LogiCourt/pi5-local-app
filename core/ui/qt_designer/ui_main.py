import sys
import asyncio
from PyQt5.QtWidgets import *
from PyQt5 import uic
from data_models import CaseData, Evidence, Profile
from game_controller import GameController

import resource_rc

#UI 연결. 단, UI파일은 Python 코드 파일과 같은 디렉토리에 위치해야한다.
startWindowUi = uic.loadUiType("core/ui/qt_designer/startWindow.ui")[0]
descriptionWindowUi = uic.loadUiType("core/ui/qt_designer/gameDescriptionWindow.ui")[0]
generateWindowUi = uic.loadUiType("core/ui/qt_designer/generateWindow.ui")[0]
generateWindow2Ui = uic.loadUiType("core/ui/qt_designer/generateWindow2.ui")[0]
interrogationWindowUi = uic.loadUiType("core/ui/qt_designer/interrogationWindow.ui")[0]
judgeWindowUi = uic.loadUiType("core/ui/qt_designer/judgeWindow.ui")[0]
lawyerWindowUi = uic.loadUiType("core/ui/qt_designer/lawyerWindow.ui")[0]
overviewWindowUi = uic.loadUiType("core/ui/qt_designer/overviewWindow.ui")[0]
prosecutorWindowUi = uic.loadUiType("core/ui/qt_designer/prosecutorWindow.ui")[0]
textInputWindowUi = uic.loadUiType("core/ui/qt_designer/textInputWindow.ui")[0]
evidenceWindowUi = uic.loadUiType("core/ui/qt_designer/evidenceWindow.ui")[0]


class startWindowClass(QDialog, startWindowUi) :
    def __init__(self) :
        super().__init__()
        self.setupUi(self)

        self.game_controller = GameController.get_instance()
        self.game_controller._signal.connect(self.receive_game_signal)

        self.gameStartButton.setEnabled(False)
        self.descriptionWindow = descriptionWindowClass()
        self.gameDescriptionButton.clicked.connect(self.descriptionClick)
    
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
        self.init_game_controller()

    def init_game_controller(self):
        print("Requesting GameController initialization...")
        self._update_start_button("컨트롤러 초기화 중...", False)
        if hasattr(GameController, '_is_initialized'):
            if GameController._is_initialized:
                print("GameController is already initialized. Loading case data...")
                self._update_start_button("게임 시작", True)
                self.is_gc_initialized = True
                self.case_data = GameController._case_data
            else:
                print("GameController is not initialized. Attempting to initialize...")
                asyncio.ensure_future(GameController.initialize())
        else:
            print("ERROR: GameController does not have a class method 'initialize'.")
            self._update_start_button("컨트롤러 오류 (재시도)", True)

    def _update_start_button(self, text: str, enabled: bool):
        #if hasattr(self, 'start_button_on_start_screen') and self.start_button_on_start_screen:
        self.gameStartButton.setText(text)
        self.gameStartButton.setEnabled(enabled)

    def handle_start_game_button(self):
        if not self.is_gc_initialized or not self.case_data:
            QMessageBox.warning(self, "준비 중", "게임 데이터를 아직 로드 중입니다. 잠시 후 다시 시도해주세요.")
            if not self.is_gc_initialized: # 초기화 시도 (만약 실패했었다면)
                self.init_game_controller()
        self.show_generateWindow()
        return
    
    def show_generateWindow(self):
        if not self.case_data: return
        self.generateWindow = generateWindowClass(
            game_controller=self.game_controller,
            case_summary_text=self.case_data.case.outline,
            profiles_data_list=self._get_profiles_as_list_of_dicts(),
            evidences_data_list=self._get_evidences_as_list_of_dicts()
        )
        self.generateWindow.show()
        self.close()

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
            })
        return evidence_list

    def _startClick(self):
        pass

    def _descriptionClick(self):
        self.hide()
        self.descriptionWindow.show()

    def _textClick(self):
        pass


class descriptionWindowClass(QDialog, descriptionWindowUi) :
    def __init__(self) :
        super().__init__()
        self.setupUi(self)
        self.backButton.clicked.connect(self.backClick)
    
    def backClick(self):
        self.hide()
        startWindow.show()
        pass


class generateWindowClass(QDialog, generateWindowUi):
    def __init__(self) :
        super().__init__()
        self.setupUi(self)
        self.generateWindow2 = generateWindow2Class()

    def _nextClick(self):
        
        pass


class generateWindow2Class(QDialog, generateWindowUi):
    def __init__(self) :
        super().__init__()
        self.setupUi(self)

if __name__ == "__main__" :
    #QApplication : 프로그램을 실행시켜주는 클래스
    app = QApplication(sys.argv) 

    #startWindowClass의 인스턴스 생성
    startWindow = startWindowClass()

    #프로그램 화면을 보여주는 코드
    startWindow.show()

    #프로그램을 이벤트루프로 진입시키는(프로그램을 작동시키는) 코드
    app.exec_()