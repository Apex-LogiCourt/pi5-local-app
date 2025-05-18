from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from pydantic import BaseModel, Field
from typing import List, Dict, Callable
from controller import CaseDataManager
from data_models import CaseData, Profile, Evidence, Case
from langchain.prompts import PromptTemplate
from langgraph.graph import StateGraph, END, START
from langchain_core.runnables import RunnableLambda

# 템플릿 임포트

# 만질 때 username_witness_templates.py으로 각자 생성해서 갈아 끼우세용 
# from .prompt_templates.username_witness_templates import (
#     ASK_WITNESS_EXPERT_TEMPLATE,
#     ASK_WITNESS_CHARACTER_TEMPLATE,
#     ASK_DEFENDANT_TEMPLATE
# )

from .prompt_templates.ex_witness_templates import (
    ASK_WITNESS_EXPERT_TEMPLATE,
    ASK_WITNESS_CHARACTER_TEMPLATE,
    ASK_DEFENDANT_TEMPLATE
)

# ... existing code ...

def get_llm(model="gpt-4o"):
    llm = ChatOpenAI(model=model)  
    return llm


def ask_witness(question, name, wtype, case_summary):
    llm = get_llm()
    
    if wtype == "expert":
        context = ASK_WITNESS_EXPERT_TEMPLATE.format(name=name, case_summary=case_summary)
    else:
        context = ASK_WITNESS_CHARACTER_TEMPLATE.format(name=name, case_summary=case_summary)

    prompt = ChatPromptTemplate.from_template("""
        {context}

        질문: {question}
        답변:
    """)

    chain = prompt | llm | StrOutputParser()
    return chain.invoke({"question": question, "context": context})


def ask_defendant(question, defendant_name, case_summary):
    llm = get_llm()
    
    context = ASK_DEFENDANT_TEMPLATE.format(defendant_name=defendant_name, case_summary=case_summary)

    prompt = ChatPromptTemplate.from_template("""
        {context}

        질문: {question}
        답변:
    """)

    chain = prompt | llm | StrOutputParser()
    return chain.invoke({"question": question, "context": context})


#===============================================
# 참고인 심문 진행


class InterrogationState(BaseModel):
    """심문 상태를 나타내는 모델"""
    case_summary: str = ""
    case_data: CaseData = Field(default_factory=lambda: CaseData(
        case=Case(outline="", behind=""),
        profiles=[],
        evidences=[]
    ))
    messages: List[Dict] = Field(default_factory=list)
    current_profile: str = ""
    current_evidence: str = ""
    current_question: str = ""
    current_answer: str = ""


class Interrogator:
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        if self._initialized:
            return
            
        self.llm = get_llm()
        self.state = InterrogationState()
        self.state.case_data = CaseData(
            case=Case(outline="", behind=""),
            profiles=[],
            evidences=[]
        )
        self.workflow = self._create_workflow()
        self.add_message_callback = None  # 메시지 추가 콜백 함수
        self._initialized = True
    
    def set_message_callback(self, callback: Callable[[str, str], None]):
        """메시지 추가 콜백 함수를 설정합니다.
        
        Args:
            callback: 메시지를 추가하는 함수 (role: str, content: str) -> None
        """
        self.add_message_callback = callback
    
    def _create_workflow(self):
        """LangGraph 워크플로우 생성"""
        # 워크플로우 그래프 생성
        workflow = StateGraph(InterrogationState)
        
        # 노드 추가
        workflow.add_node("check_interrogation_type", self.check_interrogation_type)
        
        # START에서 check_interrogation_type으로 가는 엣지 추가
        workflow.add_edge(START, "check_interrogation_type")
        
        # check_interrogation_type에서 END로 가는 엣지 추가
        workflow.add_edge("check_interrogation_type", END)
        
        # 컴파일
        return workflow.compile()
    
    
    def process_interrogation(self,  messages: List[Dict], case_data: CaseData) -> InterrogationState:
        """심문 처리를 위한 메인 메서드
        
        Args:
            input_data: 입력 데이터 (질문, 대상 등)
            
        Returns:
            Dict: 처리 결과
        """

        self.state.messages = messages
        self.state.case_data = case_data
        # print(f"[DEBUG] 현재 케이스 데이터: {self.state.case_data}")
        # print(f"[DEBUG] 현재 상태: {self.state.messages}")
        result = ""

        result = self.workflow.invoke(self.state)
        
        # # 결과가 있으면 메시지 추가
        # if self.add_message_callback and "content" in result:
        #     self.add_message_callback("system", result["content"])
            
        return result
    
    # ===============================================
    # 노드 함수들
    # ===============================================
    
    def check_interrogation_type(self, state: InterrogationState) -> InterrogationState:
        """심문 유형을 확인하는 노드

        Args:
            state: 현재 상태
            
        Returns:
            InterrogationState: 업데이트된 상태
        """

        user_input = state.messages[-1]["content"]
        input_data = {profile.name: profile.type for profile in state.case_data.profiles}

        prompt = PromptTemplate.from_template("""
            당신은 법정 역할극을 조정하는 AI입니다. 사용자가 심문을 진행하려고 합니다.
            사용자 발언: {user_input}
            프로필 : {input_data}
            사용자가 요청하는 심문 유형을 선택하여 문자열로 출력하세요.
                                            
            1. 피고 - 예시출력 : defendant
            2. 목격자 - 예시출력 : witness
            3. 참고인 - 예시출력 : reference
                                              
            단 피해자는 심문할 수 없음. 만일 위 사례에 해당하지 않는다면 retry 라고 출력.
            
        """)

        chain = prompt | self.llm | StrOutputParser()
        result = chain.invoke({"user_input": user_input, "input_data": input_data})
        print(f"check_interrogation_type 결과 : {result}")

        state.current_profile = result

        return state
    
    
    
    """
    현재 재판장에는 
    
    """