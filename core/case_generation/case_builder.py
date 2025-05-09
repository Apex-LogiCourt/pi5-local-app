import json
import random
from pathlib import Path
from typing import List, Dict, Tuple
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser

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
    CHARACTER_TEMPLATE,
    CASE_BEHIND_TEMPLATE,
)

def get_llm(model="gpt-4o-mini", temperature=1.0):
    llm = ChatOpenAI(model=model, temperature=temperature)  
    return llm

#----------------------------
def load_characters() -> List[Dict]:
    """profil.json에서 캐릭터 정보를 로드"""
    profile_path = Path(__file__).parent.parent / "assets" / "profile" / "profil.json"
    with open(profile_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    return data['characters']

def select_random_characters(num_characters: int = 4) -> List[Dict]:
    """지정 수의 캐릭터 랜덤 선택"""
    characters = load_characters()
    return random.sample(characters, num_characters)

# ---------------------------- 사건 요약 체인 ----------------------------

def build_case_chain() -> Tuple[object, Dict[str, str]]:
    """
    캐릭터를 랜덤 선택하고, 사건 개요 생성을 위한 LLM 체인과 역할 정보를 반환.
    """
    selected_characters = select_random_characters(4)

    # 역할 매핑
    character_roles = {
        "피고": selected_characters[0]['name'],
        "피해자": selected_characters[1]['name'],
        "증인1": selected_characters[2]['name'],
        "증인2": selected_characters[3]['name'],
    }

    # 템플릿 포맷팅
    formatted_template = CASE_SUMMARY_TEMPLATE.format(**character_roles)

    # 체인 구성
    llm = get_llm()
    prompt = ChatPromptTemplate.from_template(formatted_template)
    chain = prompt | llm | StrOutputParser()

    return chain, character_roles



# ----기존 케이스 빌드---------
# 사건 개요 생성을 위한 체인을 반환하는 함수
# def build_case_chain():
#     llm = get_llm() # 모델선택 / 온도설정
#     prompt = ChatPromptTemplate.from_template(CASE_SUMMARY_TEMPLATE)
#     chain = prompt | llm | StrOutputParser()
#     return chain

# 등장 인물 생성 | 매개 변수 case_summary(str)


def build_character_chain(case_summary: str):
    """
    사건 개요를 기반으로 인물 소개 생성 체인 반환.
    """
    formatted_template = CHARACTER_TEMPLATE.format(case_summary=case_summary)
    llm = get_llm(temperature=0.7)
    prompt = ChatPromptTemplate.from_template(formatted_template)
    chain = prompt | llm | StrOutputParser()
    return chain

# ---------------------------- 사건의 진실 체인 ----------------------------

def build_case_behind_chain(case_summary: str, character: str):
    """
    사건 개요와 특정 인물을 바탕으로 사건의 진실을 생성하는 체인.
    """
    formatted_template = CASE_BEHIND_TEMPLATE.format(
        case_summary=case_summary,
        character=character
    )
    llm = get_llm(temperature=0.5)
    prompt = ChatPromptTemplate.from_template(formatted_template)
    chain = prompt | llm | StrOutputParser()
    return chain


# 테스트 코드 (컨트롤러 호출 예시) 
# if __name__ == "__main__":
#     story = {} # 사건 개요 저장
    
#     # 1. 사건 개요 생성
#     print("사건 개요 생성 중...\n")
#     case_summary_chain = build_case_chain()
#     case_summary = ""
    
#     # 스트리밍으로 사건 개요 생성
#     for chunk in case_summary_chain.stream({}):
#         if hasattr(chunk, 'content'):
#             print(chunk.content, end='', flush=True)
#             case_summary += chunk.content
#         else:
#             print(chunk, end='', flush=True)
#             case_summary += chunk

#     print('\n\n---------------')  
    
#     # 등장인물 추출 테스트
#     character_chain = build_character_chain(case_summary)
#     character = character_chain.invoke({})
#     print(character)
    
    
#     print('\n\n---------------')
#     # 사건의 진실 생성
#     print("사건의 진실 생성 중...\n")

#     case_truth = ""
#     for chunk in build_case_behind_chain(case_summary, character).stream({}):
#         if hasattr(chunk, 'content'):
#             print(chunk.content, end='', flush=True)
#             case_truth += chunk.content
#         else:
#             print(chunk, end='', flush=True)
#             case_truth += chunk

    