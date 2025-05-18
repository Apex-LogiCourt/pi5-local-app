from typing import List, Dict, Optional, Annotated, Union, Literal
from data_models import CaseData, Case, Profile, Evidence
from controller import CaseDataManager
from controller import get_judge_result_wrapper as get_judge_result
from langchain_openai import ChatOpenAI
from langchain_core.tools import tool
from langchain_core.messages import HumanMessage, AIMessage
from langgraph.graph import StateGraph, END, START
from langchain_core.runnables import RunnableLambda
import asyncio
from pydantic import BaseModel, Field
from langchain.prompts import PromptTemplate
from enum import Enum
import time



# ==============================================
class Phase(Enum):
    TURN = "turn"
    INTERROGATION = "interrogation"
    EVIDENCE = "evidence"
    END = "end"

    def next_node(self) -> str:
        mapping = {
            Phase.TURN: "check_contextual_relevance",
            Phase.INTERROGATION: "interrogation_handler",
            Phase.EVIDENCE: "evidence_handler",
            Phase.END: "end"
        }
        print(f"[DEBUG] phase: {self}")
        return mapping.get(self, "check_contextual_relevance")  # fallback




# ==============================================
# State Models
# ==============================================

# 이 부분 수정해야함 메시지를 매번 전달하는 건 무리함
class GraphState(BaseModel):
    """게임 상태를 나타내는 모델"""
    case_summary: str = ""
    messages: List[Dict] = Field(default_factory=list)
    context_correct: bool = False
    check: str = ""
    phase: Phase = Phase.TURN
# ==============================================
# Game Tools
# ==============================================



def check_contextual_relevance2(state: GraphState) -> GraphState:
    """입력이 현재 재판 역할극의 문맥과 관련 있는지 판단합니다."""
    # GameState 객체를 딕셔너리로 변환 (model_dump 사용)
    state_dict = state.model_dump() if hasattr(state, 'model_dump') else state

    user_input = state_dict["messages"][-1]["content"] if state_dict["messages"] else ""
    case_summary = state_dict["messages"][0]["content"] if state_dict["messages"] else ""
    # print(f"[DEBUG] case_summary: {case_summary}")
    print(f"[DEBUG] user_input: {user_input}")
    
    prompt = PromptTemplate.from_template("""
        당신은 역할극 기반 재판 시뮬레이션의 조정자입니다.
        사건 개요: {case_summary}
        사용자의 새 발언: "{user_input}"
        이 발언이 현재 재판 역할극과 관련이 있습니까?
        사용자는 어쩌면 `제 주장은 이상입니다` 와 같은 말로 발언을 종료하려고 할 수 있습니다.
        이런 경우에도 관련 있는 것으로 판단하세요.
        당신의 주된 역할은 재판 역할극 중의 사용자의 부적절한 발언을 감지하는 것입니다.
        관련 있으면 true, 관련 없으면 false로만 답하세요.
        """)

    chain = (
        {"case_summary": lambda _: case_summary, "user_input": lambda x: x}
        | prompt
        | ChatOpenAI(model="gpt-4.1-nano", temperature=0.8)
        | RunnableLambda(lambda output: output.content.strip().lower() == "true")
    )
    
    if chain.invoke(user_input):
        print("상관 있음")
        state.context_correct = True  # ✅ 기존 state 수정
    else:
        print("상관없음")
        state.context_correct = False

    return state  # ✅ 기존 state 리턴

def route_from_phase(state: GraphState) -> str:
    print(f"[DEBUG] route_from_phase 호출됨 : {state.phase}")
    result = state.phase.next_node()
    print(f"[DEBUG] route_from_phase → {state.phase} → {result}")
    return result


# ==============================================
# Workflow Components
# ==============================================

