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

#=============기존 코드 보관========================
#========================================(테스트종료후 복구)
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

def format_gender(gender: str) -> str:
    return "남성" if gender == "남자" else "여성"

def build_case_chain(selected_characters: List[Dict]):
    """
    선택된 캐릭터를 사용하여 사건 개요 생성을 위한 LLM 체인 반환.
    """
    # 캐릭터 정보 템플릿 변수에 개별적으로 매핑
    # 순서: 피고(0), 피해자(1), 목격자(2), 참고인(3)
    character_roles = {
        "피고_이름": selected_characters[0]['name'],
        "피고_나이": selected_characters[0]['age'],
        "피고_성별": format_gender(selected_characters[0]['gender']),
        
        "피해자_이름": selected_characters[1]['name'],
        "피해자_나이": selected_characters[1]['age'],
        "피해자_성별": format_gender(selected_characters[1]['gender']),
        
        "목격자_이름": selected_characters[2]['name'],
        "목격자_나이": selected_characters[2]['age'],
        "목격자_성별": format_gender(selected_characters[2]['gender']),
        
        "참고인_이름": selected_characters[3]['name'],
        "참고인_나이": selected_characters[3]['age'],
        "참고인_성별": format_gender(selected_characters[3]['gender']),
    }

    formatted_template = CASE_SUMMARY_TEMPLATE.format(**character_roles)
    llm = get_llm()
    prompt = ChatPromptTemplate.from_template(formatted_template)
    chain = prompt | llm | StrOutputParser()

    return chain



# ----기존 케이스 빌드---------
# 사건 개요 생성을 위한 체인을 반환하는 함수
# def build_case_chain():
#     llm = get_llm() # 모델선택 / 온도설정
#     prompt = ChatPromptTemplate.from_template(CASE_SUMMARY_TEMPLATE)
#     chain = prompt | llm | StrOutputParser()
#     return chain

# 등장 인물 생성 | 매개 변수 case_summary(str)


def build_character_chain(case_summary: str, selected_characters: List[Dict]):
    """
    사건 개요를 기반으로 인물 소개 생성 체인 반환.
    """
    # 캐릭터 정보 템플릿 변수에 개별적으로 매핑
    template_vars = {
        "case_summary": case_summary,
        
        "피고_이름": selected_characters[0]['name'],
        "피고_나이": selected_characters[0]['age'],
        "피고_성별": format_gender(selected_characters[0]['gender']),
        
        "피해자_이름": selected_characters[1]['name'],
        "피해자_나이": selected_characters[1]['age'],
        "피해자_성별": format_gender(selected_characters[1]['gender']),
        
        "목격자_이름": selected_characters[2]['name'],
        "목격자_나이": selected_characters[2]['age'],
        "목격자_성별": format_gender(selected_characters[2]['gender']),
        
        "참고인_이름": selected_characters[3]['name'],
        "참고인_나이": selected_characters[3]['age'],
        "참고인_성별": format_gender(selected_characters[3]['gender']),
    }
    
    formatted_template = CHARACTER_TEMPLATE.format(**template_vars)
    llm = get_llm(temperature=0.7)
    prompt = ChatPromptTemplate.from_template(formatted_template)
    chain = prompt | llm | StrOutputParser()
    return chain

# ---------------------------- 사건의 진실 체인 ----------------------------

def build_case_behind_chain(case_summary: str, character: str, selected_characters: List[Dict]):
    """
    사건 개요와 특정 인물을 바탕으로 사건의 진실을 생성하는 체인.
    """
    # 템플릿 변수 준비
    template_vars = {
        "case_summary": case_summary,
        "character": character,
        
        "피고_이름": selected_characters[0]['name'],
        "피고_나이": selected_characters[0]['age'],
        "피고_성별": format_gender(selected_characters[0]['gender']),
        
        "피해자_이름": selected_characters[1]['name'],
        "피해자_나이": selected_characters[1]['age'],
        "피해자_성별": format_gender(selected_characters[1]['gender']),
        
        "목격자_이름": selected_characters[2]['name'],
        "목격자_나이": selected_characters[2]['age'],
        "목격자_성별": format_gender(selected_characters[2]['gender']),
        
        "참고인_이름": selected_characters[3]['name'],
        "참고인_나이": selected_characters[3]['age'],
        "참고인_성별": format_gender(selected_characters[3]['gender']),
    }
    
    formatted_template = CASE_BEHIND_TEMPLATE.format(**template_vars)
    llm = get_llm(temperature=0.5)
    prompt = ChatPromptTemplate.from_template(formatted_template)
    chain = prompt | llm | StrOutputParser()
    return chain

# ===================================================
# ============================================여기까지 기존코드

# 테스트 코드 (컨트롤러 호출 예시) 
if __name__ == "__main__":
    story = {} # 사건 개요 저장
    
    # 캐릭터를 한 번만 선택
    selected_characters = select_random_characters(4)
    print("=== 선택된 캐릭터 정보 ===")
    for i, char in enumerate(selected_characters):
        role = ["피고", "피해자", "증인1", "증인2"][i]
        print(f"{role}: {char['name']}, 나이: {char['age']}, 성별: {char['gender']}")
    print("============================\n")
    
    # 1. 사건 개요 생성
    print("사건 개요 생성 중...\n")
    case_summary_chain = build_case_chain(selected_characters)
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
    character_chain = build_character_chain(case_summary, selected_characters)
    character = character_chain.invoke({})
    print(character)
    
    
    print('\n\n---------------')
    # 사건의 진실 생성
    print("사건의 진실 생성 중...\n")

    case_truth = ""
    for chunk in build_case_behind_chain(case_summary, character, selected_characters).stream({}):
        if hasattr(chunk, 'content'):
            print(chunk.content, end='', flush=True)
            case_truth += chunk.content
        else:
            print(chunk, end='', flush=True)
            case_truth += chunk