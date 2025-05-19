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
        # self.workflow = self._create_workflow()
        self.add_message_callback = None  # 메시지 추가 콜백 함수
        self._initialized = True
    
    def set_message_callback(self, callback: Callable[[str, str], None]):
        """메시지 추가 콜백 함수를 설정합니다.
        
        Args:
            callback: 메시지를 추가하는 함수 (role: str, content: str) -> None
        """
        self.add_message_callback = callback
    
    # def _create_workflow(self):
    #     """LangGraph 워크플로우 생성"""
    #     # 워크플로우 그래프 생성
    #     workflow = StateGraph(InterrogationState)
        
    #     # 노드 추가
    #     workflow.add_node("check_interrogation_type", self.check_interrogation_type)
        
    #     # START에서 check_interrogation_type으로 가는 엣지 추가
    #     workflow.add_edge(START, "check_interrogation_type")
        
    #     # check_interrogation_type에서 END로 가는 엣지 추가
    #     workflow.add_edge("check_interrogation_type", END)
        
    #     # 컴파일
    #     return workflow.compile()
    
    
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



    def check_interrogation_type(self, state: InterrogationState) -> List[Dict]:
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
        message_list.append(message)

        if result.get("retry"):
            return message_list
        else :
            current_type = result.get("type")
            state.current_type = current_type
            state.current_profile = next((p for p in state.profiles if p.type == result.get("type")), None)
            prompt = PromptTemplate.from_template("""
                당신은 이 사건에 {current_type}로 출석한 인물입니다.
                사건 개요: {case_summary}
                사건 인물: {profiles}
                사건 증거: {evidences}
                                                    
                당신은 정보는 이렇습니다 {current_profile}            
                자기 소개를 2~3줄로 간단하게 부탁합니다           
            """)
            
            chain = prompt | get_llm() | StrOutputParser()
            answer = chain.invoke({
                "current_type": current_type,
                "case_summary": state.case_summary,
                "profiles": state.profiles,
                "evidences": state.evidences,
                "current_profile": state.current_profile
            })
            message = {
                "role": _TYPE.get(current_type),
                "content": answer
            }
        return message_list + [message]
    

    def setup_interrogation_context(self, state: InterrogationState, result: dict) -> Dict:
        current_type = result["type"]
        state.current_type = current_type
        state.current_profile = next((p for p in state.profiles if p.type == current_type), None)

        prompt = PromptTemplate.from_template("""
            당신은 이 사건에 {current_type}로 출석한 인물입니다.
            사건 개요: {case_summary}
            사건 인물: {profiles}
            사건 증거: {evidences}

            당신은 정보는 이렇습니다: {current_profile}
            자기 소개를 2~3줄로 간단하게 부탁합니다
        """)

        # ✅ RunnableWithMessageHistory 적용
        base_chain = prompt | get_llm() | StrOutputParser()

        memory = ConversationBufferMemory(
            return_messages=True,
            memory_key="history"
        )

        from langchain_core.runnables.history import RunnableWithMessageHistory
        memory_chain = RunnableWithMessageHistory(
            base_chain,
            lambda session_id: memory,
            input_messages_key="current_profile",  # context든 뭐든 일치시켜야 함
            history_messages_key="history"
        )

        # chain.invoke 대신 runnable 사용
        answer = memory_chain.invoke({
            "current_type": current_type,
            "case_summary": state.case_summary,
            "profiles": state.profiles,
            "evidences": state.evidences,
            "current_profile": state.current_profile
        }, config={"configurable": {"session_id": state.session_id}})

        return {
            "role": _TYPE.get(current_type),
            "content": answer
        }

    
    # def check_interrogation_type(self, state: InterrogationState) -> InterrogationState:
    #     """심문 유형을 확인하는 노드

    #     Args:
    #         state: 현재 상태
            
    #     Returns:
    #         InterrogationState: 업데이트된 상태
    #     """

    #     user_input = state.messages[-1]["content"]
    #     profile_data = {profile.name: profile.type for profile in state.case_data.profiles}
    #     print(f"[DEBUG] 현재 프로필 : {profile_data}")

    #     prompt = PromptTemplate.from_template("""
    #         당신은 법정 역할극을 조정하는 AI입니다. 사용자가 심문을 진행하려고 합니다.
    #         사용자 발언: {user_input}
    #         프로필 : {profile_data}
            
    #         사용자가 요청하는 심문 유형과 대상을 파악하여 JSON 형식으로 출력하세요. 
    #         사용자가 이름을 입력한 경우 프로필과 일치하는 이름인지 반드시 확인하세요.
    #         이름 출력은 오로지 프로필 `profile_data`의 name만을 출력하세요.
                                              
    #         1. 피고, 목격자 등 역할이 명시되어 있거나 이름이 일치하는 경우
    #             - 피고인 심문: "type": "defendant", "answer": "피고에 대한 심문을 진행하십시오."
    #             - 목격자 심문: "type": "witness", "answer": "목격자에 대한 심문을 진행하십시오."
    #             - 참고인 심문: "type": "reference", "answer": "참고인에 대한 심문을 진행하십시오."
                
    #         2. 피해자에 대한 심문을 요청하는 경우 
    #             - "type": "retry", "answer": "현재 재판에는 피고, 목격자, 참고인만이 출석해있습니다."
                                              
    #         3. 이름이 틀린 경우 
    #             - 오타로 예상됨: "type": "retry", "answer": "OOO 씨에 대해 얘기하시는 겁니까?"
    #             - 전혀 다른 이름 : "type": "retry", "answer": "그런 인물은 없습니다"
    #     """)

    #     # JSON 모드를 사용하는 LLM 생성
    #     llm = ChatOpenAI(
    #         model="gpt-4o-mini", 
    #         temperature=0.3,
    #         model_kwargs={"response_format": {"type": "json_object"}}
    #     )
        
    #     chain = prompt | llm | JsonOutputParser()
    #     result = chain.invoke({"user_input": user_input, "profile_data": profile_data})
    #     print(f"check_interrogation_type 결과 : {result.get('type')}, {result.get('answer')}")

    #     if result.get("retry"):
    #         # 재시도 요청
    #         state.messages.append({"role": "system", "content": result.get("answer")})
    #         self.set_message_callback("system", result.get("answer"))
    #         return state
    #     else :
    #         current_type = result.get("type")
    #         state.current_type = current_type
    #         proflies = state.case_data.profiles
    #         current_profile = next((p for p in proflies if p.type == result.get("type")), None)
    #         prompt = PromptTemplate.from_template("""
    #             당신은 이 사건에 {current_type}로 출석한 인물입니다.
    #             사건 개요: {case_summary}
    #             사건 인물: {profiles}
    #             사건 증거: {evidences}
                                                  
    #             당신은 정보는 이렇습니다 {current_profile}            
    #             자기 소개를 부탁합니다           
    #         """)
        
    #     return state


    def interrogate_witness(state: InterrogationState) -> InterrogationState:
        """참고인의 답변 생성 (질문 처리)"""
        last_question = state.messages[-1]['content']
        case = state.case_data

        context = f"사건 개요: {case.case.outline}\n\n" + \
                f"인물 목록: {[f'{p.name}({p.type})' for p in case.profiles]}"

        prompt = PromptTemplate.from_template("""
        다음은 참고인에 대한 심문입니다.
        사건 정보: {context}
        질문: {question}

        참고인의 자연스러운 답변을 생성하세요.
        """)
        chain = prompt | get_llm() | StrOutputParser()
        answer = chain.invoke({"question": last_question, "context": context})

        state.messages.append({"role": "reference", "content": answer})
        return state


    
    
    
    """
    현재 재판장에는 
    
    """