"""
LangGraph 기반 게임 워크플로우
"""
from typing import TypedDict, Annotated, Sequence, Literal
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage, SystemMessage
from langgraph.graph import StateGraph, END, START
from langgraph.graph.message import add_messages
from data_models import CaseData, Evidence, Profile, Case, GameState, Phase, Role
from langchain_openai import ChatOpenAI


# ============================================
# State 정의
# ============================================

class GameWorkflowState(TypedDict):
    """게임 워크플로우 상태"""
    # 메시지 히스토리 (LangGraph의 add_messages 사용)
    messages: Annotated[Sequence[BaseMessage], add_messages]

    # 게임 데이터
    case: Case
    profiles: list[Profile]
    evidences: list[Evidence]

    # 게임 상태
    phase: str  # "debate", "interrogate", "judgement"
    current_turn: str  # "prosecutor", "attorney"
    record_state: bool

    # 심문 관련
    current_profile: Profile | None

    # 입력 검증
    user_input: str
    validation_result: dict | None

    # 판결 관련
    done_flags: dict[str, bool]

    # 출력
    response: str | None
    signal_code: str | None
    signal_data: dict | None


# ============================================
# LLM 초기화
# ============================================

def get_llm(model="gpt-4o-mini", temperature=0.3):
    return ChatOpenAI(model=model, temperature=temperature)


# ============================================
# 노드 함수들
# ============================================

def debate_input_node(state: GameWorkflowState) -> GameWorkflowState:
    """토론 중 사용자 입력을 받는 노드"""
    user_input = state.get("user_input", "")
    current_turn = state.get("current_turn", "prosecutor")

    # 사용자 메시지 추가
    new_message = HumanMessage(content=user_input, name=current_turn)

    return {
        "messages": [new_message],
        "phase": "debate"
    }


def validate_input_node(state: GameWorkflowState) -> GameWorkflowState:
    """사용자 입력의 문맥 관련성 및 심문 요청 검증"""
    from controller import CaseDataManager
    from interrogation.interrogator import it

    user_input = state.get("user_input", "")

    # 1. 문맥 관련성 검사 (CaseDataManager 사용)
    result = CaseDataManager.get_instance().check_contextual_relevance(user_input)

    # 2. 심문 요청인 경우 Interrogator.check_request() 사용
    if result.get("relevant") == "true" and result.get("answer") == "interrogation":
        # Interrogator 클래스의 check_request 메서드 사용
        interrogation_result = it.check_request(user_input)
        type_ = interrogation_result.get("type")

        # Interrogator가 이미 _current_profile을 설정했음
        target_profile = it._current_profile

        result.update({
            "interrogation_type": type_,
            "interrogation_answer": interrogation_result.get("answer"),
            "target_profile": target_profile
        })

    return {
        "validation_result": result
    }


def interrogate_node(state: GameWorkflowState) -> GameWorkflowState:
    """심문 모드에서 증인 응답 생성"""
    from interrogation.interrogator import it

    user_input = state.get("user_input", "")
    current_profile = state.get("current_profile")

    # it._current_profile이 이미 설정되어 있어야 함
    if not current_profile and not it._current_profile:
        return {
            "response": "심문 대상을 찾을 수 없습니다.",
            "signal_code": "error"
        }

    # current_profile이 없으면 it._current_profile 사용
    if not current_profile:
        current_profile = it._current_profile

    # Interrogator가 대화 메모리를 관리하며 응답 텍스트를 직접 반환
    response_text = it.build_ask_chain(user_input, current_profile)

    # 메시지 추가
    witness_message = AIMessage(
        content=response_text,
        name=current_profile.name if current_profile else "증인"
    )

    return {
        "messages": [witness_message],
        "response": response_text,
        "signal_code": "interrogation",
        "signal_data": {
            "role": current_profile.name if current_profile else "증인",
            "message": response_text
        },
        "current_profile": current_profile  # 상태 업데이트
    }


