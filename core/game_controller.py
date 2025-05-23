from typing import List, Dict, Optional
from data_models import CaseData, Evidence, Profile, Case, GameState, Phase, Role
from controller import CaseDataManager
from PyQt5.QtCore import QObject, pyqtSignal, pyqtSlot
import asyncio
import time
from interrogation.interrogator import Interrogator, it

class GameController(QObject):
    _instance = None
    _isInitialized = False
    _state : GameState = None
    _case : Case = None
    _evidences : List[Evidence] = None
    _profiles : List[Profile] = None
    _case_data : CaseData = None
    _signal = pyqtSignal(str, object)
    _interrogator : Interrogator = it.get_instance()

    
    @classmethod
    def get_instance(cls):
        if cls._instance is None:
            cls._instance = GameController()
        return cls._instance
    
    def __init__(self):
        """
        GameController 초기화.
        - data_service: CaseDataService 인스턴스 (데이터 로드/저장 담당)
        """
        super().__init__()  # QObject 초기화
        if GameController._instance is not None:
            raise Exception("싱글톤 클래스는 직접 생성할 수 없습니다. get_instance() 메서드를 사용하세요.")
            
        GameController._instance = self
        self.signal = pyqtSignal()
        # GameState에 초기 데이터 반영

#==============================================
# UI 에서 호출하는 메서드 
#==============================================

    @classmethod
    async def initialize(cls) -> None:
        """게임 초기화 및 데이터 로드"""
        cls._state = GameState()
        cls._case_data = await CaseDataManager.initialize()
        cls._profiles = cls._case_data.profiles
        cls._case = cls._case_data.case
        cls._evidences = cls._case_data.evidences
        cls._isInitialized = True

        cls._state.messages.append({"role":"system", "content": cls._case_data.case.outline})
        cls._state.messages.append({"role":"system", "content": cls._profiles.__str__()})
        cls._state.messages.append({"role":"system", "content": cls._evidences.__str__()})

        print(f"{cls._state.messages}")

        return cls._case_data

    @classmethod
    def start_game(cls) -> bool :
        """게임을 INIT → DEBATE 상태로 시작하고, system 메시지 초기화."""
        if cls._isInitialized is False:
            return False

        if cls._isInitialized is True:
            cls._state.phase = Phase.DEBATE

        cls._interrogator.set_case_data()
            
        return True
    

    @classmethod
    def record_start(cls) -> None:
        """녹음 시작 후에 controller에서 호출 API 호출"""
        cls._state.record_state = True

    
    @classmethod
    def record_end(cls) -> bool:
        """
        녹음 종료 버튼을 누름
        Returns:
            bool: True면 턴 전환, False면 턴 전환 없음
        """
        cls._state.record_state = False

        """
        녹음 종료 후에 no_context 인지 interrogation_accepted 인지 확인 
        """
        
        return True
    
    @classmethod
    def user_input(cls, text: str) -> bool:
        """
        사용자의 수동 입력, 텍스트를 전송
        Args:
            text: 사용자가 입력한 텍스트
        Returns:
            bool: 처리 성공 여부
        """
        if not text.strip():
            return False
            
        cls._add_message(cls._state.turn, text)
        return True
    
    @classmethod
    def interrogation_end(cls) -> None:
        """심문 화면에서 뒤로 가기 버튼을 눌렀을 때 호출, 심문 종료"""
        cls._state.phase = Phase.DEBATE
        cls._state.current_profile = None
        if cls._state.record_state is True:
            cls.record_end()

    @classmethod
    def done(cls) -> None:
        """발언 완전 종료 시에 호출, 양쪽 다 됐을 때는 최종 판결 시작"""
        cls._state.done_flags[cls._state.turn] = True
        
        if all(cls._state.done_flags.values()):
            cls._state.phase = Phase.JUDGEMENT
            cls._send_signal("judgement", {"role": "판사", "message": "최종 판결을 내리겠습니다."})
            cls._add_message("판사", "최종 판결을 내리겠습니다.")
            cls._switch_turn()

    @classmethod
    def get_state(cls) -> GameState:
        """GameState 객체 반환."""
        return cls._state
    

#==============================================
# 내부 함수
#==============================================

    def _send_signal(self, code, arg):
        """ 신호 전송"""
        self._signal.emit(code, arg)

    
    @classmethod
    def _objection(cls) -> None:
        """
        이의 제기.
        - objection_count 증가, 메시지 추가, 턴 전환
        """
        cls._state.objection_count[cls._state.turn] += 1
        cls._send_signal("objection", {"role": cls._state.turn.label, "message": "이의 있음!"})
        cls._switch_turn()

    @classmethod
    def _get_judgement(cls) -> str:
        """판결 단계에서 최종 결과를 얻어와 메시지에 추가하고 반환."""
        pass

    @classmethod
    def _add_message(cls, role: Role, content: str) -> None:
        """messages 리스트에 (role, content) 추가."""
        role_str = role.value if isinstance(role, Role) else role
        cls._state.messages.append({"role": role_str, "content": content})

    @classmethod
    def _switch_turn(cls) -> None:
        """Role.PROSECUTOR ↔ Role.ATTORNEY 토글."""
        cls._state.turn = cls._state.turn.next()





if __name__ == "__main__":
    class DummyReceiver(QObject):
        @pyqtSlot(str, object)
        def receive(self, code, arg):
            print(f"[Signal Received] code: {code}, arg: {arg}")

    import sys
    from PyQt5.QtWidgets import QApplication

    app = QApplication(sys.argv)

    gc = GameController.get_instance()
    receiver = DummyReceiver()
    gc._signal.connect(receiver.receive)

    # 테스트 시그널 발신
    gc._send_signal("test_code", {"key": "value"})
    gc._send_signal("verdict", "유죄입니다.")

    cd = asyncio.run(gc.initialize())
    # gc._send_signal("case_data", cd)

    gc.start_game()



    sys.exit(0)