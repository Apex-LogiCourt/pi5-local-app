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

def get_llm(model="gpt-4o-mini", temperature=1.0):
    llm = ChatOpenAI(model=model, temperature=temperature)  
    return llm

# 사건 개요 생성을 위한 체인을 반환하는 함수
def get_case_summary_chain():
    llm = get_llm(model="gpt-4o-mini", temperature=1.0) # 모델선택 / 온도설정
    prompt = ChatPromptTemplate.from_template(CASE_SUMMARY_TEMPLATE)
    chain = prompt | llm | StrOutputParser()
    return chain

# 등장 인물 생성 | 매개 변수 case_summary(str)
def get_character_chain(case_summary: str):
    llm = get_llm(model="gpt-4o-mini", temperature=0.7) # 모델선택 / 온도설정
    formatted_template = CREATE_CHARACTER_TEMPLATE.format(case_summary=case_summary)
    prompt = ChatPromptTemplate.from_template(formatted_template)
    chain = prompt | llm | StrOutputParser()
    return chain

# 사건의 진실(내막) 생성 | 매개 변수 case_summary(str), character(str)
def get_case_truth_chain(case_summary: str, character: str):
    llm = get_llm(model="gpt-4o-mini", temperature=0.5) # 모델선택 / 온도설정
    formatted_template = CASE_BEHIND_TEMPLATE.format(case_summary=case_summary, character=character)
    prompt = ChatPromptTemplate.from_template(formatted_template)
    chain = prompt | llm | StrOutputParser()
    return chain


# 테스트 코드 (컨트롤러 호출 예시) 
if __name__ == "__main__":
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
    
    # 등장인물 추출 테스트
    character_chain = get_character_chain(case_summary)
    character = character_chain.invoke({})
    print(character)
    
    
    print('\n\n---------------')
    # 사건의 진실 생성
    print("사건의 진실 생성 중...\n")

    case_truth = ""
    for chunk in get_case_truth_chain(case_summary, character).stream({}):
        if hasattr(chunk, 'content'):
            print(chunk.content, end='', flush=True)
            case_truth += chunk.content
        else:
            print(chunk, end='', flush=True)
            case_truth += chunk

    