def judgement_node(state: GameWorkflowState) -> GameWorkflowState:
    """최종 판결 생성 (RAG 포함)"""
    from verdict import get_judge_result

    # 메시지를 dict 형식으로 변환
    messages = state.get("messages", [])
    message_list = []

    for msg in messages:
        if isinstance(msg, HumanMessage):
            role = getattr(msg, 'name', '검사')
        elif isinstance(msg, AIMessage):
            role = getattr(msg, 'name', '변호사')
        elif isinstance(msg, SystemMessage):
            role = 'system'
        else:
            role = 'unknown'

        message_list.append({
            "role": role,
            "content": msg.content
        })

    # 판결 생성
    judgement_result = get_judge_result(message_list)

    # 판결 메시지 추가
    judge_message = AIMessage(content=judgement_result, name="판사")

    return {
        "messages": [judge_message],
        "response": judgement_result,
        "signal_code": "verdict",
        "signal_data": judgement_result,
        "phase": "judgement"
    }


# ============================================
# 조건부 엣지 함수들
# ============================================

def route_after_validation(state: GameWorkflowState) -> Literal["interrogate", "continue", "reject"]:
    """검증 결과에 따라 라우팅"""
    validation_result = state.get("validation_result", {})

    relevant = validation_result.get("relevant")
    answer = validation_result.get("answer")
    interrogation_type = validation_result.get("interrogation_type")

    # 문맥과 관련 없음
    if relevant == "false":
        return "reject"

    # 심문 요청
    if answer == "interrogation":
        if interrogation_type == "retry":
            return "reject"
        else:
            return "interrogate"

    # 정상 발언
    return "continue"


def should_judge(state: GameWorkflowState) -> bool:
    """판결로 이동할지 여부"""
    done_flags = state.get("done_flags", {})
    return all(done_flags.values())


# ============================================
# 워크플로우 그래프 구성
# ============================================

def route_initial(state: GameWorkflowState) -> Literal["debate_input", "interrogate", "judgement"]:
    """초기 라우팅: phase에 따라 시작 노드 결정"""
    phase = state.get("phase", "debate")

    # phase가 enum인 경우 문자열로 변환
    if hasattr(phase, 'value'):
        phase = phase.value

    # 소문자로 정규화
    phase = str(phase).lower()

    if phase == "judgement":
        return "judgement"
    elif phase == "interrogate":
        return "interrogate"
    else:
        return "debate_input"


def create_game_workflow() -> StateGraph:
    """게임 워크플로우 그래프 생성"""

    workflow = StateGraph(GameWorkflowState)

    # 노드 추가
    workflow.add_node("debate_input", debate_input_node)
    workflow.add_node("validate", validate_input_node)
    workflow.add_node("interrogate", interrogate_node)
    workflow.add_node("judgement", judgement_node)

    # 엣지 추가
    # START → phase에 따라 라우팅
    workflow.add_conditional_edges(
        START,
        route_initial,
        {
            "debate_input": "debate_input",
            "interrogate": "interrogate",
            "judgement": "judgement"
        }
    )

    # debate_input → validate
    workflow.add_edge("debate_input", "validate")

    # validate → conditional routing
    workflow.add_conditional_edges(
        "validate",
        route_after_validation,
        {
            "interrogate": "interrogate",
            "continue": END,
            "reject": END
        }
    )

    # interrogate → END
    workflow.add_edge("interrogate", END)

    # judgement → END
    workflow.add_edge("judgement", END)

    return workflow.compile()


# ============================================
# 워크플로우 실행 헬퍼
# ============================================

async def run_workflow(
    workflow,
    user_input: str,
    game_state: GameState,
    case_data: CaseData
):
    """워크플로우 실행"""

    # Phase enum을 문자열로 변환 (name 사용)
    phase_str = game_state.phase.name.lower() if hasattr(game_state.phase, 'name') else str(game_state.phase).lower()
    turn_str = game_state.turn.value if hasattr(game_state.turn, 'value') else str(game_state.turn)

    # 초기 상태 구성
    initial_state = {
        "messages": [],
        "case": case_data.case,
        "profiles": case_data.profiles,
        "evidences": case_data.evidences,
        "phase": phase_str,  # "interrogate", "debate" 등
        "current_turn": turn_str,
        "record_state": game_state.record_state,
        "current_profile": game_state.current_profile,
        "user_input": user_input,
        "validation_result": None,
        "done_flags": game_state.done_flags,
        "response": None,
        "signal_code": None,
        "signal_data": None
    }

    # 워크플로우 실행
    result = await workflow.ainvoke(initial_state)

    return result
