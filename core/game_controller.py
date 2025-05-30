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

        from tools.service import handler_send_initial_evidence
        handler_send_initial_evidence(cls._evidences)
        print(f"[GameController] initialize() ended")
        

        return cls._case_data

    @classmethod
    async def start_game(cls) -> bool :
        """게임을 INIT → DEBATE 상태로 시작하고, system 메시지 초기화."""
        if cls._isInitialized is False:
            return False

        if cls._isInitialized is True:
            cls._state.phase = Phase.DEBATE

        from tools.service import handler_tts_service
        asyncio.create_task(handler_tts_service(cls._case_data.case.outline))
        cls._interrogator.set_case_data()
        cls._send_signal("initialized", cls._case_data)

        return True
    

    @classmethod
    async def record_start(cls) -> None:
        """녹음 시작 후에 API 호출"""
        cls._state.record_state = True
        from tools.service import handler_record_start
        await handler_record_start()

    
    @classmethod
    async def record_end(cls) -> bool:
        """
        녹음 종료 버튼을 누름
        Returns:
            bool: True면 턴 전환, False면 턴 전환 없음
        """
        cls._state.record_state = False
        from tools.service import handler_record_stop
        await handler_record_stop()
        
        if cls._state.phase == Phase.INTERROGATE:
            return False
        return True
    
    @classmethod
    async def user_input(cls, text: str) -> bool:
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
        if cls._state.phase == Phase.DEBATE:
            return await cls._handle_user_input_validation(text)
        
        if cls._state.phase == Phase.INTERROGATE:
            from tools.service import run_chain_streaming, handler_tts_service
            cls._state.current_profile = it._current_profile
            
            
            def handle_response(sentence):
                # 심문 응답을 처리하는 콜백
                asyncio.create_task(handler_tts_service(sentence))
                cls._send_signal("interrogation", {
                    "role": cls._state.current_profile.name if cls._state.current_profile else "증인",
                    "message": sentence
                })
                # cls._add_message(cls._state.current_profile.name if cls._state.current_profile else "증인", sentence)
                
            response_text = await run_chain_streaming(it.build_ask_chain(text, cls._state.current_profile), handle_response)
            cls._add_message(cls._state.current_profile.name if cls._state.current_profile else "증인", response_text)
        # print(f"user_input() called, 현재 턴{cls._state.turn}")
        return True

    @classmethod
    def interrogation_end(cls) -> None:
        """심문 화면에서 뒤로 가기 버튼을 눌렀을 때 호출, 심문 종료"""
        cls._state.phase = Phase.DEBATE
        cls._state.current_profile = None
        if cls._state.record_state is True:
            asyncio.create_task(cls.record_end())

    @classmethod
    def done(cls) -> None:
        """발언 완전 종료 시에 호출, 양쪽 다 됐을 때는 최종 판결 시작"""
        cls._state.done_flags[cls._state.turn] = True
        
        if all(cls._state.done_flags.values()):
            cls._state.phase = Phase.JUDGEMENT
            cls._send_signal("judgement", {'role': '판사', 'message': '최종 판결을 내리겠습니다.'})
            cls._add_message("판사", "최종 판결을 내리겠습니다.")
            cls._switch_turn()

    @classmethod
    def get_state(cls) -> GameState:
        """GameState 객체 반환."""
        return cls._state
    

    @classmethod
    async def _handle_user_input_validation(cls, text: str) -> bool:

        async def request_speak_judge(cls, msg: dict, code:str) -> bool:
            """판사의 발언을 음성으로 출력. return False 는 턴 전환 없음.
            msg 형식 {'role' : '판사', 'message': '지금은 재판 중인데 갑자기 배고프다니요? 재판과 상관 없는 발언 같습니다'}
            """
            cls._send_signal(code, msg)
            cls._add_message("판사", msg.get("message"))  # 판사 메시지 추가
            from tools.service import handler_tts_service
            asyncio.create_task(handler_tts_service(msg.get("message")))
            return False

        result = CaseDataManager.get_instance().check_contextual_relevance(text)

        print(f"디버깅 : {result}")
        if result.get("relevant") == "false": # 문맥 관련 없음
            return await request_speak_judge(cls, {'role': '판사', 'message': result.get("answer")}, "no_context")
   
        if result.get("relevant") == "true" :
            if result.get("answer") == "interrogation":
                # 심문 세팅
                temp = it.check_request(text)
                type_ = temp.get("type")
                if type_ == "retry": 
                    return await request_speak_judge(cls, {'role': '판사', 'message' : temp.get("answer")}, "no_context")
                else : 
                    cls._state.phase = Phase.INTERROGATE 
                    return await request_speak_judge(cls, {'role': '판사', 'message': temp.get("answer"), 'type':type_}, "interrogation_accepted")
            else :
                cls._add_message(cls._state.turn, text)
                return True

    

#==============================================
# 내부 함수
#==============================================

    @classmethod
    def _send_signal(cls, code, arg):
        """ 신호 전송"""
        instance = cls.get_instance()
        instance._signal.emit(code, arg)

    
    @classmethod
    def _objection(cls) -> None:
        """
        이의 제기.
        - objection_count 증가, 메시지 추가, 턴 전환
        """
        cls._switch_turn()
        cls._state.objection_count[cls._state.turn] += 1
        cls._send_signal("objection", {"role": cls._state.turn.label(), "message": "이의 있음!"})
        print(f"[GameController] _objection() called: {cls._state.turn.label()}")

    @classmethod
    def _get_judgement(cls) -> str:
        """판결 단계에서 최종 결과를 얻어와 메시지에 추가하고 반환."""
        pass

    @classmethod
    def _add_message(cls, role: Role, content: str) -> None:
        """messages 리스트에 (role, content) 추가."""
        role_str = role.label() if isinstance(role, Role) else role
        cls._state.messages.append({"role": role_str, "content": content})
        print(f"[GameController] _add_message() called: {cls._state.messages[-1]}")

    @classmethod
    def _switch_turn(cls) -> None:
        """Role.PROSECUTOR ↔ Role.ATTORNEY 토글."""
        cls._state.turn = cls._state.turn.next()

    @classmethod
    def _handle_bnt_event(cls, role : str) -> None:
        """버튼 이벤트 처리 메서드"""
        # print(f"input_role : {role}, 현재 턴: {cls._state.turn.value}, 여부 : {role != cls._state.turn.value}")
        if cls._state.record_state is True:
            asyncio.create_task(cls.record_end())
        
        # 현재 턴과 다른 사람이 버튼을 눌렀을 때만 이의제기
        if role != cls._state.turn.value and cls._state.phase == Phase.DEBATE:
            cls._objection()



