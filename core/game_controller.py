from typing import List, Dict, Optional, Annotated, Union, Literal
from data_models import CaseData, Case, Profile, Evidence
from controller import CaseDataManager
from controller import get_judge_result_wrapper as get_judge_result
from langchain_openai import ChatOpenAI
from langchain_core.tools import tool
from langchain_core.messages import HumanMessage, AIMessage
from langgraph.graph import StateGraph, END, START
from langchain_core.utils.function_calling import convert_to_openai_tool
from langchain_core.runnables import RunnableLambda, RunnablePassthrough
import asyncio
from pydantic import BaseModel, Field
from langgraph.prebuilt import create_react_agent, ToolNode, tools_condition
from langchain.prompts import PromptTemplate








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
    last_action: Optional[str] = None  # 새 필드 추가
# ==============================================
# Game Tools
# ==============================================


@tool
def check_contextual_relevance(user_input: str, case_summary: str) -> bool:
    """입력이 현재 재판 역할극의 문맥과 관련 있는지 판단합니다."""
    prompt = PromptTemplate.from_template("""
    당신은 역할극 기반 재판 시뮬레이션의 조정자입니다.
    사건 개요: {case_summary}
    사용자의 새 발언: "{user_input}"
    이 발언이 현재 재판 역할극 흐름과 관련이 있습니까?
    관련 있으면 true, 관련 없으면 false로만 답하세요.
    """)

    chain = (
        {"case_summary": lambda _: case_summary, "user_input": lambda x: x}
        | prompt
        | ChatOpenAI(model="gpt-4o-mini", temperature=0.7)
        | RunnableLambda(lambda output: output.content.strip().lower() == "true")
    )
    return chain.invoke(user_input)




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
        self.workflow = self._create_react_workflow()
        self.state = GameState()  # 워크플로우 상태를 유지하기 위한 초기화
    
    def _initialize_game_state(self):
        """게임 상태 초기화"""
        self.game_phase = "init"
        self.turn = True  # True: 검사, False: 변호사
        self.done_flags = {"검사": False, "변호사": False}
        self.mode = "debate"
        self.objection_count = {"검사": 0, "변호사": 0}
        
        # CaseData 관련 객체들
        self.case_data = None
        self.case = None
        self.profiles = None
        self.evidences = None

    @staticmethod
    def prepare_prompt_input(state: dict) -> dict:
        messages = state.get("messages", [])
        last_message = messages[-1].content if messages else ""
        role = state.get("current_role", "검사")
        return {
            "last_user_input": last_message,
            "current_role": role
        }
    
    def _create_react_workflow(self):
        """ReAct 기반 워크플로우 생성"""
        # LLM과 도구 초기화

        @tool
        def handle_turn_end(role: str) -> dict:
            """현재 발언자가 발언을 종료하고자 할 때 호출됩니다. 턴을 종료하고 다음 차례로 넘깁니다.

            Args:
                role: 현재 발언자 ("검사" 또는 "변호사")
            """
            print(f"[DEBUG] handle_turn_end() 호출됨: {role}")
            self.state.last_action = {
                "action": "turn_end",
                "role": role,
                "should_continue": False  # ★ 추가: 워크플로우 종료 여부
            }
            print(f"[DEBUG] last_action: {self.state.last_action}")
            return self.state.last_action

        @tool
        def handle_interrogation(subject: str, question: str) -> dict:
            """심문을 진행할 때 호출됩니다.

            Args:
                subject: 질문 대상 (예: "피고인", "참고인")
                question: 질문 내용
            """
            print(f"[DEBUG] handle_interrogation() 호출됨: {subject}, {question}")
            return {
                "action": "question",
                "target": subject,
                "content": question
            }


        @tool
        def handle_evidence_submission(description: str, role: str) -> dict:
            """증거를 제출할 때 호출됩니다.

            Args:
                description: 제출하려는 증거에 대한 설명
                role: 제출자 ("검사" 또는 "변호사")
            """
            print(f"[DEBUG] handle_evidence_submission() 호출됨: {description}, {role}")
            return {
                "action": "submit_evidence",
                "description": description,
                "submitted_by": role
            }
        
        self.llm = ChatOpenAI(model="gpt-4o", temperature=0.3)
        self.tools = [
            handle_turn_end,
            handle_interrogation,
            handle_evidence_submission
        ]
        
        # ReAct 에이전트 생성
        prompt = PromptTemplate.from_template("""
        당신은 법정 역할극을 조정하는 AI입니다. 사용자 발언을 읽고, 아래 세 가지 중 **정확히 하나의 도구만** 선택해 실행하세요.

        현재 사용자 발언: {last_user_input}
        현재 역할: {current_role}

        도구 목록:

        1. `handle_turn_end(role: str)`  
            - 발언을 마치거나 턴을 종료하려는 의도가 감지되면 선택합니다.  
            - 예: "이상입니다", "더 이상 없습니다", "발언을 마치겠습니다"
            - 이 도구를 호출할 때는 다른 도구를 호출하지 마세요.

        2. `handle_interrogation(subject: str, question: str)`  
            - 참고인 또는 피고인에게 질문하려는 경우 사용합니다.  
            - subject는 "참고인" 또는 "피고인" 중 하나입니다.  
            - 예: "참고인을 심문하겠습니다", "피고인에게 묻겠습니다"
            - 이 도구를 호출할 때는 다른 도구를 호출하지 마세요.

        3. `handle_evidence_submission(description: str, role: str)`  
            - 증거를 제출하려는 경우 사용합니다.  
            - description에는 증거에 대한 설명이 들어갑니다.  
            - 예: "이것은 흉기입니다", "증거를 제출합니다"
            - 이 도구를 호출할 때는 다른 도구를 호출하지 마세요.

        지침:
        - 반드시 위 도구 중 하나만을 선택하여 호출해야 합니다. 절대로 일반 텍스트 응답을 하지 마세요.
        - 도구 호출 시, 사용자 발언에서 인자를 추론해 채워야 합니다.
        - 인자를 추론할 수 없을 경우, 가능한 한 합리적으로 보완하여 채우세요.
        - 발언의 의도가 명확하지 않더라도 가장 적합한 도구를 선택하여 처리하세요.
        - 사용자의 발언이 의미 없거나 관련 없는 내용이라도 handle_turn_end를 호출하여 처리하세요.
        - 한 번에 하나의 도구만 호출하세요. 여러 도구를 동시에 호출하지 마세요.
        - 도구를 한 번 호출한 후에는 즉시 종료하세요.
        """)

        agent = create_react_agent(
            model=self.llm,
            tools=self.tools,
            prompt=RunnableLambda(self.prepare_prompt_input) | prompt,
            
        )

        # 상태 그래프 구성
        workflow = StateGraph(GameState)
        
        # 노드 추가
        workflow.add_node("agent", agent)
        workflow.add_node("tools", ToolNode(self.tools))
        workflow.add_node("check_turn", self.check_turn_status)

        workflow.set_entry_point("agent")
        workflow.add_edge("agent", "tools")
        workflow.add_edge("tools", "check_turn")
        workflow.add_edge("check_turn", END)

        # # 엣지 연결
        # workflow.set_entry_point("agent")
        # workflow.add_conditional_edges(
        #     "agent",
        #     tools_condition,
        #     {
        #         "tools": "tools",
        #         "end": END
        #     }
        # )
        # workflow.add_edge("tools", "check_turn")  # tools -> check_turn
        # workflow.add_conditional_edges(
        #     "check_turn",
        #     self.check_turn_status,
        #     {
        #         "agent": "agent",
        #         "end": END
        #     }
        # )

        return workflow.compile()
    
    def check_turn_status(self, state: GameState):
        """턴 지속 여부 판단"""
        last_action = state.get("last_action", {})
        print(f"[DEBUG] last_action: {last_action}")
        if last_action.get("should_continue", True):  # 기본값 True (계속 진행)
            return "agent"
        return "__end__"  # LangGraph prebuilt 조건과 통일

    
    
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

        # 문맥 관련성 체크 결과 출력
        is_relevant = check_contextual_relevance.invoke({
            "user_input": user_input,
            "case_summary": self.state.messages[0]["content"] if self.state.messages else ""
        })
        print(f"문맥 관련성 체크 결과: {is_relevant}")

        if not is_relevant:
            self.add_message("system", f"{current_role}측, 해당 발언은 현재 재판 흐름과 관련이 없습니다. 경고입니다.")

        # 별도의 제한 횟수 설정으로 무한 반복 방지
        max_attempts = 1
        attempt = 0
        action = None
        result = None

        while attempt < max_attempts:
            # LangGraph 에이전트 호출
            result = self.workflow.invoke(self.state)
            attempt += 1
            
            # 액션 타입 확인
            action = self._extract_action_from_result(result)
            
            # 액션이 감지되면 종료
            if action:
                break
        
        # 결과 처리
        response = {
            "role": current_role,
            "content": user_input,
            "should_change_turn": False,
            "phase_changed": False,
            "action_taken": None
        }
        
        print(f"[DEBUG] 감지된 액션: {action}")
        
        if action == "turn_end":
            print(f"[DEBUG] 턴 종료 액션 감지됨")
            self.set_done_flag(current_role)
            self.change_turn()
            response["should_change_turn"] = True
            response["action_taken"] = "turn_end"
            if self.check_game_end():
                self.game_phase = "judgement"
                response["phase_changed"] = True
        elif action == "question":
            print(f"[DEBUG] 질문 액션 감지됨")
            target = result.get("target", "")
            content = result.get("content", "")
            print(f"[DEBUG] 질문 대상: {target}, 내용: {content}")
            response["action_taken"] = "question"
            response["question_target"] = target
            response["question_content"] = content
        elif action == "submit_evidence":
            print(f"[DEBUG] 증거 제출 액션 감지됨")
            description = result.get("description", "")
            submitted_by = result.get("submitted_by", "")
            print(f"[DEBUG] 증거 설명: {description}, 제출자: {submitted_by}")
            response["action_taken"] = "submit_evidence"
            response["evidence_description"] = description
            response["evidence_submitted_by"] = submitted_by

        return response
    
    def _extract_action_from_result(self, result):
        """결과에서 액션 추출"""
        action = None
        if isinstance(result, dict):
            if "action" in result:
                action = result["action"]
            elif "return_values" in result and isinstance(result["return_values"], dict) and "action" in result["return_values"]:
                action = result["return_values"]["action"]
            elif "output" in result and isinstance(result["output"], dict) and "action" in result["output"]:
                action = result["output"]["action"]
            # 도구 호출 결과가 다른 구조에 있을 수 있는 추가 확인
            elif "node_outputs" in result:
                node_outputs = result["node_outputs"]
                for node in node_outputs:
                    if isinstance(node_outputs[node], dict) and "action" in node_outputs[node]:
                        action = node_outputs[node]["action"]
                        break
        return action
    
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
        self.state = GameState()  # 상태 초기화
        

if __name__ == "__main__":
    game_controller = GameController()

    game_controller.process_input("검사측 주장은 이상입니다")
    print(game_controller.state.last_action)  


    
    