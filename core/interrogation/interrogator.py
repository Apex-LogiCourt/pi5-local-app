from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from core.data_models import CaseData, Case, Profile, Evidence
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
    _profile : Profile = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(Interrogator, cls).__new__(cls)
        return cls._instance

    def __init__(self):
        if not self._initialized:
            self.llm = get_llm()
            self.chat_prompt = ChatPromptTemplate.from_template("""
                당신은 재판에 참석한 {role}입니다.
                당신의 역할은 사건에 대한 질문에 인간적으로 답변하는 것입니다.
                사건 개요: {case}
                당신의 정보 : {profile}
                증거 : {evidence}
                질문: {question}
                                                             
                답변:
            """)
            self.output_parser = StrOutputParser()
            Interrogator._initialized = True
    
    @classmethod
    def get_instance(cls):
        """싱글톤 인스턴스를 반환합니다."""
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance
    
    @classmethod
    def set_case_data(cls) -> bool:
        """CaseData 객체를 설정합니다."""
        from core.controller import Controller
        case_data = Controller.get_case_data()
        cls._case = case_data.case
        cls._profiles = case_data.profiles
        cls._evidence = case_data.evidences

    def build_ask_chain(self, question: str, profile : Profile):
        """질문과 역할에 따라 체인을 구축합니다."""
        prompt = self.chat_prompt.format(role=profile.type, case=self._case.outline, 
            profile=profile.__str__(), evidence=self._evidence.__str__(), question=question)
        self.llm = get_llm()
        chain = prompt | self.llm | self.output_parser
        return chain
    
it = Interrogator()