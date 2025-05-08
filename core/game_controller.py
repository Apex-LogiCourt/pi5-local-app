from typing import List, Dict, Optional, Annotated, Union, Literal
from data_models import CaseData, Case, Profile, Evidence
from controller import CaseDataManager
from controller import get_judge_result_wrapper as get_judge_result
from langchain_openai import ChatOpenAI
from langchain_core.tools import tool
from langchain_core.messages import HumanMessage, AIMessage
from langgraph.graph import StateGraph, END
from langchain_core.utils.function_calling import convert_to_openai_tool
from langchain_core.runnables import RunnableLambda, RunnablePassthrough
import asyncio
from pydantic import BaseModel, Field

# ==============================================
# State Models
# ==============================================

class GameState(BaseModel):
    """게임 상태를 나타내는 모델"""
    messages: List[Dict] = Field(default_factory=list)
    current_role: str = "검사"
    game_phase: str = "init"
    done_flags: Dict[str, bool] = Field(default_factory=lambda: {"검사": False, "변호사": False})
    objection_count: Dict[str, int] = Field(default_factory=lambda: {"검사": 0, "변호사": 0})

# ==============================================
# Game Tools
# ==============================================

@tool
def handle_argument(input_text: str, role: str) -> Dict:
    """검사/변호사의 주장을 처리합니다.
    
    Args:
        input_text: 주장 내용
        role: 검사 또는 변호사
    """
    return {
        "action": "argument",
        "content": input_text,
        "role": role
    }

@tool
def handle_objection(role: str) -> Dict:
    """이의제기를 처리합니다.
    
    Args:
        role: 검사 또는 변호사
    """
    return {
        "action": "objection",
        "role": role
    }

@tool
def handle_witness_question(question: str, witness_name: str, witness_type: str) -> Dict:
    """참고인에게 질문합니다.
    
    Args:
        question: 질문 내용
        witness_name: 참고인 이름
        witness_type: 참고인 유형
    """
    return {
        "action": "witness_question",
        "content": question,
        "witness": witness_name,
        "witness_type": witness_type
    }

@tool
def handle_defendant_question(question: str, defendant_name: str) -> Dict:
    """피고인에게 질문합니다.
    
    Args:
        question: 질문 내용
        defendant_name: 피고인 이름
    """
    return {
        "action": "defendant_question",
        "content": question,
        "defendant": defendant_name
    }

@tool
def handle_evidence(evidence_id: str, role: str) -> Dict:
    """증거를 제시합니다.
    
    Args:
        evidence_id: 증거 ID
        role: 검사 또는 변호사
    """
    return {
        "action": "evidence",
        "evidence_id": evidence_id,
        "role": role
    }

# ==============================================
# Workflow Components
# ==============================================

class WorkflowComponents:
    """워크플로우 구성 요소들을 관리하는 클래스"""
    
    @staticmethod
    def process_input(state: GameState) -> GameState:
        """입력을 처리합니다."""
        print(f"[DEBUG] 입력 처리됨: {state.messages[-1]['content'] if state.messages else '없음'}")
        return state

    @staticmethod
    def check_game_end(state: GameState) -> GameState:
        """게임 종료 조건을 확인합니다."""
        print("[DEBUG] check_game_end() 호출됨")
        return state

    @staticmethod
    def route_to_end(state: GameState) -> str:
        """워크플로우 종료 여부를 결정합니다."""
        return "end"

# ==============================================
# Game Controller
# ==============================================

