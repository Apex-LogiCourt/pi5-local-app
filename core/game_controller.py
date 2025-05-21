from typing import List, Dict, Optional
from data_models import CaseData, Evidence, Profile, Case, GameState, Phase, Role
from controller import CaseDataManager
from PyQt5.QtCore import QObject, pyqtSignal, pyqtSlot
import asyncio

class GameController:
    _instance = None
    _isInitialized = False
    _state : GameState = None
    _case : Case = None
    _evidences : List[Evidence] = None
    _profiles : List[Profile] = None
    _case_data : CaseData = None

    
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
        cls._case_data = asyncio.run(CaseDataManager.initialize())
        cls._profiles = cls._case_data.profiles
        cls._case = cls._case_data.case
        cls._evidences = cls._case_data.evidences
        cls._isInitialized = True

        cls._state.messages.append({"role":"system", "content": cls._case_data.case.outline})
        cls._state.messages.append({"role":"system", "content": cls._profiles.asdict()})
        cls._state.messages.append({"role":"system", "content": cls._evidences.asdict()})

        return cls._case_data

    @classmethod
    def start_game(cls) -> bool :
        """게임을 INIT → DEBATE 상태로 시작하고, system 메시지 초기화."""
        if cls._isInitialized is False:
            return False

        if cls._isInitialized is True:
            cls._state.phase = Phase.DEBATE
            
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
        should_switch_turn = True  # 실제 구현에서는 조건에 따라 결정
        
        if should_switch_turn:
            cls._switch_turn()
            return True
        return False
    
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
        if cls._state.phase == Phase.INTERROGATE:
            cls._state.phase = Phase.DEBATE
            cls._state.current_profile = None
    
    @classmethod
    def done(cls) -> None:
        """발언 완전 종료 시에 호출, 양쪽 다 됐을 때는 최종 판결 시작"""
        cls._state.done_flags[cls._state.turn] = True
        
        if all(cls._state.done_flags.values()):
            cls._state.phase = Phase.JUDGEMENT
            # cls._send_signal("judgement_start", "최종 판결이 시작됩니다")
        else:
            cls._switch_turn()

    @classmethod
    def get_state(cls) -> GameState:
        """GameState 객체 반환."""
        return cls._state
    

#==============================================
# 내부 함수
#==============================================

    def _send_signal(self, code, msg):
        """ 신호 전송"""
        pass

    
    @classmethod
    def _objection(cls) -> None:
        """
        이의 제기.
        - objection_count 증가, 메시지 추가, 턴 전환
        """
        cls._state.objection_count[cls._state.turn] += 1
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

    # def _question(self, type: str, question: str) -> None:
    #     """
    #     참고인 심문 
    #     - 내부적으로 증인 심문 체인을 호출하고, 응답을 메시지에 추가
    #     """
    #     self.state.mode = Mode.WITNESS
    #     self._add_message("user", f"[참고인:{witness_name}] {question}")
    #     # resp = self._ask_witness(question, witness_name)
    #     # self._add_message("witness", resp)