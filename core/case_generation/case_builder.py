import json
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from core.data_models import CaseData, Case, Profile, Evidence

from dotenv import load_dotenv
load_dotenv()

#==============================================
# 템플릿 갈아끼면 쉽게 사용 가능
# username_case_templates.py 와 같은 형식으로 사용 가능
#============================================== 
# from .prompt_templates.gunrein_case_templates import (
#     CASE_SUMMARY_TEMPLATE,
#     WITNESS_PROFILES_TEMPLATE,
# )

from .prompt_templates.ex_case_templates import (
    CASE_SUMMARY_TEMPLATE,
    CREATE_CHARACTER_TEMPLATE,
    CASE_BEHIND_TEMPLATE,
)


# def get_llm(model="gpt-4o"):
def get_llm(model="gpt-4o-mini", temperature=1.0):
    llm = ChatOpenAI(model=model, temperature=temperature)  
    """    
    temperature 값의 의미:
    0: 가장 결정적이고 예측 가능한 응답 (항상 가장 가능성이 높은 토큰 선택)
    0.7: ChatGPT의 기본값 (적당한 창의성과 안정성)
    ~1.0 : 창의적이지만 안정성 떨어짐
    """
    return llm

def get_case_summary_chain():
    """사건 개요 생성을 위한 체인을 반환하는 함수
    """
    llm = get_llm(model="gpt-4o-mini", temperature=1.0) # 모델선택 / 온도설정
    prompt = ChatPromptTemplate.from_template(CASE_SUMMARY_TEMPLATE)
    chain = prompt | llm | StrOutputParser()
    return chain

def get_character_chain():
    """등장인물 생성을 위한 체인을 반환하는 함수"""
    llm = get_llm(model="gpt-4o-mini", temperature=0.7) # 모델선택 / 온도설정
    prompt = ChatPromptTemplate.from_template(CREATE_CHARACTER_TEMPLATE)
    chain = prompt | llm | StrOutputParser()
    return chain

def get_case_truth_chain():
    """사건의 진실(내막)을 생성하는 체인"""
    llm = get_llm(model="gpt-4o-mini", temperature=0.5) # 모델선택 / 온도설정
    prompt = ChatPromptTemplate.from_template(CASE_BEHIND_TEMPLATE)
    chain = prompt | llm | StrOutputParser()
    return chain


""" 테스트 코드 (컨트롤러 호출 예시) """
if __name__ == "__main__":
    """ 사건 개요 생성 테스트 """
    story = {} # 사건 개요 저장
    
    # 1. 사건 개요 생성
    print("사건 개요 생성 중...\n")
    case_summary_chain = get_case_summary_chain()
    case_summary = ""
    
    # 스트리밍으로 사건 개요 생성
    for chunk in case_summary_chain.stream({}):
        if hasattr(chunk, 'content'):
            print(chunk.content, end='', flush=True)
            case_summary += chunk.content
        else:
            print(chunk, end='', flush=True)
            case_summary += chunk

    print('\n\n---------------')  
    
    """ 등장인물 추출 테스트 """
    character_chain = get_character_chain()
    character = character_chain.invoke({"case_summary": case_summary})
    print(character)
    
    
    print('\n\n---------------')
    # 사건의 진실 생성
    print("사건의 진실 생성 중...\n")
    case_truth_chain = get_case_truth_chain()
    case_truth = ""
    
    # 스트리밍으로 사건의 진실 생성
    for chunk in case_truth_chain.stream({
        "case_summary": case_summary,
        "character": character
    }):
        if hasattr(chunk, 'content'):
            print(chunk.content, end='', flush=True)
            case_truth += chunk.content
        else:
            print(chunk, end='', flush=True)
            case_truth += chunk

    