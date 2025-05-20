from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser, JsonOutputParser
from pydantic import BaseModel, Field
from typing import List, Dict, Callable
from controller import CaseDataManager
from data_models import CaseData, Profile, Evidence, Case
from langchain.prompts import PromptTemplate
from langgraph.graph import StateGraph, END, START
from langchain_core.runnables import RunnableLambda
from langchain.memory import ConversationBufferMemory
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage
from langchain_core.runnables.history import RunnableWithMessageHistory
from enum import Enum

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

def get_llm(model="gpt-4.1-nano", temperature=0.3):
    llm = ChatOpenAI(model=model, temperature=temperature)  
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

_TYPE = {
    "defendant": "피고인",
    "witness": "증인", 
    "reference": "참고인"
}



class InterrogationState(BaseModel):
    """심문 상태를 나타내는 모델"""
    case_summary: str = ""
    case_data: CaseData = Field(default_factory=lambda: CaseData(
        case=Case(outline="", behind=""),
        profiles=[],
        evidences=[]
    ))
    messages: List[Dict] = Field(default_factory=list)
    current_type : str = ""
    current_profile: Profile = None
    current_evidence: Evidence = None
    profiles: List[Profile] = Field(default_factory=list)
    evidences: List[Evidence] = Field(default_factory=list)
    

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
        self.add_message_callback = None  # 메시지 추가 콜백 함수
        
        # memory와 memory_chain 초기화
        self.memory = None
        self.memory_chain = None
        self.system_msg = None
        
        self._initialized = True
    
    
    
    def process_interrogation(self,  messages: List[Dict], case_data: CaseData) -> Dict:
        """심문 요청에 대한 처리를 위한 메서드
        
        Args:
            input_data: 입력 데이터 (질문, 대상 등)
            
        Returns:
            Dict: 처리 결과
        """

        self.state.messages = messages
        self.state.case_data = case_data
        self.state.evidences = self.state.case_data.evidences
        
        if self.state.case_data.profiles is None:
            self.state.case_summary = self.state.case_data.case.outline
            self.state.profiles = self.state.case_data.profiles

        return self.check_interrogation_type(self.state)
        



    
    # ===============================================
    # 노드 함수들
    # ===============================================



    def check_interrogation_type(self, state: InterrogationState) -> Dict:
        """심문 유형을 확인하는 노드

        Args:
            state: 현재 상태
            
        Returns:
            InterrogationState: 업데이트된 상태
        """
        message_list = []
        user_input = state.messages[-1]["content"]
        profile_data = {profile.name: profile.type for profile in state.case_data.profiles}
        print(f"[DEBUG] 현재 프로필 : {profile_data}")

        prompt = PromptTemplate.from_template("""
            당신은 법정 역할극을 조정하는 AI입니다. 사용자가 심문을 진행하려고 합니다.
            사용자 발언: {user_input}
            프로필 : {profile_data}
            
            사용자가 요청하는 심문 유형과 대상을 파악하여 JSON 형식으로 출력하세요. 
            사용자가 이름을 입력한 경우 프로필과 일치하는 이름인지 반드시 확인하세요.
            이름 출력은 오로지 프로필 `profile_data`의 name만을 출력하세요.
                                                
            1. 피고, 목격자 등 역할이 명시되어 있거나 이름이 일치하는 경우
                - 피고인 심문: "type": "defendant", "answer": "피고에 대한 심문을 진행하십시오."
                - 목격자 심문: "type": "witness", "answer": "목격자에 대한 심문을 진행하십시오."
                - 참고인 심문: "type": "reference", "answer": "참고인에 대한 심문을 진행하십시오."
                
            2. 피해자에 대한 심문을 요청하는 경우 
                - "type": "retry", "answer": "현재 재판에는 피고, 목격자, 참고인만이 출석해있습니다."
                                                
            3. 이름이 틀린 경우 
                - 오타로 예상됨: "type": "retry", "answer": "OOO 씨에 대해 얘기하시는 겁니까?"
                - 전혀 다른 이름 : "type": "retry", "answer": "그런 인물은 없습니다"
        """)

        # JSON 모드를 사용하는 LLM 생성
        llm = ChatOpenAI(
            model="gpt-4o-mini", 
            temperature=0.3,
            model_kwargs={"response_format": {"type": "json_object"}}
        )
        
        chain = prompt | llm | JsonOutputParser()
        result = chain.invoke({"user_input": user_input, "profile_data": profile_data})
        print(f"check_interrogation_type 결과 : {result.get('type')}, {result.get('answer')}")
        message = {     
            "role": "system",
            "content": result.get("answer")
        }

        current_type = result["type"]
        state.current_type = current_type
        state.current_profile = next((p for p in state.profiles if p.type == current_type), None)

        return message


    def setup_interrogation_context(self) -> Dict:
        # 사건 개요/인물/증거를 system 메시지로 딱 1회만 입력
        self.system_msg = SystemMessage(content=(
            f"사건 개요: {self.state.case_summary}\n"
            f"인물: {self.state.profiles}\n"
            f"증거: {self.state.evidences}\n"
            f"심문 대상: {self.state.current_profile}"
        ))

        #  memory 객체 초기화
        self.memory = ConversationBufferMemory(
            return_messages=True,
            memory_key="history"
        )

        # 대화 시작 질문 (항상 HumanMessage로)
        question = "자기 소개를 2~3줄로 간단하게 부탁합니다."

        # 프롬프트는 오직 {question}만!
        prompt = PromptTemplate.from_template("""
        {question}
        """)

        # runnable chain: (question -> 답변)
        base_chain = prompt | get_llm() | StrOutputParser()

        # memory-chain 설정 (session_id 제거)
        self.memory_chain = base_chain

        # 첫 history만 세팅: system message + 자기소개 질문
        history = [self.system_msg, HumanMessage(content=question)]

        # memory에 수동으로 기록
        self.memory.chat_memory.messages = history

        # 첫 답변 생성
        answer = self.memory_chain.invoke({
            "question": question
        })

        return {
            "role": _TYPE.get(self.state.current_type),
            "content": answer
        }


    def interrogate_witness(self, question: str) -> Dict:
        """참고인(혹은 대상)의 답변 생성 (질문 처리)"""
        # 메모리에 질문 추가
        self.memory.chat_memory.add_user_message(question)
        
        # 답변 생성
        answer = self.memory_chain.invoke({
            "question": question
        })
        
        # 메모리에 답변 추가
        self.memory.chat_memory.add_ai_message(answer)

        # 메시지 기록 추가
        self.state.messages.append({"role": "reference", "content": answer})

        return {
            "role": "reference",
            "content": answer
        }
