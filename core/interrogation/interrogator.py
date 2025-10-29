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
    def set_case_data(cls) -> bool:
        from controller import CaseDataManager
        case_data = CaseDataManager.get_case_data()
        cls._case = case_data.case
        cls._profiles = case_data.profiles
        cls._evidence = case_data.evidences

    @classmethod
    def set_current_profile(cls, profile: Profile) -> None:
        """Profile 객체를 직접 설정 (권장)"""
        cls._current_profile = profile
        print(f"[Interrogator] 현재 심문 대상 설정: {profile.name} ({profile.type})")

    @classmethod
    def set_current_profile_by_name(cls, name: str) -> bool:
        """이름으로 Profile을 찾아 _current_profile에 설정"""
        if cls._profiles is None:
            print("[Interrogator] 에러: profiles가 로드되지 않았습니다.")
            return False

        for profile in cls._profiles:
            if profile.name == name:
                cls._current_profile = profile
                print(f"[Interrogator] 현재 심문 대상 설정: {profile.name} ({profile.type})")
                return True

        print(f"[Interrogator] 경고: '{name}' 이름의 Profile을 찾을 수 없습니다.")
        return False

    @classmethod
    def build_ask_chain(cls, question: str, profile : Profile):
        # Profile 정보를 구조화하여 프롬프트 생성
        formatted_prompt = f"""
당신은 재판에 참석한 {profile.type}입니다.

## 당신의 신상 정보
- 이름: {profile.name}
- 나이: {profile.age}세
- 성별: {profile.gender}
- 성격: {profile.personality}
- 출석 배경: {profile.context}

## 사건 개요
{cls._case.outline}

## 관련 증거
{cls._evidence.__str__()}

## 답변 지침
1. 당신의 성격({profile.personality})을 반영하여 답변하세요.
2. 당신의 출석 배경({profile.context})을 고려하여 답변하세요.
3. 알지 못하는 것은 솔직하게 "모른다"고 답변하세요.
4. 인간적이고 자연스럽게 답변하세요.
5. 답변은 2-3문장으로 간결하게 작성하세요.

## 질문
{question}

## 답변
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