class WorkflowComponents:
    """워크플로우 구성 요소들을 관리하는 클래스"""
    
    @staticmethod
    def process_input(state: GraphState) -> GraphState:
        """입력을 처리합니다."""
        print(f"[DEBUG] 입력 처리됨: {state.messages[-1]['content'] if state.messages else '없음'}")
        return state

    @staticmethod
    def check_game_end(state: GraphState) -> GraphState:
        """게임 종료 조건을 확인합니다."""
        print("[DEBUG] check_game_end() 호출됨")
        return state

    @staticmethod
    def route_to_end(state: GraphState) -> str:
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
        self.workflow = self._create_react_workflow()
        self.state = GraphState()  # 워크플로우 상태를 유지하기 위한 초기화
    
    def _initialize_game_state(self):
        """게임 상태 초기화"""
        self.game_phase = "init"
        self.turn = True  # True: 검사, False: 변호사
        self.done_flags = {"검사": False, "변호사": False}
        self.mode = "debate"
        self.objection_count = {"검사": 0, "변호사": 0}
        
        # CaseData 관련 객체들
        self.case_data: Optional[CaseData] = None
        self.case: Optional[Case] = None
        self.profiles: Optional[List[Profile]] = None
        self.evidences: Optional[List[Evidence]] = None

    
    def _create_react_workflow(self):
        """워크플로우 생성"""


        def check_user_input(state: GraphState) -> GraphState:
            """현재 발언자의 인력을 판별합니다 
            Args:
                GraphState: 현재 상태
            """
            user_input = state.messages[-1]["content"]
            prompt = PromptTemplate.from_template("""
            당신은 법정 역할극을 조정하는 AI입니다. 사용자 발언을 보고 아래 세 가지 도구 중 **정확히 하나만** 선택하여 해당 도구의 이름만 문자열로 출력하세요.

            현재 사용자 발언: {user_input}
            도구 목록:
            1. `"turn_end"`  
                - 발언을 마치거나 턴을 종료하려는 의도가 감지.
                - 예: "이상입니다", "더 이상 없습니다", "발언을 마치겠습니다"

            2. `"interrogation"`  
                - 참고인 또는 피고인에게 질문하려는 경우. 
                - 예: "참고인을 심문하겠습니다", "피고인에게 묻겠습니다", "심문을 요청합니다"

            3. `"pass"`
                - 위 상황에 해당하지 않는 경우.
                - 사용자가 자신의 주장을 이어나가는 경우입니다.


            지침:
            - 반드시 아래 값 중 **하나만** 문자열로 출력하세요: `turn_end`, `interrogation`, `pass`
            - 절대로 설명이나 문장을 추가하지 마세요.  
            - 결과는 문자열 하나만 출력하세요.

            예시 출력 (정확히 이렇게): turn_end
            """)
            chain = (
                prompt
                | ChatOpenAI(model="gpt-4.1-nano", temperature=0.7)
                | RunnableLambda(lambda x: x.content.strip())
            )   
            # return GraphState(check_user_input=chain.invoke(user_input))
            result = chain.invoke(user_input)
            print(f"[DEBUG] check_user_input 결과: {result}")
            return GraphState(check=result)  # action_type으로 변경
            
        
        def handle_turn_end(state: GraphState) -> GraphState:
            """현재 발언자가 발언을 종료하고자 할 때 호출됩니다. 턴을 종료하고 다음 차례로 넘깁니다.

            Args:
                role: 현재 발언자 ("검사" 또는 "변호사")
            """
            state.phase = Phase.END
            print(f"[DEBUG] handle_turn_end() 호출됨 : {state.phase}")
            return GraphState(phase=Phase.END)


        def handle_interrogation(state: GraphState) -> GraphState:
            """심문을 진행할 때 호출됩니다.

            Args:
                state: 현재 게임 상태
            """
            print(f"[DEBUG] handle_interrogation() 호출됨")
            
            # Interrogator 인스턴스 생성 및 메시지 업데이트
            from interrogation.interrogator import Interrogator
            interrogator = Interrogator()
            interrogator.process_interrogation(self.state.messages, self.case_data)
            
            # add_message 콜백 설정
            interrogator.set_message_callback(self.add_message)
            
            # 여기서 심문 로직 실행
            # 예: interrogator.ask_witness() 또는 interrogator.ask_defendant() 호출
            
            return state


        # 상태 그래프 구성
        workflow = StateGraph(GraphState)
        workflow.add_node("ck", check_contextual_relevance2)
        workflow.add_node("action_checker", check_user_input)
        workflow.add_node("handle_turn_end", handle_turn_end)
        workflow.add_node("handle_interrogation", handle_interrogation)


        workflow.add_edge(START, "ck")
        workflow.add_conditional_edges(
            "ck",
            RunnableLambda(lambda x: x.context_correct, name="check_contextual_relevance"),
            {
                True: "action_checker",
                False: END
            }
        )

        workflow.add_conditional_edges(
            "action_checker",
            RunnableLambda(lambda x: x.check, name="check_action"),
            {
                "turn_end": "handle_turn_end",
                "interrogation": "handle_interrogation",
                "pass": END
            }
        )

        workflow.add_edge("handle_turn_end", END)
        workflow.add_edge("handle_interrogation", END)

        return workflow.compile()
    
    
    async def initialize_case(self, callback=None):
        """사건 초기화"""
        if not hasattr(self, 'case_initialized'):
            self.case_initialized = True
            
            # 사건 개요 생성
            await CaseDataManager.generate_case_stream(callback=callback)
            await CaseDataManager.generate_profiles_stream(callback=callback)
            await CaseDataManager.generate_evidences()
            
            self.case_data = CaseDataManager.get_case_data()
            self.case_summary = self.case_data.case.outline
            
            # 메시지 리스트에 추가
            self.add_message("system", self.case_summary)
            self.add_message("system", self.profiles)
            
            return True
        return False
    
    def add_message(self, role: str, content: str):
        """메시지 추가 - state.messages에 메시지 추가"""

        if role == "검사" or role == "변호사":
            message = {
                "role": "user",  # LangChain이 허용하는 값으로 고정
                "content": content,
                "metadata": {"actual_role": role}
            }
        if role == "system":
            message = {
                "role": "system",
                "content": content,
                "metadata": {"actual_role": "판사"}
            }
        self.state.messages.append(message)
    
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

        # 메시지를 상태에 추가
        self.add_message(current_role, user_input)
        self.workflow.invoke(self.state)

        return None
    
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
            "message_list": self.state.messages,  # state.messages 사용
            "mode": self.mode,
            "objection_count": self.objection_count
        }
    
    def get_judge_result(self) -> str:
        """판사 판결 결과 반환"""
        return get_judge_result(self.state.messages)  # state.messages 사용
    
    def reset(self):
        """게임 상태 초기화"""
        self._initialize_game_state()
        self.state = GraphState()  # 상태 초기화
        

if __name__ == "__main__":
    game_controller = GameController()
    asyncio.run(game_controller.initialize_case())

    print(f"참고인 프로필 : {game_controller.profiles}")

    # game_controller.process_input("나는 아주 많이 배고픕니다")

    # 심문 요청 테스트 
    game_controller.process_input("이주현 씨를 심문하겠습니다")
    game_controller.process_input("피고를 심문하겠습니다")


    
    