class GameController:
    """게임의 전체적인 흐름을 제어하는 클래스"""
    
    def __init__(self):
        """게임 컨트롤러 초기화"""
        self._initialize_game_state()
        self._initialize_workflow()
    
    def _initialize_game_state(self):
        """게임 상태 초기화"""
        self.game_phase = "init"
        self.turn = True  # True: 검사, False: 변호사
        self.done_flags = {"검사": False, "변호사": False}
        self.message_list = []
        self.mode = "debate"
        self.objection_count = {"검사": 0, "변호사": 0}
        
        # CaseData 관련 객체들
        self.case_data = None
        self.case = None
        self.profiles = None
        self.evidences = None
    
    def _initialize_workflow(self):
        """LangGraph 워크플로우 초기화"""
        self.llm = ChatOpenAI(temperature=0)
        self.tools = [
            handle_argument,
            handle_objection,
            handle_witness_question,
            handle_defendant_question,
            handle_evidence
        ]
        self.openai_tools = [convert_to_openai_tool(tool) for tool in self.tools]
        self.workflow = self._create_workflow()
    
    def _create_workflow(self) -> StateGraph:
        """LangGraph 워크플로우 생성"""
        workflow = StateGraph(GameState)
        
        # 노드 추가
        workflow.add_node("process_input", RunnableLambda(WorkflowComponents.process_input))
        workflow.add_node("check_game_end", RunnableLambda(WorkflowComponents.check_game_end))
        
        # 엣지 추가
        workflow.add_edge("process_input", "check_game_end")
        workflow.add_conditional_edges(
            "check_game_end",
            RunnableLambda(WorkflowComponents.route_to_end, name="route_to_end"),
            {"end": END}
        )
        
        # 시작 노드 설정
        workflow.set_entry_point("process_input")
        
        return workflow.compile()
    
    async def initialize_case(self, callback=None):
        """사건 초기화"""
        if not hasattr(self, 'case_initialized'):
            self.case_initialized = True
            
            # 사건 개요 생성
            case_summary = await CaseDataManager.generate_case_stream(callback=callback)
            profiles = await CaseDataManager.generate_profiles_stream(callback=callback)
            
            # 메시지 리스트에 추가
            self.add_message("system", case_summary)
            self.add_message("system", profiles)
            
            return True
        return False
    
    def add_message(self, role: str, content: str):
        """메시지 추가"""
        self.message_list.append({"role": role, "content": content})
    
    def change_turn(self):
        """턴 변경"""
        self.turn = not self.turn
    
    def set_done_flag(self, role: str):
        """완료 플래그 설정"""
        self.done_flags[role] = True
    
    def check_game_end(self) -> bool:
        """게임 종료 조건 확인"""
        return all(self.done_flags.values())
    
    def process_input(self, user_input: str) -> Dict:
        """사용자 입력 처리"""
        current_role = "검사" if self.turn else "변호사"
        
        # LangGraph 워크플로우 실행
        state = GameState(
            messages=self.message_list,
            current_role=current_role,
            game_phase=self.game_phase,
            done_flags=self.done_flags,
            objection_count=self.objection_count
        )
        
        result = self.workflow.invoke(state)
        
        # 결과 처리
        response = {
            "role": current_role,
            "content": user_input,
            "is_complete": False,
            "should_change_turn": False,
            "phase_changed": False
        }
        
        # 입력 정규화
        normalized_input = user_input.rstrip('.').strip()
        
        # 주장 후 "이상입니다" 입력 시 턴만 변경
        if user_input.endswith("이상입니다"):
            response["should_change_turn"] = True
            # "이상입니다"만 입력한 경우 완료 플래그 설정
            if normalized_input == "이상입니다":
                self.set_done_flag(current_role)
                if self.check_game_end():
                    self.game_phase = "judgement"
                    response["phase_changed"] = True
        
        return response
    
    def process_objection(self) -> Dict:
        """이의제기 처리"""
        current_role = "검사" if self.turn else "변호사"
        self.objection_count[current_role] += 1
        
        return {
            "role": current_role,
            "content": "이의 있음!",
            "should_change_turn": True
        }
    
    def get_current_state(self) -> Dict:
        """현재 게임 상태 반환"""
        return {
            "game_phase": self.game_phase,
            "turn": "검사" if self.turn else "변호사",
            "done_flags": self.done_flags,
            "message_list": self.message_list,
            "mode": self.mode,
            "objection_count": self.objection_count
        }
    
    def get_judge_result(self) -> str:
        """판사 판결 결과 반환"""
        return get_judge_result(self.message_list)
    
    def reset(self):
        """게임 상태 초기화"""
        self.__init__()
