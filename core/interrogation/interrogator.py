from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate, PromptTemplate
from langchain_core.output_parsers import StrOutputParser, JsonOutputParser
from data_models import CaseData, Case, Profile, Evidence
from typing import List, Dict, Optional


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

def get_llm(model="gpt-4o-mini", temperature=0.3):
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
# Interrogator 클래스

class Interrogator:
    _instance = None
    _initialized = False
    
    _evidences : Evidence = None
    _case : str = None
    _profiles : List[Profile] = None
    _role = None
    _current_profile : Profile = None
    llm = get_llm("gpt-4o-mini", temperature=0.5)  # 기본 LLM 설정
    chat_prompt = ChatPromptTemplate.from_template("""
                당신은 재판에 참석한 {role}입니다.
                당신의 역할은 사건에 대한 질문에 인간적으로 답변하는 것입니다.
                사건 개요: {case}
                당신의 정보 : {profile}
                증거 : {evidence}
                질문: {question}
                                                             
                답변:
            """)

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(Interrogator, cls).__new__(cls)
        return cls._instance

    def __init__(self):
        if not self._initialized:
            Interrogator._initialized = True
    
    @classmethod
    def get_instance(cls):
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance
    
    @classmethod
    def set_case_data(cls, case_data: CaseData) -> bool:
        cls._case = case_data.case
        cls._profiles = case_data.profiles
        cls._evidence = case_data.evidences
        return True

    @classmethod
    def build_ask_chain(cls, question: str, profile : Profile):
        # 모든 변수를 미리 포맷팅된 텍스트로 준비
        formatted_prompt = f"""
                당신은 재판에 참석한 {profile.type}입니다.
                당신의 역할은 사건에 대한 질문에 인간적으로 답변하는 것입니다.
                사건 개요: {cls._case.outline}
                당신의 정보 : {profile.__str__()}
                증거 : {cls._evidence.__str__()}
                질문: {question}
                                                             
                답변:
            """
        
        # 단순한 프롬프트 템플릿 생성
        prompt = ChatPromptTemplate.from_template(formatted_prompt)
        cls.llm = get_llm()
        chain = prompt | cls.llm | StrOutputParser()
        
        return chain
    
    @classmethod
    def check_request(cls, user_input: str) -> Optional[Dict]:
        """사용자의 심문 요청을 분석하여 JSON 형식으로 반환합니다."""
        prompt = PromptTemplate.from_template("""
        당신은 법정 역할극을 조정하는 AI입니다. 사용자가 심문을 진행하려고 합니다.
        사용자 발언: {user_input}
        프로필 : {profile_data}
        
        사용자가 요청하는 심문 유형과 대상을 파악하여 JSON 형식으로 출력하세요. 
        사용자가 이름을 입력한 경우 프로필과 일치하는 이름인지 반드시 확인하세요.
        이름 출력은 오로지 프로필에 있는 이름만을 출력하세요.
                                            
        1. 피고, 피해자, 목격자, 참고인 등 역할이 명시되어 있거나 이름이 일치하는 경우
            - 피고인 심문: {{"type": "defendant", "answer": "피고에 대한 심문을 진행하십시오."}}
            - 피해자 심문: {{"type": "victim", "answer": "피해자에 대한 심문을 진행하십시오."}}
            - 목격자 심문: {{"type": "witness", "answer": "목격자에 대한 심문을 진행하십시오."}}
            - 참고인 심문: {{"type": "reference", "answer": "참고인에 대한 심문을 진행하십시오."}}
                                            
        2. 이름이 틀린 경우 
            - 오타로 예상됨: {{"type": "retry", "answer": "OOO 씨에 대해 얘기하시는 겁니까?"}}
            - 전혀 다른 이름 : {{"type": "retry", "answer": "그런 인물은 없습니다"}}
        """)

        llm = get_llm()
        chain = prompt | llm | JsonOutputParser()
        result = chain.invoke({"profile_data": cls._profiles.__str__(), "user_input": user_input})
        type = result.get("type")

        if type != "retry":
            # 심문 요청이 유효한 경우, 프로필 리스트에서 해당 타입과 일치하는 프로필 찾기
            target_profile = None
            
            # 사용자가 이름을 직접 언급했는지 확인
            for profile in cls._profiles:
                if profile.name in user_input:
                    target_profile = profile
                    break
            
            # 이름이 없으면 타입으로 찾기
            if not target_profile:
                for profile in cls._profiles:
                    if profile.type == type:
                        target_profile = profile
                        break
            
            cls._current_profile = target_profile

        return result


# 싱글톤 인스턴스 생성
    
it = Interrogator()
